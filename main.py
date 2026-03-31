"""
Entry point — aiohttp web server that hosts the Teams bot endpoint.

Teams sends POST requests to /api/messages.
Run with: python main.py
"""
from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity

from bot import PipelineBot
from config import Config

# ── Bot Framework adapter ─────────────────────────────────────────────────────
settings = BotFrameworkAdapterSettings(
    app_id=Config.MICROSOFT_APP_ID,
    app_password=Config.MICROSOFT_APP_PASSWORD,
)
adapter = BotFrameworkAdapter(settings)
bot = PipelineBot()


async def on_error(context, error):
    print(f"[BotFramework] Unhandled error: {error}")
    await context.send_activity("Something went wrong. Please try again.")


adapter.on_turn_error = on_error


# ── HTTP routes ───────────────────────────────────────────────────────────────

async def messages(request: web.Request) -> web.Response:
    if request.content_type != "application/json":
        return web.Response(status=415)

    body = await request.json()
    activity = Activity().deserialize(body)

    auth_header = request.headers.get("Authorization", "")

    response = await adapter.process_activity(activity, auth_header, bot.on_turn)
    if response:
        return web.json_response(data=response.body, status=response.status)
    return web.Response(status=201)


async def health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/health", health)
    return app


if __name__ == "__main__":
    app = create_app()
    print(f"Bot running on port {Config.PORT}")
    print(f"Teams messaging endpoint: http://localhost:{Config.PORT}/api/messages")
    web.run_app(app, host="0.0.0.0", port=Config.PORT)
