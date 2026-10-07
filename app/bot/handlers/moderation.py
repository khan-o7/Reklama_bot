from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.bot.filters.chat_type_filter import ChatTypeFilter
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


@router.message(ChatTypeFilter(["group", "supergroup"]))
async def monitor_group_messages(message: Message, bot: Bot, session: AsyncSession) -> None:
    """
    Main real-time watchdog handler for all group/supergroup messages.
    Integrates Multi-factor scoring, User Behavioral Profiling, and Active Learning.
    """
    # Ignore system events, anonymous channels, or bot messages
    if not message.from_user or message.from_user.is_bot:
        return

    # Increment in-memory checked messages counter
    StatisticsService.increment_messages_checked()

    user_id = message.from_user.id
    chat_id = message.chat.id

    # 1. Fetch group record and settings
    group_db = await GroupRepository.get_or_create(
        session=session,
        telegram_chat_id=chat_id,
        title=message.chat.title or "Guruh",
        username=message.chat.username
    )

    group_settings = await SettingRepository.get_all_group_settings(session, group_db.id)
    if group_settings.get("enabled", "true").lower() != "true":
        return

    # 2. Check Admin Exemption
    filter_admins = group_settings.get("filter_admins", "false").lower() == "true" or settings.FILTER_ADMINS
    if not filter_admins:
        is_admin = await ModerationService.is_user_group_admin(bot, chat_id, user_id)
        if is_admin or user_id in settings.all_admin_ids:
            logger.info(f"🛡️ Admin xabari o‘tkazib yuborildi (admin imtiyozi) | user={user_id} (@{message.from_user.username or 'anon'})")
            return

    # 3. Synchronize Whitelist & Blacklist cache if TTL expired
    await cache.sync_with_db(session)

    # 4. Resolve Base Threshold & Behavioral Adjustment
    base_threshold = int(group_settings.get(
        "advertisement_threshold",
        str(settings.ADVERTISEMENT_THRESHOLD)
    ))

    # Preliminary Behavioral Metrics
    behavior_before = UserBehaviorService.get_user_metrics(user_id)
    effective_threshold = max(15, base_threshold - behavior_before["suggested_threshold_discount"])

    # 5. Execute Multi-Factor Advertisement Analysis
    analysis = AdvertisementDetector.analyze_message(
        message=message,
        whitelist_domains=cache.get_whitelist(),
        blacklist_words=cache.get_blacklist_words(),
        blacklist_domains=cache.get_blacklist_domains(),
        blacklist_usernames=cache.get_blacklist_usernames(),
        threshold=effective_threshold
    )

    # 6. Update User Behavior Profile with current message signals
    behavior = UserBehaviorService.record_activity(
        user_id=user_id,
        chat_id=chat_id,
        text=message.text or message.caption or "",
        url_count=len(analysis.get("links", [])),
        phone_count=len(analysis.get("phones", [])),
        promo_score=analysis.get("score", 0),
        is_promo=analysis.get("is_ad", False)
    )

    logger.info(
        f"🔍 Xabar tahlili | user={user_id} | score={analysis['score']}/{effective_threshold} | "
        f"adv_prob={behavior['advertiser_probability']*100:.0f}% | is_ad={analysis['is_ad']}"
    )

    # 7. Moderation action if flagged as ad
    if analysis["is_ad"]:
        await ModerationService.handle_advertisement(
            bot=bot,
            message=message,
            analysis=analysis,
            session=session
        )
    else:
        # 8. Active Learning: If score is in ambiguous boundary (25-40), prompt admins for verification
        uncertain, _ = ActiveLearningService.calculate_uncertainty(analysis["score"], base_threshold)
        if uncertain:
            await ActiveLearningService.request_admin_label(
                bot=bot,
                message=message,
                analysis=analysis,
                session=session
            )


# ==========================================
# Active Learning Admin Callbacks
# ==========================================
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
