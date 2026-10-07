from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from app.config.settings import settings


class IsBotAdmin(BaseFilter):
    """Filter that checks if user is one of the global bot administrators or owner."""
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id if event.from_user else 0
        return user_id in settings.all_admin_ids


class IsGroupAdminOrBotAdmin(BaseFilter):
    """Filter that permits either global bot admins or local group administrators."""
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        if not event.from_user:
            return False

        # Global bot admins always pass
        if event.from_user.id in settings.all_admin_ids:
            return True

        # In groups/supergroups, check Telegram admin status
        chat = event.chat if isinstance(event, Message) else (event.message.chat if event.message else None)
        if chat and chat.type in ("group", "supergroup"):
            try:
                bot = event.bot
                member = await bot.get_chat_member(chat_id=chat.id, user_id=event.from_user.id)
                return member.status in ("creator", "administrator")
            except Exception:
                return False

        return False
