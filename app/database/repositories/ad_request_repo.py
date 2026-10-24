from datetime import datetime, timezone
import random
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.advertising_request import AdvertisingRequest
from app.database.models.advertisement_answer import AdvertisementAnswer
from app.database.models.advertisement_media import AdvertisementMedia
from app.database.models.publication_job import PublicationJob
from app.database.models.order import Order


class AdvertisingRequestRepository:
    @staticmethod
    async def generate_request_number(session: AsyncSession) -> str:
        """Generates unique human-readable request code e.g. REQ-2026-000123."""
        year = datetime.now(timezone.utc).year
        stmt = select(func.count(AdvertisingRequest.id))
        res = await session.execute(stmt)
        count = (res.scalar_one() or 0) + 1
        return f"REQ-{year}-{count:06d}"

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        user_id: int,
        category_id: str,
        subcategory_id: Optional[str] = None,
        group_id: Optional[int] = None
    ) -> AdvertisingRequest:
        req_num = await cls.generate_request_number(session)
        req = AdvertisingRequest(
            request_number=req_num,
            user_id=user_id,
            category_id=category_id,
            subcategory_id=subcategory_id,
            group_id=group_id,
            status="COLLECTING_INFORMATION"
        )
        session.add(req)
        await session.commit()
        await session.refresh(req)
        return req

    @staticmethod
    async def get_by_id(session: AsyncSession, request_id: int) -> Optional[AdvertisingRequest]:
        stmt = (
            select(AdvertisingRequest)
            .where(AdvertisingRequest.id == request_id)
            .options(
                selectinload(AdvertisingRequest.user),
                selectinload(AdvertisingRequest.group),
                selectinload(AdvertisingRequest.answers),
                selectinload(AdvertisingRequest.media_items),
                selectinload(AdvertisingRequest.publication_jobs),
            )
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_by_number(session: AsyncSession, request_number: str) -> Optional[AdvertisingRequest]:
        stmt = (
            select(AdvertisingRequest)
            .where(AdvertisingRequest.request_number == request_number)
            .options(
                selectinload(AdvertisingRequest.user),
                selectinload(AdvertisingRequest.group),
                selectinload(AdvertisingRequest.answers),
                selectinload(AdvertisingRequest.media_items),
                selectinload(AdvertisingRequest.publication_jobs),
            )
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_user_active_draft(session: AsyncSession, user_id: int) -> Optional[AdvertisingRequest]:
        """Finds any in-progress draft for this user so they can resume after restart."""
        stmt = (
            select(AdvertisingRequest)
            .where(
                AdvertisingRequest.user_id == user_id,
                AdvertisingRequest.status.in_(["DRAFT", "COLLECTING_INFORMATION"])
            )
            .order_by(desc(AdvertisingRequest.created_at))
            .options(
                selectinload(AdvertisingRequest.answers),
                selectinload(AdvertisingRequest.media_items)
            )
        )
        res = await session.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def save_answer(
        session: AsyncSession,
        request_id: int,
        field_id: str,
        value: Any,
        field_label: Optional[str] = None
    ) -> AdvertisementAnswer:
        str_val = str(value) if value is not None else None

        stmt = select(AdvertisementAnswer).where(
            AdvertisementAnswer.request_id == request_id,
            AdvertisementAnswer.field_id == field_id
        )
        res = await session.execute(stmt)
        ans = res.scalar_one_or_none()

        if ans:
            ans.value = str_val
            if field_label:
                ans.field_label = field_label
        else:
            ans = AdvertisementAnswer(
                request_id=request_id,
                field_id=field_id,
                field_label=field_label,
                value=str_val
            )
            session.add(ans)

        await session.commit()
        await session.refresh(ans)
        return ans

    @staticmethod
    async def get_answers_dict(session: AsyncSession, request_id: int) -> Dict[str, Any]:
        stmt = select(AdvertisementAnswer).where(AdvertisementAnswer.request_id == request_id)
        res = await session.execute(stmt)
        answers: Dict[str, Any] = {}
        for row in res.scalars().all():
            val = row.value
            # parse numeric if applicable
            if val is not None and val.isdigit():
                answers[row.field_id] = int(val)
            else:
                answers[row.field_id] = val
        return answers

    @staticmethod
    async def delete_answer(session: AsyncSession, request_id: int, field_id: str) -> None:
        stmt = delete(AdvertisementAnswer).where(
            AdvertisementAnswer.request_id == request_id,
            AdvertisementAnswer.field_id == field_id
        )
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def add_media(
        session: AsyncSession,
        request_id: int,
        file_id: str,
        media_type: str = "PHOTO",
        file_unique_id: Optional[str] = None,
        caption: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> AdvertisementMedia:
        # Check current count for display order
        stmt = select(func.count(AdvertisementMedia.id)).where(AdvertisementMedia.request_id == request_id)
        res = await session.execute(stmt)
        order = res.scalar_one() or 0

        media = AdvertisementMedia(
            request_id=request_id,
            media_type=media_type,
            file_id=file_id,
            file_unique_id=file_unique_id,
            caption=caption,
            file_size=file_size,
            display_order=order
        )
        session.add(media)
        await session.commit()
        await session.refresh(media)
        return media

    @staticmethod
    async def get_media_items(session: AsyncSession, request_id: int) -> List[AdvertisementMedia]:
        stmt = (
            select(AdvertisementMedia)
            .where(AdvertisementMedia.request_id == request_id)
            .order_by(AdvertisementMedia.display_order)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def clear_media(session: AsyncSession, request_id: int) -> None:
        stmt = delete(AdvertisementMedia).where(AdvertisementMedia.request_id == request_id)
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def update_status(session: AsyncSession, request_id: int, new_status: str) -> Optional[AdvertisingRequest]:
        req = await AdvertisingRequestRepository.get_by_id(session, request_id)
        if req:
            req.status = new_status
            await session.commit()
            await session.refresh(req)
        return req

    @staticmethod
    async def set_price(
        session: AsyncSession,
        request_id: int,
        price: int,
        card_number: Optional[str] = None,
        cardholder: Optional[str] = None,
        admin_id: Optional[int] = None
    ) -> Optional[AdvertisingRequest]:
        req = await AdvertisingRequestRepository.get_by_id(session, request_id)
        if req:
            req.price = price
            if card_number:
                req.card_number = card_number
            if cardholder:
                req.cardholder = cardholder
            if admin_id:
                req.assigned_admin_id = admin_id
            req.status = "AWAITING_PAYMENT"
            await session.commit()
            await session.refresh(req)
        return req

    @staticmethod
    async def get_user_requests(
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[AdvertisingRequest]:
        stmt = (
            select(AdvertisingRequest)
            .where(AdvertisingRequest.user_id == user_id)
            .order_by(desc(AdvertisingRequest.created_at))
            .offset(offset)
            .limit(limit)
            .options(
                selectinload(AdvertisingRequest.answers),
                selectinload(AdvertisingRequest.media_items),
            )
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def count_by_status(session: AsyncSession, status: str) -> int:
        stmt = select(func.count(AdvertisingRequest.id)).where(AdvertisingRequest.status == status)
        res = await session.execute(stmt)
        return res.scalar_one() or 0

    @staticmethod
    async def get_by_status(
        session: AsyncSession,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[AdvertisingRequest]:
        stmt = select(AdvertisingRequest).order_by(desc(AdvertisingRequest.created_at))
        if status:
            stmt = stmt.where(AdvertisingRequest.status == status)
        stmt = stmt.offset(offset).limit(limit).options(
            selectinload(AdvertisingRequest.user),
            selectinload(AdvertisingRequest.answers),
            selectinload(AdvertisingRequest.media_items),
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())
