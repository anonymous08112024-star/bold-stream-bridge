import os
import asyncio
from aiohttp import web
from pyrogram import Client

# Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
PORT = int(os.environ.get("PORT", "10000"))
PUBLIC_URL = os.environ.get("PUBLIC_URL", "")

if not BOT_TOKEN or not API_ID or not API_HASH:
    raise ValueError("CRITICAL ERROR: BOT_TOKEN, API_ID, or API_HASH environment variable is missing!")

# Initialize Pyrogram Client as Bot
bot = Client("bold_stream_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def handle_root(request):
    return web.Response(text="Bold Cinema Hub Stream Bridge (MTProto Mode) is Live!", status=200)

async def handle_stream(request):
    message_id = request.match_info.get("msg_id")
    chat_id = request.query.get("chat_id")
    
    if not chat_id or not message_id:
        return web.Response(text="Missing chat_id or msg_id parameter", status=400)
        
    try:
        msg_id_int = int(message_id)
        chat_id_int = int(chat_id)
        
        # Fetch message metadata directly using Pyrogram client
        msg = await bot.get_messages(chat_id_int, msg_id_int)
        media = msg.video or msg.document or msg.audio
        
        if not media:
            return web.Response(text="No media found in the requested message", status=404)
            
        file_size = media.file_size
        mime_type = getattr(media, 'mime_type', 'video/x-matroska') or 'video/x-matroska'
        file_name = getattr(media, 'file_name', 'video.mkv') or 'video.mkv'

        # Build HTTP headers for Smart TV player compatibility
        headers = {
            'Content-Type': mime_type,
            'Content-Length': str(file_size),
            'Accept-Ranges': 'bytes',
            'Content-Disposition': f'inline; filename="{file_name}"'
        }
        
        response = web.StreamResponse(status=200, headers=headers)
        await response.prepare(request)
        
        # Stream chunks directly from Telegram datacenters
        async for chunk in bot.stream_media(msg):
            await response.write(chunk)
            
        return response

    except Exception as e:
        return web.Response(text=f"Streaming error: {str(e)}", status=500)

async def start_services():
    print("Starting Telegram Bot Client...")
    await bot.start()
    
    # Automatically sync dialogs on startup so all private channels/supergroups are cached in session storage
    print("Syncing Telegram dialogs to populate peer cache...")
    try:
        async for dialog in bot.get_dialogs():
            pass
        print("Dialog sync complete. All peers cached successfully.")
    except Exception as e:
        print(f"Dialog sync warning: {e}")
    
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/stream/{msg_id}', handle_stream)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"=== Web service bound successfully on port {PORT} ===")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
    loop.run_forever()
