import re
from datetime import datetime, timedelta, timezone
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.group_repo import GroupRepository
from app.database.repositories.list_repo import ListRepository
from app.database.repositories.setting_repo import SettingRepository
from app.database.repositories.audit_repo import AuditRepository
from app.database.repositories.ad_repo import AdvertisementRepository
from app.database.repositories.ad_request_repo import AdvertisingRequestRepository
from app.services.statistics_service import StatisticsService
from app.services.request_service import RequestService
from app.services.cluster_service import ClusterService
from app.services.cache_service import cache
from app.services.olx_service import OlxService
from app.bot.keyboards.admin_kb import (
    get_admin_main_menu,
    get_back_to_admin_menu,
    get_requests_dashboard_kb,
    get_admin_settings_kb,
    get_olx_admin_kb,
)
from app.utils.logger import logger

router = Router(name="admin_router")

NO_PERMISSION_TEXT = "❌ Sizda bu buyruqdan foydalanish huquqi yo‘q."


class AdminDashboardStates(StatesGroup):
    waiting_for_search_query = State()
    waiting_for_card_number = State()
    waiting_for_cardholder = State()
    waiting_for_default_price = State()
    waiting_for_target_group = State()


async def is_authorized(message: Message, bot: Bot) -> bool:
    """Checks if sender is bot admin or group administrator."""
    if not message.from_user:
        return False
    if message.from_user.id in settings.all_admin_ids:
        return True
    if message.chat.type in ("group", "supergroup"):
        try:
            m = await bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
            return m.status in ("creator", "administrator")
        except Exception:
            return False
    return False


# ==========================================
# /admin Command
# ==========================================
@router.message(Command("admin"))
async def cmd_admin(message: Message, bot: Bot) -> None:
    if not await is_authorized(message, bot):
        admin_contact = settings.ADMIN_USERNAME.lstrip("@")
        contact_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✍️ Adminga yozish (@{admin_contact})",
                        url=f"https://t.me/{admin_contact}"
                    )
                ]
            ]
        )
        text = (
            "👨‍💻 <b>Administratorga murojaat</b>\n\n"
            "Savol, taklif yoki reklama masalalari bo‘yicha quyidagi profil orqali bog‘lanishingiz mumkin:\n"
            f"👉 @{admin_contact}\n\n"
            "<i>Biz imkon qadar tezroq javob beramiz!</i>"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=contact_kb)
        return

    text = (
        f"Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        f"🛡 <b>Defender Bot Administrator Boshqaruv Paneli</b>\n\n"
        f"Guruh moderatsiyasi, reklama arizalari, to‘lovlar va tizim sozlamalarini "
        f"quyidagi menyu orqali boshqarishingiz mumkin:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_menu())


# ==========================================
# /requests Command
# ==========================================
@router.message(Command("requests"))
async def cmd_requests(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return
    items, total_count = await RequestService.get_requests_by_filter(
        session, status_filter=None, limit=5, offset=0
    )
    text = (
        "📢 <b>REKLAMA SO‘ROVLARI VA TO‘LOVLAR:</b>\n\n"
        f"Jami arizalar soni: <b>{total_count} ta</b>\n"
        "Ko‘rib chiqish yoki tafsilotlarni ko‘rish uchun quyidagi arizani tanlang:"
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_requests_dashboard_kb(items, total_count, "ALL", page=0)
    )


# ==========================================
# /status Command
# ==========================================
@router.message(Command("status"))
async def cmd_status(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return
    text = await StatisticsService.get_bot_status(session)
    await message.reply(text, parse_mode="HTML")


# ==========================================
# /stats Command
# ==========================================
@router.message(Command("stats"))
async def cmd_stats(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return
    mod_stats = await StatisticsService.get_statistics(session)
    fin_stats = await RequestService.get_financial_statistics(session)
    combined = (
        f"{mod_stats}\n\n"
        f"💰 <b>REKLAMA MOLIYA VA OPERATSION STATISTIKASI:</b>\n"
        f"• Jami qabul qilingan so‘rovlar: <b>{fin_stats['total_orders']} ta</b>\n"
        f"• Bugungi yangi so‘rovlar: <b>{fin_stats['today_orders']} ta</b>\n"
        f"• Shu oydagi so‘rovlar: <b>{fin_stats['month_orders']} ta</b>\n\n"
        f"📊 <b>Holatlar bo‘yicha:</b>\n"
        f"• ⏳ Narx kutilmoqda: <b>{fin_stats['pending_pricing']} ta</b>\n"
        f"• 💳 To‘lov kutilmoqda: <b>{fin_stats['awaiting_payment']} ta</b>\n"
        f"• 🧾 Chek tekshiruvda: <b>{fin_stats['receipt_submitted']} ta</b>\n"
        f"• 📢 Chop etilgan reklamalar: <b>{fin_stats['published']} ta</b>\n"
        f"• ❌ Rad etilgan to‘lovlar: <b>{fin_stats['rejected']} ta</b>\n"
        f"• ⚠️ Xatolik yuz berganlar: <b>{fin_stats['failed']} ta</b>\n\n"
        f"💵 <b>Tushumlar (Bot ma’lumotlari bo‘yicha):</b>\n"
        f"• Bugungi tasdiqlangan to‘lovlar: <b>{fin_stats['today_revenue']:,} so‘m</b>\n"
        f"• Jami tasdiqlangan to‘lovlar: <b>{fin_stats['total_revenue']:,} so‘m</b>\n\n"
        f"<i>(Eslatma: Moliyaviy statistika botda administrator tasdiqlagan arizalar bo‘yicha qayd etilgan ma’lumotdir).</i>"
    ).replace(",", " ")
    await message.reply(combined, parse_mode="HTML")


# ==========================================
# /whitelist Command
# ==========================================
@router.message(Command("whitelist"))
async def cmd_whitelist(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return

    parts = message.text.split() if message.text else []
    # /whitelist add <domain>
    if len(parts) >= 3 and parts[1].lower() == "add":
        val = parts[2].strip()
        await ListRepository.add_to_whitelist(session, "domain", val)
        cache.invalidate()
        await cache.sync_with_db(session, force=True)
        await AuditRepository.create(session, "whitelist_added", details=f"domain: {val}")
        await message.reply(f"✅ <b>{val}</b> oq ro‘yxatga (whitelist) muvaffaqiyatli qo‘shildi.", parse_mode="HTML")
        return

    # /whitelist del <domain>
    if len(parts) >= 3 and parts[1].lower() in ("del", "remove", "delete"):
        val = parts[2].strip()
        removed = await ListRepository.remove_from_whitelist(session, val)
        cache.invalidate()
        await cache.sync_with_db(session, force=True)
        if removed:
            await message.reply(f"🗑 <b>{val}</b> oq ro‘yxatdan o‘chirildi.", parse_mode="HTML")
        else:
            await message.reply(f"⚠️ <b>{val}</b> oq ro‘yxatda topilmadi.", parse_mode="HTML")
        return

    # List whitelist
    items = await ListRepository.get_all_whitelist(session)
    if not items:
        resp = (
            "🛡 <b>Oq ro‘yxat (Whitelist):</b>\n\n"
            "Hozircha qo‘shimcha domenlar yo‘q.\n"
            "Standart ruxsat etilganlar: <code>gov.uz, edu.uz, customs.uz, my.gov.uz</code>\n\n"
            "<i>Qo‘shish:</i> <code>/whitelist add domen.uz</code>\n"
            "<i>O‘chirish:</i> <code>/whitelist del domen.uz</code>"
        )
    else:
        dom_list = "\n".join([f"• <code>{it.value}</code>" for it in items])
        resp = (
            "🛡 <b>Oq ro‘yxatdagi domenlar (Whitelist):</b>\n\n"
            f"{dom_list}\n\n"
            "<i>Qo‘shish:</i> <code>/whitelist add domen.uz</code>\n"
            "<i>O‘chirish:</i> <code>/whitelist del domen.uz</code>"
        )
    await message.reply(resp, parse_mode="HTML")


# ==========================================
# /blacklist Command
# ==========================================
@router.message(Command("blacklist"))
async def cmd_blacklist(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return

    parts = message.text.split() if message.text else []
    # /blacklist add <type: word|domain|username> <val>
    if len(parts) >= 4 and parts[1].lower() == "add":
        b_type = parts[2].lower()
        if b_type not in ("word", "domain", "username"):
            b_type = "word"
        val = parts[3].strip()
        await ListRepository.add_to_blacklist(session, b_type, val)
        cache.invalidate()
        await cache.sync_with_db(session, force=True)
        await AuditRepository.create(session, "blacklist_added", details=f"{b_type}: {val}")
        await message.reply(f"✅ <b>{val}</b> ({b_type}) qora ro‘yxatga (blacklist) qo‘shildi.", parse_mode="HTML")
        return

    # /blacklist del <val>
    if len(parts) >= 3 and parts[1].lower() in ("del", "remove", "delete"):
        val = parts[2].strip()
        removed = await ListRepository.remove_from_blacklist(session, val)
        cache.invalidate()
        await cache.sync_with_db(session, force=True)
        if removed:
            await message.reply(f"🗑 <b>{val}</b> qora ro‘yxatdan o‘chirildi.", parse_mode="HTML")
        else:
            await message.reply(f"⚠️ <b>{val}</b> qora ro‘yxatda topilmadi.", parse_mode="HTML")
        return

    # List blacklist
    items = await ListRepository.get_all_blacklist(session)
    if not items:
        resp = (
            "🚫 <b>Qora ro‘yxat (Blacklist):</b>\n\n"
            "Ro‘yxat hozircha bo‘sh.\n\n"
            "<i>Qo‘shish formati:</i>\n"
            "• <code>/blacklist add word so'z</code>\n"
            "• <code>/blacklist add domain domen.com</code>\n"
            "• <code>/blacklist add username kanal_yoki_user</code>\n"
            "<i>O‘chirish:</i> <code>/blacklist del qiymat</code>"
        )
    else:
        lines = []
        for it in items:
            lines.append(f"• [{it.type}] <code>{it.value}</code>")
        resp = (
            "🚫 <b>Qora ro‘yxat (Blacklist):</b>\n\n"
            f"{chr(10).join(lines)}\n\n"
            "<i>Qo‘shish:</i> <code>/blacklist add word so'z</code>\n"
            "<i>O‘chirish:</i> <code>/blacklist del qiymat</code>"
        )
    await message.reply(resp, parse_mode="HTML")


# ==========================================
# /users Command
# ==========================================
@router.message(Command("users"))
async def cmd_users(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return

    top_offenders = await UserRepository.get_top_offenders(session, limit=10)
    total_users = await UserRepository.get_total_count(session)

    if not top_offenders:
        await message.reply(
            f"👥 Jami ro‘yxatdan o‘tgan userlar: {total_users}\n"
            "Hozircha birorta ham ogohlantirilgan user yo‘q."
        )
        return

    lines = [f"👥 <b>FOYDALANUVCHILAR (Jami: {total_users}):</b>\n\n<b>Eng ko‘p ogohlantirilganlar:</b>"]
    for idx, u in enumerate(top_offenders, 1):
        name = f"@{u.username}" if u.username else (u.first_name or f"ID:{u.telegram_id}")
        status = ""
        if u.is_banned:
            status = " [🚫 Banned]"
        elif u.is_muted:
            status = " [🔇 Muted]"
        lines.append(f"{idx}. {name} — {u.warnings_count} ta ogohlantirish{status}")

    await message.reply("\n".join(lines), parse_mode="HTML")


# ==========================================
# /warnings Command
# ==========================================
@router.message(Command("warnings"))
async def cmd_warnings(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return

    target_user_id = None
    target_name = ""

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
        target_user_id = target_user.id
        target_name = target_user.full_name
    else:
        parts = message.text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            target_user_id = int(parts[1])
            target_name = f"ID: {target_user_id}"

    if not target_user_id:
        await message.reply(
            "ℹ️ Foydalanuvchi ogohlantirishlarini tekshirish uchun uning xabariga reply qilib "
            "<code>/warnings</code> deb yuboring yoki <code>/warnings USER_ID</code> yozing.",
            parse_mode="HTML"
        )
        return

    user_db = await UserRepository.get_by_telegram_id(session, target_user_id)
    count = user_db.warnings_count if user_db else 0
    is_m = user_db.is_muted if user_db else False
    is_b = user_db.is_banned if user_db else False

    await message.reply(
        f"👤 <b>Foydalanuvchi:</b> {target_name}\n"
        f"🆔 <b>Telegram ID:</b> <code>{target_user_id}</code>\n"
        f"⚠️ <b>Ogohlantirishlar soni:</b> {count}\n"
        f"🔇 <b>Mute holati:</b> {'Ha' if is_m else 'Yo‘q'}\n"
        f"🚫 <b>Ban holati:</b> {'Ha' if is_b else 'Yo‘q'}",
        parse_mode="HTML"
    )


# ==========================================
# /mute Command
# ==========================================
@router.message(Command("mute"))
async def cmd_mute(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return

    if message.chat.type not in ("group", "supergroup"):
        await message.reply("Bu buyruq faqat guruhlarda ishlaydi.")
        return

    target_user = None
    minutes = 10

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
        parts = message.text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            minutes = int(parts[1])
    else:
        parts = message.text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            target_id = int(parts[1])
            if len(parts) >= 3 and parts[2].isdigit():
                minutes = int(parts[2])
            target_user_id = target_id
        else:
            await message.reply(
                "ℹ️ Foydalanuvchini mute qilish uchun uning xabariga reply qilib "
                "<code>/mute [daqiqa]</code> yuboring.",
                parse_mode="HTML"
            )
            return

    target_id = target_user.id if target_user else target_user_id
    until_date = datetime.now(timezone.utc) + timedelta(minutes=minutes)

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        u_db = await UserRepository.get_by_telegram_id(session, target_id)
        if u_db:
            await UserRepository.set_muted(session, u_db.id, True)

        await AuditRepository.create(
            session=session,
            event_type="user_muted",
            group_id=None,
            user_id=u_db.id if u_db else None,
            details=f"user={target_id} | duration={minutes}m"
        )
        await message.reply(f"🔇 Foydalanuvchi {minutes} daqiqaga yozishdan cheklandi (MUTE).")
    except Exception as e:
        await message.reply(f"❌ Mute qilishda xatolik: {e}")


# ==========================================
# /unmute Command
# ==========================================
@router.message(Command("unmute"))
async def cmd_unmute(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return

    if message.chat.type not in ("group", "supergroup"):
        await message.reply("Bu buyruq faqat guruhlarda ishlaydi.")
        return

    target_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    else:
        parts = message.text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            target_id = int(parts[1])

    if not target_id:
        await message.reply("ℹ️ Unmute qilish uchun foydalanuvchi xabariga reply qilib <code>/unmute</code> yuboring.", parse_mode="HTML")
        return

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        u_db = await UserRepository.get_by_telegram_id(session, target_id)
        if u_db:
            await UserRepository.set_muted(session, u_db.id, False)

        await message.reply("🔊 Foydalanuvchidan cheklov yechildi (UNMUTE).")
    except Exception as e:
        await message.reply(f"❌ Cheklovni yechishda xatolik: {e}")


# ==========================================
# /ban Command
# ==========================================
@router.message(Command("ban"))
async def cmd_ban(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return

    if message.chat.type not in ("group", "supergroup"):
        await message.reply("Bu buyruq faqat guruhlarda ishlaydi.")
        return

    target_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    else:
        parts = message.text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            target_id = int(parts[1])

    if not target_id:
        await message.reply("ℹ️ Ban qilish uchun foydalanuvchi xabariga reply qilib <code>/ban</code> yuboring.", parse_mode="HTML")
        return

    try:
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=target_id)
        u_db = await UserRepository.get_by_telegram_id(session, target_id)
        if u_db:
            await UserRepository.set_banned(session, u_db.id, True)

        await AuditRepository.create(
            session=session,
            event_type="user_banned",
            group_id=None,
            user_id=u_db.id if u_db else None,
            details=f"user={target_id}"
        )
        await message.reply("🚫 Foydalanuvchi guruhdan chetlatildi (BAN).")
    except Exception as e:
        await message.reply(f"❌ Ban qilishda xatolik: {e}")


# ==========================================
# /unban Command
# ==========================================
@router.message(Command("unban"))
async def cmd_unban(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return

    if message.chat.type not in ("group", "supergroup"):
        await message.reply("Bu buyruq faqat guruhlarda ishlaydi.")
        return

    target_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    else:
        parts = message.text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            target_id = int(parts[1])

    if not target_id:
        await message.reply("ℹ️ Unban qilish uchun <code>/unban USER_ID</code> yuboring.", parse_mode="HTML")
        return

    try:
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=target_id, only_if_banned=True)
        u_db = await UserRepository.get_by_telegram_id(session, target_id)
        if u_db:
            await UserRepository.set_banned(session, u_db.id, False)

        await message.reply("✅ Foydalanuvchi bandan chiqarildi (UNBAN).")
    except Exception as e:
        await message.reply(f"❌ Bandan chiqarishda xatolik: {e}")


# ==========================================
# /logs Command
# ==========================================
@router.message(Command("logs"))
async def cmd_logs(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return

    recent_logs = await AuditRepository.get_recent(session, limit=10)
    if not recent_logs:
        await message.reply("📋 Audit jurnali hozircha bo‘sh.")
        return

    lines = ["📋 <b>OXIRGI AUDIT HODISALARI:</b>\n"]
    for log in recent_logs:
        date_str = log.created_at.strftime("%d.%m %H:%M:%S")
        lines.append(f"• <code>{date_str}</code> | <b>{log.event_type}</b>\n  <i>{log.details or ''}</i>")

    await message.reply("\n".join(lines), parse_mode="HTML")


# ==========================================
# /settings Command
# ==========================================
@router.message(Command("settings"))
async def cmd_settings(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return

    group_id = None
    if message.chat.type in ("group", "supergroup"):
        grp = await GroupRepository.get_by_chat_id(session, message.chat.id)
        if grp:
            group_id = grp.id

    all_settings = await SettingRepository.get_all_group_settings(session, group_id)

    lines = ["⚙️ <b>BOT VA GURUH SOZLAMALARI:</b>\n"]
    for k, v in all_settings.items():
        if k == "warning_message":
            continue
        lines.append(f"• <b>{k}</b>: <code>{v}</code>")

    lines.append("\n<i>Sozlamalarni Web Admin Panel orqali ham qulay boshqarishingiz mumkin.</i>")
    await message.reply("\n".join(lines), parse_mode="HTML")


# ==========================================
# Inline Menu Callbacks
# ==========================================
@router.callback_query(F.data == "admin_stats")
async def cb_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    mod_stats = await StatisticsService.get_statistics(session)
    fin_stats = await RequestService.get_financial_statistics(session)
    combined = (
        f"{mod_stats}\n\n"
        f"💰 <b>REKLAMA MOLIYA VA OPERATSION STATISTIKASI:</b>\n"
        f"• Jami qabul qilingan so‘rovlar: <b>{fin_stats['total_orders']} ta</b>\n"
        f"• Bugungi yangi so‘rovlar: <b>{fin_stats['today_orders']} ta</b>\n"
        f"• Shu oydagi so‘rovlar: <b>{fin_stats['month_orders']} ta</b>\n\n"
        f"📊 <b>Holatlar bo‘yicha:</b>\n"
        f"• ⏳ Narx kutilmoqda: <b>{fin_stats['pending_pricing']} ta</b>\n"
        f"• 💳 To‘lov kutilmoqda: <b>{fin_stats['awaiting_payment']} ta</b>\n"
        f"• 🧾 Chek tekshiruvda: <b>{fin_stats['receipt_submitted']} ta</b>\n"
        f"• 📢 Chop etilgan reklamalar: <b>{fin_stats['published']} ta</b>\n"
        f"• ❌ Rad etilgan to‘lovlar: <b>{fin_stats['rejected']} ta</b>\n"
        f"• ⚠️ Xatolik yuz berganlar: <b>{fin_stats['failed']} ta</b>\n\n"
        f"💵 <b>Tushumlar (Bot ma’lumotlari bo‘yicha):</b>\n"
        f"• Bugungi tasdiqlangan to‘lovlar: <b>{fin_stats['today_revenue']:,} so‘m</b>\n"
        f"• Jami tasdiqlangan to‘lovlar: <b>{fin_stats['total_revenue']:,} so‘m</b>\n\n"
        f"<i>(Eslatma: Moliyaviy statistika botda administrator tasdiqlagan arizalar bo‘yicha qayd etilgan ma’lumotdir).</i>"
    ).replace(",", " ")
    await callback.message.edit_text(combined, parse_mode="HTML", reply_markup=get_back_to_admin_menu())


@router.callback_query(F.data.startswith("admin_requests:"))
async def cb_admin_requests(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    parts = callback.data.split(":")
    status_filter = parts[1] if len(parts) > 1 else "ALL"
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    limit = 5
    offset = page * limit
    real_filter = None if status_filter == "ALL" else status_filter

    items, total_count = await RequestService.get_requests_by_filter(
        session, status_filter=real_filter, limit=limit, offset=offset
    )
    status_label = "Barchasi" if status_filter == "ALL" else status_filter
    text = (
        f"📢 <b>REKLAMA SO‘ROVLARI ({status_label}):</b>\n\n"
        f"Mavjud arizalar soni: <b>{total_count} ta</b> (Sahifa: {page + 1})\n"
        "Batafsil ma’lumot yoki amallar uchun arizani tanlang:"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_requests_dashboard_kb(items, total_count, status_filter, page, limit)
    )


@router.callback_query(F.data == "admin_req_search")
async def cb_admin_req_search(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    await state.set_state(AdminDashboardStates.waiting_for_search_query)
    text = (
        "🔍 <b>REKLAMA SO‘ROVINI QIDIRISH:</b>\n\n"
        "Iltimos, qidirilayotgan buyurtma raqamini (masalan: <code>AD-2026-000001</code>) "
        "yoki foydalanuvchining Telegram ID raqamini yuboring:"
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.message(AdminDashboardStates.waiting_for_search_query)
async def handle_admin_search_query(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.from_user.id not in settings.all_admin_ids:
        return
    query = (message.text or "").strip()
    await state.clear()
    items, total_count = await RequestService.get_requests_by_filter(
        session, search_query=query, limit=5, offset=0
    )
    if not items:
        await message.answer(
            f"🔍 «{query}» bo‘yicha hech qanday reklama so‘rovi topilmadi.",
            reply_markup=get_requests_dashboard_kb([], 0, "ALL", 0)
        )
        return
    text = (
        f"🔍 <b>«{query}» BO‘YICHA QIDIRUV NATIJALARI:</b>\n\n"
        f"Topildi: <b>{total_count} ta</b> ariza\n"
        "Kerakli buyurtmani tanlang:"
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_requests_dashboard_kb(items, total_count, "ALL", 0)
    )


@router.callback_query(F.data == "admin_status")
async def cb_status(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    text = await StatisticsService.get_bot_status(session)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_to_admin_menu())


@router.callback_query(F.data == "admin_logs")
async def cb_logs(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    recent_logs = await AuditRepository.get_recent(session, limit=8)
    if not recent_logs:
        text = "📋 Audit jurnali hozircha bo‘sh."
    else:
        lines = ["📋 <b>OXIRGI AUDIT HODISALARI:</b>\n"]
        for log in recent_logs:
            date_str = log.created_at.strftime("%d.%m %H:%M:%S")
            lines.append(f"• <code>{date_str}</code> | <b>{log.event_type}</b>\n  <i>{log.details or ''}</i>")
        text = "\n".join(lines)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_to_admin_menu())


@router.callback_query(F.data == "admin_groups")
async def cb_groups(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    groups = await GroupRepository.get_all_active(session)
    if not groups:
        text = "👥 Hozircha faol guruhlar yo‘q."
    else:
        lines = [f"👥 <b>FAOL GURUHLAR ({len(groups)}):</b>\n"]
        for g in groups[:10]:
            lines.append(f"• <b>{g.title}</b> (<code>{g.telegram_chat_id}</code>)")
        text = "\n".join(lines)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_to_admin_menu())


@router.callback_query(F.data == "admin_whitelist")
async def cb_whitelist(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    items = await ListRepository.get_all_whitelist(session)
    doms = "\n".join([f"• <code>{i.value}</code>" for i in items]) if items else "• <i>Qo‘shimcha domenlar yo‘q</i>"
    text = f"🛡 <b>OQ RO‘YXAT (WHITELIST):</b>\n\n{doms}\n\n<i>Qo‘shish:</i> <code>/whitelist add domen.uz</code>"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_to_admin_menu())


@router.callback_query(F.data == "admin_blacklist")
async def cb_blacklist(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    items = await ListRepository.get_all_blacklist(session)
    bls = "\n".join([f"• [{i.type}] <code>{i.value}</code>" for i in items]) if items else "• <i>Hozircha bo‘sh</i>"
    text = f"🚫 <b>QORA RO‘YXAT (BLACKLIST):</b>\n\n{bls}\n\n<i>Qo‘shish:</i> <code>/blacklist add word so'z</code>"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_to_admin_menu())


@router.callback_query(F.data == "admin_settings")
async def cb_settings(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    db_card = await SettingRepository.get_setting(session, None, "ad_payment_card", settings.AD_PAYMENT_CARD)
    db_holder = await SettingRepository.get_setting(session, None, "ad_cardholder_name", settings.AD_CARDHOLDER_NAME)
    db_price = await SettingRepository.get_setting(session, None, "ad_price", str(settings.AD_PRICE))
    db_target = await SettingRepository.get_setting(session, None, "target_group_id", settings.TARGET_GROUP_ID)

    text = (
        "⚙️ <b>REKLAMA VA TIZIM SOZLAMALARI:</b>\n\n"
        f"💳 <b>To‘lov kartasi:</b> <code>{db_card}</code>\n"
        f"👤 <b>Karta egasi:</b> <code>{db_holder}</code>\n"
        f"💰 <b>Standart narx:</b> <code>{db_price}</code> so‘m\n"
        f"🎯 <b>Moderatsiya guruhi ID:</b> <code>{db_target or 'Barcha guruhlar'}</code>\n\n"
        "O‘zgartirmoqchi bo‘lgan parametrni tanlang:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_settings_kb())


@router.callback_query(F.data == "admin_set_card")
async def cb_set_card(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    await state.set_state(AdminDashboardStates.waiting_for_card_number)
    await callback.message.answer(
        "💳 <b>Yangi to‘lov karta raqamini kiriting</b> (masalan: <code>8600 1234 5678 9012</code>):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminDashboardStates.waiting_for_card_number)
async def handle_set_card_number(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.from_user.id not in settings.all_admin_ids:
        return
    card_raw = (message.text or "").replace(" ", "").replace("-", "").strip()
    if not (card_raw.isdigit() and len(card_raw) == 16):
        await message.answer("❌ Noto‘g‘ri karta raqami. Karta raqami 16 ta raqamdan iborat bo‘lishi lozim.")
        return

    formatted = f"{card_raw[:4]} {card_raw[4:8]} {card_raw[8:12]} {card_raw[12:]}"
    await SettingRepository.set_setting(session, None, "ad_payment_card", formatted)
    settings.AD_PAYMENT_CARD = formatted
    await AuditRepository.create(session, "setting_changed", details=f"ad_payment_card updated by {message.from_user.id}")
    await state.clear()
    await message.answer(
        f"✅ To‘lov karta raqami muvaffaqiyatli o‘zgartirildi: <code>{formatted}</code>",
        parse_mode="HTML",
        reply_markup=get_admin_main_menu()
    )


@router.callback_query(F.data == "admin_set_cardholder")
async def cb_set_cardholder(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    await state.set_state(AdminDashboardStates.waiting_for_cardholder)
    await callback.message.answer(
        "👤 <b>Yangi karta egasining ism-sharifini kiriting</b> (masalan: <code>Falonchi Pismadonchiyev</code>):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminDashboardStates.waiting_for_cardholder)
async def handle_set_cardholder(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.from_user.id not in settings.all_admin_ids:
        return
    holder = (message.text or "").strip()
    if len(holder) < 3:
        await message.answer("❌ Karta egasining ismi kamida 3 ta belgidan iborat bo‘lishi lozim.")
        return

    await SettingRepository.set_setting(session, None, "ad_cardholder_name", holder)
    settings.AD_CARDHOLDER_NAME = holder
    await AuditRepository.create(session, "setting_changed", details=f"ad_cardholder_name updated by {message.from_user.id}")
    await state.clear()
    await message.answer(
        f"✅ Karta egasi muvaffaqiyatli saqlandi: <b>{holder}</b>",
        parse_mode="HTML",
        reply_markup=get_admin_main_menu()
    )


@router.callback_query(F.data == "admin_set_price")
async def cb_set_price(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    await state.set_state(AdminDashboardStates.waiting_for_default_price)
    await callback.message.answer(
        f"💰 <b>Standart reklama narxini so‘mda kiriting</b> (masalan: <code>150000</code>)\n"
        f"Cheklovlar: {settings.MIN_AD_PRICE:,} — {settings.MAX_AD_PRICE:,} so‘m".replace(",", " "),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminDashboardStates.waiting_for_default_price)
async def handle_set_default_price(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.from_user.id not in settings.all_admin_ids:
        return
    raw = (message.text or "").replace(" ", "").replace(",", "").strip()
    if not raw.isdigit():
        await message.answer("❌ Narx faqat butun musbat son bo‘lishi lozim.")
        return
    price = int(raw)
    if price < settings.MIN_AD_PRICE or price > settings.MAX_AD_PRICE:
        await message.answer(
            f"❌ Narx {settings.MIN_AD_PRICE:,} dan {settings.MAX_AD_PRICE:,} so‘mgacha bo‘lishi lozim.".replace(",", " ")
        )
        return

    await SettingRepository.set_setting(session, None, "ad_price", str(price))
    settings.AD_PRICE = price
    await AuditRepository.create(session, "setting_changed", details=f"ad_price updated to {price} by {message.from_user.id}")
    await state.clear()
    await message.answer(
        f"✅ Standart reklama narxi muvaffaqiyatli saqlandi: <b>{price:,} so‘m</b>".replace(",", " "),
        parse_mode="HTML",
        reply_markup=get_admin_main_menu()
    )


@router.callback_query(F.data == "admin_set_target_group")
async def cb_set_target_group(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    await state.set_state(AdminDashboardStates.waiting_for_target_group)
    await callback.message.answer(
        "🎯 <b>Moderatsiya qilinadigan guruh ID raqamini kiriting</b> (masalan: <code>-1001234567890</code>)\n"
        "Barcha guruhlar uchun bo‘sh qoldirish yoki <code>0</code> yozishingiz mumkin:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminDashboardStates.waiting_for_target_group)
async def handle_set_target_group(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.from_user.id not in settings.all_admin_ids:
        return
    gid_raw = (message.text or "").strip()
    val = "" if gid_raw in ("0", "") else gid_raw
    await SettingRepository.set_setting(session, None, "target_group_id", val)
    settings.TARGET_GROUP_ID = val
    await AuditRepository.create(session, "setting_changed", details=f"target_group_id updated to {val} by {message.from_user.id}")
    await state.clear()
    await message.answer(
        f"✅ Moderatsiya guruhi sozlandi: <code>{val or 'Barcha guruhlar'}</code>",
        parse_mode="HTML",
        reply_markup=get_admin_main_menu()
    )


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "admin_main_menu")
async def cb_main_menu(callback: CallbackQuery) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    user = callback.from_user
    text = (
        f"Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
        f"🛡 <b>Defender Bot Admin Paneli</b>ga xush kelibsiz.\n"
        f"Quyidagi menyu orqali botni boshqarishingiz mumkin:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_main_menu())


# ==========================================
# /olx Command & OLX Management Callbacks
# ==========================================
async def _build_olx_status_text(session: AsyncSession) -> Tuple[str, bool]:
    session_status = OlxService.get_session_status()
    metrics = await AdvertisingRequestRepository.get_olx_metrics(session)

    db_val = await SettingRepository.get_setting(session, None, "olx_auto_post")
    if db_val is not None:
        auto_post = db_val.lower() in ("true", "1", "yes")
    else:
        auto_post = getattr(settings, "OLX_AUTO_POST", True)

    status_icon = "🟢 Faol" if session_status["is_valid"] else "🔴 Ulangan emas"
    auto_icon = "🟢 Yoqilgan" if auto_post else "🔴 O‘chirilgan"

    text = (
        "🌐 <b>OLX.uz INTEGRATSIYASI VA BOSHQARUVI:</b>\n\n"
        f"• Ulanish holati: <b>{status_icon}</b>\n"
        f"• Foydalanuvchi: <b>{session_status.get('account_name') or 'Noma’lum'}</b>\n"
        f"• Sessiya fayli: <code>{session_status.get('updated_at') or 'Mavjud emas'}</code>\n"
        f"• Avtomatik e’lon: <b>{auto_icon}</b>\n\n"
        "📊 <b>E’lonlar statistikasi:</b>\n"
        f"• Jami so‘rovlar: <b>{metrics['total_requests']} ta</b>\n"
        f"• OLX ga chiqqan: <b>{metrics['olx_published']} ta</b>\n"
        f"• Jarayonda: <b>{metrics['olx_pending']} ta</b>\n"
        f"• Xatolik bo‘lgan: <b>{metrics['olx_failed']} ta</b>\n\n"
        "<i>Sozlamalarni o‘zgartirish uchun quyidagi tugmalardan foydalaning:</i>"
    )
    return text, auto_post


@router.message(Command("olx"))
async def cmd_olx(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return
    text, auto_post = await _build_olx_status_text(session)
    await message.reply(text, parse_mode="HTML", reply_markup=get_olx_admin_kb(auto_post))


@router.callback_query(F.data == "admin_olx_menu")
async def cb_olx_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    text, auto_post = await _build_olx_status_text(session)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_olx_admin_kb(auto_post))


@router.callback_query(F.data == "admin_olx_toggle_auto")
async def cb_olx_toggle_auto(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user.id not in settings.all_admin_ids:
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return

    db_val = await SettingRepository.get_setting(session, None, "olx_auto_post")
    if db_val is not None:
        curr = db_val.lower() in ("true", "1", "yes")
    else:
        curr = getattr(settings, "OLX_AUTO_POST", True)

    new_val = not curr
    await SettingRepository.set_setting(session, None, "olx_auto_post", "true" if new_val else "false")
    settings.OLX_AUTO_POST = new_val

    await AuditRepository.create(
        session,
        "setting_changed",
        details=f"OLX auto-post toggled to {new_val} by {callback.from_user.id}"
    )

    text, auto_post = await _build_olx_status_text(session)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_olx_admin_kb(auto_post))
    await callback.answer(f"Avto-e’lon {'yoqildi' if new_val else 'o‘chirildi'}.")


@router.callback_query(F.data == "admin_olx_check_session")
async def cb_olx_check_session(callback: CallbackQuery) -> None:
    st = OlxService.get_session_status()
    if st["is_valid"]:
        msg = f"✅ OLX sessiyasi faol!\nOxirgi yangilanish: {st.get('updated_at')}"
    else:
        msg = "❌ OLX sessiyasi topilmadi yoki eskirgan. Admin panel orqali yangilang."
    await callback.answer(msg, show_alert=True)


# ==========================================
# /clusters Command (AI Semantic Ad Clusters)
# ==========================================
@router.message(Command("clusters"))
async def cmd_clusters(message: Message, bot: Bot, session: AsyncSession) -> None:
    if not await is_authorized(message, bot):
        await message.reply(NO_PERMISSION_TEXT)
        return

    ad_texts = await AdvertisementRepository.get_all_texts(session, limit=500)
    if not ad_texts:
        await message.reply("📊 Hozircha klasterlash uchun yetarli reklama xabarlari mavjud emas.")
        return

    clusters = ClusterService.cluster_advertisements(ad_texts)
    if not clusters:
        await message.reply("📊 Hozircha faol reklama klasterlari aniqlanmadi.")
        return

    lines = ["🧠 <b>AI REKLAMA KLASTERLARI VA KAMPANIYALAR:</b>\n"]
    for c in clusters[:6]:
        kws_str = ", ".join(c.keywords[:4]) if c.keywords else "aniqlanmoqda"
        samples_preview = ""
        if c.sample_texts:
            sample_clean = c.sample_texts[0].replace("\n", " ")[:60]
            samples_preview = f"\n  <i>Namuna:</i> \"{sample_clean}...\""

        lines.append(
            f"🔹 <b>Klaster #{c.cluster_id}: {c.topic}</b>\n"
            f"• Xabarlar soni: <b>{c.message_count} ta</b>\n"
            f"• Reklama ishonchliligi: <b>{c.confidence_pct}%</b>\n"
            f"• Kalit so‘zlar: <code>{kws_str}</code>"
            f"{samples_preview}\n"
        )

    await message.reply("\n".join(lines), parse_mode="HTML")
