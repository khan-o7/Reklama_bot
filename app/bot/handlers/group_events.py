from aiogram import Router, Bot
from aiogram.types import ChatMemberUpdated
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION, PROMOTED_TRANSITION, KICKED
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.group_repo import GroupRepository
from app.database.repositories.audit_repo import AuditRepository
from app.utils.logger import logger

router = Router(name="group_events_router")


@router.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION | PROMOTED_TRANSITION))
async def bot_added_or_promoted(event: ChatMemberUpdated, bot: Bot, session: AsyncSession) -> None:
    """Triggered when bot is added to a group or promoted to administrator."""
    chat = event.chat
    new_member = event.new_chat_member

    logger.info(f"Bot membership updated in chat {chat.title} ({chat.id}): status={new_member.status}")

    # Register or activate group in DB
    group = await GroupRepository.get_or_create(
        session=session,
        telegram_chat_id=chat.id,
        title=chat.title or "Noma'lum guruh",
        username=chat.username
    )

    await AuditRepository.create(
        session=session,
        event_type="bot_added_to_group",
        group_id=group.id,
        details=f"title={chat.title} | status={new_member.status}"
    )

    # Check if bot has required administrator permissions
    if new_member.status != "administrator":
        warning_text = (
            "⚠️ <b>Botga administrator huquqi berilmagan!</b>\n\n"
            "Bot reklamalarni avtomatik o‘chirishi va guruhni himoya qilishi uchun "
            "iltimos botga <b>Administrator</b> maqomini bering."
        )
        try:
            await bot.send_message(chat_id=chat.id, text=warning_text, parse_mode="HTML")
        except Exception as e:
            logger.debug(f"Could not send admin warning to chat {chat.id}: {e}")
        return

    # Check specific administrator rights
    missing_rights = []
    if not getattr(new_member, "can_delete_messages", False):
        missing_rights.append("• Xabarlarni o‘chirish (Delete messages)")
    if not getattr(new_member, "can_restrict_members", False):
        missing_rights.append("• Foydalanuvchilarni cheklash (Restrict members)")

    if missing_rights:
        missing_str = "\n".join(missing_rights)
        warning_text = (
            "⚠️ <b>Administrator huquqlari to‘liq berilmagan!</b>\n\n"
            "Bot to‘liq ishlashi uchun quyidagi huquqlarni yoqing:\n"
            f"{missing_str}"
        )
        try:
            await bot.send_message(chat_id=chat.id, text=warning_text, parse_mode="HTML")
        except Exception as e:
            logger.debug(f"Could not send rights warning to chat {chat.id}: {e}")
    else:
        welcome_text = (
            "✅ <b>Defender Bot muvaffaqiyatli faollashtirildi!</b>\n\n"
            "Guruhdagi barcha xabarlar va reklamalar real vaqt rejimida nazorat qilinadi."
        )
        try:
            await bot.send_message(chat_id=chat.id, text=welcome_text, parse_mode="HTML")
        except Exception:
            pass


@router.my_chat_member(ChatMemberUpdatedFilter(KICKED))
async def bot_removed_from_group(event: ChatMemberUpdated, session: AsyncSession) -> None:
    """Triggered when bot is removed/banned from a group."""
    chat = event.chat
    logger.info(f"Bot was removed from chat {chat.title} ({chat.id})")
    await GroupRepository.set_active_status(session, chat.id, is_active=False)
    await AuditRepository.create(
        session=session,
        event_type="bot_removed_from_group",
        details=f"chat_id={chat.id} | title={chat.title}"
    )
