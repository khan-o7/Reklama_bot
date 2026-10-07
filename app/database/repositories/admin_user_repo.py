from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.admin_user import AdminUser


class AdminUserRepository:
    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> Optional[AdminUser]:
        stmt = select(AdminUser).where(AdminUser.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, username: str, password_hash: str) -> AdminUser:
        admin = AdminUser(username=username, password_hash=password_hash, is_active=True)
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        return admin
