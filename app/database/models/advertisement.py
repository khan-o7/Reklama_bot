from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base


class Advertisement(Base):
    __tablename__ = "advertisements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    message_type: Mapped[str] = mapped_column(String(50), default="TEXT", nullable=False)
    media_type: Mapped[str] = mapped_column(String(50), default="TEXT", nullable=False)
    media_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    media_file_unique_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    combined_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    detected_links: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    detection_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    deleted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Workflow Status:
    # DETECTED, DELETED, WAITING_CONTACT, PRICE_PENDING, PRICE_SENT, WAITING_PAYMENT,
    # PAYMENT_RECEIVED, PAYMENT_REVIEW, PAYMENT_APPROVED, PAYMENT_REJECTED, PUBLISHING, PUBLISHED, CANCELLED, EXPIRED
    status: Mapped[str] = mapped_column(String(50), default="DELETED", nullable=False, index=True)

    published_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    published_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    group = relationship("Group", back_populates="advertisements")
    user = relationship("User", back_populates="advertisements")
    warnings = relationship("Warning", back_populates="advertisement")
    orders = relationship("Order", back_populates="advertisement", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Advertisement id={self.id} status={self.status} score={self.score} user_id={self.user_id}>"
