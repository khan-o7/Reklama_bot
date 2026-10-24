from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import settings
from app.utils.logger import logger


class Base(DeclarativeBase):
    pass


# Async engine configured with pool pre-ping to ensure stable connections
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)
async_session_factory = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency helper to yield async db session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


async def init_db() -> None:
    """Creates tables if they don't already exist and safely adds newly introduced columns."""
    from sqlalchemy import text
    try:
        async with engine.begin() as conn:
            # Import models so Base has all table metadata
            from app.database import models  # noqa
            await conn.run_sync(Base.metadata.create_all)

            # Auto-migrate newly added columns for advertisements table
            alter_queries = [
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS chat_id BIGINT",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS username VARCHAR(255)",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS first_name VARCHAR(255)",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS media_type VARCHAR(50) DEFAULT 'TEXT'",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS media_file_id VARCHAR(255)",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS media_file_unique_id VARCHAR(255)",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS original_text TEXT",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS original_caption TEXT",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS ocr_text TEXT",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS combined_text TEXT",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS detected_keywords TEXT",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS risk_score INTEGER DEFAULT 0",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'DELETED'",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS published_message_id BIGINT",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS published_chat_id BIGINT",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS published_at TIMESTAMP WITH TIME ZONE",
                "ALTER TABLE advertisements ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "ALTER TABLE payments ADD COLUMN IF NOT EXISTS request_id INTEGER",
                "ALTER TABLE payments ALTER COLUMN order_id DROP NOT NULL",
            ]
            for query in alter_queries:
                try:
                    await conn.execute(text(query))
                except Exception as alter_err:
                    logger.debug(f"Column migration skipped or already applied: {alter_err}")

        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise e
