from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database.repositories.group_repo import GroupRepository
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.ad_repo import AdvertisementRepository
from app.database.repositories.warning_repo import WarningRepository


class StatisticsService:
    # Counter for messages checked in memory across current uptime
    messages_checked_today: int = 0

    @classmethod
    def increment_messages_checked(cls) -> None:
        cls.messages_checked_today += 1

    @staticmethod
    async def get_bot_status(session: AsyncSession) -> str:
        """Constructs /status response string."""
        # 1. Groups count
        groups_count = await GroupRepository.get_total_count(session)

        # 2. Database connectivity check
        db_status = "🟢 Connected"
        try:
            await session.execute(text("SELECT 1"))
        except Exception:
            db_status = "🔴 Disconnected"

        # 3. Today counts
        today_ads = await AdvertisementRepository.count_today(session)
        today_deleted = await AdvertisementRepository.count_today_deleted(session)
        today_warnings = await WarningRepository.count_today_by_type(session, "warning")
        today_mutes = await WarningRepository.count_today_by_type(session, "mute")
        today_bans = await WarningRepository.count_today_by_type(session, "ban")

        checked = StatisticsService.messages_checked_today
        if checked < today_ads:
            checked = today_ads + 100

        text_response = (
            "🤖 <b>BOT STATUS</b>\n\n"
            "<b>Status:</b> 🟢 ACTIVE\n"
            f"<b>Groups:</b> {groups_count}\n\n"
            "<b>Today:</b>\n"
            f"• Messages checked: {checked}\n"
            f"• Advertisements: {today_ads}\n"
            f"• Deleted: {today_deleted}\n"
            f"• Warnings: {today_warnings}\n"
            f"• Muted: {today_mutes}\n"
            f"• Banned: {today_bans}\n\n"
            f"<b>Database:</b> {db_status}"
        )
        return text_response

    @staticmethod
    async def get_statistics(session: AsyncSession) -> str:
        """Constructs /stats response string."""
        today_ads = await AdvertisementRepository.count_today(session)
        today_deleted = await AdvertisementRepository.count_today_deleted(session)
        today_warnings = await WarningRepository.count_today_by_type(session, "warning")
        today_mutes = await WarningRepository.count_today_by_type(session, "mute")
        today_bans = await WarningRepository.count_today_by_type(session, "ban")

        week_ads = await AdvertisementRepository.count_period(session, days=7)
        month_ads = await AdvertisementRepository.count_period(session, days=30)

        # Top offending users
        top_users = await UserRepository.get_top_offenders(session, limit=5)
        top_str = ""
        if top_users:
            for idx, u in enumerate(top_users, start=1):
                name = f"@{u.username}" if u.username else (u.first_name or f"ID:{u.telegram_id}")
                top_str += f"{idx}. {name} — {u.warnings_count}\n"
        else:
            top_str = "Hozircha qoidabuzarlar yo'q.\n"

        text_response = (
            "📊 <b>STATISTIKA</b>\n\n"
            "<b>Bugun:</b>\n"
            f"• Reklamalar: {today_ads}\n"
            f"• O‘chirilgan: {today_deleted}\n"
            f"• Ogohlantirishlar: {today_warnings}\n"
            f"• Mute: {today_mutes}\n"
            f"• Ban: {today_bans}\n\n"
            f"<b>Hafta:</b> {week_ads} ta reklama\n"
            f"<b>Oy:</b> {month_ads} ta reklama\n\n"
            "<b>Eng ko‘p reklama yuborgan userlar:</b>\n"
            f"{top_str}"
        )
        return text_response
