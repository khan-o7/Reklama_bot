from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.training_sample import TrainingSample


class TrainingRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        telegram_message_id: int,
        chat_id: int,
        user_id: int,
        text: str,
        score: int,
        predicted_is_ad: bool,
        uncertainty_score: float,
        detection_reasons: str
    ) -> TrainingSample:
        sample = TrainingSample(
            telegram_message_id=telegram_message_id,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            score=score,
            predicted_is_ad=predicted_is_ad,
            uncertainty_score=uncertainty_score,
            detection_reasons=detection_reasons
        )
        session.add(sample)
        await session.commit()
        await session.refresh(sample)
        return sample

    @staticmethod
    async def set_label(
        session: AsyncSession,
        sample_id: int,
        admin_label: bool
    ) -> Optional[TrainingSample]:
        stmt = (
            update(TrainingSample)
            .where(TrainingSample.id == sample_id)
            .values(
                admin_label=admin_label,
                labeled_at=datetime.now(timezone.utc)
            )
            .returning(TrainingSample)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, sample_id: int) -> Optional[TrainingSample]:
        stmt = select(TrainingSample).where(TrainingSample.id == sample_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def count_labeled_samples(session: AsyncSession) -> int:
        stmt = select(func.count(TrainingSample.id)).where(TrainingSample.admin_label != None)
        result = await session.execute(stmt)
        return result.scalar_one() or 0

    @staticmethod
    async def get_labeled_batch(session: AsyncSession, limit: int = 1000) -> List[TrainingSample]:
        stmt = (
            select(TrainingSample)
            .where(TrainingSample.admin_label != None)
            .order_by(desc(TrainingSample.labeled_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
