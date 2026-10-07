from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.audit_log import AuditLog


class AuditRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        event_type: str,
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        details: Optional[str] = None
    ) -> AuditLog:
        log = AuditLog(
            event_type=event_type,
            group_id=group_id,
            user_id=user_id,
            details=details
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log

    @staticmethod
    async def get_recent(session: AsyncSession, limit: int = 100) -> List[AuditLog]:
        stmt = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())
