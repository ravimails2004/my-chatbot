from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity

from app.bot import TeamsBot
from app.config import Config

adapter = BotFrameworkAdapter(
    BotFrameworkAdapterSettings(Config.MICROSOFT_APP_ID, Config.MICROSOFT_APP_PASSWORD)
)
bot = TeamsBot()


async def messages(req: Request) -> Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def call_bot(turn_context):
        await bot.on_turn(turn_context)

    await adapter.process_activity(activity, auth_header, call_bot)
    return Response(status=200)


async def health(_: Request) -> Response:
    return Response(text="ok", status=200)


web_app = web.Application()
web_app.router.add_post("/api/messages", messages)
web_app.router.add_get("/health", health)

if __name__ == "__main__":
    web.run_app(web_app, host="0.0.0.0", port=Config.PORT)
