import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from aiogram import Bot
from aiogram.types import Message, ChatPermissions
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
    TelegramNetworkError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.group_repo import GroupRepository
from app.database.repositories.ad_repo import AdvertisementRepository
from app.database.repositories.warning_repo import WarningRepository
from app.database.repositories.setting_repo import SettingRepository
from app.database.repositories.audit_repo import AuditRepository
from app.bot.keyboards.warning_kb import get_warning_keyboard
from app.services.notification_service import NotificationService
from app.utils.logger import logger


class ModerationService:
    @staticmethod
    async def is_user_group_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
        """Checks if a user is administrator or creator of the chat."""
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            return member.status in ("creator", "administrator")
        except Exception:
            return False

    @staticmethod
    async def schedule_message_deletion(bot: Bot, chat_id: int, message_id: int, delay_seconds: int) -> None:
        """Asynchronously deletes a message after delay_seconds."""
        async def _delete_task():
            try:
                await asyncio.sleep(delay_seconds)
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                logger.debug(f"Could not auto-delete warning message {message_id}: {e}")

        asyncio.create_task(_delete_task())

    @staticmethod
    async def apply_penalty_action(
        bot: Bot,
        chat_id: int,
        user_id: int,
        action: str
    ) -> str:
        """
        Executes escalation action: warning, mute_10m, mute_1h, mute_24h, ban.
        Returns description string for warning message.
        """
        now = datetime.now(timezone.utc)
        action_desc = ""

        try:
            if action == "mute_10m":
                until_date = now + timedelta(minutes=10)
                await bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until_date
                )
                action_desc = "🔇 <b>10 daqiqa yozishdan cheklash (MUTE) qo‘llanildi.</b>"
            elif action == "mute_1h":
                until_date = now + timedelta(hours=1)
                await bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until_date
                )
                action_desc = "🔇 <b>1 soat yozishdan cheklash (MUTE) qo‘llanildi.</b>"
            elif action == "mute_24h":
                until_date = now + timedelta(days=1)
                await bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until_date
                )
                action_desc = "🔇 <b>24 soat yozishdan cheklash (MUTE) qo‘llanildi.</b>"
            elif action == "ban":
                await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            err_msg = str(e).lower()
            if "can't remove chat owner" in err_msg or "chat owner" in err_msg:
                logger.info(f"Foydalanuvchi {user_id} guruh egasi (creator), unga jazo qo‘llanmaydi, faqat reklama o‘chirildi.")
                action_desc = "👑 <i>(Guruh egasiga cheklov qo‘llanmaydi)</i>"
            else:
                logger.error(f"Cannot execute penalty action {action} for user {user_id} in {chat_id}: {e}")
                action_desc = "⚠️ <i>(Botda foydalanuvchini jazolash huquqi yetarli emas)</i>"

        return action_desc

    @staticmethod
    async def handle_advertisement(
        bot: Bot,
        message: Message,
        analysis: Dict[str, Any],
        session: AsyncSession
    ) -> None:
        """
        Full orchestration workflow:
        1. Register user & group in DB
        2. Delete message
        3. Save advertisement
        4. Send admin alerts
        5. Warn user with inline keyboard
        6. Schedule warning deletion
        7. Escalation penalty (Mute/Ban)
        8. Audit logging
        """
        user = message.from_user
        chat_id = message.chat.id

        # Channel post handling (no individual user)
        if not user:
            group_db = await GroupRepository.get_or_create(
                session=session,
                telegram_chat_id=chat_id,
                title=message.chat.title or "Kanal",
                username=message.chat.username
            )
            deleted_success = False
            for del_attempt in range(1, 4):
                try:
                    await message.delete()
                    deleted_success = True
                    logger.warning(f"Channel advertisement deleted | chat={chat_id} msg={message.message_id}")
                    break
                except TelegramRetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                except TelegramNetworkError as net_err:
                    logger.warning(f"Kanal xabarini o‘chirishda tarmoq xatosi ({del_attempt}/3): {net_err}")
                    await asyncio.sleep(1)
                except (TelegramBadRequest, TelegramForbiddenError) as e:
                    logger.error(f"Failed to delete channel ad message {message.message_id} in {chat_id}: {e}")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error deleting channel ad message {message.message_id} in {chat_id}: {e}")
                    break

            asyncio.create_task(
                NotificationService.send_to_admins(
                    bot=bot,
                    message=message,
                    analysis=analysis,
                    deleted=deleted_success
                )
            )
            return

        user_id = user.id

        # Fetch or register group
        group_db = await GroupRepository.get_or_create(
            session=session,
            telegram_chat_id=chat_id,
            title=message.chat.title or "Guruh",
            username=message.chat.username
        )

        # Fetch or register user
        user_db = await UserRepository.get_or_create(
            session=session,
            telegram_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        # Fetch group settings
        group_settings = await SettingRepository.get_all_group_settings(session, group_db.id)
        if group_settings.get("enabled", "true").lower() != "true":
            return

        delete_ads = group_settings.get("delete_ads", "true").lower() == "true"
        warning_enabled = group_settings.get("warning_enabled", "true").lower() == "true"
        del_sec = int(group_settings.get("warning_delete_seconds", str(settings.WARNING_DELETE_SECONDS)))

        logger.warning(f"Advertisement detected | user={user_id} | chat={chat_id} | score={analysis.get('score')}")

        # 1. IMMEDIATE Message Deletion from Group (Top Priority!)
        deleted_success = False
        if delete_ads:
            for del_attempt in range(1, 4):
                try:
                    await message.delete()
                    deleted_success = True
                    logger.info(f"🗑️ Reklama xabari guruhdan o‘chirildi | chat={chat_id} msg={message.message_id}")
                    break
                except TelegramRetryAfter as e:
                    logger.warning(f"Telegram flood limit: {e.retry_after}s kutilmoqda...")
                    await asyncio.sleep(e.retry_after)
                except TelegramNetworkError as net_err:
                    logger.warning(f"Tarmoq uzilishi tufayli xabarni o‘chirishda urinish {del_attempt}/3 ({net_err}). Qayta urinilmoqda...")
                    await asyncio.sleep(1)
                except (TelegramBadRequest, TelegramForbiddenError) as e:
                    logger.error(f"Failed to delete ad message {message.message_id} in chat {chat_id}: {e}")
                    break
                except Exception as e:
                    logger.error(f"Kutilmagan xatolik tufayli xabar o‘chirilmadi: {e}")
                    break

        # 2. Asynchronous Admin Notification (Does NOT block or abort moderation)
        asyncio.create_task(
            NotificationService.send_to_admins(
                bot=bot,
                message=message,
                analysis=analysis,
                deleted=deleted_success
            )
        )

        # 3. Record Advertisement in DB
        raw_text = message.text or ""
        caption = message.caption or ""
        links_str = ", ".join(analysis.get("links", []))
        reasons_str = "; ".join(analysis.get("reasons", []))

        ad_record = await AdvertisementRepository.create(
            session=session,
            group_id=group_db.id,
            user_id=user_db.id,
            telegram_message_id=message.message_id,
            message_type=analysis.get("message_type", "TEXT"),
            text=raw_text if raw_text else None,
            caption=caption if caption else None,
            detected_links=links_str if links_str else None,
            score=analysis.get("score", 0),
            detection_reason=reasons_str,
            deleted=deleted_success
        )

        # 4. Increment User Warnings Count
        warnings_count = await UserRepository.increment_warnings(session, user_db.id)

        # 5. Determine Escalation Action
        action_to_take = "warning"
        if warnings_count == 1:
            action_to_take = group_settings.get("first_action", settings.FIRST_ACTION)
        elif warnings_count == 2:
            action_to_take = group_settings.get("second_action", settings.SECOND_ACTION)
        elif warnings_count == 3:
            action_to_take = group_settings.get("third_action", settings.THIRD_ACTION)
        else:
            action_to_take = group_settings.get("fourth_action", settings.FOURTH_ACTION)

        penalty_text = ""
        if action_to_take != "warning":
            penalty_text = await ModerationService.apply_penalty_action(
                bot=bot,
                chat_id=chat_id,
                user_id=user_id,
                action=action_to_take
            )
            if "mute" in action_to_take:
                await UserRepository.set_muted(session, user_db.id, True)
            elif action_to_take == "ban":
                await UserRepository.set_banned(session, user_db.id, True)

        # 6. Record Warning Entry in DB
        await WarningRepository.create(
            session=session,
            user_id=user_db.id,
            group_id=group_db.id,
            advertisement_id=ad_record.id,
            warning_type=action_to_take
        )

        # 7. Send Otmetka Warning to User in Group
        if warning_enabled:
            # Format user mention
            user_mention = f"@{user.username}" if user.username else f'<a href="tg://user?id={user_id}">{user.full_name}</a>'

            if warnings_count == 1:
                warn_msg_content = (
                    f"⚠️ <b>REKLAMA TAQIQLANGAN!</b>\n\n"
                    f"Hurmatli {user_mention}, guruhda ruxsatsiz reklama tarqatish taqiqlangan!\n"
                    f"Reklama bermoqchi bo‘lsangiz, <b>botga murojaat qiling!</b>\n\n"
                    f"📊 <b>Holat:</b> 1-ogohlantirish\n"
                    f"⚡️ <i>Eslatma: Yana reklama yuborsangiz, 10 daqiqa yozishdan cheklanasiz (MUTE).</i>"
                )
            elif warnings_count == 2:
                warn_msg_content = (
                    f"⚠️ <b>QAYTA REKLAMA ANIQLANDI!</b>\n\n"
                    f"Hurmatli {user_mention}, sizga avval ogohlantirish berilgan edi.\n\n"
                    f"📊 <b>Holat:</b> 2-ogohlantirish\n"
                    f"🔇 <b>Jazo:</b> 10 daqiqaga guruhda yozish cheklandi (MUTE).\n"
                    f"⚡️ <i>Eslatma: Keyingi reklamada 1 soatlik MUTE qo‘llaniladi.</i>"
                )
            elif warnings_count == 3:
                warn_msg_content = (
                    f"⚠️ <b>QAYTA REKLAMA ANIQLANDI!</b>\n\n"
                    f"Hurmatli {user_mention}, qoidabuzarlik davom etmoqda.\n\n"
                    f"📊 <b>Holat:</b> 3-ogohlantirish\n"
                    f"🔇 <b>Jazo:</b> 1 soatga guruhda yozish cheklandi (MUTE).\n"
                    f"🚫 <i>Eslatma: Yana reklama yuborsangiz, guruhdan butunlay chetlatilasiz (BAN).</i>"
                )
            else:
                warn_msg_content = (
                    f"🚫 <b>GURUHDAN CHETLATILDI (BAN)!</b>\n\n"
                    f"Foydalanuvchi {user_mention} ketma-ket reklama tashlagani sababli guruhdan butunlay chetlatildi (BAN)."
                )

            if penalty_text and "yetarli emas" in penalty_text:
                warn_msg_content += f"\n\n{penalty_text}"

            try:
                bot_user = await bot.get_me()
                sent_warning = await bot.send_message(
                    chat_id=chat_id,
                    text=warn_msg_content,
                    parse_mode="HTML",
                    reply_markup=get_warning_keyboard(bot_username=bot_user.username)
                )
                # Auto-delete warning message after N seconds
                if del_sec > 0:
                    await ModerationService.schedule_message_deletion(
                        bot=bot,
                        chat_id=chat_id,
                        message_id=sent_warning.message_id,
                        delay_seconds=del_sec
                    )
            except Exception as e:
                logger.error(f"Failed to send warning message in chat {chat_id}: {e}")

        # 8. Record Audit Log
        await AuditRepository.create(
            session=session,
            event_type="advertisement_detected",
            group_id=group_db.id,
            user_id=user_db.id,
            details=f"score={analysis.get('score')} | action={action_to_take} | warnings={warnings_count}"
        )
