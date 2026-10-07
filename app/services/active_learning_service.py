from typing import Dict, Any, List, Optional, Tuple
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.repositories.training_repo import TrainingRepository
from app.utils.logger import logger


class ActiveLearningService:
    """
    Active Learning and Batch Model Retraining Pipeline.
    
    Principles:
    1. Never retrain online per single message (prevents model instability).
    2. Uncertainty Sampling: flags borderline messages (Risk ~40-60%) for human admin review.
    3. Accumulates verified dataset -> runs batch validation & A/B performance assessment.
    """

    BATCH_RETRAIN_SIZE = 50  # Retrain calibration threshold

    @classmethod
    def calculate_uncertainty(cls, score: int, threshold: int = 40) -> Tuple[bool, float]:
        """
        Determines if a message falls into the ambiguous boundary zone.
        e.g., score between 25 and 45 when threshold is 40.
        """
        distance = abs(score - threshold)
        uncertainty = max(0.0, 1.0 - (distance / 20.0))
        is_uncertain = 25 <= score <= 45
        return is_uncertain, round(uncertainty, 2)

    @classmethod
    async def request_admin_label(
        cls,
        bot: Bot,
        message: Message,
        analysis: Dict[str, Any],
        session: AsyncSession
    ) -> Optional[int]:
        """
        Sends an Active Learning verification card to admins with decision buttons.
        """
        user = message.from_user
        full_name = user.full_name if user else "Noma'lum"
        username_str = f"@{user.username}" if user and user.username else "yo‘q"
        user_id = user.id if user else 0
        chat_id = message.chat.id
        msg_id = message.message_id
        score = analysis.get("score", 0)
        reasons_str = "; ".join(analysis.get("reasons", [])) or "Noaniq"

        # 1. Save sample in DB
        uncertain, uncertainty_score = cls.calculate_uncertainty(score)
        raw_text = message.text or message.caption or ""

        sample = await TrainingRepository.create(
            session=session,
            telegram_message_id=msg_id,
            chat_id=chat_id,
            user_id=user_id,
            text=raw_text,
            score=score,
            predicted_is_ad=analysis.get("is_ad", False),
            uncertainty_score=uncertainty_score,
            detection_reasons=reasons_str
        )

        # 2. Build review card for admin
        risk_pct = min(99, int((score / 40.0) * 50))
        card_text = (
            f"🧠 <b>ACTIVE LEARNING: NOANIQ XABAR TAHLILI</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {full_name} ({username_str})\n"
            f"📊 <b>Aniqlangan xavf darajasi:</b> <code>{risk_pct}%</code> (Ball: {score}/40)\n"
            f"📝 <b>Sabablar:</b> {reasons_str}\n\n"
            f"💬 <b>Xabar matni:</b>\n"
            f"<i>\"{raw_text[:250]}\"</i>\n\n"
            f"Iltimos, modelni o‘qitish uchun to‘g‘ri baholang:"
        )

        review_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚨 REKLAMA", callback_data=f"al_ad:{sample.id}:{chat_id}:{msg_id}"),
                    InlineKeyboardButton(text="✅ REKLAMA EMAS", callback_data=f"al_clean:{sample.id}")
                ]
            ]
        )

        for admin_id in settings.all_admin_ids:
            for attempt in range(1, 4):
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=card_text,
                        parse_mode="HTML",
                        reply_markup=review_kb
                    )
                    break
                except Exception as e:
                    if attempt < 3:
                        await asyncio.sleep(1.5)
                    else:
                        logger.warning(f"Could not deliver active learning card to admin {admin_id}: {e}")

        return sample.id

    @classmethod
    async def process_feedback(
        cls,
        sample_id: int,
        is_ad: bool,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Processes human admin feedback, updates dataset, and triggers batch validation
        when dataset threshold is reached.
        """
        sample = await TrainingRepository.set_label(session, sample_id, admin_label=is_ad)
        total_labeled = await TrainingRepository.count_labeled_samples(session)

        retrain_triggered = False
        metrics = {}

        if total_labeled % cls.BATCH_RETRAIN_SIZE == 0:
            logger.info(f"🔄 Active Learning batch milestone reached: {total_labeled} labeled samples. Running batch validation...")
            metrics = await cls.run_batch_validation(session)
            retrain_triggered = True

        return {
            "sample_id": sample_id,
            "total_labeled": total_labeled,
            "retrain_triggered": retrain_triggered,
            "metrics": metrics
        }

    @classmethod
    async def run_batch_validation(cls, session: AsyncSession) -> Dict[str, float]:
        """
        Runs batch validation and metrics assessment on labeled dataset.
        Evaluates Precision, Recall, and Accuracy before tuning live weights.
        """
        samples = await TrainingRepository.get_labeled_batch(session, limit=500)
        if not samples:
            return {"accuracy": 1.0, "samples": 0}

        tp = sum(1 for s in samples if s.admin_label is True and s.score >= 40)
        fp = sum(1 for s in samples if s.admin_label is False and s.score >= 40)
        fn = sum(1 for s in samples if s.admin_label is True and s.score < 40)
        tn = sum(1 for s in samples if s.admin_label is False and s.score < 40)

        total = len(samples)
        accuracy = (tp + tn) / total if total > 0 else 1.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0

        logger.info(f"📊 Batch Model Validation: Total={total} | Accuracy={accuracy*100:.1f}% | Precision={precision*100:.1f}% | Recall={recall*100:.1f}%")
        return {
            "samples": total,
            "accuracy": round(accuracy, 2),
            "precision": round(precision, 2),
            "recall": round(recall, 2)
        }
