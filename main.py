import os
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message

# Fetch Environment Variables from Zeabur
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", "6"))
API_HASH = os.environ.get("API_HASH", "eb06d4abfb49d3eeb1a5780f2524d262")
PORT = int(os.environ.get("PORT", 8080))
PUBLIC_URL = os.environ.get("PUBLIC_URL", "http://localhost:8080")

# Initialize Pyrogram Bot Client
bot = Client("bold_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Web Server Handlers
async def handle_root(request):
    return web.Response(text="Bold Cinema Hub Stream Bridge is Online!", status=200)

async def handle_stream(request):
    message_id = int(request.match_info.get("msg_id"))
    chat_id = request.query.get("chat_id")
    
    if not chat_id:
        return web.Response(text="Missing chat_id parameter", status=400)
        
    try:
        msg = await bot.get_messages(int(chat_id), message_id)
        media = msg.video or msg.document
        if not media:
            return web.Response(text="Media not found", status=404)
            
        file_size = media.file_size
        
        # Prepare streaming response headers
        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': media.mime_type or 'video/x-matroska',
                'Content-Length': str(file_size),
                'Accept-Ranges': 'bytes',
                'Content-Disposition': f'inline; filename="{media.file_name or "video.mkv"}"'
            }
        )
        await response.prepare(request)
        
        # Stream file chunks directly from Telegram to user browser
        async for chunk in bot.stream_media(msg):
            await response.write(chunk)
            
        return response
    except Exception as e:
        return web.Response(text=f"Streaming error: {str(e)}", status=500)

# Telegram Bot Handlers
@bot.on_message(filters.private & (filters.video | filters.document))
async def generate_link(client, message: Message):
    chat_id = message.chat.id
    msg_id = message.id
    stream_link = f"{PUBLIC_URL.rstrip('/')}/stream/{msg_id}?chat_id={chat_id}"
    
    reply_text = (
        f"🎬 **Stream Link Generated!**\n\n"
        f"🔗 **URL:** `{stream_link}`\n\n"
        f"Open this link on your Smart TV browser or paste it into your Mini App catalog."
    )
    await message.reply_text(reply_text)

# Main Application Entry Point
async def main():
    await bot.start()
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/stream/{msg_id}', handle_stream)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"Server started on port {PORT}")
    
    # Keep server running concurrently
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
