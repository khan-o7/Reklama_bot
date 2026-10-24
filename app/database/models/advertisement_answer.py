from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base


class AdvertisementAnswer(Base):
    __tablename__ = "advertisement_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("advertising_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    field_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    request = relationship("AdvertisingRequest", back_populates="answers")

    def __repr__(self) -> str:
        return f"<AdvertisementAnswer id={self.id} field={self.field_id} val={self.value[:20] if self.value else ''}>"
