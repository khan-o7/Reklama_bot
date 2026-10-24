from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=True)
    request_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("advertising_requests.id", ondelete="CASCADE"), index=True, nullable=True)
    advertisement_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("advertisements.id", ondelete="SET NULL"), index=True, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="UZS", nullable=False)

    receipt_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    receipt_file_unique_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    receipt_hash: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    receipt_type: Mapped[str] = mapped_column(String(50), default="PHOTO", nullable=False)

    # Status: PENDING, APPROVED, REJECTED
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False, index=True)
    reviewed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    order = relationship("Order", back_populates="payments")
    advertisement = relationship("Advertisement")
    user = relationship("User", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} order_id={self.order_id} status={self.status} amount={self.amount}>"
