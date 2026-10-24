from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.models.warning import Warning


class WarningRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int,
        group_id: int,
        advertisement_id: Optional[int],
        warning_type: str,
        message_id: Optional[int] = None
    ) -> Warning:
        warn = Warning(
            user_id=user_id,
            group_id=group_id,
            advertisement_id=advertisement_id,
            warning_type=warning_type,
            message_id=message_id
        )
        session.add(warn)
        await session.commit()
        await session.refresh(warn)
        return warn

    @staticmethod
    async def count_today_by_type(session: AsyncSession, warning_type: Optional[str] = None) -> int:
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        stmt = select(func.count(Warning.id)).where(Warning.created_at >= today_start)
        if warning_type:
            stmt = stmt.where(Warning.warning_type.like(f"%{warning_type}%"))
        result = await session.execute(stmt)
        return result.scalar_one() or 0

    @staticmethod
    async def get_recent(session: AsyncSession, limit: int = 50) -> List[Warning]:
        stmt = (
            select(Warning)
            .options(selectinload(Warning.user), selectinload(Warning.group))
            .order_by(desc(Warning.created_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, warning_id: int) -> Optional[Warning]:
        stmt = (
            select(Warning)
            .where(Warning.id == warning_id)
            .options(selectinload(Warning.user), selectinload(Warning.group))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_by_id(session: AsyncSession, warning_id: int) -> bool:
        stmt = select(Warning).where(Warning.id == warning_id)
        result = await session.execute(stmt)
        w = result.scalar_one_or_none()
        if w:
            await session.delete(w)
            await session.commit()
            return True
        return False

    @staticmethod
    async def delete_multiple(session: AsyncSession, warning_ids: List[int]) -> int:
        if not warning_ids:
            return 0
        from sqlalchemy import delete
        stmt = delete(Warning).where(Warning.id.in_(warning_ids))
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    @staticmethod
    async def clear_all(session: AsyncSession) -> int:
        from sqlalchemy import delete
        stmt = delete(Warning)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    @staticmethod
    async def update_warning(session: AsyncSession, warning_id: int, warning_type: str) -> Optional[Warning]:
        w = await WarningRepository.get_by_id(session, warning_id)
        if w:
            w.warning_type = warning_type
            await session.commit()
            await session.refresh(w)
        return w
