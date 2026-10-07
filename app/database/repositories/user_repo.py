from typing import Optional, List
from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.user import User


class UserRepository:
    @staticmethod
    async def get_or_create(
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_admin: bool = False
    ) -> User:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Update latest username/name
            updated = False
            if username is not None and user.username != username:
                user.username = username
                updated = True
            if first_name is not None and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name is not None and user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if is_admin != user.is_admin:
                user.is_admin = is_admin
                updated = True
            if updated:
                await session.commit()
                await session.refresh(user)
            return user

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
            warnings_count=0
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def increment_warnings(session: AsyncSession, user_id: int) -> int:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(warnings_count=User.warnings_count + 1)
            .returning(User.warnings_count)
        )
        result = await session.execute(stmt)
        await session.commit()
        new_count = result.scalar_one()
        return new_count

    @staticmethod
    async def reset_warnings(session: AsyncSession, user_id: int) -> None:
        stmt = update(User).where(User.id == user_id).values(warnings_count=0)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def set_muted(session: AsyncSession, user_id: int, is_muted: bool) -> None:
        stmt = update(User).where(User.id == user_id).values(is_muted=is_muted)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def set_banned(session: AsyncSession, user_id: int, is_banned: bool) -> None:
        stmt = update(User).where(User.id == user_id).values(is_banned=is_banned)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def get_top_offenders(session: AsyncSession, limit: int = 10) -> List[User]:
        stmt = (
            select(User)
            .where(User.warnings_count > 0)
            .order_by(desc(User.warnings_count))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_total_count(session: AsyncSession) -> int:
        stmt = select(func.count(User.id))
        result = await session.execute(stmt)
        return result.scalar_one() or 0

    @staticmethod
    async def get_recent_users(session: AsyncSession, limit: int = 50) -> List[User]:
        stmt = select(User).order_by(desc(User.created_at)).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())
