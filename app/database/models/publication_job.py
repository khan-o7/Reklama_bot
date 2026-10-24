from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base


class PublicationJob(Base):
    __tablename__ = "publication_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("advertising_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Status: PENDING, IN_PROGRESS, SUCCESS, FAILED, RETRY
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    request = relationship("AdvertisingRequest", back_populates="publication_jobs")

    def __repr__(self) -> str:
        return f"<PublicationJob id={self.id} req_id={self.request_id} status={self.status}>"
