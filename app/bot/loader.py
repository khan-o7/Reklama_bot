import socket
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from app.config.settings import settings
from app.bot.middlewares.error_middleware import ErrorHandlerMiddleware
from app.bot.middlewares.db_middleware import DatabaseMiddleware
from app.bot.middlewares.throttling_middleware import ThrottlingMiddleware
from app.bot.middlewares.album_middleware import AlbumMiddleware
from app.bot.handlers import (
    start_router,
    ad_order_router,
    admin_router,
    group_events_router,
    moderation_router,
)


class WindowsSafeAiohttpSession(AiohttpSession):
    """
    Enforces IPv4 (socket.AF_INET) to prevent Windows WinError 52 / NetBIOS collisions,
    while maintaining HTTP Keep-Alive connection pooling (no port exhaustion).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connector_init["family"] = socket.AF_INET
        self._connector_init["keepalive_timeout"] = 25
        self._connector_init["enable_cleanup_closed"] = True


def create_bot() -> Bot:
    proxy = settings.TELEGRAM_PROXY.strip() if settings.TELEGRAM_PROXY else None
    return Bot(
        token=settings.BOT_TOKEN,
        session=WindowsSafeAiohttpSession(proxy=proxy),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    # Middlewares registration
    dp.update.middleware(ErrorHandlerMiddleware())
    dp.update.middleware(DatabaseMiddleware())
    dp.message.middleware(AlbumMiddleware())
    dp.message.middleware(ThrottlingMiddleware())

    # Routers registration (order matters: command routers first, generic moderation handler last)
    dp.include_router(start_router)
    from app.bot.handlers import questionnaire_router, ad_request_admin_router
    dp.include_router(questionnaire_router)
    dp.include_router(ad_request_admin_router)
    dp.include_router(ad_order_router)
    dp.include_router(admin_router)
    dp.include_router(group_events_router)
    dp.include_router(moderation_router)

    return dp
