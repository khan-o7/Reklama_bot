from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, ErrorEvent
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
    TelegramNetworkError,
)
from app.utils.logger import logger


class ErrorHandlerMiddleware(BaseMiddleware):
    """Global error handler capturing Telegram API errors gracefully."""
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except TelegramRetryAfter as e:
            logger.warning(f"Telegram API Flood Limit: retry after {e.retry_after} seconds.")
        except TelegramForbiddenError as e:
            logger.debug(f"Telegram API Forbidden Error (bot blocked or no rights): {e}")
        except TelegramBadRequest as e:
            logger.warning(f"Telegram API Bad Request: {e}")
        except TelegramNetworkError as e:
            logger.debug(f"Telegram API Network transient retry (auto-retrying): {e}")
        except Exception as e:
            logger.exception(f"Unhandled error in Telegram update handler: {e}")
            return None
