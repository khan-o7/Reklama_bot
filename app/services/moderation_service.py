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
        session: AsyncSession,
        content: Optional[Dict[str, Any]] = None,
        album: Optional[list] = None
    ) -> None:
        """
        Full orchestration workflow:
        1. Register user & group in DB
        2. Delete message from group
        3. Save detailed advertisement record
        4. Create commercial order
        5. Send admin alerts with [💰 Narx belgilash] button
        6. Warn user with deep-link [📩 Reklama joylashtirish] button
        7. Escalation penalty (Mute/Ban)
        8. Audit logging
        """
        from app.services.order_service import OrderService

        user = message.from_user
        chat_id = message.chat.id
        content = content or {}

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
            messages_to_delete = album if album else [message]
            for msg_item in messages_to_delete:
                for del_attempt in range(1, 4):
                    try:
                        await msg_item.delete()
                        deleted_success = True
                        break
                    except TelegramRetryAfter as e:
                        logger.warning(f"Telegram flood limit: {e.retry_after}s kutilmoqda...")
                        await asyncio.sleep(e.retry_after)
                    except TelegramNetworkError as net_err:
                        logger.warning(f"Tarmoq uzilishi tufayli xabarni o‘chirishda urinish {del_attempt}/3 ({net_err}). Qayta urinilmoqda...")
                        await asyncio.sleep(1)
                    except (TelegramBadRequest, TelegramForbiddenError) as e:
                        logger.error(f"Failed to delete ad message {getattr(msg_item, 'message_id', 0)} in chat {chat_id}: {e}")
                        break
                    except Exception as e:
                        logger.error(f"Kutilmagan xatolik tufayli xabar o‘chirilmadi: {e}")
                        break
            if deleted_success:
                logger.info(f"🗑️ Reklama xabari ({len(messages_to_delete)} ta xabar/media) guruhdan o‘chirildi | chat={chat_id}")

        # 2. Record Advertisement in DB with media metadata
        raw_text = content.get("text") or getattr(message, "text", "") or ""
        caption = content.get("caption") or getattr(message, "caption", "") or ""
        links_str = ", ".join(analysis.get("links", []))
        reasons_str = "; ".join(analysis.get("reasons", []))
        keywords_str = ", ".join(analysis.get("matched_keywords", []))

        ad_record = await AdvertisementRepository.create(
            session=session,
            group_id=group_db.id,
            user_id=user_db.id,
            telegram_message_id=message.message_id,
            chat_id=chat_id,
            username=user.username,
            first_name=user.first_name,
            message_type=analysis.get("message_type", "TEXT"),
            media_type=content.get("media_type", "TEXT"),
            media_file_id=content.get("media_file_id"),
            media_file_unique_id=content.get("media_file_unique_id"),
            text=raw_text if raw_text else None,
            caption=caption if caption else None,
            original_text=raw_text if raw_text else None,
            original_caption=caption if caption else None,
            ocr_text=content.get("ocr_text"),
            combined_text=content.get("combined_text"),
            detected_links=links_str if links_str else None,
            detected_keywords=keywords_str if keywords_str else None,
            score=analysis.get("score", 0),
            risk_score=analysis.get("score", 0),
            detection_reason=reasons_str,
            deleted=deleted_success,
            status="DELETED"
        )

        # 3. Create Commercial Order
        order = await OrderService.create_order_for_ad(session, ad_record)

        # 4. Asynchronous Admin Notification with Action Keyboard
        asyncio.create_task(
            NotificationService.send_to_admins(
                bot=bot,
                message=message,
                analysis=analysis,
                deleted=deleted_success,
                ad_id=ad_record.id,
                order_id=order.id if order else None,
                order_number=order.order_number if order else None
            )
        )

        # 4. Increment User Warnings Count
        warnings_count = await UserRepository.increment_warnings(session, user_db.id)

        # 5. Escalation Action:
        action_to_take = "warning"
        if settings.AUTO_MUTE or settings.AUTO_BAN:
            if group_settings.get("auto_mute", "false").lower() == "true" or group_settings.get("auto_ban", "false").lower() == "true":
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

        # 7. Send Exact Warning to User in Group (with User Mention/Tag)
        if warning_enabled:
            import html
            if user and user.username:
                user_mention = f"@{user.username}"
            elif user:
                safe_name = html.escape(user.full_name or user.first_name or "foydalanuvchi")
                user_mention = f'<a href="tg://user?id={user_id}">{safe_name}</a>'
            else:
                user_mention = "foydalanuvchi"

            custom_template = group_settings.get("warning_message")
            if custom_template and custom_template != SettingRepository.DEFAULT_SETTINGS.get("warning_message"):
                warn_msg_content = custom_template.replace("{user}", user_mention).replace("{mention}", user_mention)
            else:
                warn_msg_content = (
                    f"⚠️ <b>REKLAMA TAQIQLANGAN!</b>\n\n"
                    f"Hurmatli {user_mention}, guruhda ruxsatsiz reklama tarqatish taqiqlangan.\n"
                    f"Guruhga rasmiy e’lon joylashtirish uchun quyidagi <b>«📢 Reklama joylash»</b> tugmasi orqali botga o‘ting."
                )

            if penalty_text and "yetarli emas" not in penalty_text:
                warn_msg_content += f"\n\n{penalty_text}"

            try:
                bot_user = await bot.get_me()
                sent_warning = await bot.send_message(
                    chat_id=chat_id,
                    text=warn_msg_content,
                    parse_mode="HTML",
                    reply_markup=get_warning_keyboard(bot_username=bot_user.username, ad_id=ad_record.id)
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

        # 7.1 Send Private Message to Advertiser when possible (Section 4.4 step 5)
        async def _send_private_notice():
            try:
                bot_info = await bot.get_me()
                clean_bot = bot_info.username.lstrip("@") if bot_info and bot_info.username else ""
                deep_link = f"https://t.me/{clean_bot}?start=new_ad" if clean_bot else None
                pm_text = (
                    "Assalomu alaykum! Guruhda ruxsatsiz reklama joylashtirish taqiqlangan.\n\n"
                    "E’loningizni guruh qoidalariga mos rasmiy tartibda joylashtirish uchun quyidagi "
                    "<b>«📢 Reklama joylash»</b> tugmasini bosing va kerakli toifani tanlang:"
                )
                pm_kb = None
                if deep_link:
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    pm_kb = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text="📢 Reklama joylash", url=deep_link)
                    ]])
                await bot.send_message(chat_id=user_id, text=pm_text, parse_mode="HTML", reply_markup=pm_kb)
                logger.info(f"Foydalanuvchiga shaxsiy ogohlantirish (PM) yetkazildi | user={user_id}")
            except (TelegramForbiddenError, TelegramBadRequest):
                logger.debug(f"Foydalanuvchi {user_id} botni ishga tushirmagani sababli shaxsiy xabar yetkazib bo‘lmadi.")
            except Exception as pm_err:
                logger.debug(f"Shaxsiy xabar yuborishda xatolik ({user_id}): {pm_err}")

        asyncio.create_task(_send_private_notice())

        # 8. Record Audit Log
        await AuditRepository.create(
            session=session,
            event_type="advertisement_detected",
            group_id=group_db.id,
            user_id=user_db.id,
            details=f"score={analysis.get('score')} | action={action_to_take} | warnings={warnings_count}"
        )
