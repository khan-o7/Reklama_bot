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

    @staticmethod
    async def delete_by_id(session: AsyncSession, user_id: int) -> bool:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            await session.delete(user)
            await session.commit()
            return True
        return False

    @staticmethod
    async def delete_multiple(session: AsyncSession, user_ids: List[int]) -> int:
        if not user_ids:
            return 0
        from sqlalchemy import delete
        stmt = delete(User).where(User.id.in_(user_ids))
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    @staticmethod
    async def clear_all(session: AsyncSession, exclude_admins: bool = True) -> int:
        from sqlalchemy import delete
        stmt = delete(User)
        if exclude_admins:
            stmt = stmt.where(User.is_admin == False)  # noqa
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    @staticmethod
    async def bulk_reset_warnings(session: AsyncSession, user_ids: List[int]) -> int:
        if not user_ids:
            return 0
        stmt = update(User).where(User.id.in_(user_ids)).values(warnings_count=0)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    @staticmethod
    async def clear_all_warnings(session: AsyncSession) -> int:
        stmt = update(User).values(warnings_count=0)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

    @staticmethod
    async def update_user(
        session: AsyncSession,
        user_id: int,
        first_name: Optional[str] = None,
        username: Optional[str] = None,
        warnings_count: Optional[int] = None,
        is_muted: Optional[bool] = None,
        is_banned: Optional[bool] = None
    ) -> Optional[User]:
        user = await UserRepository.get_by_id(session, user_id)
        if user:
            if first_name is not None:
                user.first_name = first_name
            if username is not None:
                user.username = username.lstrip("@") if username else None
            if warnings_count is not None:
                user.warnings_count = max(0, warnings_count)
            if is_muted is not None:
                user.is_muted = is_muted
            if is_banned is not None:
                user.is_banned = is_banned
            await session.commit()
            await session.refresh(user)
        return user
