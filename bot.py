import threading
from aiohttp import web

async def handle(request):
    return web.Response(text="Bot ishlayapti")

def run_web():
    app = web.Application()
    app.router.add_get('/', handle)
    web.run_app(app, port=8080)

threading.Thread(target=run_web).start()
