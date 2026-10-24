import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings
from app.database.database import AsyncSessionLocal, init_db
from app.database.repositories.admin_user_repo import AdminUserRepository
from app.web.auth import hash_password
from app.web.routes import auth_router, dashboard_router, api_router, olx_router
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and ensure admin user
    await init_db()
    async with AsyncSessionLocal() as session:
        admin = await AdminUserRepository.get_by_username(session, settings.WEB_ADMIN_USERNAME)
        if not admin:
            hashed = hash_password(settings.WEB_ADMIN_PASSWORD)
            await AdminUserRepository.create(session, settings.WEB_ADMIN_USERNAME, hashed)
            logger.info(f"Initialized default Web Admin user: '{settings.WEB_ADMIN_USERNAME}'")

    logger.info(f"FastAPI Web Admin started at http://{settings.WEB_ADMIN_HOST}:{settings.WEB_ADMIN_PORT}")
    yield
    logger.info("FastAPI Web Admin stopped.")


def create_web_app() -> FastAPI:
    app = FastAPI(
        title="Defender Bot Web Admin",
        description="Professional Telegram Ad Defender Management Panel",
        version="1.0.0",
        lifespan=lifespan
    )

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(api_router)
    app.include_router(olx_router)

    return app
