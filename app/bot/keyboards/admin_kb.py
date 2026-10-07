from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Main administrative dashboard keyboard for bot commands."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
                InlineKeyboardButton(text="🤖 Bot Status", callback_data="admin_status")
            ],
            [
                InlineKeyboardButton(text="👥 Guruhlar", callback_data="admin_groups"),
                InlineKeyboardButton(text="📋 Loglar", callback_data="admin_logs")
            ],
            [
                InlineKeyboardButton(text="🛡 Whitelist", callback_data="admin_whitelist"),
                InlineKeyboardButton(text="🚫 Blacklist", callback_data="admin_blacklist")
            ],
            [
                InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings")
            ]
        ]
    )


def get_back_to_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="admin_main_menu")]
        ]
    )
