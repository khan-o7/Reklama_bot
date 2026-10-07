from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, Integer, Float, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base


class TrainingSample(Base):
    __tablename__ = "training_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    predicted_is_ad: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    admin_label: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None, index=True)
    uncertainty_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    detection_reasons: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    labeled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<TrainingSample id={self.id} label={self.admin_label} score={self.score}>"
