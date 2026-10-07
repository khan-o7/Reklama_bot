from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.models.advertisement import Advertisement


class AdvertisementRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        group_id: Optional[int],
        user_id: Optional[int],
        telegram_message_id: int,
        message_type: str,
        text: Optional[str],
        caption: Optional[str],
        detected_links: Optional[str],
        score: int,
        detection_reason: str,
        deleted: bool = True
    ) -> Advertisement:
        ad = Advertisement(
            group_id=group_id,
            user_id=user_id,
            telegram_message_id=telegram_message_id,
            message_type=message_type,
            text=text,
            caption=caption,
            detected_links=detected_links,
            score=score,
            detection_reason=detection_reason,
            deleted=deleted
        )
        session.add(ad)
        await session.commit()
        await session.refresh(ad)
        return ad

    @staticmethod
    async def count_today(session: AsyncSession) -> int:
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        stmt = select(func.count(Advertisement.id)).where(Advertisement.created_at >= today_start)
        result = await session.execute(stmt)
        return result.scalar_one() or 0

    @staticmethod
    async def count_today_deleted(session: AsyncSession) -> int:
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        stmt = select(func.count(Advertisement.id)).where(
            Advertisement.created_at >= today_start,
            Advertisement.deleted == True  # noqa
        )
        result = await session.execute(stmt)
        return result.scalar_one() or 0

    @staticmethod
    async def count_period(session: AsyncSession, days: int) -> int:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(func.count(Advertisement.id)).where(Advertisement.created_at >= start_date)
        result = await session.execute(stmt)
        return result.scalar_one() or 0

    @staticmethod
    async def get_recent(session: AsyncSession, limit: int = 50) -> List[Advertisement]:
        stmt = (
            select(Advertisement)
            .options(selectinload(Advertisement.user), selectinload(Advertisement.group))
            .order_by(desc(Advertisement.created_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_chart_data_7_days(session: AsyncSession) -> List[Dict[str, any]]:
        """Returns advertisement counts for the last 7 calendar days."""
        now = datetime.now(timezone.utc)
        data = []
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            stmt = select(func.count(Advertisement.id)).where(
                Advertisement.created_at >= day_start,
                Advertisement.created_at < day_end
            )
            count = (await session.execute(stmt)).scalar_one() or 0
            data.append({
                "date": day_start.strftime("%d.%m"),
                "count": count
            })
        return data

    @staticmethod
    async def get_all_texts(session: AsyncSession, limit: int = 1000) -> List[str]:
        """Fetches raw text and caption from recent advertisements for AI clustering."""
        stmt = (
            select(Advertisement.text, Advertisement.caption)
            .order_by(desc(Advertisement.created_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        texts = []
        for text, caption in result.all():
            combined = (text or "") + " " + (caption or "")
            if combined.strip():
                texts.append(combined.strip())
        return texts
