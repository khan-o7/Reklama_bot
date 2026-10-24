from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.order import Order
from app.database.models.advertisement import Advertisement
from app.database.models.payment import Payment
from app.database.models.audit_log import AuditLog
from app.database.repositories.order_repo import OrderRepository
from app.database.repositories.ad_repo import AdvertisementRepository
from app.services.state_machine import RequestStatus, normalize_status, validate_transition, get_status_label
from app.config.settings import settings
from app.utils.logger import logger


class RequestService:
    @staticmethod
    async def get_by_id(session: AsyncSession, order_id: int) -> Optional[Order]:
        return await OrderRepository.get_by_id(session, order_id)

    @staticmethod
    async def get_by_number(session: AsyncSession, order_number: str) -> Optional[Order]:
        return await OrderRepository.get_by_order_number(session, order_number)

    @staticmethod
    async def get_by_ad_id(session: AsyncSession, ad_id: int) -> Optional[Order]:
        return await OrderRepository.get_by_ad_id(session, ad_id)

    @staticmethod
    async def get_user_requests(
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[Order]:
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(desc(Order.created_at))
            .offset(offset)
            .limit(limit)
            .options(
                selectinload(Order.advertisement),
                selectinload(Order.payments),
            )
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def count_user_requests(session: AsyncSession, user_id: int) -> int:
        stmt = select(func.count(Order.id)).where(Order.user_id == user_id)
        res = await session.execute(stmt)
        return res.scalar_one() or 0

    @staticmethod
    async def get_user_active_payment_orders(session: AsyncSession, user_id: int) -> List[Order]:
        """Finds orders for a user awaiting payment or receipt review."""
        stmt = (
            select(Order)
            .where(
                Order.user_id == user_id,
                Order.status.in_([
                    "WAITING_PAYMENT",
                    "AWAITING_PAYMENT",
                    "PRICE_PENDING",
                    "AWAITING_PRICE",
                    "PAYMENT_REJECTED",
                    "REJECTED"
                ])
            )
            .order_by(desc(Order.created_at))
            .options(
                selectinload(Order.advertisement),
                selectinload(Order.payments)
            )
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_requests_by_filter(
        session: AsyncSession,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 5,
        offset: int = 0
    ) -> Tuple[List[Order], int]:
        """
        Retrieves paginated requests with optional status filtering and search query.
        Returns (orders_list, total_count).
        """
        query = select(Order).options(
            selectinload(Order.advertisement),
            selectinload(Order.user),
            selectinload(Order.payments),
            selectinload(Order.group),
        )

        count_query = select(func.count(Order.id))

        if status_filter:
            norm = normalize_status(status_filter)
            # Match both canonical and legacy
            aliases = [norm]
            if norm == "NEW":
                aliases.extend(["CREATED"])
            elif norm == "AWAITING_PRICE":
                aliases.extend(["PRICE_PENDING"])
            elif norm == "AWAITING_PAYMENT":
                aliases.extend(["WAITING_PAYMENT"])
            elif norm == "RECEIPT_SUBMITTED":
                aliases.extend(["PAYMENT_REVIEW"])
            elif norm == "PAYMENT_APPROVED":
                aliases.extend(["APPROVED"])
            elif norm == "PAYMENT_REJECTED":
                aliases.extend(["REJECTED"])

            query = query.where(Order.status.in_(aliases))
            count_query = count_query.where(Order.status.in_(aliases))

        if search_query:
            clean_q = search_query.strip()
            if clean_q.isdigit():
                uid = int(clean_q)
                # match telegram_id or order_id
                query = query.join(Order.user).where(
                    or_(
                        Order.id == uid,
                        Order.advertisement_id == uid,
                        Order.user.has(telegram_id=uid)
                    )
                )
                count_query = count_query.join(Order.user).where(
                    or_(
                        Order.id == uid,
                        Order.advertisement_id == uid,
                        Order.user.has(telegram_id=uid)
                    )
                )
            else:
                pattern = f"%{clean_q}%"
                query = query.where(Order.order_number.ilike(pattern))
                count_query = count_query.where(Order.order_number.ilike(pattern))

        total_res = await session.execute(count_query)
        total_count = total_res.scalar_one() or 0

        query = query.order_by(desc(Order.created_at)).offset(offset).limit(limit)
        items_res = await session.execute(query)
        items = list(items_res.scalars().all())

        return items, total_count

    @staticmethod
    async def get_financial_statistics(session: AsyncSession) -> Dict[str, Any]:
        """Calculates rich operational and financial metrics."""
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        # Total counts
        total_stmt = select(func.count(Order.id))
        total_orders = (await session.execute(total_stmt)).scalar_one() or 0

        # Status breakdown
        stmt = select(Order.status, func.count(Order.id)).group_by(Order.status)
        status_counts_raw = (await session.execute(stmt)).all()
        status_counts: Dict[str, int] = {}
        for st, cnt in status_counts_raw:
            norm = normalize_status(st)
            status_counts[norm] = status_counts.get(norm, 0) + cnt

        # Today's orders
        today_stmt = select(func.count(Order.id)).where(Order.created_at >= today_start)
        today_orders = (await session.execute(today_stmt)).scalar_one() or 0

        # Month's orders
        month_stmt = select(func.count(Order.id)).where(Order.created_at >= month_start)
        month_orders = (await session.execute(month_stmt)).scalar_one() or 0

        # Recorded Revenue from APPROVED or PUBLISHED orders
        rev_stmt = select(func.sum(Order.price)).where(
            Order.status.in_(["APPROVED", "PAYMENT_APPROVED", "PUBLISHED"])
        )
        total_revenue = (await session.execute(rev_stmt)).scalar_one() or 0

        today_rev_stmt = select(func.sum(Order.price)).where(
            Order.status.in_(["APPROVED", "PAYMENT_APPROVED", "PUBLISHED"]),
            Order.updated_at >= today_start
        )
        today_revenue = (await session.execute(today_rev_stmt)).scalar_one() or 0

        return {
            "total_orders": total_orders,
            "today_orders": today_orders,
            "month_orders": month_orders,
            "status_counts": status_counts,
            "total_revenue": total_revenue,
            "today_revenue": today_revenue,
            "pending_pricing": status_counts.get("NEW", 0) + status_counts.get("AWAITING_PRICE", 0),
            "awaiting_payment": status_counts.get("AWAITING_PAYMENT", 0),
            "receipt_submitted": status_counts.get("RECEIPT_SUBMITTED", 0),
            "published": status_counts.get("PUBLISHED", 0),
            "failed": status_counts.get("PUBLICATION_FAILED", 0),
            "rejected": status_counts.get("PAYMENT_REJECTED", 0),
            "cancelled": status_counts.get("CANCELLED", 0),
        }
