import asyncio
from typing import Any, Callable, Dict, List, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message


class AlbumMiddleware(BaseMiddleware):
    """
    Collects multiple messages belonging to the same media_group_id (Telegram album)
    into a single list `album` passed in `data['album']`.
    """
    def __init__(self, latency: float = 0.4):
        self.latency = latency
        self.albums: Dict[str, List[Message]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.media_group_id:
            return await handler(event, data)

        mg_id = event.media_group_id

        # If this media_group is already waiting, append message and return early
        if mg_id in self.albums:
            self.albums[mg_id].append(event)
            return None

        # First message of the album: start waiting window
        self.albums[mg_id] = [event]

        # Wait briefly for all album parts to arrive from Telegram
        await asyncio.sleep(self.latency)

        # Retrieve and remove all accumulated album messages
        messages = self.albums.pop(mg_id, [event])
        data["album"] = messages

        # Invoke handler with the primary event and data['album']
        return await handler(event, data)
