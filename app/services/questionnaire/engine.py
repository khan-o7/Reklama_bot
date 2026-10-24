import re
from typing import Dict, Any, List, Optional, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.services.questionnaire.schema import QuestionField, FieldType, Category
from app.services.questionnaire.definitions import get_categories


class QuestionnaireEngine:
    @classmethod
    def get_categories(cls) -> Dict[str, Category]:
        return get_categories()

    @classmethod
    def get_category(cls, category_id: str) -> Optional[Category]:
        return cls.get_categories().get(category_id)

    @classmethod
    def get_applicable_fields(
        cls,
        category_id: str,
        subcategory_id: Optional[str],
        answers: Dict[str, Any]
    ) -> List[QuestionField]:
        """
        Dynamically computes the list of active/applicable fields based on current answers.
        If a conditional field's condition is not met, it is excluded.
        """
        cat = cls.get_category(category_id)
        if not cat:
            return []

        all_fields = cat.get_all_fields_for_subcategory(subcategory_id)
        applicable = [f for f in all_fields if f.is_applicable(answers)]
        return applicable

    @classmethod
    def get_field_by_id(
        cls,
        category_id: str,
        subcategory_id: Optional[str],
        field_id: str
    ) -> Optional[QuestionField]:
        cat = cls.get_category(category_id)
        if not cat:
            return None
        all_fields = cat.get_all_fields_for_subcategory(subcategory_id)
        for f in all_fields:
            if f.id == field_id:
                return f
        return None

    @classmethod
    def get_next_field(
        cls,
        category_id: str,
        subcategory_id: Optional[str],
        answers: Dict[str, Any],
        current_field_id: Optional[str] = None
    ) -> Tuple[Optional[QuestionField], int, int]:
        """
        Returns (next_field, current_index_1_based, total_applicable_fields).
        """
        applicable = cls.get_applicable_fields(category_id, subcategory_id, answers)
        total = len(applicable)
        if total == 0:
            return None, 0, 0

        if not current_field_id:
            return applicable[0], 1, total

        for idx, f in enumerate(applicable):
            if f.id == current_field_id:
                if idx + 1 < total:
                    return applicable[idx + 1], idx + 2, total
                else:
                    return None, total, total

        # If current_field_id was skipped or condition changed, find first unanswered field
        for idx, f in enumerate(applicable):
            if f.id not in answers and f.required:
                return f, idx + 1, total

        return None, total, total

    @classmethod
    def get_previous_field(
        cls,
        category_id: str,
        subcategory_id: Optional[str],
        answers: Dict[str, Any],
        current_field_id: str
    ) -> Optional[QuestionField]:
        """
        Finds the previous applicable field for the Back (Orqaga) button.
        """
        applicable = cls.get_applicable_fields(category_id, subcategory_id, answers)
        for idx, f in enumerate(applicable):
            if f.id == current_field_id and idx > 0:
                return applicable[idx - 1]
        return None

    @classmethod
    def validate_input(
        cls,
        field_def: QuestionField,
        value: Any
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Validates user submitted value against field rules.
        Returns (is_valid, parsed_value, error_message_uzbek).
        """
        rules = field_def.validation_rules or {}

        # Handle empty/skipped
        if value is None or (isinstance(value, str) and not value.strip()):
            if field_def.required:
                return False, None, "Ushbu ma’lumotni kiritish majburiy. Iltimos, javobingizni yuboring."
            return True, None, None

        ftype = field_def.field_type

        # String-based text fields
        if ftype in (FieldType.TEXT, FieldType.DESCRIPTION, FieldType.OPTIONAL_TEXT):
            s_val = str(value).strip()
            min_l = rules.get("min_length", 1 if field_def.required else 0)
            max_l = rules.get("max_length", 3000)

            if len(s_val) < min_l:
                return False, None, f"Matn juda qisqa. Kamida {min_l} ta belgi kiriting."
            if len(s_val) > max_l:
                return False, None, f"Matn juda uzun. Maksimal {max_l} ta belgi kiritish mumkin."
            return True, s_val, None

        # Price validation
        elif ftype == FieldType.PRICE:
            # Clean numeric string: remove spaces, commas, som, $
            clean_str = re.sub(r"[^\d]", "", str(value))
            if not clean_str:
                return False, None, "Iltimos, narxni faqat butun musbat son bilan kiriting (masalan: <code>500000</code>)."
            try:
                num = int(clean_str)
            except ValueError:
                return False, None, "Narx formati noto‘g‘ri. Faqat raqam kiriting."

            min_v = rules.get("min", 1)
            max_v = rules.get("max", 100_000_000_000)
            if num < min_v:
                return False, None, f"Narx noldan katta bo‘lishi kerak (kamida {min_v})."
            if num > max_v:
                return False, None, "Kiritilgan summa ruxsat etilgan maksimal qiymatdan katta."
            return True, num, None

        # Integer validation
        elif ftype == FieldType.INTEGER:
            clean_str = re.sub(r"[^\d\-]", "", str(value))
            try:
                num = int(clean_str)
            except ValueError:
                return False, None, "Iltimos, butun son kiriting (masalan: <code>3</code>)."
            min_v = rules.get("min", 1)
            max_v = rules.get("max", 1000)
            if num < min_v:
                return False, None, f"Raqam kamida {min_v} bo‘lishi kerak."
            if num > max_v:
                return False, None, f"Raqam ko‘pi bilan {max_v} bo‘lishi kerak."
            return True, num, None

        # Decimal validation
        elif ftype == FieldType.DECIMAL:
            clean_str = str(value).replace(",", ".").strip()
            try:
                num = float(clean_str)
            except ValueError:
                return False, None, "Iltimos, o‘nlik son kiriting (masalan: <code>65.5</code>)."
            min_v = rules.get("min", 0.1)
            max_v = rules.get("max", 100000.0)
            if num < min_v:
                return False, None, f"Qiymat kamida {min_v} bo‘lishi kerak."
            if num > max_v:
                return False, None, f"Qiymat ko‘pi bilan {max_v} bo‘lishi kerak."
            # Round to 2 decimals
            return True, round(num, 2), None

        # Phone validation
        elif ftype == FieldType.PHONE:
            raw_phone = str(value).strip()
            # Allow international formats (+998, etc.)
            clean_digits = re.sub(r"[^\d\+]", "", raw_phone)
            regex = rules.get("regex", r"^\+?[0-9]{7,15}$")
            if not re.match(regex, clean_digits):
                return False, None, "Telefon raqami formati noto‘g‘ri. Masalan: <code>+998901234567</code> tarzida kiriting."
            return True, clean_digits, None

        # Single select validation
        elif ftype == FieldType.SINGLE_SELECT:
            s_val = str(value).strip()
            valid_ids = [opt.id for opt in field_def.options]
            valid_vals = [opt.value for opt in field_def.options]
            if s_val in valid_ids:
                # Return label or value
                for opt in field_def.options:
                    if opt.id == s_val:
                        return True, opt.value, None
            if s_val in valid_vals:
                return True, s_val, None
            return False, None, "Iltimos, taklif etilgan variantlardan birini tanlang."

        # Boolean validation
        elif ftype == FieldType.BOOLEAN:
            s_val = str(value).strip().lower()
            if field_def.options:
                valid_ids = [opt.id for opt in field_def.options]
                if s_val in valid_ids:
                    for opt in field_def.options:
                        if opt.id == s_val:
                            return True, opt.value, None
            if s_val in ("ha", "yes", "true", "1"):
                return True, "Ha", None
            if s_val in ("yo‘q", "yoq", "no", "false", "0"):
                return True, "Yo‘q", None
            return True, str(value), None

        # Media fields
        elif ftype in (FieldType.PHOTO, FieldType.VIDEO, FieldType.MULTI_PHOTO):
            return True, value, None

        return True, value, None

    @classmethod
    def build_field_keyboard(
        cls,
        field_def: QuestionField,
        can_go_back: bool = True,
        is_optional: bool = False,
        include_done_media_btn: bool = False,
        media_count: int = 0
    ) -> InlineKeyboardMarkup:
        """
        Builds dynamic inline keyboard for the current question:
        - Options for SINGLE_SELECT / BOOLEAN
        - Navigation row: [⬅️ Orqaga], [⏭ O‘tkazib yuborish], [❌ Bekor qilish]
        """
        rows: List[List[InlineKeyboardButton]] = []

        # Options buttons
        if field_def.field_type in (FieldType.SINGLE_SELECT, FieldType.BOOLEAN) and field_def.options:
            opts = field_def.options
            # If 2 or 3 options, lay them out neatly
            if len(opts) <= 4:
                btn_row = []
                for opt in opts:
                    label = f"{opt.icon} {opt.label}" if opt.icon else opt.label
                    btn_row.append(
                        InlineKeyboardButton(
                            text=label,
                            callback_data=f"qans:{field_def.id}:{opt.id}"
                        )
                    )
                    if len(btn_row) == 2:
                        rows.append(btn_row)
                        btn_row = []
                if btn_row:
                    rows.append(btn_row)
            else:
                for opt in opts:
                    label = f"{opt.icon} {opt.label}" if opt.icon else opt.label
                    rows.append([
                        InlineKeyboardButton(
                            text=label,
                            callback_data=f"qans:{field_def.id}:{opt.id}"
                        )
                    ])

        # For media fields with items uploaded, show "Tayyor / Tugatish" button
        if include_done_media_btn or (field_def.field_type == FieldType.MULTI_PHOTO and media_count > 0):
            rows.append([
                InlineKeyboardButton(
                    text=f"✅ Yuklashni yakunlash ({media_count} ta rasm)",
                    callback_data="qnav:media_done"
                )
            ])

        # Navigation row
        nav_row: List[InlineKeyboardButton] = []
        if can_go_back:
            nav_row.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="qnav:back"))
        if is_optional or not field_def.required:
            nav_row.append(InlineKeyboardButton(text="⏭ O‘tkazib yuborish", callback_data="qnav:skip"))
        nav_row.append(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="qnav:cancel"))

        if nav_row:
            rows.append(nav_row)

        return InlineKeyboardMarkup(inline_keyboard=rows)
