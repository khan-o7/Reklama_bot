from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.config.settings import settings


def get_warning_keyboard() -> InlineKeyboardMarkup:
    """Creates inline keyboard under the warning message with link to admin profile."""
    username = settings.ADMIN_USERNAME.lstrip("@")
    admin_url = f"https://t.me/{username}"

    button = InlineKeyboardButton(
        text="👨‍💼 Adminga murojaat qilish",
        url=admin_url
    )
    return InlineKeyboardMarkup(inline_keyboard=[[button]])
