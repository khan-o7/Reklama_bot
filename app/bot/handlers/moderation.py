from typing import Optional, List
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.bot.filters.chat_type_filter import ChatTypeFilter
from app.services.content_extractor import ContentExtractor
from app.services.advertisement_detector import AdvertisementDetector
from app.services.moderation_service import ModerationService
from app.services.statistics_service import StatisticsService
from app.services.cache_service import cache
from app.services.user_behavior_service import UserBehaviorService
from app.services.active_learning_service import ActiveLearningService
from app.database.repositories.group_repo import GroupRepository
from app.database.repositories.setting_repo import SettingRepository
from app.utils.logger import logger

router = Router(name="moderation_router")


async def process_incoming_message(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    is_edited: bool = False,
    update_type: str = "message",
    album: Optional[List[Message]] = None
) -> None:
    """
    Unified multi-source message processing and moderation pipeline.
    
    Handles:
    - message, edited_message, channel_post, edited_channel_post
    - text, caption, photo OCR, and combined content
    - edit deduplication via content hash comparison
    - detailed detection auditing and progressive penalty escalation
    """
    chat_id = message.chat.id
    chat_type = message.chat.type

    # 1. Check Bot & System filter for groups
    if chat_type in ("group", "supergroup"):
        if settings.target_group_id_int and chat_id != settings.target_group_id_int:
            return
        from app.services.publication_service import PublicationService
        if PublicationService.is_bot_published(chat_id, message.message_id):
            logger.info(f"🛡️ Bot tomonidan tasdiqlangan va chop etilgan reklama o'tkazib yuborildi | chat={chat_id} msg={message.message_id}")
            return
        if message.from_user and message.from_user.is_bot:
            return
        if not message.from_user and not message.sender_chat:
            return

    # Increment statistics counter
    StatisticsService.increment_messages_checked()

    # 2. Extract Universal Content (text, caption, photo OCR, combined_text, hash)
    content = await ContentExtractor.extract_message_content(
        message=message,
        bot=bot,
        is_edited=is_edited,
        update_type=update_type,
        album=album
    )

    # 3. Content Hash Deduplication: If edited message content didn't change, avoid duplicate processing
    if content["is_duplicate"]:
        logger.debug(f"⏩ Tahrirlangan xabar o'zgarmagan (duplicate content hash) | chat={chat_id} msg={message.message_id}")
        return

    # If completely empty content with no text, caption, or links -> nothing to check
    if not content["combined_text"]:
        return

    user_id = content["user_id"]

    # 4. Fetch group / channel record and settings
    group_db = await GroupRepository.get_or_create(
        session=session,
        telegram_chat_id=chat_id,
        title=message.chat.title or ("Kanal" if chat_type == "channel" else "Guruh"),
        username=message.chat.username
    )

    group_settings = await SettingRepository.get_all_group_settings(session, group_db.id)
    if group_settings.get("enabled", "true").lower() != "true":
        return

    # 5. Check Admin Exemption (for groups/supergroups)
    if chat_type in ("group", "supergroup"):
        filter_admins = group_settings.get("filter_admins", "false").lower() == "true" or settings.FILTER_ADMINS
        if not filter_admins:
            # Anonymous admin posting as chat itself
            if message.sender_chat and message.sender_chat.id == chat_id:
                logger.info(f"🛡️ Guruh egasi/admini xabari o‘tkazib yuborildi | chat={chat_id}")
                return

            if user_id > 0:
                is_admin = await ModerationService.is_user_group_admin(bot, chat_id, user_id)
                if is_admin or user_id in settings.all_admin_ids:
                    logger.info(f"🛡️ Admin xabari o‘tkazib yuborildi (admin imtiyozi) | user={user_id} (@{message.from_user.username if message.from_user else 'anon'})")
                    return

    # 6. Synchronize Whitelist & Blacklist cache if TTL expired
    await cache.sync_with_db(session)

    # 7. Resolve Base Threshold & Behavioral Adjustment
    base_threshold = int(group_settings.get(
        "advertisement_threshold",
        str(settings.ADVERTISEMENT_THRESHOLD)
    ))

    # Preliminary Behavioral Metrics (for users)
    if user_id > 0:
        behavior_before = UserBehaviorService.get_user_metrics(user_id)
        effective_threshold = max(15, base_threshold - behavior_before["suggested_threshold_discount"])
    else:
        effective_threshold = base_threshold

    # 8. Execute Multi-Factor Advertisement Analysis on COMBINED content
    analysis = AdvertisementDetector.analyze_message(
        message=message,
        whitelist_domains=cache.get_whitelist(),
        blacklist_words=cache.get_blacklist_words(),
        blacklist_domains=cache.get_blacklist_domains(),
        blacklist_usernames=cache.get_blacklist_usernames(),
        threshold=effective_threshold,
        custom_text=content["combined_text"]
    )

    # 9. Update User Behavior Profile with current message signals
    if user_id > 0:
        UserBehaviorService.record_activity(
            user_id=user_id,
            chat_id=chat_id,
            text=content["combined_text"],
            url_count=len(analysis.get("links", [])),
            phone_count=len(analysis.get("phones", [])),
            promo_score=analysis.get("score", 0),
            is_promo=analysis.get("is_ad", False)
        )

    # 10. Comprehensive Detection Logging as requested
    decision_str = "REKLAMA (DELETE)" if analysis["is_ad"] else "TOZA (CLEAN)"
    logger.info(
        f"🔍 Detection Audit | update_type={update_type} | msg_id={content['message_id']} | "
        f"chat_id={content['chat_id']} | user_id={content['user_id']} | "
        f"is_edited={content['is_edited']} | has_photo={content['has_photo']} | "
        f"has_caption={bool(content['caption'])} | ocr_detected={bool(content['ocr_text'])} | "
        f"extracted_text='{content['text'][:40]}' | combined_text='{content['combined_text'][:60]}' | "
        f"risk_score={analysis['score']}/{effective_threshold} | "
        f"matched_keywords={analysis.get('matched_keywords', [])} | "
        f"final_decision={decision_str}"
    )

    # 11. Moderation Action if Flagged as Advertisement
    if analysis["is_ad"]:
        await ModerationService.handle_advertisement(
            bot=bot,
            message=message,
            analysis=analysis,
            session=session,
            content=content,
            album=album
        )
    else:
        # 12. Active Learning: If score is in ambiguous boundary (25-40), prompt admins
        if not is_edited and user_id > 0 and chat_type in ("group", "supergroup"):
            uncertain, _ = ActiveLearningService.calculate_uncertainty(analysis["score"], base_threshold)
            if uncertain:
                await ActiveLearningService.request_admin_label(
                    bot=bot,
                    message=message,
                    analysis=analysis,
                    session=session
                )


# =========================================================================
# Registered Telegram Update Handlers (message, edited_message, channel_post, edited_channel_post)
# =========================================================================

@router.message(ChatTypeFilter(["group", "supergroup"]))
async def handle_new_group_message(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    album: Optional[List[Message]] = None
) -> None:
    """Handles regular messages in groups and supergroups."""
    await process_incoming_message(message, bot, session, is_edited=False, update_type="message", album=album)


@router.edited_message(ChatTypeFilter(["group", "supergroup"]))
async def handle_edited_group_message(message: Message, bot: Bot, session: AsyncSession) -> None:
    """Handles edited messages in groups and supergroups."""
    await process_incoming_message(message, bot, session, is_edited=True, update_type="edited_message")


@router.channel_post(ChatTypeFilter(["channel"]))
async def handle_new_channel_post(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    album: Optional[List[Message]] = None
) -> None:
    """Handles new channel posts."""
    await process_incoming_message(message, bot, session, is_edited=False, update_type="channel_post", album=album)


@router.edited_channel_post(ChatTypeFilter(["channel"]))
async def handle_edited_channel_post(message: Message, bot: Bot, session: AsyncSession) -> None:
    """Handles edited channel posts."""
    await process_incoming_message(message, bot, session, is_edited=True, update_type="edited_channel_post")


# =========================================================================
# Active Learning Admin Verification Callbacks
# =========================================================================

@router.callback_query(F.data.startswith("al_ad:"))
async def handle_active_learning_ad(callback: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    """Admin confirmed an ambiguous message as Advertisement."""
    parts = callback.data.split(":")
    sample_id = int(parts[1])
    chat_id = int(parts[2])
    msg_id = int(parts[3])

    await callback.answer("🚨 Reklama deb belgilandi va saqlandi.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Delete message from group if still exists
    try:
        await bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception as e:
        logger.debug(f"Could not delete message after active learning label: {e}")

    result = await ActiveLearningService.process_feedback(sample_id=sample_id, is_ad=True, session=session)
    if callback.message:
        await callback.message.reply(
            f"🚨 <b>Xabar REKLAMA deb belgilandi va guruhdan o‘chirildi!</b>\n"
            f"📊 Jami belgilangan misollar: <b>{result['total_labeled']} ta</b>",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("al_clean:"))
async def handle_active_learning_clean(callback: CallbackQuery, session: AsyncSession) -> None:
    """Admin confirmed an ambiguous message as Clean (False Positive control)."""
    parts = callback.data.split(":")
    sample_id = int(parts[1])

    await callback.answer("✅ Toza xabar deb tasdiqlandi.")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    result = await ActiveLearningService.process_feedback(sample_id=sample_id, is_ad=False, session=session)
    if callback.message:
        await callback.message.reply(
            f"✅ <b>Xabar TOZA deb tasdiqlandi (False Positive nazorati).</b>\n"
            f"📊 Jami belgilangan misollar: <b>{result['total_labeled']} ta</b>",
            parse_mode="HTML"
        )
