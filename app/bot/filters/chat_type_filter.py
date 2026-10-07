from typing import Union, Sequence
from aiogram.filters import BaseFilter
from aiogram.types import Message


class ChatTypeFilter(BaseFilter):
    """Filter messages based on chat types (private, group, supergroup, channel)."""
    def __init__(self, chat_types: Union[str, Sequence[str]]):
        if isinstance(chat_types, str):
            self.chat_types = [chat_types]
        else:
            self.chat_types = list(chat_types)

    async def __call__(self, message: Message) -> bool:
        return message.chat.type in self.chat_types
