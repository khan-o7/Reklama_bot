from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    advertisement_id: Mapped[int] = mapped_column(Integer, ForeignKey("advertisements.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)

    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="UZS", nullable=False)
    card_number: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Status: CREATED, PRICE_PENDING, WAITING_PAYMENT, PAYMENT_REVIEW, APPROVED, PUBLISHED, REJECTED, CANCELLED, EXPIRED
    status: Mapped[str] = mapped_column(String(50), default="CREATED", nullable=False, index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    advertisement = relationship("Advertisement", back_populates="orders")
    user = relationship("User", back_populates="orders")
    group = relationship("Group")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order id={self.id} number={self.order_number} status={self.status} price={self.price}>"
