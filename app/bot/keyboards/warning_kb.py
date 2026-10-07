from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.config.settings import settings


def get_warning_keyboard(bot_username: str | None = None) -> InlineKeyboardMarkup:
    """Creates inline keyboard under the warning message directing to the bot for ad orders."""
    keyboard = []
    if bot_username:
        clean_bot = bot_username.lstrip("@")
        keyboard.append([
            InlineKeyboardButton(
                text="🤖 Reklama uchun botga murojaat qiling",
                url=f"https://t.me/{clean_bot}?start=ad_order"
            )
        ])

    if settings.ADMIN_USERNAME:
        username = settings.ADMIN_USERNAME.lstrip("@")
        keyboard.append([
            InlineKeyboardButton(
                text="👨‍💼 Adminga murojaat qilish",
                url=f"https://t.me/{username}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
