from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base


class AdvertisingRequest(Base):
    __tablename__ = "advertising_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    subcategory_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    # Status: DRAFT, COLLECTING_INFORMATION, AWAITING_USER_CONFIRMATION, NEW,
    # AWAITING_ADMIN_REVIEW, AWAITING_PRICE, AWAITING_PAYMENT, RECEIPT_SUBMITTED,
    # PAYMENT_APPROVED, PAYMENT_REJECTED, READY_TO_PUBLISH, SCHEDULED, PUBLISHED,
    # PUBLICATION_FAILED, CANCELLED
    status: Mapped[str] = mapped_column(String(50), default="COLLECTING_INFORMATION", index=True, nullable=False)

    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="UZS", nullable=False)
    card_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cardholder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    preview_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)

    published_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    published_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship("User")
    group = relationship("Group")
    answers = relationship("AdvertisementAnswer", back_populates="request", cascade="all, delete-orphan")
    media_items = relationship("AdvertisementMedia", back_populates="request", cascade="all, delete-orphan")
    publication_jobs = relationship("PublicationJob", back_populates="request", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<AdvertisingRequest id={self.id} number={self.request_number} category={self.category_id} status={self.status}>"
