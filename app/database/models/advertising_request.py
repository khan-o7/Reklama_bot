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

    # OLX.uz Integration Fields
    # Statuses: NONE, PENDING, PUBLISHING, PUBLISHED, FAILED
    olx_status: Mapped[str] = mapped_column(String(50), default="NONE", index=True, nullable=False)
    olx_ad_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    olx_ad_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    olx_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    olx_error: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    @property
    def product_price(self) -> int | None:
        """Returns the user's item selling price from questionnaire answers or preview_text."""
        import re
        has_answers = "answers" in self.__dict__ and self.answers
        if has_answers:
            for ans in self.answers:
                if ans.field_id in ("price", "price_amount", "narx") and ans.value:
                    digits = re.sub(r"[^\d]", "", str(ans.value))
                    if digits:
                        return int(digits)
        if self.preview_text:
            clean_text = re.sub(r"<[^>]+>", "", self.preview_text)
            match = re.search(r"(?:Narxi?|Baho|Narx):\s*([0-9\s.,]+)", clean_text, re.IGNORECASE)
            if match:
                digits = re.sub(r"[^\d]", "", match.group(1))
                if digits:
                    return int(digits)
        return None

    @property
    def product_currency(self) -> str:
        """Returns the user's item currency (UZS or USD)."""
        has_answers = "answers" in self.__dict__ and self.answers
        if has_answers:
            for ans in self.answers:
                if ans.field_id in ("currency", "valyuta") and ans.value:
                    val = str(ans.value).lower()
                    if "usd" in val or "y.e" in val or "$" in val:
                        return "USD"
                    return "UZS"
        if self.preview_text:
            text_lower = self.preview_text.lower()
            if "usd" in text_lower or "y.e" in text_lower or "$" in self.preview_text:
                return "USD"
        return "UZS"

    @property
    def product_title(self) -> str:
        """Returns user's headline or product title."""
        import re
        has_answers = "answers" in self.__dict__ and self.answers
        if has_answers:
            for ans in self.answers:
                if ans.field_id in ("title", "product_name", "name", "sarlavha") and ans.value:
                    return str(ans.value).strip()
        if self.preview_text:
            clean_text = re.sub(r"<[^>]+>", "", self.preview_text)
            lines = [l.strip() for l in clean_text.splitlines() if l.strip()]
            if lines:
                return re.sub(r"^[^\w\d]+", "", lines[0]).strip()
        return f"{self.category_id} e’loni"

    @property
    def product_phone(self) -> str:
        """Returns user's contact phone number."""
        import re
        has_answers = "answers" in self.__dict__ and self.answers
        if has_answers:
            for ans in self.answers:
                if ans.field_id in ("phone", "contact_phone", "aloqa") and ans.value:
                    return str(ans.value).strip()
        if self.preview_text:
            clean_text = re.sub(r"<[^>]+>", "", self.preview_text)
            match = re.search(r"(?:Aloqa|Telefon|Tel):\s*([+0-9\s]+)", clean_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    @property
    def product_location(self) -> str:
        """Returns user's city/district/address."""
        import re
        has_answers = "answers" in self.__dict__ and self.answers
        if has_answers:
            for ans in self.answers:
                if ans.field_id in ("city_district", "location", "address", "shahar", "manzil") and ans.value:
                    return str(ans.value).strip()
        if self.preview_text:
            clean_text = re.sub(r"<[^>]+>", "", self.preview_text)
            match = re.search(r"(?:Manzil|Shahar|Joylashuv):\s*([^\n\r]+)", clean_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Toshkent"

