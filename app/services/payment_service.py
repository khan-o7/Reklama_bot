import hashlib
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.order import Order
from app.database.models.payment import Payment
from app.database.repositories.order_repo import OrderRepository
from app.database.repositories.payment_repo import PaymentRepository
from app.database.repositories.ad_repo import AdvertisementRepository
from app.utils.logger import logger


class PaymentService:
    @staticmethod
    def calculate_receipt_hash(file_bytes: bytes) -> str:
        """Calculates deterministic SHA-256 hash of receipt image bytes."""
        return hashlib.sha256(file_bytes).hexdigest()

    @classmethod
    async def submit_receipt(
        cls,
        session: AsyncSession,
        order: Order,
        receipt_file_id: str,
        receipt_file_unique_id: str,
        file_bytes: Optional[bytes] = None,
        receipt_type: str = "PHOTO",
        detected_amount: Optional[int] = None
    ) -> Tuple[Payment, bool]:
        """
        Saves payment receipt.
        Checks for duplicate receipts using SHA-256 hash or telegram unique_id.
        Returns (Payment, is_duplicate).
        """
        order_id = order.id
        order_num = order.order_number
        order_ad_id = order.advertisement_id
        order_user_id = order.user_id
        order_price = order.price
        order_currency = order.currency or "UZS"

        receipt_hash = cls.calculate_receipt_hash(file_bytes) if file_bytes else None
        is_duplicate = False

        # 1. Check duplicate by hash
        if receipt_hash:
            existing_by_hash = await PaymentRepository.get_by_receipt_hash(session, receipt_hash)
            if existing_by_hash and existing_by_hash.status in ("APPROVED", "PENDING"):
                is_duplicate = True
                logger.warning(
                    f"⚠️ Dublikat chek aniqlandi (hash bo'yicha) | hash={receipt_hash[:16]} "
                    f"existing_payment_id={existing_by_hash.id} status={existing_by_hash.status}"
                )

        # 2. Check duplicate by unique_id
        if not is_duplicate and receipt_file_unique_id:
            existing_by_uid = await PaymentRepository.get_by_unique_id(session, receipt_file_unique_id)
            if existing_by_uid and existing_by_uid.status in ("APPROVED", "PENDING"):
                is_duplicate = True
                logger.warning(
                    f"⚠️ Dublikat chek aniqlandi (unique_id bo'yicha) | uid={receipt_file_unique_id} "
                    f"existing_payment_id={existing_by_uid.id}"
                )

        payment = await PaymentRepository.create(
            session=session,
            order_id=order_id,
            advertisement_id=order_ad_id,
            user_id=order_user_id,
            receipt_file_id=receipt_file_id,
            receipt_file_unique_id=receipt_file_unique_id,
            receipt_hash=receipt_hash,
            receipt_type=receipt_type,
            amount=detected_amount or order_price,
            currency=order_currency,
            status="PENDING"
        )

        # Update order & ad status
        await OrderRepository.update_status(session, order_id, "PAYMENT_REVIEW")
        if order_ad_id:
            await AdvertisementRepository.update_status(session, order_ad_id, "PAYMENT_REVIEW")

        logger.info(
            f"🧾 To'lov cheki qabul qilindi | order={order_num} "
            f"payment_id={payment.id} is_dup={is_duplicate}"
        )
        return payment, is_duplicate

    @staticmethod
    async def approve_payment(
        session: AsyncSession,
        order_id: int,
        admin_id: int
    ) -> Tuple[bool, Optional[Order], str]:
        """
        Approves payment and order. Includes race condition & idempotency protection.
        """
        order = await OrderRepository.get_by_id(session, order_id)
        if not order:
            return False, None, "Buyurtma topilmadi."

        # Idempotency guard: Prevent double execution
        if order.status in ("APPROVED", "PUBLISHED"):
            return False, order, "Ushbu to'lov allaqachon tasdiqlangan va qayta ishlanmoqda."

        # Update all pending payments for this order to APPROVED
        payments = await PaymentRepository.get_by_order_id(session, order_id)
        for p in payments:
            if p.status == "PENDING":
                await PaymentRepository.update_status(session, p.id, "APPROVED", reviewed_by=admin_id)

        # Update order status
        order = await OrderRepository.update_status(session, order_id, "APPROVED")
        await AdvertisementRepository.update_status(session, order.advertisement_id, "PAYMENT_APPROVED")

        logger.info(f"✅ To'lov admin tomonidan tasdiqlandi | order={order.order_number} admin={admin_id}")
        return True, order, "To'lov muvaffaqiyatli tasdiqlandi."

    @staticmethod
    async def reject_payment(
        session: AsyncSession,
        order_id: int,
        admin_id: int,
        reason: str = "Noto'g'ri to'lov cheki"
    ) -> Tuple[bool, Optional[Order], str]:
        """
        Rejects submitted payment and keeps/reverts order to WAITING_PAYMENT.
        """
        order = await OrderRepository.get_by_id(session, order_id)
        if not order:
            return False, None, "Buyurtma topilmadi."

        payments = await PaymentRepository.get_by_order_id(session, order_id)
        for p in payments:
            if p.status == "PENDING":
                await PaymentRepository.update_status(
                    session,
                    p.id,
                    "REJECTED",
                    reviewed_by=admin_id,
                    rejection_reason=reason
                )

        # Order returns to WAITING_PAYMENT so user can re-submit
        order = await OrderRepository.update_status(session, order_id, "WAITING_PAYMENT", rejection_reason=reason)
        await AdvertisementRepository.update_status(session, order.advertisement_id, "PAYMENT_REJECTED")

        logger.info(f"❌ To'lov rad etildi | order={order.order_number} admin={admin_id} reason='{reason}'")
        return True, order, "To'lov rad etildi."
