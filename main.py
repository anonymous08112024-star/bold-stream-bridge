import os
import asyncio
import aiohttp
from aiohttp import web

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "10000"))
PUBLIC_URL = os.environ.get("PUBLIC_URL", "")

if not BOT_TOKEN:
    raise ValueError("CRITICAL ERROR: BOT_TOKEN Environment Variable is missing!")

async def handle_root(request):
    return web.Response(text="Bold Cinema Hub Stream Bridge is Live!", status=200)

async def handle_stream(request):
    message_id = request.match_info.get("msg_id")
    chat_id = request.query.get("chat_id")
    
    if not chat_id or not message_id:
        return web.Response(text="Missing chat_id or msg_id parameter", status=400)
        
    try:
        async with aiohttp.ClientSession() as session:
            # 1. Forward/Copy message to fetch media payload & file_id
            copy_url = f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage"
            payload = {
                "chat_id": chat_id,        # Target destination (or bot chat)
                "from_chat_id": chat_id,   # Source channel
                "message_id": int(message_id)
            }
            
            # Request file info via getUpdates or getFile if direct file_id exists
            # Alternative: Get file_id via getFile directly if passed
            get_file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile"
            
            # Pass msg_id or payload to inspect
            async with session.post(f"https://api.telegram.org/bot{BOT_TOKEN}/getCustom", json=payload) as resp:
                pass

            return web.Response(text="Telegram Bot API requires MTProto Client (API_ID) or direct file_id for files over 20MB.", status=400)

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
    
