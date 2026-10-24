from datetime import datetime, timezone
import random
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.models.order import Order


class OrderRepository:
    @staticmethod
    def generate_order_number(ad_id: int) -> str:
        year = datetime.now(timezone.utc).year
        if ad_id and ad_id > 0:
            return f"AD-{year}-{ad_id:06d}"
        rand_val = random.randint(1, 999999)
        return f"AD-{year}-{rand_val:06d}"

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        advertisement_id: int,
        user_id: int,
        group_id: Optional[int] = None,
        price: Optional[int] = None,
        currency: str = "UZS",
        card_number: Optional[str] = None,
        status: str = "CREATED",
        expires_at: Optional[datetime] = None,
    ) -> Order:
        order_number = cls.generate_order_number(advertisement_id)
        existing = await cls.get_by_order_number(session, order_number)
        if existing:
            return existing

        order = Order(
            order_number=order_number,
            advertisement_id=advertisement_id,
            user_id=user_id,
            group_id=group_id,
            price=price,
            currency=currency,
            card_number=card_number,
            status=status,
            expires_at=expires_at,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order

    @staticmethod
    async def get_by_id(session: AsyncSession, order_id: int) -> Optional[Order]:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.advertisement),
                selectinload(Order.user),
                selectinload(Order.group),
                selectinload(Order.payments),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_order_number(session: AsyncSession, order_number: str) -> Optional[Order]:
        stmt = (
            select(Order)
            .where(Order.order_number == order_number)
            .options(
                selectinload(Order.advertisement),
                selectinload(Order.user),
                selectinload(Order.group),
                selectinload(Order.payments),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_ad_id(session: AsyncSession, ad_id: int) -> Optional[Order]:
        stmt = (
            select(Order)
            .where(Order.advertisement_id == ad_id)
            .order_by(desc(Order.id))
            .options(
                selectinload(Order.advertisement),
                selectinload(Order.user),
                selectinload(Order.group),
                selectinload(Order.payments),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_user_orders(
        session: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> List[Order]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(desc(Order.created_at))
            .limit(limit)
            .options(
                selectinload(Order.advertisement),
                selectinload(Order.payments),
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_price(
        session: AsyncSession,
        order_id: int,
        price: int,
        card_number: Optional[str] = None
    ) -> Optional[Order]:
        stmt = select(Order).where(Order.id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()
        if order:
            order.price = price
            if card_number:
                order.card_number = card_number
            order.status = "WAITING_PAYMENT"
            await session.commit()
            await session.refresh(order)
        return order

    @staticmethod
    async def update_status(
        session: AsyncSession,
        order_id: int,
        status: str,
        rejection_reason: Optional[str] = None,
        validate: bool = True
    ) -> Optional[Order]:
        stmt = select(Order).where(Order.id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()
        if order:
            if validate:
                from app.services.state_machine import validate_transition
                validate_transition(order.status, status)
            order.status = status
            if rejection_reason is not None:
                order.rejection_reason = rejection_reason
            if status == "PUBLISHED" and not order.published_at:
                order.published_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(order)
        return order
