import re
from datetime import datetime, timedelta, timezone
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ChatPermissions
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.group_repo import GroupRepository
from app.database.repositories.list_repo import ListRepository
from app.database.repositories.setting_repo import SettingRepository
from app.database.repositories.audit_repo import AuditRepository
from app.services.statistics_service import StatisticsService
from app.services.cache_service import cache
from app.bot.keyboards.admin_kb import get_admin_main_menu, get_back_to_admin_menu
from app.utils.logger import logger

router = Router(name="admin_router")

NO_PERMISSION_TEXT = "❌ Sizda bu buyruqdan foydalanish huquqi yo‘q."


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
    text = await StatisticsService.get_statistics(session)
    await message.reply(text, parse_mode="HTML")


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
    text = await StatisticsService.get_statistics(session)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_to_admin_menu())


@router.callback_query(F.data == "admin_status")
async def cb_status(callback: CallbackQuery, session: AsyncSession) -> None:
    text = await StatisticsService.get_bot_status(session)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_to_admin_menu())


@router.callback_query(F.data == "admin_logs")
async def cb_logs(callback: CallbackQuery, session: AsyncSession) -> None:
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
    items = await ListRepository.get_all_whitelist(session)
    doms = "\n".join([f"• <code>{i.value}</code>" for i in items]) if items else "• <i>Qo‘shimcha domenlar yo‘q</i>"
    text = f"🛡 <b>OQ RO‘YXAT (WHITELIST):</b>\n\n{doms}\n\n<i>Qo‘shish:</i> <code>/whitelist add domen.uz</code>"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_to_admin_menu())


@router.callback_query(F.data == "admin_blacklist")
async def cb_blacklist(callback: CallbackQuery, session: AsyncSession) -> None:
    items = await ListRepository.get_all_blacklist(session)
    bls = "\n".join([f"• [{i.type}] <code>{i.value}</code>" for i in items]) if items else "• <i>Hozircha bo‘sh</i>"
    text = f"🚫 <b>QORA RO‘YXAT (BLACKLIST):</b>\n\n{bls}\n\n<i>Qo‘shish:</i> <code>/blacklist add word so'z</code>"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_to_admin_menu())


@router.callback_query(F.data == "admin_settings")
async def cb_settings(callback: CallbackQuery, session: AsyncSession) -> None:
    all_s = await SettingRepository.get_all_group_settings(session, None)
    lines = ["⚙️ <b>GLOBAL BOT SOZLAMALARI:</b>\n"]
    for k, v in list(all_s.items())[:8]:
        lines.append(f"• <b>{k}</b>: <code>{v}</code>")
    text = "\n".join(lines)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_to_admin_menu())


@router.callback_query(F.data == "admin_main_menu")
async def cb_main_menu(callback: CallbackQuery) -> None:
    user = callback.from_user
    text = (
        f"Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
        f"🛡 <b>Defender Bot Admin Paneli</b>ga xush kelibsiz.\n"
        f"Quyidagi menyu orqali botni boshqarishingiz mumkin:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_main_menu())
