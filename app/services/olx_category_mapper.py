"""
OLX.uz Category and Field Mapping Service.

Translates Defender Bot structured questionnaire categories, subcategories,
and answers into standardized parameters accepted by OLX.uz advert placement.
"""

from typing import Dict, Any, Optional, List
import re


class OlxCategoryMapping:
    def __init__(
        self,
        category_name_uz: str,
        category_name_ru: str,
        search_terms: List[str],
        default_params: Optional[Dict[str, str]] = None
    ):
        self.category_name_uz = category_name_uz
        self.category_name_ru = category_name_ru
        self.search_terms = search_terms
        self.default_params = default_params or {}


class OlxCategoryMapper:
    # Hierarchical mapping from (category_id, subcategory_id) to OLX categories
    MAPPINGS: Dict[str, OlxCategoryMapping] = {
        # Real Estate
        "real_estate:novostroyka": OlxCategoryMapping(
            category_name_uz="Ko‘chmas mulk > Kvartiralar > Yangi qurilgan uylar",
            category_name_ru="Недвижимость > Квартиры > Новостройки",
            search_terms=["Квартиры", "Новостройки", "Yangi qurilgan uylar", "Kvartiralar"]
        ),
        "real_estate:secondary_apt": OlxCategoryMapping(
            category_name_uz="Ko‘chmas mulk > Kvartiralar > Ikkilamchi bozor",
            category_name_ru="Недвижимость > Квартиры > Вторичный рынок",
            search_terms=["Квартиры", "Вторичный рынок", "Kvartiralar", "Ikkilamchi bozor"]
        ),
        "real_estate:house": OlxCategoryMapping(
            category_name_uz="Ko‘chmas mulk > Uylar > Uylar sotuvi",
            category_name_ru="Недвижимость > Дома > Продажа домов",
            search_terms=["Дома", "Продажа домов", "Uylar", "Hovli"]
        ),
        "real_estate:land": OlxCategoryMapping(
            category_name_uz="Ko‘chmas mulk > Yer uchastkalari",
            category_name_ru="Недвижимость > Земля > Продажа земли",
            search_terms=["Земля", "Yer uchastkalari", "Продажа земли"]
        ),
        "real_estate:commercial": OlxCategoryMapping(
            category_name_uz="Ko‘chmas mulk > Tijorat binolari",
            category_name_ru="Недвижимость > Коммерческая недвижимость",
            search_terms=["Коммерческая недвижимость", "Tijorat"]
        ),
        "real_estate:rent": OlxCategoryMapping(
            category_name_uz="Ko‘chmas mulk > Kvartiralar > Uzoq muddatli ijara",
            category_name_ru="Недвижимость > Квартиры > Долгосрочная аренда",
            search_terms=["Квартиры", "Долгосрочная аренда", "Ijara", "Аренда"]
        ),
        "real_estate": OlxCategoryMapping(
            category_name_uz="Ko‘chmas mulk > Kvartiralar",
            category_name_ru="Недвижимость > Квартиры",
            search_terms=["Недвижимость", "Квартиры"]
        ),

        # Furniture
        "furniture:sofa": OlxCategoryMapping(
            category_name_uz="Uy va bog' > Mebel > Mehmonxona mebeli",
            category_name_ru="Дом и сад > Мебель > Мебель для гостиной",
            search_terms=["Мебель для гостиной", "Диваны", "Диван", "Divan"]
        ),
        "furniture:bed": OlxCategoryMapping(
            category_name_uz="Uy va bog' > Mebel > Yotoqxona mebeli",
            category_name_ru="Дом и сад > Мебель > Мебель для спальни",
            search_terms=["Мебель для спальни", "Кровати", "Karavot"]
        ),
        "furniture:table_chairs": OlxCategoryMapping(
            category_name_uz="Uy va bog' > Mebel > Stol va stullar",
            category_name_ru="Дом и сад > Мебель > Столы и стулья",
            search_terms=["Столы и стулья", "Stol", "Stul"]
        ),
        "furniture:kitchen_furniture": OlxCategoryMapping(
            category_name_uz="Uy va bog' > Mebel > Oshxona mebeli",
            category_name_ru="Дом и сад > Мебель > Кухонная мебель",
            search_terms=["Кухонная мебель", "Oshxona mebeli"]
        ),
        "furniture:wardrobe": OlxCategoryMapping(
            category_name_uz="Uy va bog' > Mebel > Shkaflar",
            category_name_ru="Дом и сад > Мебель > Шкафы и комоды",
            search_terms=["Шкафы", "Комоды", "Shkaf"]
        ),
        "furniture:kids_furniture": OlxCategoryMapping(
            category_name_uz="Uy va bog' > Mebel > Bolalar mebeli",
            category_name_ru="Дом и сад > Мебель > Детская мебель",
            search_terms=["Детская мебель", "Bolalar mebeli"]
        ),
        "furniture:office_furniture": OlxCategoryMapping(
            category_name_uz="Biznes va xizmatlar > Uskunalar > Ofis mebeli",
            category_name_ru="Бизнес и услуги > Оборудование > Офисная мебель",
            search_terms=["Офисная мебель", "Ofis mebeli"]
        ),
        "furniture": OlxCategoryMapping(
            category_name_uz="Uy va bog' > Mebel",
            category_name_ru="Дом и сад > Мебель",
            search_terms=["Мебель", "Mebel"]
        ),

        # Curtains and Blinds
        "curtains_blinds": OlxCategoryMapping(
            category_name_uz="Uy va bog' > Interyer jihozlari > Pardalar va jalyuzi",
            category_name_ru="Дом и сад > Предметы интерьера > Шторы, жалюзи",
            search_terms=["Шторы", "Жалюзи", "Pardalar", "Jalyuzi"]
        ),

        # Electronics & Other
        "electronics_other:phones": OlxCategoryMapping(
            category_name_uz="Elektronika > Telefonlar > Mobil telefonlar",
            category_name_ru="Электроника > Телефоны > Мобильные телефоны",
            search_terms=["Мобильные телефоны", "Телефоны", "Telefonlar"]
        ),
        "electronics_other:computers": OlxCategoryMapping(
            category_name_uz="Elektronika > Kompyuterlar va noutbuklar",
            category_name_ru="Электроника > Компьютеры и ноутбуки",
            search_terms=["Компьютеры", "Ноутбуки", "Kompyuterlar"]
        ),
        "electronics_other:appliances": OlxCategoryMapping(
            category_name_uz="Elektronika > Maishiy texnika",
            category_name_ru="Электроника > Техника для дома",
            search_terms=["Техника для дома", "Бытовая техника", "Maishiy texnika"]
        ),
        "electronics_other:building_materials": OlxCategoryMapping(
            category_name_uz="Uy va bog' > Qurilish va ta'mirlash",
            category_name_ru="Дом и сад > Строительство и ремонт",
            search_terms=["Строительство и ремонт", "Qurilish mollari"]
        ),
        "electronics_other:services": OlxCategoryMapping(
            category_name_uz="Biznes va xizmatlar > Xizmatlar",
            category_name_ru="Бизнес и услуги > Услуги",
            search_terms=["Услуги", "Xizmatlar"]
        ),
        "electronics_other:auto": OlxCategoryMapping(
            category_name_uz="Transport > Yengil avtomobillar",
            category_name_ru="Транспорт > Легковые автомобили",
            search_terms=["Легковые автомобили", "Авто", "Mashinalar"]
        ),
        "electronics_other": OlxCategoryMapping(
            category_name_uz="Elektronika > Boshqa texnika",
            category_name_ru="Электроника > Прочая электроника",
            search_terms=["Электроника", "Boshqa"]
        ),
    }

    @classmethod
    def get_olx_category(cls, category_id: str, subcategory_id: Optional[str] = None) -> OlxCategoryMapping:
        """Finds closest matching OLX category for category and subcategory."""
        key = f"{category_id}:{subcategory_id}" if subcategory_id else category_id
        if key in cls.MAPPINGS:
            return cls.MAPPINGS[key]
        if category_id in cls.MAPPINGS:
            return cls.MAPPINGS[category_id]
        # Default fallback
        return OlxCategoryMapping(
            category_name_uz="Boshqa tovarlar",
            category_name_ru="Другие товары",
            search_terms=["Другие товары", "Boshqa"]
        )

    @classmethod
    def prepare_advert_data(
        cls,
        category_id: str,
        subcategory_id: Optional[str],
        answers: Dict[str, Any],
        preview_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extracts and normalizes all fields to satisfy OLX validation rules:
        - Title: 16 to 70 chars (enriched from user answers).
        - Description: 80 to 9000 chars (from clean preview_text and user answers).
        - Price: numeric item selling price (from user answers or preview_text, NEVER bot fee).
        - Currency: UZS / USD.
        - Location: City / District.
        - Phone: Normalized contact phone.
        - Condition: 'yangi' or 'ishlatilgan'.
        """
        mapping = cls.get_olx_category(category_id, subcategory_id)

        # 1. Title formatting from user data
        raw_title = answers.get("title") or answers.get("product_name") or answers.get("name") or answers.get("sarlavha")
        if not raw_title and preview_text:
            lines = [l.strip() for l in preview_text.splitlines() if l.strip()]
            if lines:
                raw_title = re.sub(r"<[^>]+>", "", lines[0])

        title = (raw_title or "").strip()
        # Strip leading icons/emojis
        title = re.sub(r"^[^\w\d]+", "", title).strip()

        # If title is short (< 16 chars), enrich with actual user answers (brand, model, storage, color)
        if len(title) < 16:
            enrich_parts = []
            for k in ["brand", "model", "storage", "color", "rooms"]:
                val = answers.get(k)
                if val and str(val).lower() not in title.lower():
                    enrich_parts.append(str(val))
            if enrich_parts:
                title = f"{title} {' '.join(enrich_parts)}".strip()

        # OLX requires at least 16 characters for title
        if len(title) < 16:
            title = f"{title} sotiladi (yaxshi holatda)" if title else "Sifatli mahsulot sotiladi"
        title = title[:70]

        # 2. Description formatting from user data
        desc_parts = []
        user_desc = answers.get("description") or answers.get("details") or answers.get("tavsif")
        if user_desc:
            desc_parts.append(str(user_desc).strip())

        # Use full formatted preview_text (stripped of HTML tags) as it contains all user answers
        if preview_text:
            clean_preview = re.sub(r"<[^>]+>", "", preview_text).strip()
            if clean_preview and clean_preview not in desc_parts:
                desc_parts.append(clean_preview)
        else:
            # Build attributes list from answers
            attr_lines = []
            skip_keys = {
                "title", "product_name", "name", "sarlavha",
                "description", "details", "tavsif",
                "price", "price_amount", "currency", "valyuta",
                "phone", "contact_phone", "media"
            }
            for k, v in answers.items():
                if k not in skip_keys and v:
                    label = k.replace("_", " ").capitalize()
                    attr_lines.append(f"• {label}: {v}")
            if attr_lines:
                desc_parts.append("Qo‘shimcha ma’lumotlar:\n" + "\n".join(attr_lines))

        phone_val = answers.get("phone") or answers.get("contact_phone")
        if phone_val and phone_val not in "\n".join(desc_parts):
            desc_parts.append(f"\nMurojaat uchun telefon: {phone_val}")

        description = "\n\n".join(desc_parts).strip()
        # OLX requires at least 80 characters for description
        if len(description) < 80:
            description += "\n\nBatafsil ma'lumot olish uchun ko'rsatilgan telefon raqami orqali bog'lanishingiz mumkin. Sifati kafolatlangan."
        description = description[:9000]

        # 3. Item Selling Price (USER'S product price, NOT bot advertising fee)
        price_val = answers.get("price") or answers.get("price_amount") or answers.get("narx")
        price_num = 0
        if price_val is not None:
            digits = re.sub(r"[^\d]", "", str(price_val))
            if digits:
                price_num = int(digits)

        clean_preview = re.sub(r"<[^>]+>", "", preview_text) if preview_text else ""

        # Fallback to extracting price from preview_text if missing from answers dict
        if price_num == 0 and clean_preview:
            match = re.search(r"(?:Narxi?|Baho|Narx):\s*([0-9\s.,]+)", clean_preview, re.IGNORECASE)
            if match:
                digits = re.sub(r"[^\d]", "", match.group(1))
                if digits:
                    price_num = int(digits)

        # Currency
        currency_val = str(answers.get("currency") or answers.get("valyuta") or "").lower()
        if not currency_val and clean_preview:
            currency_val = clean_preview.lower()
        if "usd" in currency_val or "y.e" in currency_val or "$" in currency_val:
            currency = "USD"
        else:
            currency = "UZS"

        # 4. Location formatting
        city_district = answers.get("city_district") or answers.get("location") or answers.get("address") or answers.get("shahar")
        if not city_district and clean_preview:
            match = re.search(r"(?:Manzil|Shahar|Joylashuv):\s*([^\n\r]+)", clean_preview, re.IGNORECASE)
            if match:
                city_district = match.group(1).strip()
        city_district = city_district or "Toshkent"
        address = answers.get("address") or ""

        # 5. Contact phone
        phone = answers.get("phone") or answers.get("contact_phone") or answers.get("aloqa") or ""
        if not phone and clean_preview:
            match = re.search(r"(?:Aloqa|Telefon|Tel):\s*([+0-9\s]+)", clean_preview, re.IGNORECASE)
            if match:
                phone = match.group(1).strip()

        # 6. Condition (Yangi / Ishlatilgan)
        condition_val = str(answers.get("condition") or answers.get("holati") or "").lower()
        if "yangi" in condition_val or "yangi" in description.lower():
            state = "yangi"
        elif "ishlatilgan" in condition_val or "b/u" in condition_val or "ikkinchi" in condition_val:
            state = "ishlatilgan"
        else:
            state = "ishlatilgan" if "ideal" not in condition_val and "yaxshi" in condition_val else "yangi"

        # 7. Brand extraction (Apple, Samsung, etc.)
        brand = answers.get("brand") or answers.get("brend") or answers.get("marka") or ""
        if not brand:
            known_brands = [
                "Apple", "Samsung", "Xiaomi", "Honor", "Huawei", "Vivo", "Oppo",
                "Realme", "Nokia", "Redmi", "Poco", "Artel", "ASUS", "Lenovo",
                "Sony", "LG", "ZTE", "Motorola", "Infinix", "Tecno"
            ]
            check_text = f"{title} {clean_preview}".lower()
            for b in known_brands:
                if b.lower() in check_text:
                    brand = b
                    break

        return {
            "title": title,
            "description": description,
            "category_mapping": mapping,
            "price": price_num,
            "currency": currency,
            "city_district": city_district,
            "address": address,
            "phone": phone,
            "condition": state,
            "brand": brand,
        }
