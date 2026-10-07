import socket
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from app.config.settings import settings
from app.bot.middlewares.error_middleware import ErrorHandlerMiddleware
from app.bot.middlewares.db_middleware import DatabaseMiddleware
from app.bot.middlewares.throttling_middleware import ThrottlingMiddleware
from app.bot.handlers import (
    start_router,
    ad_order_router,
    admin_router,
    group_events_router,
    moderation_router,
)


class WindowsSafeAiohttpSession(AiohttpSession):
    """
    Custom AiohttpSession configured for stable Windows & cross-platform socket behavior:
    - Enforces IPv4 (socket.AF_INET) to prevent WinError 52 / NetBIOS collisions.
    - Enables force_close to prevent stale sockets during rapid restarts.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connector_init["family"] = socket.AF_INET
        self._connector_init["force_close"] = True
        self._connector_init["enable_cleanup_closed"] = True


def create_bot() -> Bot:
    session = WindowsSafeAiohttpSession()
    return Bot(
        token=settings.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    # Middlewares registration
    dp.update.middleware(ErrorHandlerMiddleware())
    dp.update.middleware(DatabaseMiddleware())
    dp.message.middleware(ThrottlingMiddleware())

    # Routers registration (order matters: command routers first, generic moderation handler last)
    dp.include_router(start_router)
    dp.include_router(ad_order_router)
    dp.include_router(admin_router)
    dp.include_router(group_events_router)
    dp.include_router(moderation_router)

    return dp
