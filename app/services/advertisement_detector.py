import re
from typing import Dict, Any, List, Set, Optional
from aiogram.types import Message
from aiogram.enums import MessageEntityType, ContentType

from app.utils.text_utils import normalize_text, cyrillic_to_latin, extract_phone_numbers, extract_mentions
from app.utils.link_parser import extract_links, extract_domain, is_domain_whitelisted
from app.utils.logger import logger


class AdvertisementDetector:
    """
    Production-grade Advertisement Detection Engine with:
    - Multi-factor scoring system
    - Whitelist & Blacklist integration
    - False-positive mitigation
    - Telegram entities inspection (URL, TEXT_LINK, MENTION)
    - Full Cyrillic and Latin Uzbek/Russian vocabulary support
    """

    # Scoring weights as specified in system requirements
    KEYWORD_WEIGHTS: Dict[str, int] = {
        # High impact
        "reklama": 40,
        "admin bilan bog'laning": 25,
        "admin bilan boglaning": 25,
        "bog'lanish uchun": 20,
        "boglanish uchun": 20,
        "murojaat uchun": 20,
        "obuna bo'ling": 25,
        "obuna boling": 25,
        "kanalimizga obuna": 30,
        "kanalga obuna": 30,
        "obuna": 20,

        # Medium impact commercial terms
        "sotiladi": 20,
        "sotamiz": 20,
        "aksiya": 20,
        "aktsiya": 20,
        "chegirma": 20,
        "skidka": 20,
        "zakaz": 15,
        "buyurtma": 15,
        "dostavka": 15,
        "yetkazib berish": 15,
        "kurs": 15,
        "narx": 10,
        "narxi": 10,
        "murojaat": 10,
        "telefon": 10,
        "kanal": 15,
        "telegram": 15,
        "instagram": 15,
        "so'm": 10,
        "som": 10,
        "dollar": 10,
        "usd": 10,
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
        Analyzes a Telegram message for commercial advertisements.

        Returns:
            {
                "is_ad": bool,
                "score": int,
                "reasons": list[str],
                "links": list[str],
                "phones": list[str],
                "mentions": list[str],
                "message_type": str
            }
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
        # Check blacklisted words
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

        # Check blacklisted domains in extracted links
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

        # Check blacklisted usernames in mentions
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

        if non_whitelisted_links:
            score += cls.URL_SCORE
            reasons.append("external_url")

        # -------------------------------------------------------------
        # STEP 3: MENTIONS & TELEGRAM CHANNELS SCORING
        # -------------------------------------------------------------
        if all_mentions:
            score += cls.MENTION_SCORE
            reasons.append("telegram_mention")

        # -------------------------------------------------------------
        # STEP 4: PHONE NUMBER SCORING
        # -------------------------------------------------------------
        if phones:
            score += cls.PHONE_SCORE
            reasons.append("phone_number")

        # -------------------------------------------------------------
        # STEP 5: KEYWORD SCORING (Phrase & Word boundary checks)
        # -------------------------------------------------------------
        found_keywords: Set[str] = set()
        for kw, kw_weight in cls.KEYWORD_WEIGHTS.items():
            kw_clean = cyrillic_to_latin(kw).lower()
            # For multi-word phrases (e.g. "admin bilan bog'laning")
            if " " in kw_clean:
                pattern = re.compile(rf'\b{re.escape(kw_clean)}\b', re.IGNORECASE)
                if pattern.search(latin_text):
                    score += kw_weight
                    found_keywords.add(kw)
            else:
                # For single words, use regex word boundaries
                pattern = re.compile(rf'\b{re.escape(kw_clean)}\b', re.IGNORECASE)
                if pattern.search(latin_text):
                    score += kw_weight
                    found_keywords.add(kw)

        if found_keywords:
            reasons.append(f"keywords: {', '.join(sorted(found_keywords))}")

        # -------------------------------------------------------------
        # STEP 6: FALSE POSITIVE PREVENTION
        # -------------------------------------------------------------
        # Case A: If message has ONLY whitelisted link and zero commercial keywords -> score 0
        if all_links and not non_whitelisted_links and not found_keywords and not phones:
            score = 0
            reasons.clear()

        # Case B: If message has only a single casual mention without commercial intent -> keep below threshold
        if not non_whitelisted_links and not phones and len(found_keywords) <= 1 and score < threshold:
            pass  # Normal behavior, score remains low

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
