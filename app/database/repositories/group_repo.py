from typing import Optional, List
from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.group import Group


class GroupRepository:
    @staticmethod
    async def get_or_create(
        session: AsyncSession,
        telegram_chat_id: int,
        title: str,
        username: Optional[str] = None
    ) -> Group:
        stmt = select(Group).where(Group.telegram_chat_id == telegram_chat_id)
        result = await session.execute(stmt)
        group = result.scalar_one_or_none()

        if group:
            updated = False
            if group.title != title:
                group.title = title
                updated = True
            if username is not None and group.username != username:
                group.username = username
                updated = True
            if not group.is_active:
                group.is_active = True
                updated = True
            if updated:
                await session.commit()
                await session.refresh(group)
            return group

        group = Group(
            telegram_chat_id=telegram_chat_id,
            title=title,
            username=username,
            is_active=True
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)
        return group

    @staticmethod
    async def get_by_chat_id(session: AsyncSession, telegram_chat_id: int) -> Optional[Group]:
        stmt = select(Group).where(Group.telegram_chat_id == telegram_chat_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, group_id: int) -> Optional[Group]:
        stmt = select(Group).where(Group.id == group_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def set_active_status(session: AsyncSession, telegram_chat_id: int, is_active: bool) -> None:
        stmt = (
            update(Group)
            .where(Group.telegram_chat_id == telegram_chat_id)
            .values(is_active=is_active)
        )
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def get_all_active(session: AsyncSession) -> List[Group]:
        stmt = select(Group).where(Group.is_active == True).order_by(desc(Group.created_at))  # noqa
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_total_count(session: AsyncSession) -> int:
        stmt = select(func.count(Group.id))
        result = await session.execute(stmt)
        return result.scalar_one() or 0

    @staticmethod
    async def get_all(session: AsyncSession, limit: int = 100) -> List[Group]:
        stmt = select(Group).order_by(desc(Group.created_at)).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())
