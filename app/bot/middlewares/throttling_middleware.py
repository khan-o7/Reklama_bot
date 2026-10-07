import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message


class ThrottlingMiddleware(BaseMiddleware):
    """Simple in-memory rate limiter per user to prevent rapid command spamming."""
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.users: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            now = time.time()
            last_time = self.users.get(user_id, 0.0)

            # If user sent message in private chat too fast
            if event.chat.type == "private" and (now - last_time) < self.rate_limit:
                return None

            self.users[user_id] = now
            # Clean up users dict if too large
            if len(self.users) > 10000:
                self.users.clear()

        return await handler(event, data)
