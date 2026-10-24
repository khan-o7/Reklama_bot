from enum import Enum
from typing import Dict, Set, Optional


class RequestStatus(str, Enum):
    NEW = "NEW"
    AWAITING_PRICE = "AWAITING_PRICE"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    RECEIPT_SUBMITTED = "RECEIPT_SUBMITTED"
    PAYMENT_APPROVED = "PAYMENT_APPROVED"
    PAYMENT_REJECTED = "PAYMENT_REJECTED"
    READY_TO_PUBLISH = "READY_TO_PUBLISH"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    PUBLICATION_FAILED = "PUBLICATION_FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

    # Backward-compatibility aliases
    CREATED = "NEW"
    PRICE_PENDING = "AWAITING_PRICE"
    WAITING_PAYMENT = "AWAITING_PAYMENT"
    PAYMENT_REVIEW = "RECEIPT_SUBMITTED"
    APPROVED = "PAYMENT_APPROVED"
    REJECTED = "PAYMENT_REJECTED"


# Legal transitions mapping
LEGAL_TRANSITIONS: Dict[str, Set[str]] = {
    # From NEW
    "NEW": {"AWAITING_PRICE", "AWAITING_PAYMENT", "CANCELLED", "PRICE_PENDING", "WAITING_PAYMENT"},
    "CREATED": {"AWAITING_PRICE", "AWAITING_PAYMENT", "CANCELLED", "PRICE_PENDING", "WAITING_PAYMENT"},

    # From AWAITING_PRICE
    "AWAITING_PRICE": {"AWAITING_PAYMENT", "CANCELLED", "EXPIRED", "WAITING_PAYMENT"},
    "PRICE_PENDING": {"AWAITING_PAYMENT", "CANCELLED", "EXPIRED", "WAITING_PAYMENT"},

    # From AWAITING_PAYMENT
    "AWAITING_PAYMENT": {"RECEIPT_SUBMITTED", "CANCELLED", "EXPIRED", "PAYMENT_REVIEW"},
    "WAITING_PAYMENT": {"RECEIPT_SUBMITTED", "CANCELLED", "EXPIRED", "PAYMENT_REVIEW"},

    # From RECEIPT_SUBMITTED
    "RECEIPT_SUBMITTED": {"PAYMENT_APPROVED", "PAYMENT_REJECTED", "AWAITING_PAYMENT", "WAITING_PAYMENT", "CANCELLED", "APPROVED", "REJECTED"},
    "PAYMENT_REVIEW": {"PAYMENT_APPROVED", "PAYMENT_REJECTED", "AWAITING_PAYMENT", "WAITING_PAYMENT", "CANCELLED", "APPROVED", "REJECTED"},

    # From PAYMENT_REJECTED (user can resubmit receipt)
    "PAYMENT_REJECTED": {"AWAITING_PAYMENT", "RECEIPT_SUBMITTED", "CANCELLED", "EXPIRED", "WAITING_PAYMENT", "PAYMENT_REVIEW"},
    "REJECTED": {"AWAITING_PAYMENT", "RECEIPT_SUBMITTED", "CANCELLED", "EXPIRED", "WAITING_PAYMENT", "PAYMENT_REVIEW"},

    # From PAYMENT_APPROVED
    "PAYMENT_APPROVED": {"READY_TO_PUBLISH", "SCHEDULED", "PUBLISHED", "PUBLICATION_FAILED"},
    "APPROVED": {"READY_TO_PUBLISH", "SCHEDULED", "PUBLISHED", "PUBLICATION_FAILED"},

    # From READY_TO_PUBLISH
    "READY_TO_PUBLISH": {"PUBLISHED", "PUBLICATION_FAILED", "SCHEDULED", "CANCELLED"},

    # From SCHEDULED
    "SCHEDULED": {"PUBLISHED", "PUBLICATION_FAILED", "CANCELLED"},

    # From PUBLICATION_FAILED (safe retry allows trying again)
    "PUBLICATION_FAILED": {"READY_TO_PUBLISH", "PUBLISHED", "CANCELLED", "SCHEDULED"},

    # Terminal states
    "PUBLISHED": set(),
    "CANCELLED": set(),
    "EXPIRED": set(),
}


def normalize_status(status: str) -> str:
    """Normalizes legacy aliases to canonical RequestStatus enum strings."""
    s = status.upper().strip()
    mapping = {
        "CREATED": "NEW",
        "PRICE_PENDING": "AWAITING_PRICE",
        "WAITING_PAYMENT": "AWAITING_PAYMENT",
        "PAYMENT_REVIEW": "RECEIPT_SUBMITTED",
        "APPROVED": "PAYMENT_APPROVED",
        "REJECTED": "PAYMENT_REJECTED",
    }
    return mapping.get(s, s)


def is_valid_transition(current_status: str, next_status: str) -> bool:
    """Validates whether transitioning from current_status to next_status is permitted."""
    curr = current_status.upper().strip()
    nxt = next_status.upper().strip()

    # Same state is always idempotent/allowed
    if curr == nxt:
        return True

    allowed = LEGAL_TRANSITIONS.get(curr, set())
    if nxt in allowed:
        return True

    # Also check normalized forms
    norm_curr = normalize_status(curr)
    norm_nxt = normalize_status(nxt)
    if norm_curr == norm_nxt:
        return True

    norm_allowed = LEGAL_TRANSITIONS.get(norm_curr, set())
    return norm_nxt in norm_allowed or any(normalize_status(x) == norm_nxt for x in norm_allowed)


def validate_transition(current_status: str, next_status: str) -> bool:
    """Raises ValueError if transition is illegal, otherwise returns True."""
    if not is_valid_transition(current_status, next_status):
        raise ValueError(
            f"Ruxsat etilmagan holat o‘tishi: '{current_status}' -> '{next_status}'. "
            f"To‘lov tasdiqlanmasdan reklama chop etilishi mumkin emas!"
        )
    return True


STATUS_UZBEK_LABELS: Dict[str, str] = {
    "NEW": "🆕 Yangi so‘rov",
    "AWAITING_PRICE": "⏳ Narx kutilmoqda (Admin ko‘rib chiqmoqda)",
    "AWAITING_PAYMENT": "💳 To‘lov kutilmoqda",
    "RECEIPT_SUBMITTED": "🔍 To‘lov cheki tekshirilmoqda",
    "PAYMENT_APPROVED": "✅ To‘lov tasdiqlandi",
    "PAYMENT_REJECTED": "❌ To‘lov rad etildi (qayta yuborish mumkin)",
    "READY_TO_PUBLISH": "⏳ Chop etishga tayyor",
    "SCHEDULED": "📅 Rejalashtirilgan",
    "PUBLISHED": "🚀 Guruhga chop etilgan",
    "PUBLICATION_FAILED": "⚠️ Chop etishda xatolik yuz berdi",
    "CANCELLED": "🚫 Bekor qilingan",
    "EXPIRED": "⌛️ Muddati o‘tgan",
    # Legacy aliases
    "CREATED": "🆕 Yangi so‘rov",
    "PRICE_PENDING": "⏳ Narx kutilmoqda",
    "WAITING_PAYMENT": "💳 To‘lov kutilmoqda",
    "PAYMENT_REVIEW": "🔍 Chek tekshirilmoqda",
    "APPROVED": "✅ To‘lov tasdiqlandi",
    "REJECTED": "❌ Rad etilgan",
}


def get_status_label(status: str) -> str:
    """Returns human-friendly Uzbek Latin label for status."""
    return STATUS_UZBEK_LABELS.get(status.upper().strip(), status)
