from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.models.payment import Payment


class PaymentRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        order_id: int,
        advertisement_id: Optional[int],
        user_id: int,
        receipt_file_id: str,
        receipt_file_unique_id: str,
        receipt_hash: Optional[str] = None,
        receipt_type: str = "PHOTO",
        amount: Optional[int] = None,
        currency: str = "UZS",
        status: str = "PENDING",
    ) -> Payment:
        payment = Payment(
            order_id=order_id,
            advertisement_id=advertisement_id,
            user_id=user_id,
            receipt_file_id=receipt_file_id,
            receipt_file_unique_id=receipt_file_unique_id,
            receipt_hash=receipt_hash,
            receipt_type=receipt_type,
            amount=amount,
            currency=currency,
            status=status,
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment

    @staticmethod
    async def get_by_id(session: AsyncSession, payment_id: int) -> Optional[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.id == payment_id)
            .options(
                selectinload(Payment.order),
                selectinload(Payment.advertisement),
                selectinload(Payment.user),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_unique_id(session: AsyncSession, receipt_file_unique_id: str) -> Optional[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.receipt_file_unique_id == receipt_file_unique_id)
            .options(
                selectinload(Payment.order),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_receipt_hash(session: AsyncSession, receipt_hash: str) -> Optional[Payment]:
        if not receipt_hash:
            return None
        stmt = (
            select(Payment)
            .where(Payment.receipt_hash == receipt_hash)
            .options(
                selectinload(Payment.order),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_order_id(session: AsyncSession, order_id: int) -> List[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(desc(Payment.created_at))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_status(
        session: AsyncSession,
        payment_id: int,
        status: str,
        reviewed_by: Optional[int] = None,
        rejection_reason: Optional[str] = None
    ) -> Optional[Payment]:
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await session.execute(stmt)
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = status
            payment.reviewed_by = reviewed_by
            payment.reviewed_at = datetime.now(timezone.utc)
            if rejection_reason is not None:
                payment.rejection_reason = rejection_reason
            await session.commit()
            await session.refresh(payment)
        return payment
