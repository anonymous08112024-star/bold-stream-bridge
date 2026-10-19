import os
import asyncio
import aiohttp
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
    
    if not chat_id or not message_id:
        return web.Response(text="Missing chat_id or msg_id parameter", status=400)
        
    try:
        async with aiohttp.ClientSession() as session:
            # 1. Ask Telegram for the file path via Bot API
            # Note: Works for files up to 20MB under standard Bot Token limits
            get_file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={message_id}"
            
            async with session.get(get_file_url) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    return web.Response(text=f"Telegram Error: {data.get('description', 'File not found')}", status=400)
                
                file_path = data["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                
                # 2. Redirect/Proxy stream directly to Smart TV browser
                return web.HTTPFound(download_url)

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
    
