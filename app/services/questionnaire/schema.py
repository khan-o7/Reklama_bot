from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Callable


class FieldType(str, Enum):
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    TEXT = "text"
    DESCRIPTION = "description"
    INTEGER = "integer"
    DECIMAL = "decimal"
    PRICE = "price"
    PHONE = "phone"
    LOCATION = "location"
    PHOTO = "photo"
    VIDEO = "video"
    MULTI_PHOTO = "multi_photo"
    DOCUMENT = "document"
    BOOLEAN = "boolean"
    OPTIONAL_TEXT = "optional_text"


@dataclass
class FieldOption:
    id: str
    label: str
    value: str
    icon: Optional[str] = None


@dataclass
class QuestionField:
    id: str
    label: str
    prompt: str
    field_type: FieldType
    required: bool = True
    options: List[FieldOption] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    condition_key: Optional[str] = None
    condition_values: Optional[List[str]] = None
    help_text: Optional[str] = None
    display_order: int = 0
    include_in_ad: bool = True
    is_public: bool = True
    placeholder: Optional[str] = None

    def is_applicable(self, current_answers: Dict[str, Any]) -> bool:
        if self.condition:
            try:
                return self.condition(current_answers)
            except Exception:
                return True
        if self.condition_key and self.condition_values is not None:
            val = current_answers.get(self.condition_key)
            if isinstance(val, list):
                return any(v in self.condition_values for v in val)
            return str(val) in [str(v) for v in self.condition_values]
        return True


@dataclass
class Subcategory:
    id: str
    label: str
    icon: Optional[str] = None
    description: Optional[str] = None
    specific_fields: List[QuestionField] = field(default_factory=list)


@dataclass
class Category:
    id: str
    label: str
    icon: Optional[str] = None
    description: Optional[str] = None
    subcategories: Dict[str, Subcategory] = field(default_factory=dict)
    common_fields: List[QuestionField] = field(default_factory=list)

    def get_all_fields_for_subcategory(self, subcategory_id: Optional[str]) -> List[QuestionField]:
        fields = list(self.common_fields)
        if subcategory_id and subcategory_id in self.subcategories:
            fields.extend(self.subcategories[subcategory_id].specific_fields)
        fields.sort(key=lambda f: f.display_order)
        return fields
