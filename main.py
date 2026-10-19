import os
import asyncio
from aiohttp import web

# Fetch Environment Variables from Render
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "10000"))
PUBLIC_URL = os.environ.get("PUBLIC_URL", "")

if not BOT_TOKEN:
    raise ValueError("CRITICAL ERROR: BOT_TOKEN Environment Variable is missing!")

# Web Server Handlers
async def handle_root(request):
    return web.Response(text="Bold Cinema Hub Stream Bridge is Live!", status=200)

async def handle_stream(request):
    message_id = request.match_info.get("msg_id")
    chat_id = request.query.get("chat_id")
    
    if not chat_id:
        return web.Response(text="Missing chat_id parameter", status=400)
        
    try:
        # Fetch file details directly using pure Telegram Bot API (No API_ID/API_HASH needed)
        async with aiohttp.ClientSession() as session:
            get_msg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/forwardMessage" # Or use getChat / getMessage via Bot API
            # For direct file downloading via Bot API:
            file_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat?chat_id={chat_id}"
            
        return web.Response(text="Stream bridge active. Use direct file proxy.", status=200)
    except Exception as e:
        return web.Response(text=f"Streaming error: {str(e)}", status=500)

async def start_services():
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
