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
        message_type: str = "TEXT",
        text: Optional[str] = None,
        caption: Optional[str] = None,
        detected_links: Optional[str] = None,
        score: int = 0,
        detection_reason: str = "",
        deleted: bool = True,
        chat_id: Optional[int] = None,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        media_type: str = "TEXT",
        media_file_id: Optional[str] = None,
        media_file_unique_id: Optional[str] = None,
        original_text: Optional[str] = None,
        original_caption: Optional[str] = None,
        ocr_text: Optional[str] = None,
        combined_text: Optional[str] = None,
        detected_keywords: Optional[str] = None,
        risk_score: int = 0,
        status: str = "DELETED",
    ) -> Advertisement:
        ad = Advertisement(
            group_id=group_id,
            user_id=user_id,
            telegram_message_id=telegram_message_id,
            chat_id=chat_id,
            username=username,
            first_name=first_name,
            message_type=message_type,
            media_type=media_type,
            media_file_id=media_file_id,
            media_file_unique_id=media_file_unique_id,
            text=text,
            caption=caption,
            original_text=original_text,
            original_caption=original_caption,
            ocr_text=ocr_text,
            combined_text=combined_text,
            detected_links=detected_links,
            detected_keywords=detected_keywords,
            score=score,
            risk_score=risk_score,
            detection_reason=detection_reason,
            deleted=deleted,
            status=status,
        )
        session.add(ad)
        await session.commit()
        await session.refresh(ad)
        return ad

    @staticmethod
    async def get_by_id(session: AsyncSession, ad_id: int) -> Optional[Advertisement]:
        stmt = (
            select(Advertisement)
            .where(Advertisement.id == ad_id)
            .options(
                selectinload(Advertisement.user),
                selectinload(Advertisement.group),
                selectinload(Advertisement.orders),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_status(session: AsyncSession, ad_id: int, status: str) -> Optional[Advertisement]:
        stmt = select(Advertisement).where(Advertisement.id == ad_id)
        result = await session.execute(stmt)
        ad = result.scalar_one_or_none()
        if ad:
            ad.status = status
            await session.commit()
            await session.refresh(ad)
        return ad

    @staticmethod
    async def set_published(
        session: AsyncSession,
        ad_id: int,
        published_message_id: int,
        published_chat_id: int
    ) -> Optional[Advertisement]:
        stmt = select(Advertisement).where(Advertisement.id == ad_id)
        result = await session.execute(stmt)
        ad = result.scalar_one_or_none()
        if ad:
            ad.status = "PUBLISHED"
            ad.published_message_id = published_message_id
            ad.published_chat_id = published_chat_id
            ad.published_at = datetime.now(timezone.utc)
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

    @staticmethod
    async def delete_by_id(session: AsyncSession, ad_id: int) -> bool:
        stmt = select(Advertisement).where(Advertisement.id == ad_id)
        result = await session.execute(stmt)
        ad = result.scalar_one_or_none()
        if ad:
            await session.delete(ad)
            await session.commit()
            return True
        return False

    @staticmethod
    async def delete_multiple(session: AsyncSession, ad_ids: List[int]) -> int:
        if not ad_ids:
            return 0
        from sqlalchemy import delete
        stmt = delete(Advertisement).where(Advertisement.id.in_(ad_ids))
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    @staticmethod
    async def clear_all(session: AsyncSession) -> int:
        from sqlalchemy import delete
        stmt = delete(Advertisement)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    @staticmethod
    async def update_ad(
        session: AsyncSession,
        ad_id: int,
        status: Optional[str] = None,
        risk_score: Optional[int] = None,
        detection_reason: Optional[str] = None,
        text: Optional[str] = None
    ) -> Optional[Advertisement]:
        ad = await AdvertisementRepository.get_by_id(session, ad_id)
        if ad:
            if status is not None:
                ad.status = status
            if risk_score is not None:
                ad.risk_score = risk_score
                ad.score = risk_score
            if detection_reason is not None:
                ad.detection_reason = detection_reason
            if text is not None:
                ad.text = text
            await session.commit()
            await session.refresh(ad)
        return ad
