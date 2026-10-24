from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base


class AdvertisementCategory(Base):
    __tablename__ = "advertisement_categories"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    fields = relationship("CategoryFieldModel", back_populates="category", cascade="all, delete-orphan")


class CategoryFieldModel(Base):
    __tablename__ = "category_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[str] = mapped_column(String(64), ForeignKey("advertisement_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    subcategory_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    field_label: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    include_in_ad: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category = relationship("AdvertisementCategory", back_populates="fields")
    options = relationship("CategoryOptionModel", back_populates="field", cascade="all, delete-orphan")


class CategoryOptionModel(Base):
    __tablename__ = "category_field_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    field_id: Mapped[int] = mapped_column(Integer, ForeignKey("category_fields.id", ondelete="CASCADE"), nullable=False, index=True)
    option_key: Mapped[str] = mapped_column(String(64), nullable=False)
    option_label: Mapped[str] = mapped_column(String(255), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    field = relationship("CategoryFieldModel", back_populates="options")
