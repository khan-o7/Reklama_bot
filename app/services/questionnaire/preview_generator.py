import html
from typing import Dict, Any, Optional
from app.services.questionnaire.definitions import get_categories


class AdvertisementPreviewGenerator:
    @classmethod
    def generate_preview(
        cls,
        category_id: str,
        subcategory_id: Optional[str],
        answers: Dict[str, Any],
        for_telegram: bool = True
    ) -> str:
        """
        Generates structured and human-readable advertisement preview text in Uzbek Latin.
        Strictly avoids 'None', 'null', or empty placeholders.
        """
        cats = get_categories()
        cat = cats.get(category_id)
        subcat = cat.subcategories.get(subcategory_id) if (cat and subcategory_id) else None

        if category_id == "real_estate":
            return cls._preview_real_estate(subcat, answers)
        elif category_id == "furniture":
            return cls._preview_furniture(subcat, answers)
        elif category_id == "curtains_blinds":
            return cls._preview_curtains(subcat, answers)
        elif category_id == "electronics_other":
            return cls._preview_electronics(subcat, answers)
        else:
            return cls._preview_generic(cat, subcat, answers)

    @classmethod
    def _preview_real_estate(cls, subcat: Optional[Any], answers: Dict[str, Any]) -> str:
        lines = []
        deal_type = answers.get("deal_type", "E’lon").upper()
        title = answers.get("title") or (subcat.label if subcat else "Ko‘chmas mulk")

        header_icon = "🏠"
        if subcat:
            if subcat.id == "commercial":
                header_icon = "🏬"
            elif subcat.id == "land":
                header_icon = "🌱"
            elif subcat.id == "house":
                header_icon = "🏡"
            elif subcat.id == "novostroyka":
                header_icon = "🏗"

        lines.append(f"{header_icon} <b>{deal_type} — {html.escape(title).upper()}</b>\n")

        # Specific details
        if answers.get("complex_name"):
            lines.append(f"🏢 <b>TJM / Majmua:</b> {html.escape(str(answers['complex_name']))}")
        if answers.get("developer"):
            lines.append(f"🏗 <b>Quruvchi:</b> {html.escape(str(answers['developer']))}")
        if answers.get("rooms"):
            lines.append(f"🛏 <b>Xonalar soni:</b> {html.escape(str(answers['rooms']))}")
        if answers.get("total_area"):
            lines.append(f"📐 <b>Umumiy maydon:</b> {answers['total_area']} m²")
        if answers.get("land_area"):
            lines.append(f"🌱 <b>Yer maydoni:</b> {html.escape(str(answers['land_area']))}")
        if answers.get("floor") and answers.get("total_floors"):
            lines.append(f"🏙 <b>Qavat:</b> {answers['floor']}/{answers['total_floors']}")
        elif answers.get("floor"):
            lines.append(f"🏙 <b>Qavat:</b> {answers['floor']}")
        elif answers.get("house_floors"):
            lines.append(f"🏙 <b>Uy qavatlari:</b> {answers['house_floors']}")

        if answers.get("construction_status"):
            lines.append(f"⏳ <b>Qurilish holati:</b> {html.escape(str(answers['construction_status']))}")
        if answers.get("repair_status"):
            lines.append(f"🛠 <b>Ta’mir holati:</b> {html.escape(str(answers['repair_status']))}")
        elif answers.get("repair_condition"):
            lines.append(f"🛠 <b>Ta’mir holati:</b> {html.escape(str(answers['repair_condition']))}")

        if answers.get("furniture_included"):
            lines.append(f"🛋 <b>Mebel va texnika:</b> {html.escape(str(answers['furniture_included']))}")
        if answers.get("commercial_purpose"):
            lines.append(f"💼 <b>Bino maqsadi:</b> {html.escape(str(answers['commercial_purpose']))}")
        if answers.get("land_use"):
            lines.append(f"📌 <b>Yer toifasi:</b> {html.escape(str(answers['land_use']))}")
        if answers.get("utilities"):
            lines.append(f"⚡️ <b>Kommunikatsiyalar:</b> {html.escape(str(answers['utilities']))}")

        # Location
        loc_parts = []
        if answers.get("city_district"):
            loc_parts.append(str(answers["city_district"]))
        if answers.get("address"):
            loc_parts.append(str(answers["address"]))
        if loc_parts:
            lines.append(f"📍 <b>Manzil:</b> {html.escape(', '.join(loc_parts))}")
        if answers.get("landmark"):
            lines.append(f"🎯 <b>Mo‘ljal:</b> {html.escape(str(answers['landmark']))}")

        # Price and Payment
        if answers.get("price"):
            cur = answers.get("currency", "so‘m")
            try:
                p_num = int(answers["price"])
                p_formatted = f"{p_num:,}".replace(",", " ")
            except (ValueError, TypeError):
                p_formatted = str(answers["price"])
            neg = " (kelishiladi)" if "kelishiladi" in str(answers.get("price_negotiable", "")).lower() else ""
            lines.append(f"💰 <b>Narxi:</b> {p_formatted} {cur}{neg}")

        if answers.get("deposit"):
            lines.append(f"🔒 <b>Depozit (garov):</b> {html.escape(str(answers['deposit']))}")
        if answers.get("payment_method"):
            lines.append(f"💳 <b>To‘lov usuli:</b> {html.escape(str(answers['payment_method']))}")

        # Contact
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("phone_secondary"):
            lines.append(f"☎️ <b>Qo‘shimcha tel:</b> <code>{html.escape(str(answers['phone_secondary']))}</code>")

        # Description
        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    @classmethod
    def _preview_furniture(cls, subcat: Optional[Any], answers: Dict[str, Any]) -> str:
        lines = []
        title = answers.get("title") or (subcat.label if subcat else "Mebel")
        lines.append(f"🛋 <b>SOTILADI — {html.escape(title).upper()}</b>\n")

        if subcat:
            lines.append(f"🪑 <b>Mebel turi:</b> {html.escape(subcat.label)}")
        if answers.get("condition"):
            lines.append(f"✨ <b>Holati:</b> {html.escape(str(answers['condition']))}")
        if answers.get("ready_or_custom"):
            lines.append(f"📐 <b>Ishlab chiqarish:</b> {html.escape(str(answers['ready_or_custom']))}")
        if answers.get("brand"):
            lines.append(f"🏷 <b>Ishlab chiqaruvchi:</b> {html.escape(str(answers['brand']))}")
        if answers.get("material"):
            lines.append(f"🪵 <b>Material:</b> {html.escape(str(answers['material']))}")
        if answers.get("color"):
            lines.append(f"🎨 <b>Rangi:</b> {html.escape(str(answers['color']))}")
        if answers.get("dimensions"):
            lines.append(f"📏 <b>O‘lchamlari:</b> {html.escape(str(answers['dimensions']))}")
        if answers.get("lead_time"):
            lines.append(f"⏱ <b>Tayyorlanish muddati:</b> {html.escape(str(answers['lead_time']))}")
        if answers.get("defects"):
            lines.append(f"⚠️ <b>Holati/Nuqsoni:</b> {html.escape(str(answers['defects']))}")

        if answers.get("delivery"):
            lines.append(f"🚚 <b>Yetkazib berish:</b> {html.escape(str(answers['delivery']))}")
        if answers.get("assembly"):
            lines.append(f"🔧 <b>O‘rnatish:</b> {html.escape(str(answers['assembly']))}")

        if answers.get("location"):
            lines.append(f"📍 <b>Joylashuv:</b> {html.escape(str(answers['location']))}")

        if answers.get("price"):
            try:
                p_num = int(answers["price"])
                p_formatted = f"{p_num:,}".replace(",", " ")
            except (ValueError, TypeError):
                p_formatted = str(answers["price"])
            neg = " (kelishiladi)" if "kelishiladi" in str(answers.get("price_negotiable", "")).lower() else ""
            lines.append(f"💰 <b>Narxi:</b> {p_formatted} so‘m{neg}")

        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")

        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    @classmethod
    def _preview_curtains(cls, subcat: Optional[Any], answers: Dict[str, Any]) -> str:
        lines = []
        title = answers.get("title") or (subcat.label if subcat else "Jalyuzi va pardalar")
        lines.append(f"🪟 <b>{html.escape(title).upper()}</b>\n")

        if subcat:
            lines.append(f"📌 <b>Turi:</b> {html.escape(subcat.label)}")
        if answers.get("ready_or_custom"):
            lines.append(f"📐 <b>Xizmat:</b> {html.escape(str(answers['ready_or_custom']))}")
        if answers.get("material"):
            lines.append(f"🧵 <b>Material / Mato:</b> {html.escape(str(answers['material']))}")
        if answers.get("color_design"):
            lines.append(f"🎨 <b>Rangi va dizayni:</b> {html.escape(str(answers['color_design']))}")
        if answers.get("measurement_service"):
            lines.append(f"📏 <b>O‘lchash (zamer):</b> {html.escape(str(answers['measurement_service']))}")
        if answers.get("installation"):
            lines.append(f"🔩 <b>O‘rnatish:</b> {html.escape(str(answers['installation']))}")
        if answers.get("lead_time"):
            lines.append(f"⏱ <b>Tayyorlanish muddati:</b> {html.escape(str(answers['lead_time']))}")
        if answers.get("warranty"):
            lines.append(f"🛡 <b>Kafolat:</b> {html.escape(str(answers['warranty']))}")

        if answers.get("unit_price"):
            try:
                p_num = int(answers["unit_price"])
                p_formatted = f"{p_num:,}".replace(",", " ")
            except (ValueError, TypeError):
                p_formatted = str(answers["unit_price"])
            unit = answers.get("pricing_unit", "1 m² uchun")
            lines.append(f"💰 <b>Narxi:</b> {p_formatted} so‘m ({unit})")

        if answers.get("location"):
            lines.append(f"📍 <b>Hudud:</b> {html.escape(str(answers['location']))}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")

        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    @staticmethod
    def _format_price(answers: Dict[str, Any], suffix: str = "") -> str:
        if not answers.get("price"):
            return ""
        cur = answers.get("currency", "so‘m")
        try:
            p_num = int(answers["price"])
            p_formatted = f"{p_num:,}".replace(",", " ")
        except (ValueError, TypeError):
            p_formatted = str(answers["price"])
        neg = " (kelishiladi)" if "kelishiladi" in str(answers.get("price_negotiable", "")).lower() else ""
        return f"{p_formatted} {cur}{suffix}{neg}"

    @classmethod
    def _preview_electronics(cls, subcat: Optional[Any], answers: Dict[str, Any]) -> str:
        subcat_id = subcat.id if subcat else ""
        if subcat_id == "smartphones":
            return cls._preview_smartphones(answers)
        elif subcat_id == "computers":
            return cls._preview_computers(answers)
        elif subcat_id == "tv_audio":
            return cls._preview_tv_audio(answers)
        elif subcat_id == "home_appliances":
            return cls._preview_home_appliances(answers)
        elif subcat_id == "hvac":
            return cls._preview_hvac(answers)
        elif subcat_id == "construction":
            return cls._preview_construction(answers)
        elif subcat_id == "tools":
            return cls._preview_tools(answers)
        elif subcat_id == "auto_parts":
            return cls._preview_auto_parts(answers)
        elif subcat_id == "clothing":
            return cls._preview_clothing(answers)
        elif subcat_id == "services":
            return cls._preview_services(answers)
        elif subcat_id == "other_goods":
            return cls._preview_other_goods(answers)
        else:
            return cls._preview_smartphones(answers)

    # 1. SMARTPHONES
    @classmethod
    def _preview_smartphones(cls, answers: Dict[str, Any]) -> str:
        lines = []
        title = answers.get("title") or "Telefon / Planshet"
        lines.append(f"📱 <b>TELEFON — {html.escape(title).upper()}</b>\n")

        brand = answers.get("brand")
        model = answers.get("model")
        if brand and model:
            lines.append(f"🏷 <b>Brend va model:</b> {html.escape(str(brand))} {html.escape(str(model))}")
        elif brand:
            lines.append(f"🏷 <b>Brend:</b> {html.escape(str(brand))}")
        elif model:
            lines.append(f"🏷 <b>Model:</b> {html.escape(str(model))}")

        if answers.get("storage"):
            lines.append(f"💾 <b>Xotira hajmi (ROM):</b> {html.escape(str(answers['storage']))}")
        if answers.get("ram") and str(answers["ram"]) != "Tegishli emas":
            lines.append(f"⚡️ <b>Operativ xotira (RAM):</b> {html.escape(str(answers['ram']))}")
        if answers.get("color"):
            lines.append(f"🎨 <b>Rangi:</b> {html.escape(str(answers['color']))}")
        if answers.get("condition"):
            lines.append(f"✨ <b>Holati:</b> {html.escape(str(answers['condition']))}")
        if answers.get("battery_health"):
            lines.append(f"🔋 <b>Batareya:</b> {html.escape(str(answers['battery_health']))}")
        if answers.get("sim_config"):
            lines.append(f"📶 <b>SIM karta:</b> {html.escape(str(answers['sim_config']))}")
        if answers.get("repaired_status"):
            lines.append(f"🔧 <b>Ta’mirlash:</b> {html.escape(str(answers['repaired_status']))}")
        if answers.get("defects"):
            lines.append(f"⚠️ <b>Nuqsonlar:</b> {html.escape(str(answers['defects']))}")
        if answers.get("accessories"):
            lines.append(f"📦 <b>Komplekt:</b> {html.escape(str(answers['accessories']))}")
        if answers.get("warranty"):
            lines.append(f"🛡 <b>Kafolat:</b> {html.escape(str(answers['warranty']))}")
        if answers.get("delivery"):
            lines.append(f"🚚 <b>Yetkazib berish:</b> {html.escape(str(answers['delivery']))}")
        if answers.get("location"):
            lines.append(f"📍 <b>Manzil:</b> {html.escape(str(answers['location']))}")

        p_str = cls._format_price(answers)
        if p_str:
            lines.append(f"💰 <b>Narxi:</b> {p_str}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    # 2. COMPUTERS & LAPTOPS
    @classmethod
    def _preview_computers(cls, answers: Dict[str, Any]) -> str:
        lines = []
        dev_type = answers.get("device_type", "Kompyuter")
        title = answers.get("title") or dev_type
        lines.append(f"💻 <b>{html.escape(dev_type).upper()} — {html.escape(title).upper()}</b>\n")

        if answers.get("brand_model"):
            lines.append(f"🏷 <b>Brend va model:</b> {html.escape(str(answers['brand_model']))}")
        if answers.get("cpu"):
            lines.append(f"⚙️ <b>Protsessor (CPU):</b> {html.escape(str(answers['cpu']))}")
        if answers.get("ram"):
            lines.append(f"⚡️ <b>Tezkor xotira (RAM):</b> {html.escape(str(answers['ram']))}")
        if answers.get("storage"):
            lines.append(f"💾 <b>Doimiy xotira (SSD/HDD):</b> {html.escape(str(answers['storage']))}")
        if answers.get("gpu"):
            lines.append(f"🎮 <b>Videokarta (GPU):</b> {html.escape(str(answers['gpu']))}")
        if answers.get("screen_size"):
            lines.append(f"📺 <b>Ekran:</b> {html.escape(str(answers['screen_size']))}")
        if answers.get("os"):
            lines.append(f"💿 <b>Operatsion tizim:</b> {html.escape(str(answers['os']))}")
        if answers.get("battery_status"):
            lines.append(f"🔋 <b>Batareya holati:</b> {html.escape(str(answers['battery_status']))}")
        if answers.get("condition"):
            lines.append(f"✨ <b>Texnik holati:</b> {html.escape(str(answers['condition']))}")
        if answers.get("defects"):
            lines.append(f"⚠️ <b>Nuqsonlar:</b> {html.escape(str(answers['defects']))}")
        if answers.get("accessories"):
            lines.append(f"📦 <b>Komplekt:</b> {html.escape(str(answers['accessories']))}")
        if answers.get("warranty"):
            lines.append(f"🛡 <b>Kafolat:</b> {html.escape(str(answers['warranty']))}")
        if answers.get("delivery"):
            lines.append(f"🚚 <b>Yetkazib berish:</b> {html.escape(str(answers['delivery']))}")
        if answers.get("location"):
            lines.append(f"📍 <b>Manzil:</b> {html.escape(str(answers['location']))}")

        p_str = cls._format_price(answers)
        if p_str:
            lines.append(f"💰 <b>Narxi:</b> {p_str}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    # 3. TV & AUDIO
    @classmethod
    def _preview_tv_audio(cls, answers: Dict[str, Any]) -> str:
        lines = []
        dev_type = answers.get("device_type", "Audio / Video")
        title = answers.get("title") or dev_type
        lines.append(f"📺 <b>{html.escape(dev_type).upper()} — {html.escape(title).upper()}</b>\n")

        brand = answers.get("brand")
        model = answers.get("model")
        if brand and model:
            lines.append(f"🏷 <b>Brend va model:</b> {html.escape(str(brand))} {html.escape(str(model))}")
        elif brand:
            lines.append(f"🏷 <b>Brend:</b> {html.escape(str(brand))}")
        elif model:
            lines.append(f"🏷 <b>Model:</b> {html.escape(str(model))}")

        if answers.get("screen_size"):
            lines.append(f"📏 <b>Ekran diagonali:</b> {html.escape(str(answers['screen_size']))}")
        if answers.get("screen_tech"):
            lines.append(f"🖥 <b>Displey texnologiyasi:</b> {html.escape(str(answers['screen_tech']))}")
        if answers.get("resolution"):
            lines.append(f"🔍 <b>Ekran aniqligi:</b> {html.escape(str(answers['resolution']))}")
        if answers.get("smart_tv"):
            lines.append(f"🌐 <b>Smart TV:</b> {html.escape(str(answers['smart_tv']))}")
        if answers.get("audio_power"):
            lines.append(f"🔊 <b>Audio quvvati:</b> {html.escape(str(answers['audio_power']))}")
        if answers.get("wireless"):
            lines.append(f"📶 <b>Simsiz ulanish:</b> {html.escape(str(answers['wireless']))}")
        if answers.get("interfaces"):
            lines.append(f"🔌 <b>Ulanish portlari:</b> {html.escape(str(answers['interfaces']))}")
        if answers.get("condition"):
            lines.append(f"✨ <b>Holati:</b> {html.escape(str(answers['condition']))}")
        if answers.get("defects"):
            lines.append(f"⚠️ <b>Nuqsonlar:</b> {html.escape(str(answers['defects']))}")
        if answers.get("accessories"):
            lines.append(f"📦 <b>Komplekt:</b> {html.escape(str(answers['accessories']))}")
        if answers.get("warranty"):
            lines.append(f"🛡 <b>Kafolat:</b> {html.escape(str(answers['warranty']))}")
        if answers.get("delivery"):
            lines.append(f"🚚 <b>Yetkazib berish:</b> {html.escape(str(answers['delivery']))}")
        if answers.get("location"):
            lines.append(f"📍 <b>Manzil:</b> {html.escape(str(answers['location']))}")

        p_str = cls._format_price(answers)
        if p_str:
            lines.append(f"💰 <b>Narxi:</b> {p_str}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    # 4. HOME APPLIANCES
    @classmethod
    def _preview_home_appliances(cls, answers: Dict[str, Any]) -> str:
        lines = []
        app_type = answers.get("appliance_type", "Maishiy texnika")
        title = answers.get("title") or app_type
        lines.append(f"🧊 <b>{html.escape(app_type).upper()} — {html.escape(title).upper()}</b>\n")

        if answers.get("brand_model"):
            lines.append(f"🏷 <b>Brend va model:</b> {html.escape(str(answers['brand_model']))}")
        if answers.get("capacity"):
            lines.append(f"📦 <b>Sig‘imi / Hajmi:</b> {html.escape(str(answers['capacity']))}")
        if answers.get("spin_speed"):
            lines.append(f"🔄 <b>Aylanish tezligi:</b> {html.escape(str(answers['spin_speed']))}")
        if answers.get("dimensions"):
            lines.append(f"📐 <b>O‘lchamlari:</b> {html.escape(str(answers['dimensions']))}")
        if answers.get("color"):
            lines.append(f"🎨 <b>Rangi:</b> {html.escape(str(answers['color']))}")
        if answers.get("energy_class") and str(answers["energy_class"]) != "Noma’lum":
            lines.append(f"⚡️ <b>Energiya sinfi:</b> {html.escape(str(answers['energy_class']))}")
        if answers.get("condition"):
            lines.append(f"✨ <b>Holati:</b> {html.escape(str(answers['condition']))}")
        if answers.get("working_status"):
            lines.append(f"⚙️ <b>Ishlash holati:</b> {html.escape(str(answers['working_status']))}")
        if answers.get("manufacture_year"):
            lines.append(f"🗓 <b>Ishlab chiqarilgan yili:</b> {html.escape(str(answers['manufacture_year']))}")
        if answers.get("defects"):
            lines.append(f"⚠️ <b>Nuqsonlar:</b> {html.escape(str(answers['defects']))}")
        if answers.get("installation"):
            lines.append(f"🛠 <b>O‘rnatish xizmati:</b> {html.escape(str(answers['installation']))}")
        if answers.get("warranty"):
            lines.append(f"🛡 <b>Kafolat:</b> {html.escape(str(answers['warranty']))}")
        if answers.get("delivery"):
            lines.append(f"🚚 <b>Yetkazib berish:</b> {html.escape(str(answers['delivery']))}")
        if answers.get("location"):
            lines.append(f"📍 <b>Manzil:</b> {html.escape(str(answers['location']))}")

        p_str = cls._format_price(answers)
        if p_str:
            lines.append(f"💰 <b>Narxi:</b> {p_str}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    # 5. HVAC
    @classmethod
    def _preview_hvac(cls, answers: Dict[str, Any]) -> str:
        lines = []
        hvac_type = answers.get("hvac_type", "Isitish/Sovutish")
        title = answers.get("title") or hvac_type
        lines.append(f"❄️ <b>{html.escape(hvac_type).upper()} — {html.escape(title).upper()}</b>\n")

        if answers.get("brand_model"):
            lines.append(f"🏷 <b>Brend va model:</b> {html.escape(str(answers['brand_model']))}")
        if answers.get("capacity_power"):
            lines.append(f"⚡️ <b>Quvvati:</b> {html.escape(str(answers['capacity_power']))}")
        if answers.get("recommended_area"):
            lines.append(f"📐 <b>Tavsiya etilgan maydon:</b> {html.escape(str(answers['recommended_area']))}")
        if answers.get("inverter") and "Tegishli emas" not in str(answers["inverter"]):
            lines.append(f"🔄 <b>Inverter:</b> {html.escape(str(answers['inverter']))}")
        if answers.get("energy_class"):
            lines.append(f"🌿 <b>Energiya samaradorligi:</b> {html.escape(str(answers['energy_class']))}")
        if answers.get("freon_type") and "Tegishli emas" not in str(answers["freon_type"]) and "Noma’lum" not in str(answers["freon_type"]):
            lines.append(f"🧪 <b>Freon turi:</b> {html.escape(str(answers['freon_type']))}")
        if answers.get("condition"):
            lines.append(f"✨ <b>Holati:</b> {html.escape(str(answers['condition']))}")
        if answers.get("technical_condition"):
            lines.append(f"⚙️ <b>Texnik holati:</b> {html.escape(str(answers['technical_condition']))}")
        if answers.get("installation"):
            lines.append(f"🛠 <b>O‘rnatish xizmati:</b> {html.escape(str(answers['installation']))}")
        if answers.get("dismantling"):
            lines.append(f"🔧 <b>Demontaj:</b> {html.escape(str(answers['dismantling']))}")
        if answers.get("warranty"):
            lines.append(f"🛡 <b>Kafolat:</b> {html.escape(str(answers['warranty']))}")
        if answers.get("delivery"):
            lines.append(f"🚚 <b>Yetkazib berish:</b> {html.escape(str(answers['delivery']))}")
        if answers.get("location"):
            lines.append(f"📍 <b>Manzil:</b> {html.escape(str(answers['location']))}")

        p_str = cls._format_price(answers)
        if p_str:
            lines.append(f"💰 <b>Narxi:</b> {p_str}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    # 6. CONSTRUCTION MATERIALS
    @classmethod
    def _preview_construction(cls, answers: Dict[str, Any]) -> str:
        lines = []
        title = answers.get("title") or "Qurilish materiali"
        lines.append(f"🧱 <b>QURILISH MATERIALI — {html.escape(title).upper()}</b>\n")

        if answers.get("material_type"):
            lines.append(f"📌 <b>Toifasi:</b> {html.escape(str(answers['material_type']))}")
        if answers.get("brand_manufacturer"):
            lines.append(f"🏭 <b>Ishlab chiqaruvchi:</b> {html.escape(str(answers['brand_manufacturer']))}")
        if answers.get("grade_model"):
            lines.append(f"🏷 <b>Markasi / Modeli:</b> {html.escape(str(answers['grade_model']))}")
        if answers.get("dimensions"):
            lines.append(f"📐 <b>O‘lchamlari:</b> {html.escape(str(answers['dimensions']))}")
        if answers.get("color"):
            lines.append(f"🎨 <b>Rangi:</b> {html.escape(str(answers['color']))}")
        if answers.get("condition"):
            lines.append(f"✨ <b>Holati:</b> {html.escape(str(answers['condition']))}")
        if answers.get("stock_quantity"):
            lines.append(f"📦 <b>Mavjud zaxira:</b> {html.escape(str(answers['stock_quantity']))}")
        if answers.get("min_order"):
            lines.append(f"⚖️ <b>Minimal buyurtma:</b> {html.escape(str(answers['min_order']))}")
        if answers.get("wholesale"):
            lines.append(f"🤝 <b>Ulgurji narx:</b> {html.escape(str(answers['wholesale']))}")
        if answers.get("certificate"):
            lines.append(f"📜 <b>Sifat sertifikati:</b> {html.escape(str(answers['certificate']))}")
        if answers.get("loading_service"):
            lines.append(f"🏗 <b>Yuklash / tushirish:</b> {html.escape(str(answers['loading_service']))}")
        if answers.get("delivery_area"):
            lines.append(f"🚚 <b>Yetkazib berish hududi:</b> {html.escape(str(answers['delivery_area']))}")
        if answers.get("location"):
            lines.append(f"📍 <b>Ombor manzili:</b> {html.escape(str(answers['location']))}")

        unit = answers.get("unit_of_measure", "birlik")
        p_str = cls._format_price(answers, suffix=f" / {unit}")
        if p_str:
            lines.append(f"💰 <b>Birlik narxi:</b> {p_str}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    # 7. TOOLS & EQUIPMENT
    @classmethod
    def _preview_tools(cls, answers: Dict[str, Any]) -> str:
        lines = []
        deal = answers.get("deal_type", "Sotiladi")
        title = answers.get("title") or "Asbob-uskuna"
        lines.append(f"🛠 <b>{html.escape(deal).upper()} — {html.escape(title).upper()}</b>\n")

        if answers.get("tool_type"):
            lines.append(f"⚙️ <b>Asbob turi:</b> {html.escape(str(answers['tool_type']))}")
        if answers.get("brand_model"):
            lines.append(f"🏷 <b>Brend va model:</b> {html.escape(str(answers['brand_model']))}")
        if answers.get("purpose_specs"):
            lines.append(f"📋 <b>Vazifasi:</b> {html.escape(str(answers['purpose_specs']))}")
        if answers.get("power_specs"):
            lines.append(f"⚡️ <b>Quvvati:</b> {html.escape(str(answers['power_specs']))}")
        if answers.get("operation_type"):
            lines.append(f"🔌 <b>Ishlash turi:</b> {html.escape(str(answers['operation_type']))}")
        if answers.get("accessories"):
            lines.append(f"📦 <b>Komplekt:</b> {html.escape(str(answers['accessories']))}")
        if answers.get("condition"):
            lines.append(f"✨ <b>Holati:</b> {html.escape(str(answers['condition']))}")
        if answers.get("defects"):
            lines.append(f"⚠️ <b>Nuqsonlar:</b> {html.escape(str(answers['defects']))}")
        if answers.get("quantity"):
            lines.append(f"🔢 <b>Miqdori:</b> {html.escape(str(answers['quantity']))}")
        if answers.get("warranty"):
            lines.append(f"🛡 <b>Kafolat:</b> {html.escape(str(answers['warranty']))}")
        if answers.get("rental_terms"):
            lines.append(f"🔄 <b>Ijara shartlari:</b> {html.escape(str(answers['rental_terms']))}")
        if answers.get("delivery"):
            lines.append(f"🚚 <b>Yetkazib berish:</b> {html.escape(str(answers['delivery']))}")
        if answers.get("location"):
            lines.append(f"📍 <b>Joylashuv:</b> {html.escape(str(answers['location']))}")

        p_str = cls._format_price(answers)
        if p_str:
            prefix = "Ijara narxi" if "ijara" in str(deal).lower() else "Narxi"
            lines.append(f"💰 <b>{prefix}:</b> {p_str}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    # 8. AUTO PARTS
    @classmethod
    def _preview_auto_parts(cls, answers: Dict[str, Any]) -> str:
        lines = []
        title = answers.get("title") or "Avto ehtiyot qism"
        lines.append(f"🚗 <b>AVTO EHTIYOT QISM — {html.escape(title).upper()}</b>\n")

        if answers.get("part_category"):
            lines.append(f"⚙️ <b>Kategoriya:</b> {html.escape(str(answers['part_category']))}")

        car_brand = answers.get("car_brand", "")
        car_model = answers.get("car_model", "")
        year_range = answers.get("year_range", "")
        if car_brand and car_model:
            yr_str = f" ({html.escape(year_range)})" if year_range else ""
            lines.append(f"🚘 <b>Mos avtomobil:</b> {html.escape(car_brand)} {html.escape(car_model)}{yr_str}")
        elif car_model:
            lines.append(f"🚘 <b>Mos avtomobil:</b> {html.escape(car_model)}")

        if answers.get("part_originality"):
            lines.append(f"🏷 <b>Qism turi:</b> {html.escape(str(answers['part_originality']))}")
        if answers.get("part_number"):
            lines.append(f"🔢 <b>OEM / Detal raqami:</b> <code>{html.escape(str(answers['part_number']))}</code>")
        if answers.get("brand_manufacturer"):
            lines.append(f"🏭 <b>Ishlab chiqaruvchi:</b> {html.escape(str(answers['brand_manufacturer']))}")
        if answers.get("condition"):
            lines.append(f"✨ <b>Holati:</b> {html.escape(str(answers['condition']))}")
        if answers.get("defects"):
            lines.append(f"⚠️ <b>Nuqsonlar:</b> {html.escape(str(answers['defects']))}")
        if answers.get("compatibility_notes"):
            lines.append(f"ℹ️ <b>Moslik:</b> {html.escape(str(answers['compatibility_notes']))}")
        if answers.get("quantity"):
            lines.append(f"📦 <b>Miqdori:</b> {html.escape(str(answers['quantity']))}")
        if answers.get("warranty_return"):
            lines.append(f"🛡 <b>Kafolat va qaytarish:</b> {html.escape(str(answers['warranty_return']))}")
        if answers.get("delivery"):
            lines.append(f"🚚 <b>Yetkazib berish:</b> {html.escape(str(answers['delivery']))}")
        if answers.get("location"):
            lines.append(f"📍 <b>Manzil:</b> {html.escape(str(answers['location']))}")

        p_str = cls._format_price(answers)
        if p_str:
            lines.append(f"💰 <b>Narxi:</b> {p_str}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    # 9. CLOTHING & ACCESSORIES
    @classmethod
    def _preview_clothing(cls, answers: Dict[str, Any]) -> str:
        lines = []
        c_type = answers.get("clothing_type", "Kiyim-kechak")
        title = answers.get("title") or c_type
        lines.append(f"👔 <b>KIYIM-KECHAK — {html.escape(title).upper()}</b>\n")

        if answers.get("clothing_type"):
            lines.append(f"📌 <b>Turi:</b> {html.escape(str(answers['clothing_type']))}")

        brand = answers.get("brand")
        coll = answers.get("model_collection")
        if brand and coll:
            lines.append(f"🏷 <b>Brend:</b> {html.escape(brand)} ({html.escape(coll)})")
        elif brand:
            lines.append(f"🏷 <b>Brend:</b> {html.escape(brand)}")

        if answers.get("target_group"):
            lines.append(f"👥 <b>Mo‘ljallangan:</b> {html.escape(str(answers['target_group']))}")
        if answers.get("size"):
            lines.append(f"📏 <b>O‘lchami (Razmer):</b> {html.escape(str(answers['size']))}")
        if answers.get("color"):
            lines.append(f"🎨 <b>Rangi:</b> {html.escape(str(answers['color']))}")
        if answers.get("material"):
            lines.append(f"🧵 <b>Material:</b> {html.escape(str(answers['material']))}")
        if answers.get("condition"):
            lines.append(f"✨ <b>Holati:</b> {html.escape(str(answers['condition']))}")
        if answers.get("available_sizes_colors"):
            lines.append(f"📋 <b>Mavjud variantlar:</b> {html.escape(str(answers['available_sizes_colors']))}")
        if answers.get("sale_type"):
            lines.append(f"🛍 <b>Savdo turi:</b> {html.escape(str(answers['sale_type']))}")
        if answers.get("stock_qty"):
            lines.append(f"📦 <b>Omborda:</b> {html.escape(str(answers['stock_qty']))}")
        if answers.get("return_policy"):
            lines.append(f"🔄 <b>Qaytarish / Almashtirish:</b> {html.escape(str(answers['return_policy']))}")
        if answers.get("delivery"):
            lines.append(f"🚚 <b>Yetkazib berish:</b> {html.escape(str(answers['delivery']))}")
        if answers.get("location"):
            lines.append(f"📍 <b>Manzil:</b> {html.escape(str(answers['location']))}")

        p_str = cls._format_price(answers)
        if p_str:
            lines.append(f"💰 <b>Birlik narxi:</b> {p_str}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    # 10. SERVICES
    @classmethod
    def _preview_services(cls, answers: Dict[str, Any]) -> str:
        lines = []
        s_type = answers.get("service_type", "Xizmat ko‘rsatish")
        title = answers.get("title") or s_type
        lines.append(f"🛠 <b>XIZMAT — {html.escape(title).upper()}</b>\n")

        if answers.get("service_type"):
            lines.append(f"📌 <b>Xizmat sohasi:</b> {html.escape(str(answers['service_type']))}")
        if answers.get("service_scope"):
            lines.append(f"📋 <b>Xizmat tavsifi:</b>\n{html.escape(str(answers['service_scope']))}")
        if answers.get("service_area"):
            lines.append(f"📍 <b>Xizmat hududi:</b> {html.escape(str(answers['service_area']))}")
        if answers.get("pricing_type"):
            lines.append(f"💳 <b>To‘lov shakli:</b> {html.escape(str(answers['pricing_type']))}")

        p_str = cls._format_price(answers)
        if p_str:
            pt = answers.get("pricing_type")
            pt_note = f" ({html.escape(pt)})" if pt else ""
            lines.append(f"💰 <b>Xizmat narxi:</b> {p_str}{pt_note}")

        if answers.get("completion_time"):
            lines.append(f"⏳ <b>Bajarish muddati:</b> {html.escape(str(answers['completion_time']))}")
        if answers.get("working_hours"):
            lines.append(f"🕒 <b>Ish vaqti:</b> {html.escape(str(answers['working_hours']))}")
        if answers.get("home_visit"):
            lines.append(f"🚗 <b>Xizmat formati:</b> {html.escape(str(answers['home_visit']))}")
        if answers.get("experience"):
            lines.append(f"⭐️ <b>Tajriba / Malaka:</b> {html.escape(str(answers['experience']))}")
        if answers.get("warranty"):
            lines.append(f"🛡 <b>Kafolat:</b> {html.escape(str(answers['warranty']))}")
        if answers.get("location"):
            lines.append(f"📍 <b>Manzil / Ofis:</b> {html.escape(str(answers['location']))}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("description"):
            lines.append(f"\n📝 <b>Qo‘shimcha ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    # 11. OTHER GOODS
    @classmethod
    def _preview_other_goods(cls, answers: Dict[str, Any]) -> str:
        lines = []
        title = answers.get("title") or "Mahsulot"
        lines.append(f"📦 <b>MAHSULOT — {html.escape(title).upper()}</b>\n")

        if answers.get("item_type"):
            lines.append(f"📌 <b>Turi:</b> {html.escape(str(answers['item_type']))}")
        if answers.get("brand_model"):
            lines.append(f"🏷 <b>Brend va model:</b> {html.escape(str(answers['brand_model']))}")
        if answers.get("condition"):
            lines.append(f"✨ <b>Holati:</b> {html.escape(str(answers['condition']))}")

        qty = answers.get("quantity")
        unit = answers.get("unit_of_measure")
        if qty and unit:
            lines.append(f"🔢 <b>Miqdori:</b> {html.escape(str(qty))} {html.escape(str(unit))}")
        elif qty:
            lines.append(f"🔢 <b>Miqdori:</b> {html.escape(str(qty))}")
        elif unit:
            lines.append(f"⚖️ <b>O‘lchov birligi:</b> {html.escape(str(unit))}")

        if answers.get("delivery"):
            lines.append(f"🚚 <b>Yetkazib berish:</b> {html.escape(str(answers['delivery']))}")
        if answers.get("location"):
            lines.append(f"📍 <b>Manzil:</b> {html.escape(str(answers['location']))}")

        p_str = cls._format_price(answers)
        if p_str:
            lines.append(f"💰 <b>Narxi:</b> {p_str}")
        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")
        if answers.get("description"):
            lines.append(f"\n📝 <b>Batafsil ma’lumot:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)

    @classmethod
    def _preview_generic(cls, cat: Optional[Any], subcat: Optional[Any], answers: Dict[str, Any]) -> str:
        lines = []
        title = answers.get("title") or (subcat.label if subcat else (cat.label if cat else "E’lon"))
        lines.append(f"📢 <b>{html.escape(title).upper()}</b>\n")

        for k, v in answers.items():
            if k in ("title", "description", "media", "currency", "price_negotiable") or v is None:
                continue
            clean_val = str(v)
            if clean_val and clean_val != "None":
                lines.append(f"• <b>{html.escape(k.replace('_', ' ').capitalize())}:</b> {html.escape(clean_val)}")

        if answers.get("price"):
            cur = answers.get("currency", "so‘m")
            lines.append(f"\n💰 <b>Narxi:</b> {answers['price']} {cur}")

        if answers.get("phone"):
            lines.append(f"📞 <b>Aloqa:</b> <code>{html.escape(str(answers['phone']))}</code>")

        if answers.get("description"):
            lines.append(f"\n📝 <b>Tavsif:</b>\n{html.escape(str(answers['description']))}")

        return "\n".join(lines)
