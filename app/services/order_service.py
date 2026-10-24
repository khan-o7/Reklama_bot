from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.advertisement import Advertisement
from app.database.models.order import Order
from app.database.repositories.order_repo import OrderRepository
from app.database.repositories.ad_repo import AdvertisementRepository
from app.config.settings import settings
from app.utils.logger import logger


class OrderService:
    @staticmethod
    async def create_order_for_ad(
        session: AsyncSession,
        ad: Advertisement,
        default_price: Optional[int] = None,
        default_card: Optional[str] = None
    ) -> Order:
        """
        Creates a commercial order for a detected/deleted advertisement.
        If a default price is configured, automatically transitions to WAITING_PAYMENT.
        """
        # Check if order already exists for this advertisement
        existing_order = await OrderRepository.get_by_ad_id(session, ad.id)
        if existing_order:
            return existing_order

        price_val = None
        if default_price is not None:
            try:
                price_val = int(default_price)
            except (ValueError, TypeError):
                clean = "".join(ch for ch in str(default_price) if ch.isdigit())
                price_val = int(clean) if clean else None
        elif settings.AD_PRICE:
            clean = "".join(ch for ch in str(settings.AD_PRICE) if ch.isdigit())
            price_val = int(clean) if clean else None

        card = default_card or settings.AD_PAYMENT_CARD

        initial_status = "WAITING_PAYMENT" if price_val and price_val > 0 else "PRICE_PENDING"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=48)

        order = await OrderRepository.create(
            session=session,
            advertisement_id=ad.id,
            user_id=ad.user_id,
            group_id=ad.group_id,
            price=price_val,
            card_number=card,
            status=initial_status,
            expires_at=expires_at
        )

        # Sync advertisement status
        ad_status = "WAITING_PAYMENT" if initial_status == "WAITING_PAYMENT" else "PRICE_PENDING"
        await AdvertisementRepository.update_status(session, ad.id, ad_status)

        logger.info(
            f"🛒 Reklama buyurtmasi yaratildi | order={order.order_number} "
            f"ad_id={ad.id} user={ad.user_id} status={initial_status} price={price_val}"
        )
        return order

    @staticmethod
    async def set_order_price(
        session: AsyncSession,
        order_id: int,
        price: int,
        card_number: Optional[str] = None
    ) -> Optional[Order]:
        """
        Admin sets or updates the price for an order, advancing it to WAITING_PAYMENT.
        """
        card = card_number or settings.AD_PAYMENT_CARD
        order = await OrderRepository.update_price(
            session=session,
            order_id=order_id,
            price=price,
            card_number=card
        )
        if order:
            await AdvertisementRepository.update_status(session, order.advertisement_id, "WAITING_PAYMENT")
            logger.info(f"💰 Buyurtmaga narx belgilandi | order={order.order_number} price={price} UZS")
        return order

    @staticmethod
    async def get_order_by_id(session: AsyncSession, order_id: int) -> Optional[Order]:
        return await OrderRepository.get_by_id(session, order_id)

    @staticmethod
    async def get_order_by_number(session: AsyncSession, order_number: str) -> Optional[Order]:
        return await OrderRepository.get_by_order_number(session, order_number)

    @staticmethod
    async def get_order_by_ad_id(session: AsyncSession, ad_id: int) -> Optional[Order]:
        return await OrderRepository.get_by_ad_id(session, ad_id)

    @staticmethod
    async def get_user_orders(session: AsyncSession, user_id: int, limit: int = 10) -> List[Order]:
        return await OrderRepository.get_user_orders(session, user_id, limit)

    @staticmethod
    async def cancel_order(session: AsyncSession, order_id: int, reason: str = "") -> Optional[Order]:
        order = await OrderRepository.update_status(session, order_id, "CANCELLED", rejection_reason=reason)
        if order:
            await AdvertisementRepository.update_status(session, order.advertisement_id, "CANCELLED")
        return order
