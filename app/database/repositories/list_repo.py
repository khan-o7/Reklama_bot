from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.list_item import Blacklist, Whitelist


class ListRepository:
    # --- BLACKLIST ---
    @staticmethod
    async def get_all_blacklist(session: AsyncSession) -> List[Blacklist]:
        stmt = select(Blacklist).order_by(Blacklist.created_at)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def add_to_blacklist(session: AsyncSession, item_type: str, value: str) -> Optional[Blacklist]:
        value_clean = value.strip().lower()
        stmt = select(Blacklist).where(Blacklist.value == value_clean)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        item = Blacklist(type=item_type.lower(), value=value_clean)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def remove_from_blacklist(session: AsyncSession, value: str) -> bool:
        value_clean = value.strip().lower()
        stmt = delete(Blacklist).where(Blacklist.value == value_clean)
        result = await session.execute(stmt)
        await session.commit()
        return (result.rowcount or 0) > 0

    # --- WHITELIST ---
    @staticmethod
    async def get_all_whitelist(session: AsyncSession) -> List[Whitelist]:
        stmt = select(Whitelist).order_by(Whitelist.created_at)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def add_to_whitelist(session: AsyncSession, item_type: str, value: str) -> Optional[Whitelist]:
        value_clean = value.strip().lower()
        # Strip protocol or trailing slash for domain whitelist
        if value_clean.startswith(("http://", "https://")):
            value_clean = value_clean.split("://")[1]
        value_clean = value_clean.strip("/")

        stmt = select(Whitelist).where(Whitelist.value == value_clean)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        item = Whitelist(type=item_type.lower(), value=value_clean)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def remove_from_whitelist(session: AsyncSession, value: str) -> bool:
        value_clean = value.strip().lower()
        if value_clean.startswith(("http://", "https://")):
            value_clean = value_clean.split("://")[1]
        value_clean = value_clean.strip("/")

        stmt = delete(Whitelist).where(Whitelist.value == value_clean)
        result = await session.execute(stmt)
        await session.commit()
        return (result.rowcount or 0) > 0
