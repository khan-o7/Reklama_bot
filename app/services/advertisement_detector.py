import re
from typing import Dict, Any, List, Set, Optional
from aiogram.types import Message
from aiogram.enums import MessageEntityType

from app.utils.text_utils import normalize_text, cyrillic_to_latin, extract_phone_numbers, extract_mentions
from app.utils.link_parser import extract_links, extract_domain, is_domain_whitelisted
from app.utils.logger import logger


class AdvertisementDetector:
    """
    Production-grade Multi-Factor Advertisement Detection Engine.
    
    Categorized Lexicon (Uzbek 🇺🇿, Russian 🇷🇺, English 🇬🇧):
    - Sales & Commercial Offers (Sotuv / Taklif / Продажа / Sales)
    - Call to Action (CTA / Harakatga chaqirish / CTA)
    - Contact Indicators (Kontakt / Контакт / Contact)
    - Multi-Factor Synergy & Combination Signals
    - False-Positive Safeguards & Whitelist / Blacklist integration
    """

    # 1. High-impact direct advertising signals (immediate 35-40 points)
    HIGH_IMPACT_PHRASES: Dict[str, int] = {
        # Uzbek
        "reklama": 40,
        "reklama berish": 40,
        "reklama uchun": 40,
        "kanalga obuna": 35,
        "kanalimizga obuna": 35,
        "obuna bo'ling": 35,
        "obuna boling": 35,
        "kanalga kiring": 30,
        "kanalimizga kiring": 30,
        "pul ishlash": 30,
        "daromad qilish": 30,
        "mijoz qidiramiz": 30,
        "maxsus taklif": 25,
        "foydali taklif": 25,
        "hozir buyurtma bering": 30,

        # Russian
        "реклама": 40,
        "рекламное предложение": 40,
        "подписывайтесь": 35,
        "подпишитесь": 35,
        "переходите по ссылке": 35,
        "заказать сейчас": 30,
        "купить сейчас": 30,
        "выгодное предложение": 25,
        "заработок": 30,

        # English
        "advertising": 40,
        "advertisement": 40,
        "special offer": 30,
        "buy now": 30,
        "order now": 30,
        "earn money": 30,
        "make money": 30,
        "business opportunity": 30,
        "subscribe": 30,
        "join us": 25,
    }

    # 2. Sales & Offer terms (Sotuv / Taklif / Продажа / Sales) (15-20 points)
    SALES_TERMS: Dict[str, int] = {
        # Uzbek
        "sotiladi": 20,
        "sotamiz": 20,
        "sotib oling": 20,
        "buyurtma": 15,
        "buyurtma berish": 20,
        "zakaz": 15,
        "narxi": 10,
        "narx": 10,
        "chegirma": 15,
        "chegirmalar": 15,
        "aksiya": 20,
        "aktsiya": 20,
        "skidka": 15,
        "bepul": 15,
        "yangi mahsulot": 15,
        "mahsulot": 10,
        "xizmat": 10,
        "xizmatlar": 10,
        "hamkorlik": 15,
        "hamkorlik uchun": 20,
        "mijozlar": 15,
        "daromad": 15,
        "dostavka": 15,
        "yetkazib berish": 15,

        # Russian
        "продаю": 20,
        "продаем": 20,
        "продаём": 20,
        "продажа": 20,
        "купить": 15,
        "покупайте": 20,
        "закажите": 20,
        "заказать": 15,
        "заказ": 15,
        "цена": 10,
        "стоимость": 10,
        "скидка": 15,
        "скидки": 15,
        "акция": 20,
        "распродажа": 20,
        "предложение": 10,
        "товар": 10,
        "услуги": 10,
        "сотрудничество": 15,
        "доход": 15,
        "прибыль": 15,

        # English
        "for sale": 20,
        "buy": 15,
        "order": 15,
        "purchase": 15,
        "price": 10,
        "discount": 15,
        "sale": 15,
        "offer": 10,
        "deal": 10,
        "promotion": 15,
        "product": 10,
        "service": 10,
        "services": 10,
        "partnership": 15,
        "income": 15,
    }

    # 3. Call to Action terms (CTA / Harakatga chaqirish) (15-20 points)
    CTA_TERMS: Dict[str, int] = {
        # Uzbek
        "murojaat qiling": 20,
        "murojaat uchun": 20,
        "bog'laning": 20,
        "boglaning": 20,
        "bizga yozing": 20,
        "yozing": 10,
        "hoziroq": 15,
        "buyurtma uchun": 20,
        "batafsil ma'lumot": 20,
        "batafsil malumot": 20,
        "batafsil": 10,
        "link orqali": 20,
        "havola orqali": 20,
        "qo'shiling": 15,
        "qoshiling": 15,

        # Russian
        "пишите": 10,
        "напишите нам": 20,
        "обращайтесь": 20,
        "звоните": 15,
        "подробнее": 10,
        "подробности": 10,
        "переходите": 15,
        "по ссылке": 20,
        "присоединяйтесь": 15,

        # English
        "contact us": 20,
        "contact me": 20,
        "message us": 20,
        "dm me": 20,
        "dm us": 20,
        "learn more": 15,
        "click here": 20,
        "click the link": 20,
        "visit": 10,
    }

    # 4. Contact Indicators (Kontakt) (10-15 points)
    CONTACT_TERMS: Dict[str, int] = {
        # Uzbek
        "admin": 10,
        "administrator": 10,
        "menejer": 10,
        "manager": 10,
        "operator": 10,
        "telefon": 10,
        "tel": 5,
        "lichka": 15,
        "shaxsiy xabar": 15,
        "telegram": 10,
        "instagram": 10,
        "whatsapp": 10,

        # Russian
        "админ": 10,
        "администратор": 10,
        "менеджер": 10,
        "оператор": 10,
        "телефон": 10,
        "тел": 5,
        "в личку": 15,
        "лс": 15,
        "личные сообщения": 15,

        # English
        "admin": 10,
        "administrator": 10,
        "manager": 10,
        "operator": 10,
        "phone": 10,
        "whatsapp": 10,
        "telegram": 10,
        "dm": 15,
        "pm": 15,
    }

    URL_SCORE = 40
    PHONE_SCORE = 15
    MENTION_SCORE = 20
    DEFAULT_THRESHOLD = 40

    @classmethod
    def get_message_content_and_type(cls, message: Message) -> tuple[str, str]:
        """Extracts text or caption and identifies message content type."""
        msg_type = "TEXT"
        raw_text = ""

        if message.text:
            raw_text = message.text
            msg_type = "TEXT"
        elif message.caption:
            raw_text = message.caption
            if message.photo:
                msg_type = "PHOTO"
            elif message.video:
                msg_type = "VIDEO"
            elif message.document:
                msg_type = "DOCUMENT"
            elif message.animation:
                msg_type = "ANIMATION"
            elif message.audio:
                msg_type = "AUDIO"
            elif message.voice:
                msg_type = "VOICE"
            elif message.video_note:
                msg_type = "VIDEO_NOTE"
        else:
            if message.photo:
                msg_type = "PHOTO"
            elif message.video:
                msg_type = "VIDEO"
            elif message.document:
                msg_type = "DOCUMENT"
            elif message.animation:
                msg_type = "ANIMATION"
            elif message.audio:
                msg_type = "AUDIO"
            elif message.voice:
                msg_type = "VOICE"
            elif message.video_note:
                msg_type = "VIDEO_NOTE"
            elif message.sticker:
                msg_type = "STICKER"

        return raw_text, msg_type

    @classmethod
    def extract_entity_links_and_mentions(cls, message: Message) -> tuple[List[str], List[str]]:
        """Extracts links and mentions directly from Telegram message entities."""
        links: Set[str] = set()
        mentions: Set[str] = set()

        entities = message.entities or message.caption_entities or []
        text = message.text or message.caption or ""

        for entity in entities:
            if entity.type == MessageEntityType.URL:
                url_text = text[entity.offset: entity.offset + entity.length]
                links.add(url_text)
            elif entity.type == MessageEntityType.TEXT_LINK:
                if entity.url:
                    links.add(entity.url)
            elif entity.type == MessageEntityType.MENTION:
                mention_text = text[entity.offset: entity.offset + entity.length]
                mentions.add(mention_text)

        return list(links), list(mentions)

    @classmethod
    def analyze_message(
        cls,
        message: Message,
        whitelist_domains: Optional[List[str]] = None,
        blacklist_words: Optional[Set[str]] = None,
        blacklist_domains: Optional[Set[str]] = None,
        blacklist_usernames: Optional[Set[str]] = None,
        threshold: int = DEFAULT_THRESHOLD
    ) -> Dict[str, Any]:
        """
        Analyzes a Telegram message for commercial advertisements using
        multi-factor scoring and category combinations.
        """
        whitelist_domains = whitelist_domains or []
        blacklist_words = blacklist_words or set()
        blacklist_domains = blacklist_domains or set()
        blacklist_usernames = blacklist_usernames or set()

        raw_text, msg_type = cls.get_message_content_and_type(message)
        normalized = normalize_text(raw_text)
        latin_text = cyrillic_to_latin(normalized)

        score = 0
        reasons: List[str] = []

        # 1. Extract Links from regex + Telegram Entities
        regex_links = extract_links(normalized)
        entity_links, entity_mentions = cls.extract_entity_links_and_mentions(message)
        all_links = list(set(regex_links + entity_links))

        # 2. Extract Mentions and Phones
        regex_mentions = extract_mentions(normalized)
        all_mentions = list(set(regex_mentions + entity_mentions))
        phones = extract_phone_numbers(normalized)

        # -------------------------------------------------------------
        # STEP 1: BLACKLIST CHECKS (Immediate 100-score Ad flag)
        # -------------------------------------------------------------
        for bl_word in blacklist_words:
            if not bl_word:
                continue
            bl_clean = cyrillic_to_latin(normalize_text(bl_word)).lower()
            pattern = re.compile(rf'\b{re.escape(bl_clean)}\b', re.IGNORECASE)
            if pattern.search(latin_text):
                return {
                    "is_ad": True,
                    "score": 100,
                    "reasons": [f"blacklist_word: {bl_word}"],
                    "links": all_links,
                    "phones": phones,
                    "mentions": all_mentions,
                    "message_type": msg_type
                }

        for link in all_links:
            dom = extract_domain(link)
            if dom in blacklist_domains:
                return {
                    "is_ad": True,
                    "score": 100,
                    "reasons": [f"blacklist_domain: {dom}"],
                    "links": all_links,
                    "phones": phones,
                    "mentions": all_mentions,
                    "message_type": msg_type
                }

        for mention in all_mentions:
            u_name = mention.lstrip("@").lower()
            if u_name in blacklist_usernames:
                return {
                    "is_ad": True,
                    "score": 100,
                    "reasons": [f"blacklist_username: @{u_name}"],
                    "links": all_links,
                    "phones": phones,
                    "mentions": all_mentions,
                    "message_type": msg_type
                }

        # -------------------------------------------------------------
        # STEP 2: LINK SCORING WITH WHITELIST FILTER
        # -------------------------------------------------------------
        non_whitelisted_links = []
        for link in all_links:
            if not is_domain_whitelisted(link, whitelist_domains):
                non_whitelisted_links.append(link)

        has_url = bool(non_whitelisted_links)
        if has_url:
            score += cls.URL_SCORE
            reasons.append("external_url")

        # -------------------------------------------------------------
        # STEP 3: MENTIONS & TELEGRAM CHANNELS SCORING
        # -------------------------------------------------------------
        has_mention = bool(all_mentions)
        if has_mention:
            score += cls.MENTION_SCORE
            reasons.append("telegram_mention")

        # -------------------------------------------------------------
        # STEP 4: PHONE NUMBER SCORING
        # -------------------------------------------------------------
        has_phone = bool(phones)
        if has_phone:
            score += cls.PHONE_SCORE
            reasons.append("phone_number")

        # -------------------------------------------------------------
        # STEP 5: CATEGORIZED KEYWORDS INSPECTION
        # -------------------------------------------------------------
        found_high_impact: Set[str] = set()
        found_sales: Set[str] = set()
        found_cta: Set[str] = set()
        found_contact: Set[str] = set()

        # A. High Impact Phrases
        for phrase, weight in cls.HIGH_IMPACT_PHRASES.items():
            phrase_clean = cyrillic_to_latin(phrase).lower()
            pattern = re.compile(rf'\b{re.escape(phrase_clean)}\b', re.IGNORECASE)
            if pattern.search(latin_text):
                score += weight
                found_high_impact.add(phrase)

        # B. Sales Terms
        for term, weight in cls.SALES_TERMS.items():
            term_clean = cyrillic_to_latin(term).lower()
            pattern = re.compile(rf'\b{re.escape(term_clean)}\b', re.IGNORECASE)
            if pattern.search(latin_text):
                score += weight
                found_sales.add(term)

        # C. CTA Terms
        for term, weight in cls.CTA_TERMS.items():
            term_clean = cyrillic_to_latin(term).lower()
            pattern = re.compile(rf'\b{re.escape(term_clean)}\b', re.IGNORECASE)
            if pattern.search(latin_text):
                score += weight
                found_cta.add(term)

        # D. Contact Terms
        for term, weight in cls.CONTACT_TERMS.items():
            term_clean = cyrillic_to_latin(term).lower()
            pattern = re.compile(rf'\b{re.escape(term_clean)}\b', re.IGNORECASE)
            if pattern.search(latin_text):
                score += weight
                found_contact.add(term)

        # E. Numerical Discount & Price Patterns
        discount_pattern = re.compile(r'\b\d+\s*%\s*(chegirma|skidka|skidk|off|discount|aksiya|aktsiya|sale)\b', re.IGNORECASE)
        has_discount_percent = bool(discount_pattern.search(latin_text))
        if has_discount_percent:
            score += 25
            reasons.append("discount_percentage_pattern")

        all_detected_kws = found_high_impact | found_sales | found_cta | found_contact
        if all_detected_kws:
            reasons.append(f"keywords: {', '.join(sorted(all_detected_kws))}")

        # -------------------------------------------------------------
        # STEP 6: MULTI-FACTOR COMBINATION SYNERGY (Kombinatsiyalar)
        # -------------------------------------------------------------
        has_sales = bool(found_sales or found_high_impact or has_discount_percent)
        has_cta = bool(found_cta)
        has_contact = bool(found_contact or has_phone or has_mention)

        # Combination 1: (Sales + CTA)
        if has_sales and has_cta:
            score += 20
            reasons.append("combo_sales_and_cta")

        # Combination 2: (Sales + Direct Link or Contact)
        if has_sales and (has_url or has_contact):
            score += 20
            reasons.append("combo_sales_and_contact")

        # Combination 3: (CTA + Direct Link or Phone)
        if has_cta and (has_url or has_phone):
            score += 20
            reasons.append("combo_cta_and_link")

        # -------------------------------------------------------------
        # STEP 7: FALSE POSITIVE SAFEGUARDS
        # -------------------------------------------------------------
        # If message only has a whitelisted link with zero commercial keywords -> reset score
        if all_links and not non_whitelisted_links and not all_detected_kws and not phones:
            score = 0
            reasons.clear()

        # If message is just a simple innocent question with 1 weak keyword ("soat", "telefonim")
        if not non_whitelisted_links and not phones and not has_cta and len(found_sales) <= 1 and score < threshold:
            pass  # Remains below threshold safely

        is_ad = score >= threshold

        return {
            "is_ad": is_ad,
            "score": score,
            "reasons": reasons,
            "links": all_links,
            "phones": phones,
            "mentions": all_mentions,
            "message_type": msg_type
        }
