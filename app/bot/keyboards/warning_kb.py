from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.config.settings import settings


def get_warning_keyboard(bot_username: str | None = None, ad_id: int | None = None) -> InlineKeyboardMarkup:
    """Creates inline keyboard under the warning message directing to the bot for ad orders."""
    keyboard = []
    if bot_username:
        clean_bot = bot_username.lstrip("@")
        if ad_id:
            btn_text = "📢 Reklama joylash"
            start_payload = f"ad_{ad_id}"
        else:
            btn_text = "📢 Reklama joylash"
            start_payload = "ad_order"
        keyboard.append([
            InlineKeyboardButton(
                text=btn_text,
                url=f"https://t.me/{clean_bot}?start={start_payload}"
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
