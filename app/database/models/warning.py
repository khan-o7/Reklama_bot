from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base


class Warning(Base):
    __tablename__ = "warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), index=True, nullable=False)
    advertisement_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("advertisements.id", ondelete="SET NULL"), nullable=True)
    warning_type: Mapped[str] = mapped_column(String(50), default="warning", nullable=False)
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="warnings")
    group = relationship("Group", back_populates="warnings")
    advertisement = relationship("Advertisement", back_populates="warnings")

    def __repr__(self) -> str:
        return f"<Warning id={self.id} user_id={self.user_id} type={self.warning_type}>"
