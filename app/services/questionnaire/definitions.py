from typing import Dict
from app.services.questionnaire.schema import (
    Category,
    Subcategory,
    QuestionField,
    FieldOption,
    FieldType,
)


def get_categories() -> Dict[str, Category]:
    categories: Dict[str, Category] = {}

    # =========================================================================
    # CATEGORY A: UY VA KO‘CHMAS MULK (real_estate)
    # =========================================================================
    re_common_fields = [
        QuestionField(
            id="deal_type",
            label="Bitim turi",
            prompt="Iltimos, bitim turini tanlang:",
            field_type=FieldType.SINGLE_SELECT,
            required=True,
            display_order=10,
            options=[
                FieldOption(id="sotiladi", label="Sotiladi", value="Sotiladi", icon="🏷"),
                FieldOption(id="ijara_uzoq", label="Uzoq muddatli ijara", value="Uzoq muddatli ijara", icon="📅"),
                FieldOption(id="ijara_kunlik", label="Kunlik ijara", value="Kunlik ijara", icon="⏰"),
                FieldOption(id="boshqa", label="Boshqa bitim", value="Boshqa", icon="🔄"),
            ]
        ),
        QuestionField(
            id="title",
            label="E’lon sarlavhasi",
            prompt="E’loningiz uchun qisqa sarlavha kiriting (masalan: <i>Yunusobodda 3 xonali shinam xonadon</i>):",
            field_type=FieldType.TEXT,
            required=True,
            display_order=20,
            validation_rules={"min_length": 5, "max_length": 150}
        ),
        QuestionField(
            id="city_district",
            label="Shahar va tuman",
            prompt="Shahar va tumanni kiriting (masalan: <i>Toshkent shahar, Yunusobod tumani</i>):",
            field_type=FieldType.TEXT,
            required=True,
            display_order=30,
            validation_rules={"min_length": 3, "max_length": 120}
        ),
        QuestionField(
            id="address",
            label="Aniq manzil",
            prompt="Aniq manzilni kiriting (ko‘cha, mavze, uy raqami):",
            field_type=FieldType.TEXT,
            required=True,
            display_order=40,
            validation_rules={"min_length": 3, "max_length": 200}
        ),
        QuestionField(
            id="landmark",
            label="Mo‘ljal",
            prompt="Yaqin atrofidagi mashhur mo‘ljalni kiriting (masalan: <i>Mega Planet ro‘parasida</i>):",
            field_type=FieldType.TEXT,
            required=False,
            display_order=50,
            validation_rules={"max_length": 150}
        ),
        QuestionField(
            id="price",
            label="Narx",
            prompt="Obyekt narxini kiriting (faqat raqam bilan, masalan: <code>650000000</code> yoki <code>55000</code>):",
            field_type=FieldType.PRICE,
            required=True,
            display_order=60,
            validation_rules={"min": 1, "max": 100_000_000_000}
        ),
        QuestionField(
            id="currency",
            label="Valyuta",
            prompt="Narx valyutasini tanlang:",
            field_type=FieldType.SINGLE_SELECT,
            required=True,
            display_order=65,
            options=[
                FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m", icon="🇺🇿"),
                FieldOption(id="usd", label="AQSH Dollari (USD)", value="y.e. (USD)", icon="🇺🇸"),
            ]
        ),
        QuestionField(
            id="price_negotiable",
            label="Narx kelishiladimi",
            prompt="Narxni kelishish (savdolashish) imkoniyati bormi?",
            field_type=FieldType.BOOLEAN,
            required=True,
            display_order=70,
            options=[
                FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi", icon="🤝"),
                FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx", icon="🔒"),
            ]
        ),
        QuestionField(
            id="phone",
            label="Aloqa telefoni",
            prompt="Bog‘lanish uchun asosiy telefon raqamingizni kiriting (masalan: <code>+998901234567</code>):",
            field_type=FieldType.PHONE,
            required=True,
            display_order=80,
            validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
        ),
        QuestionField(
            id="phone_secondary",
            label="Qo‘shimcha telefon",
            prompt="Qo‘shimcha aloqa telefon raqami (agar bo‘lsa, aks holda «O‘tkazib yuborish»ni bosing):",
            field_type=FieldType.PHONE,
            required=False,
            display_order=85,
            validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
        ),
        QuestionField(
            id="payment_method",
            label="To‘lov usuli",
            prompt="To‘lov qabul qilish shartlarini tanlang:",
            field_type=FieldType.SINGLE_SELECT,
            required=False,
            display_order=90,
            options=[
                FieldOption(id="naqd", label="Naqd to‘lov", value="Naqd", icon="💵"),
                FieldOption(id="ipoteka", label="Ipoteka / Bank", value="Ipoteka mumkin", icon="🏦"),
                FieldOption(id="bolib", label="Bo‘lib to‘lash (Rassrochka)", value="Bo‘lib to‘lash", icon="📊"),
                FieldOption(id="har_qanday", label="Ixtiyoriy to‘lov usuli", value="Ixtiyoriy", icon="💳"),
            ]
        ),
        QuestionField(
            id="description",
            label="Qo‘shimcha tavsif",
            prompt="Obyekt haqida batafsil ma’lumot va qo‘shimcha tavsif yozing:",
            field_type=FieldType.DESCRIPTION,
            required=False,
            display_order=95,
            validation_rules={"max_length": 2500}
        ),
        QuestionField(
            id="media",
            label="Rasmlar va video",
            prompt="Obyektning sifatli rasmlarini yuboring (1 tadan 10 tagacha rasm yoki video yuborishingiz mumkin):",
            field_type=FieldType.MULTI_PHOTO,
            required=False,
            display_order=100,
            validation_rules={"max_items": 10}
        )
    ]

    re_subcategories: Dict[str, Subcategory] = {
        "novostroyka": Subcategory(
            id="novostroyka",
            label="Yangi qurilgan xonadon (novostroyka)",
            icon="🏗",
            specific_fields=[
                QuestionField(
                    id="complex_name",
                    label="Uy-joy majmuasi nomi",
                    prompt="Turar-joy majmuasi (TJM) nomini kiriting (masalan: <i>Nest One, Modern City</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=22,
                    validation_rules={"max_length": 150}
                ),
                QuestionField(
                    id="developer",
                    label="Quruvchi / Developer",
                    prompt="Quruvchi yoki developer kompaniya nomi (agar ma’lum bo‘lsa):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=24,
                    validation_rules={"max_length": 150}
                ),
                QuestionField(
                    id="rooms",
                    label="Xonalar soni",
                    prompt="Xonadon necha xonali?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=25,
                    options=[
                        FieldOption(id="1", label="1 xonali", value="1 xona"),
                        FieldOption(id="2", label="2 xonali", value="2 xona"),
                        FieldOption(id="3", label="3 xonali", value="3 xona"),
                        FieldOption(id="4", label="4 xonali", value="4 xona"),
                        FieldOption(id="5_plus", label="5+ xonali", value="5+ xona"),
                        FieldOption(id="studio", label="Studiya", value="Studiya"),
                    ]
                ),
                QuestionField(
                    id="total_area",
                    label="Umumiy maydon (m²)",
                    prompt="Xonadonning umumiy maydoni necha m² (masalan: <code>68.5</code>):",
                    field_type=FieldType.DECIMAL,
                    required=True,
                    display_order=26,
                    validation_rules={"min": 10, "max": 2000}
                ),
                QuestionField(
                    id="living_area",
                    label="Yashash maydoni (m²)",
                    prompt="Yashash maydoni necha m² (agar ma’lum bo‘lsa):",
                    field_type=FieldType.DECIMAL,
                    required=False,
                    display_order=27,
                    validation_rules={"min": 5, "max": 1500}
                ),
                QuestionField(
                    id="floor",
                    label="Qavat",
                    prompt="Xonadon joylashgan qavat (masalan: <code>5</code>):",
                    field_type=FieldType.INTEGER,
                    required=True,
                    display_order=28,
                    validation_rules={"min": 1, "max": 100}
                ),
                QuestionField(
                    id="total_floors",
                    label="Binoning jami qavatlari",
                    prompt="Binoning umumiy qavatlari soni (masalan: <code>16</code>):",
                    field_type=FieldType.INTEGER,
                    required=True,
                    display_order=29,
                    validation_rules={"min": 1, "max": 100}
                ),
                QuestionField(
                    id="construction_status",
                    label="Qurilish holati",
                    prompt="Qurilish holati yoki topshirish muddatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=31,
                    options=[
                        FieldOption(id="topshirilgan", label="Foydalanishga topshirilgan", value="Topshirilgan / Tayyor"),
                        FieldOption(id="qurilmoqda", label="Qurilish jarayonida", value="Qurilmoqda"),
                        FieldOption(id="kotlovan", label="Poydevor bosqichida", value="Poydevor bosqichida"),
                    ]
                ),
                QuestionField(
                    id="repair_status",
                    label="Ta’mir holati",
                    prompt="Xonadonning ichki holati qanday?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=32,
                    options=[
                        FieldOption(id="qora", label="Qora suvoq (korobka)", value="Qora suvoq"),
                        FieldOption(id="oq", label="Oq suvoq (chistovoy)", value="Oq suvoq"),
                        FieldOption(id="tamirlangan", label="To‘liq ta’mirlangan (evro)", value="To‘liq ta’mirlangan"),
                        FieldOption(id="mualliflik", label="Mualliflik dizayni (dizaynerskiy)", value="Dizaynerskiy"),
                    ]
                ),
            ]
        ),
        "secondary_apt": Subcategory(
            id="secondary_apt",
            label="Ikkilamchi bozordagi xonadon",
            icon="🏢",
            specific_fields=[
                QuestionField(
                    id="rooms",
                    label="Xonalar soni",
                    prompt="Xonadon necha xonali?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=25,
                    options=[
                        FieldOption(id="1", label="1 xonali", value="1 xona"),
                        FieldOption(id="2", label="2 xonali", value="2 xona"),
                        FieldOption(id="3", label="3 xonali", value="3 xona"),
                        FieldOption(id="4", label="4 xonali", value="4 xona"),
                        FieldOption(id="5_plus", label="5+ xonali", value="5+ xona"),
                    ]
                ),
                QuestionField(
                    id="total_area",
                    label="Umumiy maydon (m²)",
                    prompt="Umumiy maydon necha m² (masalan: <code>54</code>):",
                    field_type=FieldType.DECIMAL,
                    required=True,
                    display_order=26,
                    validation_rules={"min": 10, "max": 1000}
                ),
                QuestionField(
                    id="floor",
                    label="Qavat",
                    prompt="Xonadon nechanchi qavatda (masalan: <code>3</code>):",
                    field_type=FieldType.INTEGER,
                    required=True,
                    display_order=28,
                    validation_rules={"min": 1, "max": 30}
                ),
                QuestionField(
                    id="total_floors",
                    label="Bino qavatlari soni",
                    prompt="Uy necha qavatli (masalan: <code>4</code> yoki <code>9</code>):",
                    field_type=FieldType.INTEGER,
                    required=True,
                    display_order=29,
                    validation_rules={"min": 1, "max": 50}
                ),
                QuestionField(
                    id="building_type",
                    label="Bino turi",
                    prompt="Bino qurilish materialini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=31,
                    options=[
                        FieldOption(id="gisht", label="G‘ishtli (kirpich)", value="G‘ishtli"),
                        FieldOption(id="panel", label="Panelli", value="Panelli"),
                        FieldOption(id="monolit", label="Monolit", value="Monolit"),
                    ]
                ),
                QuestionField(
                    id="repair_condition",
                    label="Ta’mir holati",
                    prompt="Ta’mir holatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=32,
                    options=[
                        FieldOption(id="evro", label="Evrota’mir", value="Evrota’mir"),
                        FieldOption(id="yaxshi", label="Yaxshi holatda", value="Yaxshi holatda"),
                        FieldOption(id="orta", label="O‘rtacha ta’mir", value="O‘rtacha"),
                        FieldOption(id="talab", label="Ta’mir talab", value="Ta’mir talab"),
                    ]
                ),
                QuestionField(
                    id="furniture_included",
                    label="Mebel va texnika",
                    prompt="Mebel va maishiy texnikalar qoladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=33,
                    options=[
                        FieldOption(id="barchasi", label="Barcha mebel va texnika bilan", value="To‘liq jihozlangan"),
                        FieldOption(id="qisman", label="Qisman jihozlangan (oshxona)", value="Qisman jihozlangan"),
                        FieldOption(id="mebelsiz", label="Mebelsiz bo‘sh xonadon", value="Mebelsiz"),
                    ]
                ),
            ]
        ),
        "house": Subcategory(
            id="house",
            label="Hovli uy",
            icon="🏡",
            specific_fields=[
                QuestionField(
                    id="land_area",
                    label="Yer maydoni (sotix)",
                    prompt="Hovlining yer maydoni necha sotix (masalan: <code>4.5</code>):",
                    field_type=FieldType.DECIMAL,
                    required=True,
                    display_order=25,
                    validation_rules={"min": 0.5, "max": 500}
                ),
                QuestionField(
                    id="total_area",
                    label="Uy binosi maydoni (m²)",
                    prompt="Uy binosining umumiy yashash maydoni necha m²:",
                    field_type=FieldType.DECIMAL,
                    required=True,
                    display_order=26,
                    validation_rules={"min": 20, "max": 5000}
                ),
                QuestionField(
                    id="rooms",
                    label="Xonalar soni",
                    prompt="Uyda jami necha xona bor:",
                    field_type=FieldType.INTEGER,
                    required=True,
                    display_order=27,
                    validation_rules={"min": 1, "max": 50}
                ),
                QuestionField(
                    id="house_floors",
                    label="Uy qavatlari soni",
                    prompt="Uy necha qavatli (1, 2, 3...):",
                    field_type=FieldType.INTEGER,
                    required=True,
                    display_order=28,
                    validation_rules={"min": 1, "max": 5}
                ),
                QuestionField(
                    id="utilities",
                    label="Kommunikatsiyalar",
                    prompt="Kommunikatsiya ta’minotini tanlang (gaz, suv, elektr, kanalizatsiya):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=29,
                    placeholder="Gaz, svet, suv doimiy, kanalizatsiya bor"
                ),
            ]
        ),
        "land": Subcategory(
            id="land",
            label="Yer uchastkasi",
            icon="🌱",
            specific_fields=[
                QuestionField(
                    id="land_area",
                    label="Yer maydoni",
                    prompt="Yer maydoni qancha (masalan: <code>6 sotix</code> yoki <code>1 gektar</code>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=25,
                    validation_rules={"min_length": 2, "max_length": 50}
                ),
                QuestionField(
                    id="land_use",
                    label="Yer toifasi / maqsadi",
                    prompt="Yer qanday maqsad uchun mo‘ljallangan?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=26,
                    options=[
                        FieldOption(id="turar", label="Turar-joy qurish uchun", value="Turar-joy uchun"),
                        FieldOption(id="tijorat", label="Tijorat / Ishlab chiqarish", value="Tijorat uchun"),
                        FieldOption(id="qishloq", label="Qishloq xo‘jaligi / Fermerlik", value="Qishloq xo‘jaligi"),
                        FieldOption(id="dala_hovli", label="Dala hovli (Dacha)", value="Dala hovli uchun"),
                    ]
                ),
                QuestionField(
                    id="road_access",
                    label="Yo‘l qulayligi",
                    prompt="Yer uchastkasiga kirish yo‘li qanday?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=27,
                    options=[
                        FieldOption(id="asfalt", label="Asfalt yo‘l", value="Asfalt"),
                        FieldOption(id="tuproq", label="Tuproq / shag‘al yo‘l", value="Shag‘al / tuproq"),
                    ]
                ),
                QuestionField(
                    id="documentation_status",
                    label="Hujjatlar holati",
                    prompt="Kadastr va mulk hujjatlari bormi?",
                    field_type=FieldType.BOOLEAN,
                    required=False,
                    display_order=28,
                    options=[
                        FieldOption(id="bor", label="Kadastr bor, to‘liq tayyor", value="Kadastr bor"),
                        FieldOption(id="tayyorlanmoqda", label="Hujjatlar tayyorlanmoqda", value="Tayyorlanmoqda"),
                    ]
                ),
            ]
        ),
        "commercial": Subcategory(
            id="commercial",
            label="Tijorat binosi",
            icon="🏬",
            specific_fields=[
                QuestionField(
                    id="commercial_purpose",
                    label="Bino maqsadi",
                    prompt="Tijorat obyektining asosiy faoliyat turini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=25,
                    options=[
                        FieldOption(id="ofis", label="Ofis", value="Ofis"),
                        FieldOption(id="dokon", label="Do‘kon / Magazin", value="Do‘kon"),
                        FieldOption(id="ombor", label="Omborxona (Sklad)", value="Omborxona"),
                        FieldOption(id="ishlab", label="Ishlab chiqarish (Sex)", value="Ishlab chiqarish"),
                        FieldOption(id="restoran", label="Kafe / Restoran", value="Kafe/Restoran"),
                        FieldOption(id="boshqa", label="Boshqa tijorat", value="Boshqa"),
                    ]
                ),
                QuestionField(
                    id="total_area",
                    label="Umumiy maydon (m²)",
                    prompt="Obyektning umumiy maydoni necha m²:",
                    field_type=FieldType.DECIMAL,
                    required=True,
                    display_order=26,
                    validation_rules={"min": 5, "max": 50000}
                ),
                QuestionField(
                    id="parking",
                    label="Avtoturargoh",
                    prompt="Obyekt oldida avtoturargoh (parkovka) mavjudmi?",
                    field_type=FieldType.BOOLEAN,
                    required=False,
                    display_order=27,
                    options=[
                        FieldOption(id="ha", label="Ha, keng parkovka bor", value="Parkovka bor"),
                        FieldOption(id="yoq", label="Yo‘q", value="Parkovka yo‘q"),
                    ]
                ),
            ]
        ),
        "rent": Subcategory(
            id="rent",
            label="Ijara uchun uy yoki xonadon",
            icon="🔑",
            specific_fields=[
                QuestionField(
                    id="rent_type",
                    label="Ijara turi",
                    prompt="Ijara muddatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=23,
                    options=[
                        FieldOption(id="uzoq", label="Uzoq muddatli", value="Uzoq muddatli"),
                        FieldOption(id="kunlik", label="Kunlik", value="Kunlik"),
                    ]
                ),
                QuestionField(
                    id="deposit",
                    label="Depozit (garov) summasi",
                    prompt="Garov puli (depozit) talab qilinadimi? (masalan: <code>1 oylik</code> yoki <code>Yo‘q</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=25,
                    validation_rules={"max_length": 100}
                ),
                QuestionField(
                    id="rooms",
                    label="Xonalar soni",
                    prompt="Xonadon necha xonali?",
                    field_type=FieldType.INTEGER,
                    required=True,
                    display_order=26,
                    validation_rules={"min": 1, "max": 20}
                ),
                QuestionField(
                    id="house_rules",
                    label="Qo‘shimcha talablar / Qoidalar",
                    prompt="Ijarachilarga qo‘yiladigan talablar (masalan: <i>Faqat oilaga, talabalar olinmaydi</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=27,
                    validation_rules={"max_length": 250}
                ),
            ]
        ),
        "other_re": Subcategory(
            id="other_re",
            label="Boshqa ko‘chmas mulk",
            icon="📌",
            specific_fields=[]
        )
    }

    categories["real_estate"] = Category(
        id="real_estate",
        label="Uy va ko‘chmas mulk",
        icon="🏠",
        description="Xonadonlar, hovlilar, tijorat binolari, yer uchastkalari va ijara e’lonlari",
        subcategories=re_subcategories,
        common_fields=re_common_fields
    )

    # =========================================================================
    # CATEGORY B: MEBEL (furniture)
    # =========================================================================
    furniture_common_fields = [
        QuestionField(
            id="title",
            label="E’lon sarlavhasi",
            prompt="Mebel e’loningiz uchun sarlavha kiriting (masalan: <i>Yangi turk yumshoq mebel to‘plami</i>):",
            field_type=FieldType.TEXT,
            required=True,
            display_order=10,
            validation_rules={"min_length": 5, "max_length": 150}
        ),
        QuestionField(
            id="condition",
            label="Holati",
            prompt="Mebel holatini tanlang:",
            field_type=FieldType.SINGLE_SELECT,
            required=True,
            display_order=20,
            options=[
                FieldOption(id="yangi", label="Yangi (ishlatilmagan)", value="Yangi", icon="✨"),
                FieldOption(id="ishlatilgan", label="Ishlatilgan (ideal/yaxshi holatda)", value="Ishlatilgan", icon="📦"),
            ]
        ),
        QuestionField(
            id="ready_or_custom",
            label="Tayyor yoki buyurtma",
            prompt="Mebel tayyormi yoki buyurtma asosida yasaladimi?",
            field_type=FieldType.SINGLE_SELECT,
            required=True,
            display_order=25,
            options=[
                FieldOption(id="tayyor", label="Tayyor sotuvda", value="Tayyor mahsulot", icon="🛋"),
                FieldOption(id="buyurtma", label="Buyurtma asosida tayyorlanadi", value="Buyurtma asosida", icon="📐"),
            ]
        ),
        QuestionField(
            id="defects",
            label="Nuqson va kamchiliklar",
            prompt="Mebelda qandaydir chiziq, nuqson yoki ta’mirlangan joylari bormi?",
            field_type=FieldType.TEXT,
            required=False,
            display_order=26,
            condition_key="condition",
            condition_values=["Ishlatilgan"],
            placeholder="Chiziqlar yo‘q, holati a’lo"
        ),
        QuestionField(
            id="lead_time",
            label="Tayyorlanish muddati",
            prompt="Buyurtma qilingandan so‘ng necha kunda tayyor bo‘ladi (masalan: <i>5-7 kun</i>):",
            field_type=FieldType.TEXT,
            required=False,
            display_order=27,
            condition_key="ready_or_custom",
            condition_values=["Buyurtma asosida"],
            placeholder="5-10 kun"
        ),
        QuestionField(
            id="brand",
            label="Brend / Ishlab chiqaruvchi",
            prompt="Mebel brendi yoki fabrikasi (masalan: <i>Turkiya, Bella Mebel, Mahalliy</i>):",
            field_type=FieldType.TEXT,
            required=False,
            display_order=30,
            validation_rules={"max_length": 100}
        ),
        QuestionField(
            id="material",
            label="Material",
            prompt="Mebel qanday materialdan tayyorlangan (masalan: <i>Yog‘och, MDF, DSP, Charm, Mato</i>):",
            field_type=FieldType.TEXT,
            required=False,
            display_order=40,
            validation_rules={"max_length": 100}
        ),
        QuestionField(
            id="color",
            label="Rangi",
            prompt="Mebel rangini kiriting (masalan: <i>Kulrang, Jigarrang, Oq</i>):",
            field_type=FieldType.TEXT,
            required=False,
            display_order=45,
            validation_rules={"max_length": 60}
        ),
        QuestionField(
            id="dimensions",
            label="O‘lchamlari",
            prompt="O‘lchamlari (Kenglik x Bo‘yi x Chuqurlik yoki «O‘lchov olish kerak»):",
            field_type=FieldType.TEXT,
            required=False,
            display_order=50,
            placeholder="250x180x90 sm yoki O‘lchov olish kerak"
        ),
        QuestionField(
            id="price",
            label="Narx",
            prompt="Narxini kiriting (faqat raqam bilan, masalan: <code>4500000</code>):",
            field_type=FieldType.PRICE,
            required=True,
            display_order=60,
            validation_rules={"min": 1}
        ),
        QuestionField(
            id="price_negotiable",
            label="Kelishiladimi",
            prompt="Narx kelishiladimi?",
            field_type=FieldType.BOOLEAN,
            required=True,
            display_order=65,
            options=[
                FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
            ]
        ),
        QuestionField(
            id="delivery",
            label="Yetkazib berish",
            prompt="Yetkazib berish xizmati bormi?",
            field_type=FieldType.SINGLE_SELECT,
            required=True,
            display_order=70,
            options=[
                FieldOption(id="bepul", label="Shahar bo‘ylab bepul", value="Bepul yetkazib berish"),
                FieldOption(id="kelishuv", label="Kelishuv asosida (pullik)", value="Pullik yetkazib berish"),
                FieldOption(id="olib_ketish", label="O‘zi olib ketish (Samovivoz)", value="Samovivoz"),
            ]
        ),
        QuestionField(
            id="assembly",
            label="O‘rnatish / Yig‘ish xizmati",
            prompt="O‘rnatib va yig‘ib berish xizmati mavjudmi?",
            field_type=FieldType.BOOLEAN,
            required=False,
            display_order=75,
            options=[
                FieldOption(id="bor", label="Ha, o‘rnatib beriladi", value="O‘rnatish mavjud"),
                FieldOption(id="yoq", label="Yo‘q", value="O‘rnatish yo‘q"),
            ]
        ),
        QuestionField(
            id="location",
            label="Joylashuv / Shahar",
            prompt="Mebel joylashgan manzil yoki shahar:",
            field_type=FieldType.TEXT,
            required=True,
            display_order=80,
            validation_rules={"min_length": 2, "max_length": 150}
        ),
        QuestionField(
            id="phone",
            label="Aloqa telefoni",
            prompt="Aloqa uchun telefon raqamingizni kiriting:",
            field_type=FieldType.PHONE,
            required=True,
            display_order=85,
            validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
        ),
        QuestionField(
            id="description",
            label="Qo‘shimcha tavsif",
            prompt="Mebel haqida qo‘shimcha tavsif:",
            field_type=FieldType.DESCRIPTION,
            required=False,
            display_order=90,
            validation_rules={"max_length": 2000}
        ),
        QuestionField(
            id="media",
            label="Rasmlar va video",
            prompt="Mebelning sifatli rasmlarini yuboring (1-10 ta):",
            field_type=FieldType.MULTI_PHOTO,
            required=False,
            display_order=100,
            validation_rules={"max_items": 10}
        )
    ]

    furniture_subcategories = {
        "sofa": Subcategory(id="sofa", label="Divan va yumshoq mebel", icon="🛋"),
        "bed": Subcategory(id="bed", label="Krovat va yotoqxona mebeli", icon="🛏"),
        "wardrobe": Subcategory(id="wardrobe", label="Shkaf va garderob", icon="🚪"),
        "kitchen": Subcategory(id="kitchen", label="Oshxona mebeli", icon="🍳"),
        "table_chairs": Subcategory(id="table_chairs", label="Stol va stullar", icon="🪑"),
        "office": Subcategory(id="office", label="Ofis mebeli", icon="💼"),
        "kids": Subcategory(id="kids", label="Bolalar mebeli", icon="🧸"),
        "custom_furniture": Subcategory(id="custom_furniture", label="Buyurtma asosida mebel tayyorlash", icon="🔨"),
        "other_furniture": Subcategory(id="other_furniture", label="Boshqa mebel", icon="📦"),
    }

    categories["furniture"] = Category(
        id="furniture",
        label="Mebel",
        icon="🛋",
        description="Yumshoq mebellar, yotoqxona, oshxona, shkaf, ofis va buyurtma mebellari",
        subcategories=furniture_subcategories,
        common_fields=furniture_common_fields
    )

    # =========================================================================
    # CATEGORY C: JALYUZI VA PARDALAR (curtains_blinds)
    # =========================================================================
    curtains_common_fields = [
        QuestionField(
            id="title",
            label="E’lon sarlavhasi",
            prompt="E’lon sarlavhasini kiriting (masalan: <i>Zebra jalyuzilari — eng arzon narxlarda</i>):",
            field_type=FieldType.TEXT,
            required=True,
            display_order=10,
            validation_rules={"min_length": 5, "max_length": 150}
        ),
        QuestionField(
            id="ready_or_custom",
            label="Xizmat turi",
            prompt="Tayyor mahsulot sotishmi yoki buyurtma asosida tikish / o‘rnatish xizmatimi?",
            field_type=FieldType.SINGLE_SELECT,
            required=True,
            display_order=15,
            options=[
                FieldOption(id="buyurtma", label="Buyurtma asosida yasash / tikish", value="Buyurtma asosida"),
                FieldOption(id="tayyor", label="Tayyor mahsulot sotuvi", value="Tayyor mahsulot"),
            ]
        ),
        QuestionField(
            id="material",
            label="Material / Mato",
            prompt="Mato yoki material turi (masalan: <i>Blekaut, Jakkar, Bambuk, Aluminiy</i>):",
            field_type=FieldType.TEXT,
            required=False,
            display_order=20,
            validation_rules={"max_length": 100}
        ),
        QuestionField(
            id="color_design",
            label="Rangi va dizayni",
            prompt="Mavjud ranglar yoki dizayn variantlari (masalan: <i>100 xildan ortiq ranglar</i>):",
            field_type=FieldType.TEXT,
            required=False,
            display_order=25,
            validation_rules={"max_length": 100}
        ),
        QuestionField(
            id="measurement_service",
            label="O‘lchash xizmati",
            prompt="O‘lchov olish (zamer) xizmati qanday ko‘rsatiladi?",
            field_type=FieldType.SINGLE_SELECT,
            required=True,
            display_order=30,
            options=[
                FieldOption(id="bepul", label="Katalog bilan borib bepul o‘lchash", value="Bepul o‘lchov olish"),
                FieldOption(id="pullik", label="Pullik o‘lchash", value="Pullik o‘lchov"),
                FieldOption(id="mijoz", label="Mijoz o‘zi o‘lcham beradi", value="Mijoz o‘lchami bo‘yicha"),
            ]
        ),
        QuestionField(
            id="pricing_unit",
            label="Narx o‘lchov birligi",
            prompt="Narx qaysi birlik bo‘yicha hisoblanadi?",
            field_type=FieldType.SINGLE_SELECT,
            required=True,
            display_order=35,
            options=[
                FieldOption(id="m2", label="Kvadrat metr (m²)", value="1 m² uchun"),
                FieldOption(id="pm", label="Pogona metr (p/m)", value="1 p/m uchun"),
                FieldOption(id="dona", label="Dona / Oyna bo‘yicha", value="Dona uchun"),
                FieldOption(id="toplam", label="To‘liq to‘plam uchun", value="To‘plam uchun"),
            ]
        ),
        QuestionField(
            id="unit_price",
            label="Birlik narxi",
            prompt="Bir birlik uchun narx (so‘mda, masalan: <code>120000</code>):",
            field_type=FieldType.PRICE,
            required=True,
            display_order=40,
            validation_rules={"min": 1}
        ),
        QuestionField(
            id="installation",
            label="O‘rnatish xizmati",
            prompt="O‘rnatish (montaj) xizmati bormi?",
            field_type=FieldType.BOOLEAN,
            required=True,
            display_order=45,
            options=[
                FieldOption(id="bepul", label="Ha, bepul o‘rnatib beriladi", value="Bepul o‘rnatish"),
                FieldOption(id="pullik", label="Ha, pullik montaj", value="Pullik o‘rnatish"),
                FieldOption(id="yoq", label="Yo‘q, faqat yetkazish", value="O‘rnatishsiz"),
            ]
        ),
        QuestionField(
            id="lead_time",
            label="Tayyorlanish muddati",
            prompt="Buyurtma necha kunda tayyor bo‘ladi (masalan: <i>1-3 kun</i>):",
            field_type=FieldType.TEXT,
            required=False,
            display_order=50,
            placeholder="2-4 kun"
        ),
        QuestionField(
            id="warranty",
            label="Kafolat",
            prompt="Mahsulot yoki mexanizmga kafolat bormi (masalan: <i>1 yil kafolat</i>):",
            field_type=FieldType.TEXT,
            required=False,
            display_order=55,
            placeholder="1 yil mexanizmga kafolat"
        ),
        QuestionField(
            id="location",
            label="Hudud",
            prompt="Qaysi shahar yoki hududda xizmat ko‘rsatasiz:",
            field_type=FieldType.TEXT,
            required=True,
            display_order=60,
            validation_rules={"min_length": 2, "max_length": 150}
        ),
        QuestionField(
            id="phone",
            label="Aloqa telefoni",
            prompt="Aloqa uchun telefon raqamingizni kiriting:",
            field_type=FieldType.PHONE,
            required=True,
            display_order=70,
            validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
        ),
        QuestionField(
            id="description",
            label="Qo‘shimcha tavsif",
            prompt="Qo‘shimcha ma’lumotlar:",
            field_type=FieldType.DESCRIPTION,
            required=False,
            display_order=80,
            validation_rules={"max_length": 2000}
        ),
        QuestionField(
            id="media",
            label="Rasmlar",
            prompt="Bajarilgan ishlar va mato namunalarining rasmlarini yuboring (1-10 ta):",
            field_type=FieldType.MULTI_PHOTO,
            required=False,
            display_order=90,
            validation_rules={"max_items": 10}
        )
    ]

    curtains_subcategories = {
        "vertical_blinds": Subcategory(id="vertical_blinds", label="Vertikal jalyuzi", icon="↕️"),
        "horizontal_blinds": Subcategory(id="horizontal_blinds", label="Gorizontal jalyuzi", icon="↔️"),
        "roller_blinds": Subcategory(id="roller_blinds", label="Rulon jalyuzi", icon="📜"),
        "zebra_blinds": Subcategory(id="zebra_blinds", label="Zebra jalyuzi", icon="🦓"),
        "roman_shades": Subcategory(id="roman_shades", label="Rim pardalari", icon="🏛"),
        "classic_curtains": Subcategory(id="classic_curtains", label="Klassik pardalar", icon="🪟"),
        "tulle": Subcategory(id="tulle", label="Tulle / Tyul", icon="✨"),
        "cornice": Subcategory(id="cornice", label="Karniz va aksessuarlar", icon="🔩"),
        "custom_sewing": Subcategory(id="custom_sewing", label="Buyurtma asosida tikish", icon="🧵"),
        "measurement_install": Subcategory(id="measurement_install", label="O‘lchash va o‘rnatish xizmati", icon="📐"),
        "other_curtains": Subcategory(id="other_curtains", label="Boshqa", icon="📦"),
    }

    categories["curtains_blinds"] = Category(
        id="curtains_blinds",
        label="Jalyuzi va pardalar",
        icon="🪟",
        description="Barcha turdagi jalyuzi, klassik pardalar, tyul va o‘rnatish xizmatlari",
        subcategories=curtains_subcategories,
        common_fields=curtains_common_fields
    )

    # =========================================================================
    # CATEGORY D: BOSHQA MAHSULOTLAR VA TEXNIKALAR (electronics_other)
    # =========================================================================
    electronics_common_fields = []

    electronics_subcategories: Dict[str, Subcategory] = {
        # 1. Telefonlar va planshetlar
        "smartphones": Subcategory(
            id="smartphones",
            label="Telefonlar va planshetlar",
            icon="📱",
            description="Smartfonlar, planshetlar va aksessuarlar",
            specific_fields=[
                QuestionField(
                    id="title",
                    label="Mahsulot nomi",
                    prompt="Mahsulot nomini kiriting (masalan: <i>iPhone 15 Pro Max 256GB</i> yoki <i>Galaxy S24 Ultra</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=10,
                    validation_rules={"min_length": 3, "max_length": 150},
                    placeholder="iPhone 15 Pro Max 256GB Natural Titanium"
                ),
                QuestionField(
                    id="brand",
                    label="Brend",
                    prompt="Telefon yoki planshet brendini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=15,
                    options=[
                        FieldOption(id="apple", label="Apple", value="Apple", icon="🍎"),
                        FieldOption(id="samsung", label="Samsung", value="Samsung", icon="📱"),
                        FieldOption(id="xiaomi", label="Xiaomi", value="Xiaomi", icon="📱"),
                        FieldOption(id="redmi", label="Redmi", value="Redmi", icon="📱"),
                        FieldOption(id="huawei", label="Huawei", value="Huawei", icon="📱"),
                        FieldOption(id="honor", label="Honor", value="Honor", icon="📱"),
                        FieldOption(id="pixel", label="Google Pixel", value="Google Pixel", icon="📱"),
                        FieldOption(id="boshqa", label="Boshqa brend", value="Boshqa brend", icon="🔹"),
                    ]
                ),
                QuestionField(
                    id="model",
                    label="Model",
                    prompt="Aniq modelini kiriting (masalan: <i>15 Pro Max</i>, <i>S24 Ultra</i> yoki <i>Redmi Note 13 Pro</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=20,
                    placeholder="iPhone 15 Pro Max"
                ),
                QuestionField(
                    id="storage",
                    label="Xotira hajmi (ROM)",
                    prompt="Ichki xotira (ROM) hajmini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=25,
                    options=[
                        FieldOption(id="64", label="64 GB", value="64 GB"),
                        FieldOption(id="128", label="128 GB", value="128 GB"),
                        FieldOption(id="256", label="256 GB", value="256 GB"),
                        FieldOption(id="512", label="512 GB", value="512 GB"),
                        FieldOption(id="1024", label="1 TB", value="1 TB"),
                        FieldOption(id="2048", label="2 TB", value="2 TB"),
                        FieldOption(id="boshqa", label="Boshqa hajm", value="Boshqa hajm"),
                    ]
                ),
                QuestionField(
                    id="ram",
                    label="Operativ xotira (RAM)",
                    prompt="Operativ xotira (RAM) hajmini tanlang (agar ma’lum bo‘lsa):",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=30,
                    options=[
                        FieldOption(id="4gb", label="4 GB", value="4 GB"),
                        FieldOption(id="6gb", label="6 GB", value="6 GB"),
                        FieldOption(id="8gb", label="8 GB", value="8 GB"),
                        FieldOption(id="12gb", label="12 GB", value="12 GB"),
                        FieldOption(id="16gb", label="16 GB", value="16 GB"),
                        FieldOption(id="nomalum", label="Tegishli emas / Noma’lum", value="Tegishli emas"),
                    ]
                ),
                QuestionField(
                    id="color",
                    label="Rangi",
                    prompt="Qurilma rangi (masalan: <i>Natural Titanium, Qora, Moviy, Oltinrang</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=35,
                    placeholder="Natural Titanium"
                ),
                QuestionField(
                    id="condition",
                    label="Holati",
                    prompt="Qurilmaning holatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=40,
                    options=[
                        FieldOption(id="yangi", label="Yangi (qadoqda / ochilmagan)", value="Yangi", icon="✨"),
                        FieldOption(id="ideal", label="Ideal (yangidek, tirnalmagan)", value="Ideal", icon="💎"),
                        FieldOption(id="yaxshi", label="Yaxshi (yengil ishlatilgan)", value="Yaxshi", icon="👍"),
                        FieldOption(id="ortacha", label="O‘rtacha (ishlatilgan)", value="O‘rtacha", icon="📱"),
                        FieldOption(id="tiklangan", label="Tiklangan (Refurbished)", value="Tiklangan", icon="🔄"),
                    ]
                ),
                QuestionField(
                    id="battery_health",
                    label="Batareya holati / sig‘imi",
                    prompt="Batareya holati yoki sig‘imi (masalan: <code>88%</code>, <code>100%</code> yoki <code>5000 mAh</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=45,
                    placeholder="92%"
                ),
                QuestionField(
                    id="sim_config",
                    label="SIM karta turi",
                    prompt="SIM-karta konfiguratsiyasini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=50,
                    options=[
                        FieldOption(id="2sim", label="2 ta jismoniy SIM", value="2 ta jismoniy SIM"),
                        FieldOption(id="esim", label="1 SIM + eSIM", value="1 SIM + eSIM"),
                        FieldOption(id="dual_esim", label="Faqat 2 ta eSIM", value="Faqat 2 ta eSIM"),
                        FieldOption(id="1sim", label="1 ta jismoniy SIM", value="1 ta jismoniy SIM"),
                    ]
                ),
                QuestionField(
                    id="warranty",
                    label="Kafolat",
                    prompt="Kafolat mavjudmi (masalan: <i>1 yil rasmiy kafolat</i> yoki <i>1 oy do‘kondan</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=55,
                    placeholder="1 yil rasmiy kafolat"
                ),
                QuestionField(
                    id="repaired_status",
                    label="Ta’mirlash holati",
                    prompt="Qurilma ta’mirlanganmi yoki ochilganmi:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=60,
                    options=[
                        FieldOption(id="ochilmagan", label="Ochilmagan / Zavod holatida", value="Ochilmagan (zavod)"),
                        FieldOption(id="usta_korgan", label="Usta ko‘rgan / Detal almashgan", value="Detal almashgan"),
                        FieldOption(id="ekran_almashgan", label="Faqat ekran almashgan", value="Ekran almashgan"),
                        FieldOption(id="batareya_almashgan", label="Faqat batareya almashgan", value="Batareya almashgan"),
                    ]
                ),
                QuestionField(
                    id="defects",
                    label="Nuqsonlari",
                    prompt="Nuqsonlari bormi (tirnalgan joyi, Face ID / True Tone ishlaydimi, agar nuqson bo‘lmasa 'Yo‘q' deb yozing):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=65,
                    placeholder="Nuqsoni yo‘q, barcha funksiyalari ishlaydi"
                ),
                QuestionField(
                    id="accessories",
                    label="Komplektatsiya",
                    prompt="Qanday jihozlar bilan birga beriladi (karobka-dokument, original kabel, blok, chexol...):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=70,
                    placeholder="Karobka-dokument, kabel, 2 ta chexol"
                ),
                QuestionField(
                    id="price",
                    label="Narxi",
                    prompt="Narxini kiriting (faqat raqam bilan):",
                    field_type=FieldType.PRICE,
                    required=True,
                    display_order=75,
                    validation_rules={"min": 1}
                ),
                QuestionField(
                    id="currency",
                    label="Valyuta",
                    prompt="Valyutani tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=80,
                    options=[
                        FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m"),
                        FieldOption(id="usd", label="AQSH Dollari ($)", value="USD"),
                    ]
                ),
                QuestionField(
                    id="price_negotiable",
                    label="Kelishiladimi",
                    prompt="Narx kelishiladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=85,
                    options=[
                        FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                        FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
                    ]
                ),
                QuestionField(
                    id="delivery",
                    label="Yetkazib berish",
                    prompt="Yetkazib berish imkoniyati:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=90,
                    options=[
                        FieldOption(id="bepul", label="Bepul yetkazib berish", value="Bepul yetkazish"),
                        FieldOption(id="pullik", label="Pullik yetkazish (pochta / taksi)", value="Pullik yetkazish"),
                        FieldOption(id="olib_ketish", label="O‘zi olib ketish (samovivoz)", value="Samovivoz"),
                    ]
                ),
                QuestionField(
                    id="location",
                    label="Joylashuv",
                    prompt="Qurilma joylashgan shahar yoki tuman:",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=95,
                    validation_rules={"min_length": 2, "max_length": 150},
                    placeholder="Toshkent, Chilonzor"
                ),
                QuestionField(
                    id="phone",
                    label="Aloqa telefoni",
                    prompt="Aloqa uchun telefon raqamingizni kiriting:",
                    field_type=FieldType.PHONE,
                    required=True,
                    display_order=100,
                    validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
                ),
                QuestionField(
                    id="media",
                    label="Rasmlar",
                    prompt="Telefon/planshet rasmlarini yuboring (1-10 ta):",
                    field_type=FieldType.MULTI_PHOTO,
                    required=False,
                    display_order=105,
                    validation_rules={"max_items": 10}
                ),
                QuestionField(
                    id="description",
                    label="Batafsil tavsif",
                    prompt="Mahsulot haqida qo‘shimcha batafsil ma’lumot:",
                    field_type=FieldType.DESCRIPTION,
                    required=False,
                    display_order=110,
                    validation_rules={"max_length": 2000}
                ),
            ]
        ),

        # 2. Kompyuterlar va noutbuklar
        "computers": Subcategory(
            id="computers",
            label="Kompyuterlar va noutbuklar",
            icon="💻",
            description="Noutbuklar, kompyuterlar, monoblok va monitorlar",
            specific_fields=[
                QuestionField(
                    id="device_type",
                    label="Qurilma turi",
                    prompt="Qurilma turini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=10,
                    options=[
                        FieldOption(id="noutbuk", label="Noutbuk", value="Noutbuk", icon="💻"),
                        FieldOption(id="pc", label="Statsionar kompyuter (PC)", value="Statsionar kompyuter", icon="🖥"),
                        FieldOption(id="monoblok", label="Monoblok", value="Monoblok", icon="🖥"),
                        FieldOption(id="monitor", label="Monitor", value="Monitor", icon="📺"),
                        FieldOption(id="planshet_pc", label="Planshet-kompyuter", value="Planshet-kompyuter", icon="📟"),
                    ]
                ),
                QuestionField(
                    id="title",
                    label="E’lon sarlavhasi",
                    prompt="E’lon sarlavhasini kiriting (masalan: <i>Lenovo Legion 5 Gaming Noutbuk</i> yoki <i>Apple MacBook Pro 16 M2</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=15,
                    validation_rules={"min_length": 3, "max_length": 150},
                    placeholder="Lenovo Legion 5 Gaming 16GB SSD RTX 4060"
                ),
                QuestionField(
                    id="brand_model",
                    label="Brend va model",
                    prompt="Brend va modelini aniq kiriting (masalan: <i>Asus ROG Strix, HP Victus, Dell XPS, MacBook Pro</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=20,
                    placeholder="Asus ROG Strix G16"
                ),
                QuestionField(
                    id="cpu",
                    label="Protsessor (CPU)",
                    prompt="Protsessor ishlab chiqaruvchisi va modeli (masalan: <i>Intel Core i7-13700H</i> yoki <i>AMD Ryzen 7 7840HS</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=25,
                    condition_key="device_type",
                    condition_values=["Noutbuk", "Statsionar kompyuter", "Monoblok", "Planshet-kompyuter"],
                    placeholder="Intel Core i7-13700H"
                ),
                QuestionField(
                    id="ram",
                    label="Operativ xotira (RAM)",
                    prompt="Operativ xotira (RAM) hajmini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=30,
                    condition_key="device_type",
                    condition_values=["Noutbuk", "Statsionar kompyuter", "Monoblok", "Planshet-kompyuter"],
                    options=[
                        FieldOption(id="8gb", label="8 GB", value="8 GB"),
                        FieldOption(id="16gb", label="16 GB", value="16 GB"),
                        FieldOption(id="32gb", label="32 GB", value="32 GB"),
                        FieldOption(id="64gb", label="64 GB", value="64 GB"),
                        FieldOption(id="4gb", label="4 GB", value="4 GB"),
                        FieldOption(id="boshqa", label="Boshqa hajm", value="Boshqa hajm"),
                    ]
                ),
                QuestionField(
                    id="storage",
                    label="Doimiy xotira (SSD/HDD)",
                    prompt="Doimiy xotira turi va hajmi (masalan: <code>512 GB NVMe SSD</code> yoki <code>1 TB SSD + 2 TB HDD</code>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=35,
                    condition_key="device_type",
                    condition_values=["Noutbuk", "Statsionar kompyuter", "Monoblok", "Planshet-kompyuter"],
                    placeholder="1 TB NVMe M.2 SSD"
                ),
                QuestionField(
                    id="gpu",
                    label="Videokarta (GPU)",
                    prompt="Videokarta modeli (masalan: <i>NVIDIA RTX 4060 8GB</i>, <i>RTX 3050</i> yoki <i>Intel Iris Xe</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=40,
                    placeholder="NVIDIA GeForce RTX 4060 8GB"
                ),
                QuestionField(
                    id="screen_size",
                    label="Ekran diagonali va aniqligi",
                    prompt="Ekran o‘lchami va parametrlari (masalan: <code>15.6 dyuym FHD IPS 144Hz</code> yoki <code>27 dyuym 2K 165Hz</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=45,
                    placeholder="15.6 dyuym FHD IPS 144Hz"
                ),
                QuestionField(
                    id="os",
                    label="Operatsion tizim",
                    prompt="O‘rnatilgan operatsion tizim:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=50,
                    options=[
                        FieldOption(id="win11", label="Windows 11", value="Windows 11"),
                        FieldOption(id="win10", label="Windows 10", value="Windows 10"),
                        FieldOption(id="macos", label="macOS", value="macOS"),
                        FieldOption(id="linux", label="Linux / Ubuntu", value="Linux"),
                        FieldOption(id="dos", label="OS o‘rnatilmagan (DOS)", value="DOS"),
                    ]
                ),
                QuestionField(
                    id="battery_status",
                    label="Batareya holati",
                    prompt="Batareya holati (masalan: <code>85% salomatlik, 3-4 soatga yetadi</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=55,
                    condition_key="device_type",
                    condition_values=["Noutbuk", "Planshet-kompyuter"],
                    placeholder="90% salomatlik, 4 soat ushlaydi"
                ),
                QuestionField(
                    id="condition",
                    label="Texnik holati",
                    prompt="Qurilmaning umumiy holatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=60,
                    options=[
                        FieldOption(id="yangi", label="Yangi (qadoqda / kafolatli)", value="Yangi", icon="✨"),
                        FieldOption(id="ideal", label="Ideal (yangidek, kam ishlatilgan)", value="Ideal", icon="💎"),
                        FieldOption(id="yaxshi", label="Yaxshi (ishchi holatda)", value="Yaxshi", icon="👍"),
                        FieldOption(id="tamir_talab", label="Ta’mir talab / Ehtiyot qismga", value="Ta’mir talab", icon="🛠"),
                    ]
                ),
                QuestionField(
                    id="defects",
                    label="Nuqsonlari",
                    prompt="Nuqsonlari bormi (qizish, korpusdagi tirnalish, klaviatura yoki ekran nuqsoni... yo‘q bo‘lsa 'Yo‘q' deb yozing):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=65,
                    placeholder="Nuqsoni yo‘q, termopasta yangilangan"
                ),
                QuestionField(
                    id="accessories",
                    label="Komplektatsiyasi",
                    prompt="Komplektda nimalar bor (original zaryadnik, klaviatura, sichqoncha, quti, sumka...):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=70,
                    placeholder="Original zaryadnik, quti, sichqoncha"
                ),
                QuestionField(
                    id="warranty",
                    label="Kafolat",
                    prompt="Kafolat mavjudmi (masalan: <i>1 yil kafolat</i> yoki <i>1 oy tekshirishga</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=75,
                    placeholder="1 yil rasmiy kafolat"
                ),
                QuestionField(
                    id="price",
                    label="Narxi",
                    prompt="Narxini kiriting (faqat raqam bilan):",
                    field_type=FieldType.PRICE,
                    required=True,
                    display_order=80,
                    validation_rules={"min": 1}
                ),
                QuestionField(
                    id="currency",
                    label="Valyuta",
                    prompt="Valyutani tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=85,
                    options=[
                        FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m"),
                        FieldOption(id="usd", label="AQSH Dollari ($)", value="USD"),
                    ]
                ),
                QuestionField(
                    id="price_negotiable",
                    label="Kelishiladimi",
                    prompt="Narx kelishiladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=90,
                    options=[
                        FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                        FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
                    ]
                ),
                QuestionField(
                    id="delivery",
                    label="Yetkazib berish",
                    prompt="Yetkazib berish shartlari:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=95,
                    options=[
                        FieldOption(id="bepul", label="Bepul yetkazib berish", value="Bepul yetkazish"),
                        FieldOption(id="pullik", label="Pullik yetkazish (pochta / taksi)", value="Pullik yetkazish"),
                        FieldOption(id="olib_ketish", label="O‘zi olib ketish (samovivoz)", value="Samovivoz"),
                    ]
                ),
                QuestionField(
                    id="location",
                    label="Joylashuv",
                    prompt="Qurilma joylashgan shahar yoki tuman:",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=100,
                    validation_rules={"min_length": 2, "max_length": 150},
                    placeholder="Toshkent, Yunusobod"
                ),
                QuestionField(
                    id="phone",
                    label="Aloqa raqami",
                    prompt="Aloqa uchun telefon raqamingiz:",
                    field_type=FieldType.PHONE,
                    required=True,
                    display_order=105,
                    validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
                ),
                QuestionField(
                    id="media",
                    label="Rasmlar va video",
                    prompt="Kompyuter/noutbuk rasmlari yoki videosini yuboring (1-10 ta):",
                    field_type=FieldType.MULTI_PHOTO,
                    required=False,
                    display_order=110,
                    validation_rules={"max_items": 10}
                ),
                QuestionField(
                    id="description",
                    label="Qo‘shimcha tavsif",
                    prompt="Qo‘shimcha batafsil ma’lumotlar:",
                    field_type=FieldType.DESCRIPTION,
                    required=False,
                    display_order=115,
                    validation_rules={"max_length": 2000}
                ),
            ]
        ),

        # 3. Televizor va audio qurilmalar
        "tv_audio": Subcategory(
            id="tv_audio",
            label="Televizor va audio qurilmalar",
            icon="📺",
            description="Televizorlar, saundbarlar, akustika va quloqchinlar",
            specific_fields=[
                QuestionField(
                    id="device_type",
                    label="Mahsulot turi",
                    prompt="Qurilma turini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=10,
                    options=[
                        FieldOption(id="tv", label="Televizor", value="Televizor", icon="📺"),
                        FieldOption(id="speaker", label="Kolonka / Portativ akustika", value="Kolonka", icon="🔊"),
                        FieldOption(id="soundbar", label="Audio tizim / Saundbar", value="Audio tizim / Saundbar", icon="📻"),
                        FieldOption(id="headphones", label="Quloqchin (Naushnik)", value="Quloqchin", icon="🎧"),
                        FieldOption(id="mic", label="Mikrofon", value="Mikrofon", icon="🎙"),
                        FieldOption(id="amp", label="Kuchaytirgich (Usilitel)", value="Kuchaytirgich", icon="🎛"),
                        FieldOption(id="boshqa", label="Boshqa audio qurilma", value="Boshqa audio", icon="🔹"),
                    ]
                ),
                QuestionField(
                    id="title",
                    label="E’lon sarlavhasi",
                    prompt="E’lon sarlavhasi (masalan: <i>Samsung 55 Crystal UHD 4K Smart TV</i> yoki <i>JBL PartyBox 310</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=15,
                    validation_rules={"min_length": 3, "max_length": 150},
                    placeholder="Samsung 55 Crystal 4K Smart TV"
                ),
                QuestionField(
                    id="brand",
                    label="Brend",
                    prompt="Ishlab chiqaruvchi brendni tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=20,
                    options=[
                        FieldOption(id="samsung", label="Samsung", value="Samsung"),
                        FieldOption(id="lg", label="LG", value="LG"),
                        FieldOption(id="sony", label="Sony", value="Sony"),
                        FieldOption(id="artel", label="Artel", value="Artel"),
                        FieldOption(id="shivaki", label="Shivaki", value="Shivaki"),
                        FieldOption(id="tcl", label="TCL", value="TCL"),
                        FieldOption(id="jbl", label="JBL", value="JBL"),
                        FieldOption(id="marshall", label="Marshall", value="Marshall"),
                        FieldOption(id="boshqa", label="Boshqa brend", value="Boshqa"),
                    ]
                ),
                QuestionField(
                    id="model",
                    label="Model",
                    prompt="Aniq modelini kiriting (masalan: <i>55CU7100</i>, <i>OLED55C3</i> yoki <i>PartyBox 310</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=25,
                    placeholder="55CU7100"
                ),
                QuestionField(
                    id="screen_size",
                    label="Ekran diagonali",
                    prompt="Ekran diagonali (masalan: <code>43 dyuym (109 sm)</code>, <code>55 dyuym (140 sm)</code> yoki <code>65 dyuym</code>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=30,
                    condition_key="device_type",
                    condition_values=["Televizor"],
                    placeholder="55 dyuym (140 sm)"
                ),
                QuestionField(
                    id="screen_tech",
                    label="Ekran texnologiyasi",
                    prompt="Displey texnologiyasini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=35,
                    condition_key="device_type",
                    condition_values=["Televizor"],
                    options=[
                        FieldOption(id="oled", label="OLED", value="OLED"),
                        FieldOption(id="qled", label="QLED", value="QLED"),
                        FieldOption(id="miniled", label="Mini-LED", value="Mini-LED"),
                        FieldOption(id="led", label="LED / Crystal UHD", value="LED"),
                        FieldOption(id="lcd", label="LCD", value="LCD"),
                    ]
                ),
                QuestionField(
                    id="resolution",
                    label="Ekran aniqligi",
                    prompt="Ekran aniqligini (ruxsatini) tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=40,
                    condition_key="device_type",
                    condition_values=["Televizor"],
                    options=[
                        FieldOption(id="4k", label="4K UHD (3840x2160)", value="4K UHD"),
                        FieldOption(id="fhd", label="Full HD (1920x1080)", value="Full HD"),
                        FieldOption(id="8k", label="8K Ultra HD", value="8K UHD"),
                        FieldOption(id="hd", label="HD (1366x768)", value="HD"),
                    ]
                ),
                QuestionField(
                    id="smart_tv",
                    label="Smart TV imkoniyati",
                    prompt="Smart TV mavjudmi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=45,
                    condition_key="device_type",
                    condition_values=["Televizor"],
                    options=[
                        FieldOption(id="ha", label="Smart TV bor (Android / Google TV / Tizen / webOS)", value="Smart TV bor"),
                        FieldOption(id="yoq", label="Smart TV yo‘q (oddiy)", value="Smart TV yo‘q"),
                    ]
                ),
                QuestionField(
                    id="audio_power",
                    label="Audio quvvati",
                    prompt="Audio quvvati yoki kanallar soni (masalan: <code>40W</code>, <code>240W</code> yoki <code>5.1 tizim</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=50,
                    placeholder="240W RMS"
                ),
                QuestionField(
                    id="wireless",
                    label="Simsiz ulanish",
                    prompt="Simsiz ulanish imkoniyati:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=55,
                    options=[
                        FieldOption(id="both", label="Bluetooth va Wi-Fi mavjud", value="Bluetooth + Wi-Fi"),
                        FieldOption(id="bt", label="Faqat Bluetooth mavjud", value="Bluetooth"),
                        FieldOption(id="wire", label="Faqat simli ulanish", value="Faqat simli"),
                    ]
                ),
                QuestionField(
                    id="interfaces",
                    label="Ulanish interfeyslari",
                    prompt="Ulanish portlari (masalan: <i>HDMI x3, USB x2, Optik chiqish, AUX</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=60,
                    placeholder="HDMI, USB, Bluetooth, Optik"
                ),
                QuestionField(
                    id="condition",
                    label="Holati",
                    prompt="Mahsulot holatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=65,
                    options=[
                        FieldOption(id="yangi", label="Yangi (qadoqda / kafolatli)", value="Yangi", icon="✨"),
                        FieldOption(id="ideal", label="Ideal (kam ishlatilgan, nuqsonsiz)", value="Ideal", icon="💎"),
                        FieldOption(id="yaxshi", label="Yaxshi holatda", value="Yaxshi", icon="👍"),
                        FieldOption(id="tamir", label="Ta’mir talab", value="Ta’mir talab", icon="🛠"),
                    ]
                ),
                QuestionField(
                    id="defects",
                    label="Nuqsonlari",
                    prompt="Nuqsonlari bormi (ekranda chiziq, pult yo‘qligi, ovozdagi nuqson... yo‘q bo‘lsa 'Yo‘q' deb yozing):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=70,
                    placeholder="Nuqsoni yo‘q, barchasi ishchi"
                ),
                QuestionField(
                    id="accessories",
                    label="Komplektatsiya",
                    prompt="Komplektda nimalar bor (pult, kronshteyn (devor ushlagich), kabellar, quti...):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=75,
                    placeholder="Pult, kronshteyn, quvvat kabeli, quti"
                ),
                QuestionField(
                    id="warranty",
                    label="Kafolat",
                    prompt="Kafolat muddati (masalan: <i>1 yil rasmiy kafolat</i> yoki <i>3 oy do‘kondan</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=80,
                    placeholder="1 yil rasmiy kafolat"
                ),
                QuestionField(
                    id="price",
                    label="Narxi",
                    prompt="Narxini kiriting (faqat raqam bilan):",
                    field_type=FieldType.PRICE,
                    required=True,
                    display_order=85,
                    validation_rules={"min": 1}
                ),
                QuestionField(
                    id="currency",
                    label="Valyuta",
                    prompt="Valyutani tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=90,
                    options=[
                        FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m"),
                        FieldOption(id="usd", label="AQSH Dollari ($)", value="USD"),
                    ]
                ),
                QuestionField(
                    id="price_negotiable",
                    label="Kelishiladimi",
                    prompt="Narx kelishiladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=95,
                    options=[
                        FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                        FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
                    ]
                ),
                QuestionField(
                    id="delivery",
                    label="Yetkazib berish",
                    prompt="Yetkazib berish shartlari:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=100,
                    options=[
                        FieldOption(id="bepul", label="Bepul yetkazib berish", value="Bepul yetkazish"),
                        FieldOption(id="pullik", label="Pullik yetkazish", value="Pullik yetkazish"),
                        FieldOption(id="olib_ketish", label="O‘zi olib ketish (samovivoz)", value="Samovivoz"),
                    ]
                ),
                QuestionField(
                    id="location",
                    label="Manzil",
                    prompt="Joylashgan shahar yoki tuman:",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=105,
                    validation_rules={"min_length": 2, "max_length": 150},
                    placeholder="Toshkent, Mirzo Ulug‘bek"
                ),
                QuestionField(
                    id="phone",
                    label="Aloqa telefoni",
                    prompt="Aloqa uchun telefon raqamingiz:",
                    field_type=FieldType.PHONE,
                    required=True,
                    display_order=110,
                    validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
                ),
                QuestionField(
                    id="media",
                    label="Rasmlar/video",
                    prompt="Mahsulot rasmlari yoki videosini yuboring (1-10 ta):",
                    field_type=FieldType.MULTI_PHOTO,
                    required=False,
                    display_order=115,
                    validation_rules={"max_items": 10}
                ),
                QuestionField(
                    id="description",
                    label="Batafsil tavsif",
                    prompt="Mahsulot haqida qo‘shimcha batafsil ma’lumot:",
                    field_type=FieldType.DESCRIPTION,
                    required=False,
                    display_order=120,
                    validation_rules={"max_length": 2000}
                ),
            ]
        ),

        # 4. Maishiy texnika
        "home_appliances": Subcategory(
            id="home_appliances",
            label="Maishiy texnika",
            icon="🧊",
            description="Muzlatgich, kir yuvish mashinasi, plita va boshqa texnikalar",
            specific_fields=[
                QuestionField(
                    id="appliance_type",
                    label="Mahsulot turi",
                    prompt="Maishiy texnika turini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=10,
                    options=[
                        FieldOption(id="fridge", label="Muzlatgich (Xolodilnik)", value="Muzlatgich", icon="🧊"),
                        FieldOption(id="washer", label="Kir yuvish mashinasi", value="Kir yuvish mashinasi", icon="🧺"),
                        FieldOption(id="dishwasher", label="Idish yuvish mashinasi", value="Idish yuvish mashinasi", icon="🍽"),
                        FieldOption(id="stove", label="Gaz yoki elektr plita", value="Gaz/Elektr plita", icon="🍳"),
                        FieldOption(id="microwave", label="Mikroto‘lqinli pech", value="Mikroto‘lqinli pech", icon="📻"),
                        FieldOption(id="vacuum", label="Changyutkich (Pilesos)", value="Changyutkich", icon="🧹"),
                        FieldOption(id="heater", label="Suv isitgich (Boyler/Ariston)", value="Suv isitgich", icon="🚰"),
                        FieldOption(id="boshqa", label="Boshqa maishiy texnika", value="Boshqa maishiy texnika", icon="🔹"),
                    ]
                ),
                QuestionField(
                    id="title",
                    label="E’lon sarlavhasi",
                    prompt="E’lon sarlavhasini kiriting (masalan: <i>LG Inverter 8kg Kir yuvish mashinasi</i> yoki <i>Artel NoFrost 320L Muzlatgich</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=15,
                    validation_rules={"min_length": 3, "max_length": 150},
                    placeholder="LG Inverter 8kg Kir yuvish mashinasi"
                ),
                QuestionField(
                    id="brand_model",
                    label="Brend va model",
                    prompt="Brend va modelini kiriting (masalan: <i>Artel Grand Inverter, LG EcoBubble, Samsung, Bosch</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=20,
                    placeholder="LG F2J3HS2W"
                ),
                QuestionField(
                    id="capacity",
                    label="Hajmi / Sig‘imi",
                    prompt="Foydali hajm yoki sig‘imi (masalan: <i>Muzlatgich uchun 340 litr</i>, <i>Kir yuvish uchun 8 kg</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=25,
                    placeholder="8 kg yuklama"
                ),
                QuestionField(
                    id="spin_speed",
                    label="Aylanish tezligi",
                    prompt="Kir yuvish mashinasi siqish tezligi (masalan: <code>1200 ayl/daq</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=30,
                    condition_key="appliance_type",
                    condition_values=["Kir yuvish mashinasi"],
                    placeholder="1200 ayl/daq"
                ),
                QuestionField(
                    id="dimensions",
                    label="O‘lchamlari",
                    prompt="O‘lchamlari (Kengligi x Balandligi x Chuqurligi, masalan: <code>60x85x60 sm</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=35,
                    placeholder="60x85x55 sm"
                ),
                QuestionField(
                    id="color",
                    label="Rangi",
                    prompt="Rangi (masalan: <i>Oq, Kumushrang, Inox, Qora</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=40,
                    placeholder="Kumushrang"
                ),
                QuestionField(
                    id="energy_class",
                    label="Energiya samaradorligi",
                    prompt="Energiya samaradorligi sinfi:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=45,
                    options=[
                        FieldOption(id="a_plus3", label="A+++", value="A+++"),
                        FieldOption(id="a_plus2", label="A++", value="A++"),
                        FieldOption(id="a_plus", label="A+", value="A+"),
                        FieldOption(id="a", label="A", value="A"),
                        FieldOption(id="b", label="B", value="B"),
                        FieldOption(id="nomalum", label="Noma’lum / Tegishli emas", value="Noma’lum"),
                    ]
                ),
                QuestionField(
                    id="condition",
                    label="Holati",
                    prompt="Mahsulot holatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=50,
                    options=[
                        FieldOption(id="yangi", label="Yangi (ishlatilmagan)", value="Yangi", icon="✨"),
                        FieldOption(id="ideal", label="Ideal (kam ishlatilgan, soz)", value="Ideal", icon="💎"),
                        FieldOption(id="yaxshi", label="Yaxshi (ishchi holatda)", value="Yaxshi", icon="👍"),
                        FieldOption(id="tamir", label="Ta’mir talab", value="Ta’mir talab", icon="🛠"),
                    ]
                ),
                QuestionField(
                    id="working_status",
                    label="Ishlash holati",
                    prompt="Ishlash holati (masalan: <i>Barcha funksiyalari a’lo darajada ishlaydi, motori jim</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=55,
                    placeholder="100% soz, usta ko‘rmagan"
                ),
                QuestionField(
                    id="manufacture_year",
                    label="Ishlab chiqarilgan yili",
                    prompt="Ishlab chiqarilgan yili (masalan: <code>2023</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=60,
                    placeholder="2023-yil"
                ),
                QuestionField(
                    id="defects",
                    label="Nuqsonlari",
                    prompt="Nuqsonlari bormi (tirnalgan, zanglagan joyi bormi, yo‘q bo‘lsa 'Yo‘q' deb yozing):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=65,
                    placeholder="Yo‘q, chizilgan joyi yo‘q"
                ),
                QuestionField(
                    id="installation",
                    label="O‘rnatish xizmati",
                    prompt="O‘rnatib berish xizmati mavjudmi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=70,
                    options=[
                        FieldOption(id="bor", label="O‘rnatib berish xizmati bor", value="O‘rnatish mavjud"),
                        FieldOption(id="yoq", label="O‘rnatishsiz", value="O‘rnatishsiz"),
                    ]
                ),
                QuestionField(
                    id="warranty",
                    label="Kafolat",
                    prompt="Kafolat mavjudligi (masalan: <i>10 yil motorga, 1 yil umumiy</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=75,
                    placeholder="1 yil rasmiy kafolat"
                ),
                QuestionField(
                    id="price",
                    label="Narxi",
                    prompt="Narxini kiriting (faqat raqam bilan):",
                    field_type=FieldType.PRICE,
                    required=True,
                    display_order=80,
                    validation_rules={"min": 1}
                ),
                QuestionField(
                    id="currency",
                    label="Valyuta",
                    prompt="Valyutani tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=85,
                    options=[
                        FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m"),
                        FieldOption(id="usd", label="AQSH Dollari ($)", value="USD"),
                    ]
                ),
                QuestionField(
                    id="price_negotiable",
                    label="Kelishiladimi",
                    prompt="Narx kelishiladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=90,
                    options=[
                        FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                        FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
                    ]
                ),
                QuestionField(
                    id="delivery",
                    label="Yetkazib berish",
                    prompt="Yetkazib berish shartlari:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=95,
                    options=[
                        FieldOption(id="bepul", label="Bepul yetkazib berish", value="Bepul yetkazish"),
                        FieldOption(id="pullik", label="Pullik yetkazish (taksi/yuk mashina)", value="Pullik yetkazish"),
                        FieldOption(id="olib_ketish", label="O‘zi olib ketish (samovivoz)", value="Samovivoz"),
                    ]
                ),
                QuestionField(
                    id="location",
                    label="Manzil",
                    prompt="Mahsulot joylashgan manzil (shahar, tuman):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=100,
                    validation_rules={"min_length": 2, "max_length": 150},
                    placeholder="Toshkent, Sergeli"
                ),
                QuestionField(
                    id="phone",
                    label="Aloqa raqami",
                    prompt="Aloqa uchun telefon raqamingiz:",
                    field_type=FieldType.PHONE,
                    required=True,
                    display_order=105,
                    validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
                ),
                QuestionField(
                    id="media",
                    label="Rasmlar",
                    prompt="Texnika rasmlarini yuboring (1-10 ta):",
                    field_type=FieldType.MULTI_PHOTO,
                    required=False,
                    display_order=110,
                    validation_rules={"max_items": 10}
                ),
                QuestionField(
                    id="description",
                    label="Batafsil tavsif",
                    prompt="Mahsulot haqida qo‘shimcha batafsil ma’lumot:",
                    field_type=FieldType.DESCRIPTION,
                    required=False,
                    display_order=115,
                    validation_rules={"max_length": 2000}
                ),
            ]
        ),

        # 5. Konditsioner va isitish uskunalari
        "hvac": Subcategory(
            id="hvac",
            label="Konditsioner va isitish uskunalari",
            icon="❄️",
            description="Konditsionerlar, kotyollar, radiatorlar va isitkichlar",
            specific_fields=[
                QuestionField(
                    id="hvac_type",
                    label="Uskuna turi",
                    prompt="Uskuna turini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=10,
                    options=[
                        FieldOption(id="ac", label="Konditsioner (Split tizim)", value="Konditsioner", icon="❄️"),
                        FieldOption(id="heater", label="Isitkich (Obogrevatel)", value="Isitkich", icon="🔥"),
                        FieldOption(id="boiler", label="Isitish qozoni (Kotyol)", value="Isitish qozoni", icon="♨️"),
                        FieldOption(id="radiator", label="Radiator / Batareya", value="Radiator", icon="🧱"),
                        FieldOption(id="vent", label="Ventilyatsiya qurilmasi", value="Ventilyatsiya", icon="💨"),
                        FieldOption(id="boshqa", label="Boshqa isitish/sovutish", value="Boshqa HVAC", icon="🔹"),
                    ]
                ),
                QuestionField(
                    id="title",
                    label="E’lon sarlavhasi",
                    prompt="E’lon sarlavhasi (masalan: <i>Shivaki 12 Inverter Konditsioner</i> yoki <i>Baxi 24kW Gaz Kotyoli</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=15,
                    validation_rules={"min_length": 3, "max_length": 150},
                    placeholder="Shivaki 12 Inverter Split Konditsioner"
                ),
                QuestionField(
                    id="brand_model",
                    label="Brend va model",
                    prompt="Brend va modelini kiriting (masalan: <i>Shivaki, Midea, Gree, Artel, Ferroli, Baxi</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=20,
                    placeholder="Midea Mission II 12"
                ),
                QuestionField(
                    id="capacity_power",
                    label="Quvvati",
                    prompt="Sovutish yoki isitish quvvati (masalan: <code>12 000 BTU</code>, <code>18 000 BTU</code>, <code>24 kW</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=25,
                    placeholder="12 000 BTU"
                ),
                QuestionField(
                    id="recommended_area",
                    label="Tavsiya etilgan maydon",
                    prompt="Xona maydoni bo‘yicha tavsiya (masalan: <code>35 m² gacha</code>, <code>60 m²</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=30,
                    placeholder="35 m² gacha"
                ),
                QuestionField(
                    id="inverter",
                    label="Inverter texnologiyasi",
                    prompt="Inverter mavjudmi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=35,
                    options=[
                        FieldOption(id="inverter", label="Inverterli (tejamkor va sokin)", value="Inverterli"),
                        FieldOption(id="on_off", label="Oddiy On/Off", value="Oddiy On/Off"),
                        FieldOption(id="nomalum", label="Noma’lum / Tegishli emas", value="Tegishli emas"),
                    ]
                ),
                QuestionField(
                    id="energy_class",
                    label="Energiya samaradorligi",
                    prompt="Energiya samaradorligi sinfi:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=40,
                    options=[
                        FieldOption(id="a_plus3", label="A+++", value="A+++"),
                        FieldOption(id="a_plus2", label="A++", value="A++"),
                        FieldOption(id="a_plus", label="A+", value="A+"),
                        FieldOption(id="a", label="A", value="A"),
                        FieldOption(id="standart", label="Standart", value="Standart"),
                    ]
                ),
                QuestionField(
                    id="freon_type",
                    label="Freon turi",
                    prompt="Freon turi (agar ma’lum bo‘lsa):",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=45,
                    options=[
                        FieldOption(id="r410a", label="R410A", value="R410A"),
                        FieldOption(id="r32", label="R32 (Yangi ekologik)", value="R32"),
                        FieldOption(id="r22", label="R22", value="R22"),
                        FieldOption(id="nomalum", label="Noma’lum / Tegishli emas", value="Noma’lum"),
                    ]
                ),
                QuestionField(
                    id="condition",
                    label="Holati",
                    prompt="Uskuna holatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=50,
                    options=[
                        FieldOption(id="yangi", label="Yangi (qadoqda)", value="Yangi", icon="✨"),
                        FieldOption(id="ideal", label="Ideal (kam ishlatilgan)", value="Ideal", icon="💎"),
                        FieldOption(id="yaxshi", label="Yaxshi (ishchi holatda)", value="Yaxshi", icon="👍"),
                        FieldOption(id="tamir", label="Ta’mir talab", value="Ta’mir talab", icon="🛠"),
                    ]
                ),
                QuestionField(
                    id="technical_condition",
                    label="Texnik holati",
                    prompt="Texnik holati (masalan: <i>Freoni to‘la, trubalari bor, ximchistka qilingan</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=55,
                    placeholder="Freoni bor, trubka va pult komplektda"
                ),
                QuestionField(
                    id="installation",
                    label="O‘rnatish xizmati",
                    prompt="O‘rnatib berish xizmati bormi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=60,
                    options=[
                        FieldOption(id="bor", label="O‘rnatib berish xizmati mavjud", value="O‘rnatish mavjud"),
                        FieldOption(id="yoq", label="O‘rnatishsiz", value="O‘rnatishsiz"),
                    ]
                ),
                QuestionField(
                    id="dismantling",
                    label="Demontaj xizmati",
                    prompt="Demontaj (yechib berish) sharti:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=65,
                    options=[
                        FieldOption(id="bor", label="Demontaj qilib beriladi", value="Demontaj qilib beriladi"),
                        FieldOption(id="xaridor", label="Xaridor o‘zi yechadi", value="Xaridor yechadi"),
                        FieldOption(id="yechilgan", label="Kerak emas (yechib qo‘yilgan)", value="Yechilgan"),
                    ]
                ),
                QuestionField(
                    id="warranty",
                    label="Kafolat",
                    prompt="Kafolat muddati (masalan: <i>3 yil kafolat</i> yoki <i>1 oy tekshirishga</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=70,
                    placeholder="3 yil kompressorga kafolat"
                ),
                QuestionField(
                    id="price",
                    label="Narx",
                    prompt="Narxini kiriting (faqat raqam bilan):",
                    field_type=FieldType.PRICE,
                    required=True,
                    display_order=75,
                    validation_rules={"min": 1}
                ),
                QuestionField(
                    id="currency",
                    label="Valyuta",
                    prompt="Valyutani tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=80,
                    options=[
                        FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m"),
                        FieldOption(id="usd", label="AQSH Dollari ($)", value="USD"),
                    ]
                ),
                QuestionField(
                    id="price_negotiable",
                    label="Kelishiladimi",
                    prompt="Narx kelishiladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=85,
                    options=[
                        FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                        FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
                    ]
                ),
                QuestionField(
                    id="delivery",
                    label="Yetkazib berish",
                    prompt="Yetkazib berish shartlari:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=90,
                    options=[
                        FieldOption(id="bepul", label="Bepul yetkazib berish", value="Bepul yetkazish"),
                        FieldOption(id="pullik", label="Pullik yetkazish", value="Pullik yetkazish"),
                        FieldOption(id="olib_ketish", label="O‘zi olib ketish (samovivoz)", value="Samovivoz"),
                    ]
                ),
                QuestionField(
                    id="location",
                    label="Joylashuv",
                    prompt="Joylashgan shahar yoki tuman:",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=95,
                    validation_rules={"min_length": 2, "max_length": 150},
                    placeholder="Toshkent, Shayxontohur"
                ),
                QuestionField(
                    id="phone",
                    label="Aloqa raqami",
                    prompt="Aloqa uchun telefon raqamingiz:",
                    field_type=FieldType.PHONE,
                    required=True,
                    display_order=100,
                    validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
                ),
                QuestionField(
                    id="media",
                    label="Rasmlar/video",
                    prompt="Uskuna rasmlari yoki videosini yuboring (1-10 ta):",
                    field_type=FieldType.MULTI_PHOTO,
                    required=False,
                    display_order=105,
                    validation_rules={"max_items": 10}
                ),
                QuestionField(
                    id="description",
                    label="Batafsil tavsif",
                    prompt="Qo‘shimcha batafsil ma’lumot:",
                    field_type=FieldType.DESCRIPTION,
                    required=False,
                    display_order=110,
                    validation_rules={"max_length": 2000}
                ),
            ]
        ),

        # 6. Qurilish materiallari
        "construction": Subcategory(
            id="construction",
            label="Qurilish materiallari",
            icon="🧱",
            description="Sement, g‘isht, armatura, quruq qorishmalar va profillar",
            specific_fields=[
                QuestionField(
                    id="material_type",
                    label="Material toifasi",
                    prompt="Qurilish materiali toifasini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=10,
                    options=[
                        FieldOption(id="cement", label="Sement va quruq qorishmalar", value="Sement va qorishmalar", icon="⚪️"),
                        FieldOption(id="brick", label="G‘isht va bloklar", value="G‘isht va bloklar", icon="🧱"),
                        FieldOption(id="metal", label="Metall prokat va armatura", value="Armatura va metall", icon="⛓"),
                        FieldOption(id="roof", label="Tom yopish materiallari (Profnastil...)", value="Tom yopish materiallari", icon="🏠"),
                        FieldOption(id="drywall", label="Gipsokarton va profillar", value="Gipsokarton va profillar", icon="⬜️"),
                        FieldOption(id="sand", label="Qum / shag‘al / sheben", value="Qum va shag‘al", icon="🪨"),
                        FieldOption(id="paint", label="Bo‘yoq va laklar", value="Bo‘yoq va laklar", icon="🎨"),
                        FieldOption(id="pipes", label="Santexnika quvurlari va fitinglar", value="Santexnika quvurlari", icon="🚰"),
                        FieldOption(id="tile", label="Plitka va kafel", value="Plitka va kafel", icon="🔲"),
                        FieldOption(id="wood", label="Yog‘och va taxta", value="Yog‘och va taxta", icon="🪵"),
                        FieldOption(id="boshqa", label="Boshqa qurilish mollari", value="Boshqa qurilish mollari", icon="🔹"),
                    ]
                ),
                QuestionField(
                    id="title",
                    label="Mahsulot nomi",
                    prompt="Mahsulot nomini kiriting (masalan: <i>M500 Sement Qizilqum</i> yoki <i>Armatura 12mm Bekobod</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=15,
                    validation_rules={"min_length": 3, "max_length": 150},
                    placeholder="M500 Sement Qizilqum qopda 50kg"
                ),
                QuestionField(
                    id="brand_manufacturer",
                    label="Brend / Ishlab chiqaruvchi",
                    prompt="Ishlab chiqaruvchi zavod yoki brend (masalan: <i>Qizilqumsement, Bekobod zavodi, Knauf, Akfa</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=20,
                    placeholder="Qizilqumsement AJ"
                ),
                QuestionField(
                    id="grade_model",
                    label="Markasi va modeli",
                    prompt="Material markasi va klassi (masalan: <code>M-500</code>, <code>A500C</code>, <code>Marka 100</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=25,
                    placeholder="M-500 D0"
                ),
                QuestionField(
                    id="dimensions",
                    label="O‘lchamlari va qalinligi",
                    prompt="O‘lchamlari (masalan: <code>12 mm x 12 m</code>, <code>60x120 sm</code>, <code>qalinligi 9.5 mm</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=30,
                    placeholder="12 mm diametr, 12 metr uzunlik"
                ),
                QuestionField(
                    id="color",
                    label="Rangi",
                    prompt="Material rangi (agar mavjud bo‘lsa, masalan: <i>Kulrang, Shokolad, Qizil</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=35,
                    placeholder="Kulrang"
                ),
                QuestionField(
                    id="stock_quantity",
                    label="Mavjud zaxira",
                    prompt="Ombordagi mavjud miqdor (masalan: <code>50 tonna</code>, <code>5 000 dona</code>, <code>1 200 m²</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=40,
                    placeholder="Omborda 100 tonna mavjud"
                ),
                QuestionField(
                    id="unit_of_measure",
                    label="O‘lchov birligi",
                    prompt="Narxlash va hisoblash birligini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=45,
                    options=[
                        FieldOption(id="dona", label="dona", value="dona"),
                        FieldOption(id="m2", label="m² (kvadrat metr)", value="m²"),
                        FieldOption(id="metr", label="metr (pogono metr)", value="metr"),
                        FieldOption(id="kg", label="kg", value="kg"),
                        FieldOption(id="tonna", label="tonna", value="tonna"),
                        FieldOption(id="qop", label="qop (meshok)", value="qop"),
                        FieldOption(id="m3", label="m³ (kub metr)", value="m³"),
                        FieldOption(id="litr", label="litr", value="litr"),
                        FieldOption(id="komplekt", label="komplekt", value="komplekt"),
                    ]
                ),
                QuestionField(
                    id="price",
                    label="Birlik narxi",
                    prompt="Tanlangan o‘lchov birligi uchun narxni kiriting (masalan: 1 dona yoki 1 m² uchun narx):",
                    field_type=FieldType.PRICE,
                    required=True,
                    display_order=50,
                    validation_rules={"min": 1}
                ),
                QuestionField(
                    id="currency",
                    label="Valyuta",
                    prompt="Valyutani tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=55,
                    options=[
                        FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m"),
                        FieldOption(id="usd", label="AQSH Dollari ($)", value="USD"),
                    ]
                ),
                QuestionField(
                    id="price_negotiable",
                    label="Kelishiladimi",
                    prompt="Narx kelishiladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=60,
                    options=[
                        FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                        FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
                    ]
                ),
                QuestionField(
                    id="min_order",
                    label="Minimal buyurtma",
                    prompt="Minimal buyurtma hajmi (masalan: <i>Minimal 10 qop yoki 1 tonna</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=65,
                    placeholder="Minimal 20 qop"
                ),
                QuestionField(
                    id="wholesale",
                    label="Ulgurji narx",
                    prompt="Katta hajm uchun ulgurji narx / chegirma bormi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=70,
                    options=[
                        FieldOption(id="bor", label="Katta hajmga ulgurji chegirma bor", value="Ulgurji chegirma bor"),
                        FieldOption(id="yoq", label="Faqat ko‘rsatilgan narx", value="Faqat ko‘rsatilgan narx"),
                    ]
                ),
                QuestionField(
                    id="delivery_area",
                    label="Yetkazib berish hududi",
                    prompt="Yetkazib berish hududi (masalan: <i>Toshkent shahri va viloyati, Butun O‘zbekiston</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=75,
                    placeholder="Toshkent shahri va viloyatiga yetkazamiz"
                ),
                QuestionField(
                    id="loading_service",
                    label="Yuklash / tushirish",
                    prompt="Yuklash va tushirish xizmati sharti:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=80,
                    options=[
                        FieldOption(id="manipulator", label="Yuklab va tushirib beriladi (Manipulyator)", value="Manipulyator bilan"),
                        FieldOption(id="yuklash", label="Faqat ombordan yuklab beriladi", value="Faqat yuklab beriladi"),
                        FieldOption(id="samovivoz", label="Olib ketuvchi o‘zi yuklaydi", value="Xaridor yuklaydi"),
                    ]
                ),
                QuestionField(
                    id="certificate",
                    label="Sifat sertifikati",
                    prompt="Sifat sertifikati mavjudmi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=85,
                    options=[
                        FieldOption(id="bor", label="Sifat sertifikati va GOST mavjud", value="Sertifikat bor"),
                        FieldOption(id="yoq", label="Sertifikatsiz", value="Sertifikatsiz"),
                    ]
                ),
                QuestionField(
                    id="condition",
                    label="Mahsulot holati",
                    prompt="Material holatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=90,
                    options=[
                        FieldOption(id="zavod", label="Yangi / Zavoddan to‘g‘ridan-to‘g‘ri", value="Yangi (zavoddan)"),
                        FieldOption(id="ombor", label="Yangi / Omborda saqlangan", value="Yangi (ombor)"),
                        FieldOption(id="ishlatilgan", label="Ishlatilgan / Ikkinchi qo‘l", value="Ishlatilgan"),
                    ]
                ),
                QuestionField(
                    id="location",
                    label="Ombor manzili",
                    prompt="Ombor yoki savdo do‘koni manzili:",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=95,
                    validation_rules={"min_length": 2, "max_length": 150},
                    placeholder="Toshkent, Bektemir tumani"
                ),
                QuestionField(
                    id="phone",
                    label="Aloqa raqami",
                    prompt="Aloqa uchun telefon raqamingiz:",
                    field_type=FieldType.PHONE,
                    required=True,
                    display_order=100,
                    validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
                ),
                QuestionField(
                    id="media",
                    label="Rasmlar",
                    prompt="Material rasmlarini yuboring (1-10 ta):",
                    field_type=FieldType.MULTI_PHOTO,
                    required=False,
                    display_order=105,
                    validation_rules={"max_items": 10}
                ),
                QuestionField(
                    id="description",
                    label="Batafsil tavsif",
                    prompt="Mahsulot haqida qo‘shimcha batafsil ma’lumot:",
                    field_type=FieldType.DESCRIPTION,
                    required=False,
                    display_order=110,
                    validation_rules={"max_length": 2000}
                ),
            ]
        ),

        # 7. Asbob-uskunalar
        "tools": Subcategory(
            id="tools",
            label="Asbob-uskunalar",
            icon="🛠",
            description="Elektr va qo‘l asboblari, payvandlash, stanoklar va prokat",
            specific_fields=[
                QuestionField(
                    id="tool_type",
                    label="Asbob turi",
                    prompt="Asbob-uskuna turini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=10,
                    options=[
                        FieldOption(id="power_tools", label="Elektr asboblar (Drel, Bolgarka, Perforator...)", value="Elektr asboblari", icon="⚡️"),
                        FieldOption(id="battery_tools", label="Akkumulyatorli asboblar", value="Akkumulyatorli asboblar", icon="🔋"),
                        FieldOption(id="hand_tools", label="Qo‘l asboblari (Kalitlar, Otvyortka...)", value="Qo‘l asboblari", icon="🔧"),
                        FieldOption(id="welding", label="Payvandlash uskunalari (Svarka)", value="Payvandlash uskunalari", icon="👨‍🏭"),
                        FieldOption(id="pneumatic", label="Kompressor va pnevmatika", value="Kompressor va pnevmatika", icon="💨"),
                        FieldOption(id="generator", label="Dvigatelli / Benzinli (Generator, Drujba)", value="Dvigatelli uskunalar", icon="⛽️"),
                        FieldOption(id="machine", label="Dastgohlar va stanoklar", value="Stanoklar", icon="🏭"),
                        FieldOption(id="measuring", label="O‘lchov asboblari (Lazer uroven...)", value="O‘lchov asboblari", icon="📐"),
                        FieldOption(id="boshqa", label="Boshqa asbob-uskunalar", value="Boshqa asboblar", icon="🔹"),
                    ]
                ),
                QuestionField(
                    id="title",
                    label="Mahsulot nomi",
                    prompt="Mahsulot nomini kiriting (masalan: <i>Bosch GBH 2-26 DRE Perforator</i> yoki <i>Makita Akkumulyatorli drel</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=15,
                    validation_rules={"min_length": 3, "max_length": 150},
                    placeholder="Bosch GBH 2-26 DRE Perforator"
                ),
                QuestionField(
                    id="brand_model",
                    label="Brend va model",
                    prompt="Brend va modelini kiriting (masalan: <i>Bosch, DeWalt, Makita, Total, Crown, Ingco</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=20,
                    placeholder="Bosch GBH 2-26"
                ),
                QuestionField(
                    id="deal_type",
                    label="Bitim formati",
                    prompt="E’lon turini tanlang (Sotuv yoki Ijara):",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=25,
                    options=[
                        FieldOption(id="sale", label="Sotiladi", value="Sotiladi", icon="🏷"),
                        FieldOption(id="rent", label="Ijaraga beriladi (Prokat)", value="Ijaraga beriladi (Prokat)", icon="🔄"),
                    ]
                ),
                QuestionField(
                    id="purpose_specs",
                    label="Vazifasi va xususiyatlari",
                    prompt="Asbobning vazifasi va asosiy xususiyatlari (masalan: <i>Beton va g‘isht teshish, metall kesish uchun</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=30,
                    placeholder="Beton va g‘ishtda teshik ochish uchun"
                ),
                QuestionField(
                    id="power_specs",
                    label="Quvvat va kuchlanish",
                    prompt="Quvvati va kuchlanishi (masalan: <code>850W, 220V</code> yoki <code>20V Li-Ion</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=35,
                    placeholder="850W, 220V"
                ),
                QuestionField(
                    id="operation_type",
                    label="Ishlash turi",
                    prompt="Ishlash (quvvat olish) turini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=40,
                    options=[
                        FieldOption(id="electric", label="Elektr tarmog‘i (220V)", value="Elektr 220V"),
                        FieldOption(id="battery", label="Akkumulyatorli (Li-Ion)", value="Akkumulyatorli"),
                        FieldOption(id="fuel", label="Benzin / Dizel yoqilg‘i", value="Yoqilg‘ili"),
                        FieldOption(id="air", label="Pnevmatik (siqilgan havo)", value="Pnevmatik"),
                        FieldOption(id="manual", label="Mexanik / Qo‘lda", value="Qo‘lda"),
                    ]
                ),
                QuestionField(
                    id="accessories",
                    label="Komplektatsiya",
                    prompt="Komplektda nimalar bor (keys, 2 ta akkumulyator, zaryadnik, nasadkalar...):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=45,
                    placeholder="Keys, qo‘shimcha patron, 3 ta bur"
                ),
                QuestionField(
                    id="condition",
                    label="Holati",
                    prompt="Asbob holatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=50,
                    options=[
                        FieldOption(id="yangi", label="Yangi (qutida / ishlatilmagan)", value="Yangi", icon="✨"),
                        FieldOption(id="ideal", label="Ideal (kam ishlatilgan)", value="Ideal", icon="💎"),
                        FieldOption(id="yaxshi", label="Yaxshi (ishchi holatda)", value="Yaxshi", icon="👍"),
                        FieldOption(id="tamir", label="Ta’mir talab", value="Ta’mir talab", icon="🛠"),
                    ]
                ),
                QuestionField(
                    id="defects",
                    label="Nuqsonlari",
                    prompt="Nuqsonlari bormi (korpus tirnalgan, simi ulangan... yo‘q bo‘lsa 'Yo‘q' deb yozing):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=55,
                    placeholder="Nuqsoni yo‘q, reduktori moylangan"
                ),
                QuestionField(
                    id="warranty",
                    label="Kafolat",
                    prompt="Kafolat mavjudmi (masalan: <i>1 yil kafolat</i> yoki <i>3 kun tekshirishga</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=60,
                    placeholder="6 oy rasmiy kafolat"
                ),
                QuestionField(
                    id="quantity",
                    label="Miqdori",
                    prompt="Miqdori (masalan: <code>1 dona</code> yoki <code>3 komplekt</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=65,
                    placeholder="1 dona"
                ),
                QuestionField(
                    id="rental_terms",
                    label="Ijara shartlari va muddati",
                    prompt="Ijara shartlari va muddatini kiriting (masalan: <i>Kunlik ijara, pasport nusxasi yoki garov talab etiladi</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=70,
                    condition_key="deal_type",
                    condition_values=["Ijaraga beriladi (Prokat)"],
                    placeholder="Kunlik 100 000 so‘m, pasport garovga olinadi"
                ),
                QuestionField(
                    id="price",
                    label="Narxi",
                    prompt="Narxini kiriting (Sotuv narxi yoki Kunlik ijara narxi):",
                    field_type=FieldType.PRICE,
                    required=True,
                    display_order=75,
                    validation_rules={"min": 1}
                ),
                QuestionField(
                    id="currency",
                    label="Valyuta",
                    prompt="Valyutani tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=80,
                    options=[
                        FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m"),
                        FieldOption(id="usd", label="AQSH Dollari ($)", value="USD"),
                    ]
                ),
                QuestionField(
                    id="price_negotiable",
                    label="Kelishiladimi",
                    prompt="Narx kelishiladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=85,
                    options=[
                        FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                        FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
                    ]
                ),
                QuestionField(
                    id="delivery",
                    label="Yetkazib berish",
                    prompt="Yetkazib berish shartlari:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=90,
                    options=[
                        FieldOption(id="bor", label="Yetkazib berish bor", value="Yetkazib beriladi"),
                        FieldOption(id="olib_ketish", label="O‘zi olib ketish (samovivoz)", value="Samovivoz"),
                    ]
                ),
                QuestionField(
                    id="location",
                    label="Joylashuv",
                    prompt="Joylashgan shahar yoki tuman:",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=95,
                    validation_rules={"min_length": 2, "max_length": 150},
                    placeholder="Toshkent, Uchtepa"
                ),
                QuestionField(
                    id="phone",
                    label="Aloqa raqami",
                    prompt="Aloqa uchun telefon raqamingiz:",
                    field_type=FieldType.PHONE,
                    required=True,
                    display_order=100,
                    validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
                ),
                QuestionField(
                    id="media",
                    label="Rasmlar/video",
                    prompt="Asbob rasmlari yoki videosini yuboring (1-10 ta):",
                    field_type=FieldType.MULTI_PHOTO,
                    required=False,
                    display_order=105,
                    validation_rules={"max_items": 10}
                ),
                QuestionField(
                    id="description",
                    label="Batafsil tavsif",
                    prompt="Qo‘shimcha batafsil ma’lumot:",
                    field_type=FieldType.DESCRIPTION,
                    required=False,
                    display_order=110,
                    validation_rules={"max_length": 2000}
                ),
            ]
        ),

        # 8. Avtomobil ehtiyot qismlari
        "auto_parts": Subcategory(
            id="auto_parts",
            label="Avtomobil ehtiyot qismlari",
            icon="🚗",
            description="Kuzov, dvigatel, xodovoy qismlari va optika",
            specific_fields=[
                QuestionField(
                    id="title",
                    label="Ehtiyot qism nomi",
                    prompt="Ehtiyot qism nomini kiriting (masalan: <i>Old o‘ng fara</i>, <i>Old bamper</i> yoki <i>Tormoz kolodkasi</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=10,
                    validation_rules={"min_length": 3, "max_length": 150},
                    placeholder="Gentra 2020 Old o‘ng fara original"
                ),
                QuestionField(
                    id="part_category",
                    label="Kategoriya",
                    prompt="Ehtiyot qism toifasini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=15,
                    options=[
                        FieldOption(id="body", label="Kuzov va optika", value="Kuzov va optika", icon="🚗"),
                        FieldOption(id="engine", label="Dvigatel va yonilg‘i tizimi", value="Dvigatel", icon="⚙️"),
                        FieldOption(id="suspension", label="Xodovoy / Podveska va rul", value="Xodovoy va podveska", icon="🛞"),
                        FieldOption(id="brakes", label="Tormoz tizimi", value="Tormoz tizimi", icon="🛑"),
                        FieldOption(id="transmission", label="Transmissiya va uzatmalar qutisi", value="Transmissiya", icon="🕹"),
                        FieldOption(id="electric", label="Elektr jihozlari va datchiklar", value="Elektr jihozlari", icon="💡"),
                        FieldOption(id="interior", label="Salon jihozlari", value="Salon jihozlari", icon="💺"),
                        FieldOption(id="filters", label="Filtrlar va moylar", value="Filtrlar va moylar", icon="🛢"),
                        FieldOption(id="boshqa", label="Boshqa ehtiyot qismlar", value="Boshqa qismlar", icon="🔹"),
                    ]
                ),
                QuestionField(
                    id="brand_manufacturer",
                    label="Brend / Ishlab chiqaruvchi",
                    prompt="Ishlab chiqaruvchi brend (masalan: <i>GM Korea, UzAuto Motors, Bosch, Denso, Brembo</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=20,
                    placeholder="GM Korea Original"
                ),
                QuestionField(
                    id="part_number",
                    label="OEM / Detal raqami",
                    prompt="OEM yoki detal raqami (Part number, agar ma’lum bo‘lsa):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=25,
                    placeholder="96473218"
                ),
                QuestionField(
                    id="car_brand",
                    label="Mos avtomobil markasi",
                    prompt="Mos keluvchi avtomobil rusumini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=30,
                    options=[
                        FieldOption(id="chevrolet", label="Chevrolet", value="Chevrolet"),
                        FieldOption(id="daewoo", label="Daewoo", value="Daewoo"),
                        FieldOption(id="hyundai", label="Hyundai", value="Hyundai"),
                        FieldOption(id="kia", label="Kia", value="Kia"),
                        FieldOption(id="byd", label="BYD", value="BYD"),
                        FieldOption(id="chery", label="Chery", value="Chery"),
                        FieldOption(id="toyota", label="Toyota", value="Toyota"),
                        FieldOption(id="lada", label="Lada / VAZ", value="Lada"),
                        FieldOption(id="universal", label="Universal (barcha mashinalarga)", value="Universal"),
                        FieldOption(id="boshqa", label="Boshqa rusum", value="Boshqa"),
                    ]
                ),
                QuestionField(
                    id="car_model",
                    label="Avtomobil modeli",
                    prompt="Mos avtomobil modeli (masalan: <i>Gentra, Cobalt, Nexia 3, Malibu 2, Tracker</i> yoki <i>Universal</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=35,
                    placeholder="Chevrolet Cobalt"
                ),
                QuestionField(
                    id="year_range",
                    label="Mos yillar oralig‘i",
                    prompt="Ishlab chiqarilgan yillari (masalan: <code>2018-2024</code> yoki <code>Barcha yillar</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=40,
                    placeholder="2016-2023"
                ),
                QuestionField(
                    id="part_originality",
                    label="Original yoki analog",
                    prompt="Detalning o‘ziga xosligi:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=45,
                    options=[
                        FieldOption(id="original", label="Original (OEM / Zavod)", value="Original (OEM)"),
                        FieldOption(id="analog", label="Sifatli analog (Dublikat)", value="Analog (Dublikat)"),
                        FieldOption(id="tuning", label="Tyuning qism", value="Tyuning"),
                    ]
                ),
                QuestionField(
                    id="condition",
                    label="Mahsulot holati",
                    prompt="Detal holatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=50,
                    options=[
                        FieldOption(id="yangi", label="Yangi (ishlatilmagan)", value="Yangi", icon="✨"),
                        FieldOption(id="ideal", label="Ideal / Yangidek", value="Ideal", icon="💎"),
                        FieldOption(id="razborka", label="Ishlatilgan (Xorijiy razborka / Ideal)", value="Ishlatilgan (razborka)", icon="🚗"),
                        FieldOption(id="yechilgan", label="Ishlatilgan (O‘zimizdan yechilgan)", value="Ishlatilgan (yechilgan)", icon="🔧"),
                        FieldOption(id="tamir", label="Ta’mir talab", value="Ta’mir talab", icon="🛠"),
                    ]
                ),
                QuestionField(
                    id="defects",
                    label="Nuqsonlari",
                    prompt="Nuqsonlari bormi (tirnalgan, kronshteyni singan... yo‘q bo‘lsa 'Yo‘q' deb yozing):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=55,
                    placeholder="Nuqsoni yo‘q, barcha qotirgichlari butun"
                ),
                QuestionField(
                    id="compatibility_notes",
                    label="Moslik eslatmasi",
                    prompt="Moslik bo‘yicha qo‘shimcha ma’lumot (masalan: <i>Faqat 1.5 motor avtomat korobkaga tushadi</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=60,
                    placeholder="Faqat 1.5 mator avtomat korobka uchun"
                ),
                QuestionField(
                    id="quantity",
                    label="Miqdori",
                    prompt="Miqdori (masalan: <code>1 dona</code>, <code>1 juft (komplekt)</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=65,
                    placeholder="1 dona (o‘ng tomon)"
                ),
                QuestionField(
                    id="warranty_return",
                    label="Kafolat va qaytarish",
                    prompt="Kafolat va qaytarish shartlari (masalan: <i>O‘rnatib tekshirishga 3 kun kafolat</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=70,
                    placeholder="O‘rnatib tekshirishga 3 kun kafolat"
                ),
                QuestionField(
                    id="price",
                    label="Narxi",
                    prompt="Narxini kiriting (faqat raqam bilan):",
                    field_type=FieldType.PRICE,
                    required=True,
                    display_order=75,
                    validation_rules={"min": 1}
                ),
                QuestionField(
                    id="currency",
                    label="Valyuta",
                    prompt="Valyutani tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=80,
                    options=[
                        FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m"),
                        FieldOption(id="usd", label="AQSH Dollari ($)", value="USD"),
                    ]
                ),
                QuestionField(
                    id="price_negotiable",
                    label="Kelishiladimi",
                    prompt="Narx kelishiladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=85,
                    options=[
                        FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                        FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
                    ]
                ),
                QuestionField(
                    id="delivery",
                    label="Yetkazib berish",
                    prompt="Yetkazib berish shartlari:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=90,
                    options=[
                        FieldOption(id="bor", label="Yetkazib berish bor (Taksi / BTS / Pochta)", value="Yetkazib beriladi"),
                        FieldOption(id="olib_ketish", label="O‘zi olib ketish (samovivoz)", value="Samovivoz"),
                    ]
                ),
                QuestionField(
                    id="location",
                    label="Manzil",
                    prompt="Do‘kon yoki avtorazborka joylashgan manzil:",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=95,
                    validation_rules={"min_length": 2, "max_length": 150},
                    placeholder="Toshkent, Sergeli moshina bozori"
                ),
                QuestionField(
                    id="phone",
                    label="Aloqa raqami",
                    prompt="Aloqa uchun telefon raqamingiz:",
                    field_type=FieldType.PHONE,
                    required=True,
                    display_order=100,
                    validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
                ),
                QuestionField(
                    id="media",
                    label="Rasmlar",
                    prompt="Ehtiyot qism rasmlarini yuboring (1-10 ta):",
                    field_type=FieldType.MULTI_PHOTO,
                    required=False,
                    display_order=105,
                    validation_rules={"max_items": 10}
                ),
                QuestionField(
                    id="description",
                    label="Batafsil tavsif",
                    prompt="Qo‘shimcha batafsil ma’lumot:",
                    field_type=FieldType.DESCRIPTION,
                    required=False,
                    display_order=110,
                    validation_rules={"max_length": 2000}
                ),
            ]
        ),

        # 9. Kiyim-kechak va aksessuarlar
        "clothing": Subcategory(
            id="clothing",
            label="Kiyim-kechak va aksessuarlar",
            icon="👔",
            description="Erkaklar, ayollar, bolalar kiyimi, poyabzal va aksessuarlar",
            specific_fields=[
                QuestionField(
                    id="clothing_type",
                    label="Mahsulot turi",
                    prompt="Mahsulot toifasini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=10,
                    options=[
                        FieldOption(id="men", label="Erkaklar kiyimi", value="Erkaklar kiyimi", icon="👔"),
                        FieldOption(id="women", label="Ayollar kiyimi", value="Ayollar kiyimi", icon="👗"),
                        FieldOption(id="kids", label="Bolalar kiyimi", value="Bolalar kiyimi", icon="👶"),
                        FieldOption(id="shoes", label="Poyabzal (Oyoq kiyim)", value="Poyabzal", icon="👟"),
                        FieldOption(id="bags", label="Sumka va chamadonlar", value="Sumkalar", icon="🎒"),
                        FieldOption(id="watches", label="Soatlar va taqinchoqlar", value="Soat va taqinchoqlar", icon="⌚️"),
                        FieldOption(id="accessories", label="Bosh kiyimlar va aksessuarlar", value="Aksessuarlar", icon="🧢"),
                        FieldOption(id="sport", label="Sport kiyimlari", value="Sport kiyimlari", icon="🏃"),
                    ]
                ),
                QuestionField(
                    id="title",
                    label="Mahsulot nomi",
                    prompt="Mahsulot nomini kiriting (masalan: <i>Erkaklar charm kurtkasi</i> yoki <i>Nike Air Force 1 krossovka</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=15,
                    validation_rules={"min_length": 3, "max_length": 150},
                    placeholder="Erkaklar qishki charm kurtkasi"
                ),
                QuestionField(
                    id="brand",
                    label="Brend",
                    prompt="Brendi (masalan: <i>Zara, Massimo Dutti, Nike, Adidas, Mahalliy brend</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=20,
                    placeholder="Zara Man"
                ),
                QuestionField(
                    id="model_collection",
                    label="Model / Kolleksiya",
                    prompt="Model yoki kolleksiya nomi (masalan: <i>Bahor-Yoz 2026</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=25,
                    placeholder="Bahorgi yangi kolleksiya"
                ),
                QuestionField(
                    id="target_group",
                    label="Mo‘ljallangan guruh",
                    prompt="Kimlar uchun mo‘ljallangan:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=False,
                    display_order=30,
                    options=[
                        FieldOption(id="men", label="Erkaklar uchun", value="Erkaklar"),
                        FieldOption(id="women", label="Ayollar uchun", value="Ayollar"),
                        FieldOption(id="kids", label="Bolalar / O‘smirlar uchun", value="Bolalar"),
                        FieldOption(id="unisex", label="Unisex (har kimga)", value="Unisex"),
                    ]
                ),
                QuestionField(
                    id="size",
                    label="O‘lchami (Razmer)",
                    prompt="O‘lchamlarini kiriting (masalan: <i>S, M, L, XL, XXL</i> yoki poyabzal: <i>41, 42, 43</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=35,
                    placeholder="M, L, XL"
                ),
                QuestionField(
                    id="color",
                    label="Rangi",
                    prompt="Rangi (masalan: <i>Qora, To‘q ko‘k, Bej, Oq</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=40,
                    placeholder="Qora va jigarrang"
                ),
                QuestionField(
                    id="material",
                    label="Material tarkibi",
                    prompt="Material tarkibi (masalan: <i>100% Paxta, Tabiiy charm, Jun, Sintetika</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=45,
                    placeholder="100% Tabiiy charm"
                ),
                QuestionField(
                    id="condition",
                    label="Holati",
                    prompt="Mahsulot holatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=50,
                    options=[
                        FieldOption(id="yangi_tag", label="Yangi (etiketkasi bilan)", value="Yangi (etiketkali)", icon="✨"),
                        FieldOption(id="yangi_no_tag", label="Yangi (etiketkasiz)", value="Yangi (etiketkasiz)", icon="🆕"),
                        FieldOption(id="ideal", label="Ideal (bir marta kiyilgan)", value="Ideal", icon="💎"),
                        FieldOption(id="yaxshi", label="Ishlatilgan (yaxshi holatda)", value="Ishlatilgan", icon="👍"),
                    ]
                ),
                QuestionField(
                    id="available_sizes_colors",
                    label="Mavjud variantlar",
                    prompt="Mavjud barcha o‘lcham va ranglar (masalan: <i>O‘lchamlar: M, L, XL; Ranglar: Qora, Oq</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=55,
                    placeholder="O‘lchamlar: M, L, XL; Ranglar: Qora, To‘q ko‘k"
                ),
                QuestionField(
                    id="stock_qty",
                    label="Ombordagi miqdor",
                    prompt="Mavjud miqdor (masalan: <code>1 dona</code> yoki <code>50 dona bor</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=60,
                    placeholder="5 dona qoldi"
                ),
                QuestionField(
                    id="sale_type",
                    label="Savdo turi",
                    prompt="Savdo turini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=65,
                    options=[
                        FieldOption(id="retail", label="Chakana savdo (dona)", value="Chakana"),
                        FieldOption(id="wholesale", label="Ulgurji savdo (Optom)", value="Ulgurji (optom)"),
                        FieldOption(id="both", label="Ham chakana, ham ulgurji", value="Chakana va ulgurji"),
                    ]
                ),
                QuestionField(
                    id="price",
                    label="Birlik narxi",
                    prompt="Birlik narxini kiriting (faqat raqam bilan):",
                    field_type=FieldType.PRICE,
                    required=True,
                    display_order=70,
                    validation_rules={"min": 1}
                ),
                QuestionField(
                    id="currency",
                    label="Valyuta",
                    prompt="Valyutani tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=75,
                    options=[
                        FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m"),
                        FieldOption(id="usd", label="AQSH Dollari ($)", value="USD"),
                    ]
                ),
                QuestionField(
                    id="price_negotiable",
                    label="Kelishiladimi",
                    prompt="Narx kelishiladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=80,
                    options=[
                        FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                        FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
                    ]
                ),
                QuestionField(
                    id="return_policy",
                    label="Qaytarish / Almashtirish",
                    prompt="Qaytarish yoki almashtirish shartlari (masalan: <i>O‘lcham to‘g‘ri kelmasa 3 kunda almashtiriladi</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=85,
                    placeholder="3 kun ichida razmer almashtirib beriladi"
                ),
                QuestionField(
                    id="delivery",
                    label="Yetkazib berish",
                    prompt="Yetkazib berish shartlari:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=90,
                    options=[
                        FieldOption(id="uzb", label="O‘zbekiston bo‘ylab yetkazib berish bor", value="O‘zbekiston bo‘ylab yetkazish"),
                        FieldOption(id="tashkent", label="Toshkent bo‘ylab yetkazish", value="Toshkent bo‘ylab yetkazish"),
                        FieldOption(id="olib_ketish", label="O‘zi olib ketish (samovivoz)", value="Samovivoz"),
                    ]
                ),
                QuestionField(
                    id="location",
                    label="Joylashuv",
                    prompt="Do‘kon yoki mahsulot joylashgan manzil:",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=95,
                    validation_rules={"min_length": 2, "max_length": 150},
                    placeholder="Toshkent, Chorsu bozori"
                ),
                QuestionField(
                    id="phone",
                    label="Aloqa raqami",
                    prompt="Aloqa uchun telefon raqamingiz:",
                    field_type=FieldType.PHONE,
                    required=True,
                    display_order=100,
                    validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
                ),
                QuestionField(
                    id="media",
                    label="Rasmlar",
                    prompt="Kiyim/poyabzal rasmlarini yuboring (1-10 ta):",
                    field_type=FieldType.MULTI_PHOTO,
                    required=False,
                    display_order=105,
                    validation_rules={"max_items": 10}
                ),
                QuestionField(
                    id="description",
                    label="Batafsil tavsif",
                    prompt="Mahsulot haqida qo‘shimcha batafsil ma’lumot:",
                    field_type=FieldType.DESCRIPTION,
                    required=False,
                    display_order=110,
                    validation_rules={"max_length": 2000}
                ),
            ]
        ),

        # 10. Xizmatlar
        "services": Subcategory(
            id="services",
            label="Xizmatlar",
            icon="🛠",
            description="Ta’mirlash, usta, kuryerlik, klining, avtoservis va IT xizmatlari",
            specific_fields=[
                QuestionField(
                    id="service_type",
                    label="Xizmat sohasi",
                    prompt="Xizmat yo‘nalishini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=10,
                    options=[
                        FieldOption(id="construction", label="Qurilish va ta’mirlash", value="Qurilish va ta’mirlash", icon="🧱"),
                        FieldOption(id="appliance_repair", label="Maishiy texnika va elektronika ustasi", value="Texnika ustasi", icon="🧊"),
                        FieldOption(id="plumbing", label="Santexnika va isitish tizimlari", value="Santexnika", icon="🚰"),
                        FieldOption(id="electrician", label="Elektrika va montaj xizmatlari", value="Elektrika", icon="⚡️"),
                        FieldOption(id="autoservice", label="Avtoservis va evakuator", value="Avtoservis", icon="🚗"),
                        FieldOption(id="furniture_service", label="Mebel yasash va ta’mirlash", value="Mebel xizmati", icon="🛋"),
                        FieldOption(id="cleaning", label="Klining va tozalash xizmati", value="Klining", icon="🧹"),
                        FieldOption(id="moving", label="Yuk tashish va ko‘chirish", value="Yuk tashish", icon="🚚"),
                        FieldOption(id="it", label="IT / Dasturlash va dizayn", value="IT va dizayn", icon="💻"),
                        FieldOption(id="education", label="Ta’lim va repetitorlik", value="Ta’lim", icon="📚"),
                        FieldOption(id="beauty", label="Go‘zallik va parvarish", value="Go‘zallik", icon="💇"),
                        FieldOption(id="boshqa", label="Boshqa xizmatlar", value="Boshqa xizmat", icon="🔹"),
                    ]
                ),
                QuestionField(
                    id="title",
                    label="Xizmat nomi",
                    prompt="Xizmat nomini kiriting (masalan: <i>Santexnika va isitish tizimlarini professional o‘rnatish</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=15,
                    validation_rules={"min_length": 3, "max_length": 150},
                    placeholder="Professional santexnika va isitish ustasi"
                ),
                QuestionField(
                    id="service_scope",
                    label="Xizmat tavsifi / Muammolar",
                    prompt="Xizmat qanday muammolarni hal qilishi va bajariladigan ishlarni batafsil yozing:",
                    field_type=FieldType.DESCRIPTION,
                    required=True,
                    display_order=20,
                    validation_rules={"min_length": 10, "max_length": 2000},
                    placeholder="Kranlar, quvurlar, tyopliy pol va kotyol o‘rnatish. Nosozliklarni tezda bartaraf etish."
                ),
                QuestionField(
                    id="service_area",
                    label="Xizmat ko‘rsatish hududi",
                    prompt="Xizmat ko‘rsatish hududini kiriting (masalan: <i>Toshkent shahri va Toshkent viloyati</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=25,
                    placeholder="Toshkent shahri barcha tumanlari"
                ),
                QuestionField(
                    id="pricing_type",
                    label="Narx turi",
                    prompt="To‘lov shaklini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=30,
                    options=[
                        FieldOption(id="fixed", label="Qat’iy narx", value="Qat’iy narx"),
                        FieldOption(id="hourly", label="Soatbay to‘lov", value="Soatbay"),
                        FieldOption(id="daily", label="Kunlik to‘lov", value="Kunlik"),
                        FieldOption(id="scope", label="Ish hajmiga qarab (Smeta)", value="Ish hajmiga qarab"),
                        FieldOption(id="consult", label="Kelishuv asosida (bepul konsultatsiya)", value="Kelishuv asosida"),
                    ]
                ),
                QuestionField(
                    id="price",
                    label="Xizmat narxi",
                    prompt="Xizmat narxi yoki minimal boshlang‘ich narxni kiriting (faqat raqam bilan):",
                    field_type=FieldType.PRICE,
                    required=True,
                    display_order=35,
                    validation_rules={"min": 1}
                ),
                QuestionField(
                    id="currency",
                    label="Valyuta",
                    prompt="Valyutani tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=40,
                    options=[
                        FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m"),
                        FieldOption(id="usd", label="AQSH Dollari ($)", value="USD"),
                    ]
                ),
                QuestionField(
                    id="price_negotiable",
                    label="Kelishiladimi",
                    prompt="Narx kelishiladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=45,
                    options=[
                        FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                        FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
                    ]
                ),
                QuestionField(
                    id="completion_time",
                    label="Bajarish muddati",
                    prompt="Taxminiy bajarish muddati (masalan: <i>1-2 soatda</i>, <i>1 kunda</i> yoki <i>Loyiha hajmiga qarab</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=50,
                    placeholder="Murojaat kuni 1-2 soat ichida"
                ),
                QuestionField(
                    id="working_hours",
                    label="Ish vaqti",
                    prompt="Murojaat qilish vaqtlari (masalan: <code>08:00 dan 21:00 gacha, dam olish kunlarisiz</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=55,
                    placeholder="08:00 dan 22:00 gacha har kuni"
                ),
                QuestionField(
                    id="home_visit",
                    label="Xizmat ko‘rsatish joyi",
                    prompt="Xizmat ko‘rsatish formati:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=60,
                    options=[
                        FieldOption(id="visit", label="Uyga / Ofisga borib xizmat ko‘rsatiladi", value="Mijoz manziliga boriladi"),
                        FieldOption(id="workshop", label="Mijoz bizning ustaxonaga keladi", value="Ustaxonada"),
                        FieldOption(id="remote", label="Masofaviy / Onlayn xizmat", value="Onlayn/Masofaviy"),
                    ]
                ),
                QuestionField(
                    id="experience",
                    label="Tajriba / Malaka",
                    prompt="Ish tajribangiz (masalan: <i>8 yillik amaliy tajriba, sertifikatlar mavjud</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=65,
                    placeholder="8 yillik amaliy usta tajribasi"
                ),
                QuestionField(
                    id="warranty",
                    label="Kafolat",
                    prompt="Bajarilgan ishga kafolat beriladimi (masalan: <i>6 oy rasmiy kafolat</i>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=70,
                    placeholder="Bajarilgan ishga 6 oy kafolat"
                ),
                QuestionField(
                    id="location",
                    label="Manzil / Ofis",
                    prompt="Ofis yoki usta joylashgan shahar / tuman:",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=75,
                    validation_rules={"min_length": 2, "max_length": 150},
                    placeholder="Toshkent, Yunusobod"
                ),
                QuestionField(
                    id="phone",
                    label="Aloqa raqami",
                    prompt="Aloqa uchun telefon raqamingiz:",
                    field_type=FieldType.PHONE,
                    required=True,
                    display_order=80,
                    validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
                ),
                QuestionField(
                    id="media",
                    label="Ish namunalari (foto/video)",
                    prompt="Avvalgi ish namunalari rasmlari yoki videosini yuboring (1-10 ta):",
                    field_type=FieldType.MULTI_PHOTO,
                    required=False,
                    display_order=85,
                    validation_rules={"max_items": 10}
                ),
                QuestionField(
                    id="description",
                    label="Qo‘shimcha tavsif",
                    prompt="Qo‘shimcha ma’lumotlar:",
                    field_type=FieldType.DESCRIPTION,
                    required=False,
                    display_order=90,
                    validation_rules={"max_length": 2000}
                ),
            ]
        ),

        # 11. Boshqa mahsulotlar
        "other_goods": Subcategory(
            id="other_goods",
            label="Boshqa mahsulotlar",
            icon="📦",
            description="Yuqoridagi toifalarga kirmagan har qanday tovar va buyumlar",
            specific_fields=[
                QuestionField(
                    id="title",
                    label="Mahsulot nomi",
                    prompt="Mahsulot nomini kiriting (masalan: <i>Tog‘ velosipedi</i> yoki <i>Bolalar aravachasi</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=10,
                    validation_rules={"min_length": 3, "max_length": 150},
                    placeholder="Tog‘ velosipedi 26 dyuym"
                ),
                QuestionField(
                    id="item_type",
                    label="Mahsulot turi",
                    prompt="Mahsulot turini erkin kiriting (masalan: <i>Sport anjomi, Bolalar buyumi, Uy-ro‘zg‘or buyumi</i>):",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=15,
                    placeholder="Sport anjomi"
                ),
                QuestionField(
                    id="brand_model",
                    label="Brend va model",
                    prompt="Brend va modelini kiriting (agar mavjud bo‘lsa, ixtiyoriy):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=20,
                    placeholder="Trinx M100"
                ),
                QuestionField(
                    id="condition",
                    label="Holati",
                    prompt="Mahsulot holatini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=25,
                    options=[
                        FieldOption(id="yangi", label="Yangi (ishlatilmagan)", value="Yangi", icon="✨"),
                        FieldOption(id="ideal", label="Ideal (yangidek)", value="Ideal", icon="💎"),
                        FieldOption(id="yaxshi", label="Yaxshi (ishchi holatda)", value="Yaxshi", icon="👍"),
                        FieldOption(id="ishlatilgan", label="Ishlatilgan", value="Ishlatilgan", icon="📦"),
                    ]
                ),
                QuestionField(
                    id="unit_of_measure",
                    label="O‘lchov birligi",
                    prompt="O‘lchov birligini tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=30,
                    options=[
                        FieldOption(id="dona", label="dona", value="dona"),
                        FieldOption(id="komplekt", label="komplekt / to‘plam", value="komplekt"),
                        FieldOption(id="kg", label="kg", value="kg"),
                        FieldOption(id="metr", label="metr", value="metr"),
                        FieldOption(id="qadoq", label="qadoq", value="qadoq"),
                        FieldOption(id="boshqa", label="boshqa", value="birlik"),
                    ]
                ),
                QuestionField(
                    id="quantity",
                    label="Miqdori",
                    prompt="Miqdori (masalan: <code>1 dona</code> yoki <code>2 komplekt</code>):",
                    field_type=FieldType.TEXT,
                    required=False,
                    display_order=35,
                    placeholder="1 dona"
                ),
                QuestionField(
                    id="price",
                    label="Narxi",
                    prompt="Narxini kiriting (faqat raqam bilan):",
                    field_type=FieldType.PRICE,
                    required=True,
                    display_order=40,
                    validation_rules={"min": 1}
                ),
                QuestionField(
                    id="currency",
                    label="Valyuta",
                    prompt="Valyutani tanlang:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=45,
                    options=[
                        FieldOption(id="uzs", label="So‘m (UZS)", value="so‘m"),
                        FieldOption(id="usd", label="AQSH Dollari ($)", value="USD"),
                    ]
                ),
                QuestionField(
                    id="price_negotiable",
                    label="Kelishiladimi",
                    prompt="Narx kelishiladimi?",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=50,
                    options=[
                        FieldOption(id="ha", label="Ha, kelishiladi", value="Ha, kelishiladi"),
                        FieldOption(id="yoq", label="Yo‘q, qat’iy narx", value="Qat’iy narx"),
                    ]
                ),
                QuestionField(
                    id="delivery",
                    label="Yetkazib berish",
                    prompt="Yetkazib berish shartlari:",
                    field_type=FieldType.SINGLE_SELECT,
                    required=True,
                    display_order=55,
                    options=[
                        FieldOption(id="bepul", label="Bepul yetkazib berish", value="Bepul yetkazish"),
                        FieldOption(id="pullik", label="Pullik yetkazish (taksi/pochta)", value="Pullik yetkazish"),
                        FieldOption(id="olib_ketish", label="O‘zi olib ketish (samovivoz)", value="Samovivoz"),
                    ]
                ),
                QuestionField(
                    id="location",
                    label="Joylashuv",
                    prompt="Joylashgan shahar yoki tuman:",
                    field_type=FieldType.TEXT,
                    required=True,
                    display_order=60,
                    validation_rules={"min_length": 2, "max_length": 150},
                    placeholder="Toshkent, Olmazor"
                ),
                QuestionField(
                    id="phone",
                    label="Aloqa raqami",
                    prompt="Aloqa uchun telefon raqamingiz:",
                    field_type=FieldType.PHONE,
                    required=True,
                    display_order=65,
                    validation_rules={"regex": r"^\+?[0-9\s\-\(\)]{7,20}$"}
                ),
                QuestionField(
                    id="media",
                    label="Rasmlar/video",
                    prompt="Mahsulot rasmlari yoki videosini yuboring (1-10 ta):",
                    field_type=FieldType.MULTI_PHOTO,
                    required=False,
                    display_order=70,
                    validation_rules={"max_items": 10}
                ),
                QuestionField(
                    id="description",
                    label="Batafsil tavsif",
                    prompt="Mahsulot haqida qo‘shimcha batafsil ma’lumot:",
                    field_type=FieldType.DESCRIPTION,
                    required=False,
                    display_order=75,
                    validation_rules={"max_length": 2000}
                ),
            ]
        )
    }

    categories["electronics_other"] = Category(
        id="electronics_other",
        label="Boshqa mahsulotlar va texnikalar",
        icon="📱",
        description="Smartfonlar, kompyuterlar, maishiy texnika, qurilish mollari va xizmatlar",
        subcategories=electronics_subcategories,
        common_fields=electronics_common_fields
    )

    return categories
