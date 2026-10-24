import math
from typing import List, Optional, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services.state_machine import get_status_label


def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Main administrative dashboard keyboard for bot commands."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Reklama so‘rovlari", callback_data="admin_requests:ALL:0"),
                InlineKeyboardButton(text="📊 Statistika & Moliya", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings"),
                InlineKeyboardButton(text="👥 Guruhlar", callback_data="admin_groups")
            ],
            [
                InlineKeyboardButton(text="🛡 Whitelist", callback_data="admin_whitelist"),
                InlineKeyboardButton(text="🚫 Blacklist", callback_data="admin_blacklist")
            ],
            [
                InlineKeyboardButton(text="📋 Audit loglar", callback_data="admin_logs"),
                InlineKeyboardButton(text="🤖 Bot holati", callback_data="admin_status")
            ]
        ]
    )


def get_back_to_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="admin_main_menu")]
        ]
    )


def get_requests_dashboard_kb(
    items: List[Any],
    total_count: int,
    status_filter: str = "ALL",
    page: int = 0,
    limit: int = 5
) -> InlineKeyboardMarkup:
    """
    Renders interactive paginated requests list with category filter buttons.
    """
    keyboard = []

    # Filter tabs row 1
    filters_row_1 = [
        InlineKeyboardButton(
            text=f"{'🔘' if status_filter == 'ALL' else '⚪️'} Barchasi",
            callback_data="admin_requests:ALL:0"
        ),
        InlineKeyboardButton(
            text=f"{'🔘' if status_filter == 'NEW' else '⚪️'} Yangi",
            callback_data="admin_requests:NEW:0"
        ),
        InlineKeyboardButton(
            text=f"{'🔘' if status_filter == 'AWAITING_PRICE' else '⚪️'} Narx",
            callback_data="admin_requests:AWAITING_PRICE:0"
        )
    ]
    # Filter tabs row 2
    filters_row_2 = [
        InlineKeyboardButton(
            text=f"{'🔘' if status_filter == 'AWAITING_PAYMENT' else '⚪️'} To‘lov",
            callback_data="admin_requests:AWAITING_PAYMENT:0"
        ),
        InlineKeyboardButton(
            text=f"{'🔘' if status_filter == 'RECEIPT_SUBMITTED' else '⚪️'} Chek",
            callback_data="admin_requests:RECEIPT_SUBMITTED:0"
        ),
        InlineKeyboardButton(
            text=f"{'🔘' if status_filter == 'PUBLISHED' else '⚪️'} E’lon",
            callback_data="admin_requests:PUBLISHED:0"
        )
    ]
    keyboard.append(filters_row_1)
    keyboard.append(filters_row_2)

    # Item buttons
    if items:
        for order in items:
            lbl = get_status_label(order.status)
            short_lbl = lbl.split()[0] if lbl else ""
            price_text = f" | {order.price:,} so‘m".replace(",", " ") if order.price else ""
            btn_text = f"📄 {order.order_number} ({short_lbl}{price_text})"
            keyboard.append([
                InlineKeyboardButton(text=btn_text, callback_data=f"order_details:{order.id}")
            ])

    # Pagination row
    total_pages = max(1, math.ceil(total_count / limit))
    current_page_display = page + 1
    nav_row = []

    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"admin_requests:{status_filter}:{page - 1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="⏺", callback_data="noop"))

    nav_row.append(InlineKeyboardButton(text=f"{current_page_display}/{total_pages} ({total_count})", callback_data="noop"))

    if current_page_display < total_pages:
        nav_row.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"admin_requests:{status_filter}:{page + 1}"))
    else:
        nav_row.append(InlineKeyboardButton(text="⏺", callback_data="noop"))

    keyboard.append(nav_row)

    # Search and Back row
    keyboard.append([
        InlineKeyboardButton(text="🔍 Qidirish", callback_data="admin_req_search"),
        InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="admin_main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_settings_kb() -> InlineKeyboardMarkup:
    """Settings menu keyboard for advertising and moderation configuration."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Karta raqamini sozlash", callback_data="admin_set_card"),
            ],
            [
                InlineKeyboardButton(text="👤 Karta egasini sozlash", callback_data="admin_set_cardholder"),
            ],
            [
                InlineKeyboardButton(text="💰 Standart narxni sozlash", callback_data="admin_set_price"),
            ],
            [
                InlineKeyboardButton(text="🎯 Target guruhni sozlash", callback_data="admin_set_target_group"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="admin_main_menu")
            ]
        ]
    )
