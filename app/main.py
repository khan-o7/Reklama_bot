import asyncio
import sys
import uvicorn
from aiogram import Bot, Dispatcher

from app.config.settings import settings
from app.utils.logger import logger
from app.database.database import init_db, engine, AsyncSessionLocal
from app.database.repositories.admin_user_repo import AdminUserRepository
from app.web.auth import hash_password
from app.services.cache_service import cache
from app.bot.loader import create_bot, create_dispatcher
from app.web.app import create_web_app


async def start_web_server():
    """Runs FastAPI Web Admin via Uvicorn within asyncio loop."""
    app = create_web_app()
    config = uvicorn.Config(
        app=app,
        host=settings.WEB_ADMIN_HOST,
        port=settings.WEB_ADMIN_PORT,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    logger.info("Initializing Defender Bot and PostgreSQL Database...")

    # 1. Initialize DB tables
    await init_db()

    # 2. Seed initial Web Admin user if enabled
    if settings.WEB_ADMIN_ENABLED:
        async with AsyncSessionLocal() as session:
            admin = await AdminUserRepository.get_by_username(session, settings.WEB_ADMIN_USERNAME)
            if not admin:
                hashed = hash_password(settings.WEB_ADMIN_PASSWORD)
                await AdminUserRepository.create(session, settings.WEB_ADMIN_USERNAME, hashed)
                logger.info(f"Initialized default Web Admin user: '{settings.WEB_ADMIN_USERNAME}'")

    # 3. Synchronize Whitelist & Blacklist cache
    async with AsyncSessionLocal() as session:
        await cache.sync_with_db(session, force=True)

    # 4. Initialize Aiogram Bot & Dispatcher
    bot: Bot = create_bot()
    dp: Dispatcher = create_dispatcher()

    # Robust Telegram connection with retry for Windows / transient network hiccups
    for attempt in range(1, 11):
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            bot_info = await bot.get_me()
            logger.info(f"Bot started | @{bot_info.username} (ID: {bot_info.id})")
            break
        except Exception as conn_err:
            if attempt == 10:
                logger.critical(f"Failed to connect to Telegram API after 10 attempts: {conn_err}")
                raise
            logger.warning(f"Telegram connection attempt {attempt}/10 failed ({conn_err}). Retrying in 2 seconds...")
            await asyncio.sleep(2)

    if settings.WEB_ADMIN_ENABLED:
        logger.info(f"Web Admin Panel available at: http://localhost:{settings.WEB_ADMIN_PORT}")

    tasks = [
        dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            polling_timeout=30,
            handle_as_tasks=True
        )
    ]

    if settings.WEB_ADMIN_ENABLED:
        tasks.append(start_web_server())

    try:
        await asyncio.gather(*tasks)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot is shutting down...")
    finally:
        await bot.session.close()
        await engine.dispose()
        logger.info("Bot and database connections closed gracefully.")


import socket


def acquire_single_instance_lock(port: int = 49151):
    """
    Ensures only ONE instance of Defender Bot can run at any time on this machine.
    Prevents duplicate Telegram polling, web port 8000 collisions, and Errno 10048.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", port))
        s.listen(1)
        return s
    except OSError:
        return None


if __name__ == "__main__":
    lock_socket = acquire_single_instance_lock(port=49151)
    if not lock_socket:
        logger.error(
            "❌ DIQQAT: Defender Bot allaqachon boshqa terminal yoki fonda ishlab turibdi!\n"
            "Ikkita nusxa bir vaqtda ishlay olmaydi (Telegram polling va Web Admin port 8000 ziddiyati yuzaga keladi).\n"
            "Iltimos, avvalgi ishlayotgan oynani yoping yoki eski python jarayonini to'xtating."
        )
        sys.exit(0)

    if sys.platform == "win32":
        # WindowsSelectorEventLoopPolicy eliminates WinError 52 and socket IOCP issues with aiohttp
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        try:
            lock_socket.close()
        except Exception:
            pass
