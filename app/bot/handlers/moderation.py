from aiogram import Router, Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.bot.filters.chat_type_filter import ChatTypeFilter
from app.services.advertisement_detector import AdvertisementDetector
from app.services.moderation_service import ModerationService
from app.services.statistics_service import StatisticsService
from app.services.cache_service import cache
from app.database.repositories.group_repo import GroupRepository
from app.database.repositories.setting_repo import SettingRepository
from app.utils.logger import logger

router = Router(name="moderation_router")


@router.message(ChatTypeFilter(["group", "supergroup"]))
async def monitor_group_messages(message: Message, bot: Bot, session: AsyncSession) -> None:
    """
    Main real-time watchdog handler for all group/supergroup messages.
    Inspects Text, Photo, Video, Document, Animation, etc. for commercial ads.
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
            # Skip checking admins
            return

    # 3. Synchronize Whitelist & Blacklist cache if TTL expired
    await cache.sync_with_db(session)

    # 4. Resolve Threshold
    threshold = int(group_settings.get(
        "advertisement_threshold",
        str(settings.ADVERTISEMENT_THRESHOLD)
    ))

    # 5. Execute Multi-Factor Advertisement Analysis
    analysis = AdvertisementDetector.analyze_message(
        message=message,
        whitelist_domains=cache.get_whitelist(),
        blacklist_words=cache.get_blacklist_words(),
        blacklist_domains=cache.get_blacklist_domains(),
        blacklist_usernames=cache.get_blacklist_usernames(),
        threshold=threshold
    )

    # 6. If detected as ad, execute moderation workflow
    if analysis["is_ad"]:
        await ModerationService.handle_advertisement(
            bot=bot,
            message=message,
            analysis=analysis,
            session=session
        )
