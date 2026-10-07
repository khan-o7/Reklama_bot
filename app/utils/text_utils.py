import re
import unicodedata
from typing import List

# Cyrillic to Latin mapping for Uzbek/Russian character normalization
CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'x', 'ц': 's', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': "'",
    'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya', 'ў': "o'", 'ғ': "g'",
    'ҳ': 'h', 'қ': 'q',
}


def cyrillic_to_latin(text: str) -> str:
    """Converts Uzbek/Russian Cyrillic text to Latin equivalent for uniform keyword matching."""
    res = []
    text_lower = text.lower()
    for char in text_lower:
        if char in CYRILLIC_TO_LATIN:
            res.append(CYRILLIC_TO_LATIN[char])
        else:
            res.append(char)
    return "".join(res)


def normalize_text(text: str) -> str:
    """
    Cleans text by removing zero-width chars, normalizing unicode,
    and collapsing repetitive whitespaces.
    """
    if not text:
        return ""
    # Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", text)
    # Remove hidden / zero-width characters commonly used to evade filters
    normalized = re.sub(r'[\u200B-\u200D\uFEFF\u00A0]', ' ', normalized)
    # Collapse multiple whitespaces
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def extract_phone_numbers(text: str) -> List[str]:
    """
    Detects phone numbers in various formats:
    - Uzbek format: +998901234567, 998 90 123 45 67, 90 123-45-67, etc.
    - International format: +1234567890
    """
    if not text:
        return []

    # Uzbek numbers with or without country code
    uzbek_pattern = re.compile(
        r'(?:(?:\+?998[\s\-_.]?)|\b)(?:\(?\d{2}\)?[\s\-_.]?)\d{3}[\s\-_.]?\d{2}[\s\-_.]?\d{2}\b'
    )
    # Generic international phone numbers with plus sign: +1 234 567 8900
    intl_pattern = re.compile(r'\+\d{1,3}[\s\-_.]?\(?\d{2,4}\)?[\s\-_.]?\d{3,4}[\s\-_.]?\d{3,4}\b')

    found = set()
    for match in uzbek_pattern.finditer(text):
        digits = re.sub(r'\D', '', match.group(0))
        if 9 <= len(digits) <= 12:
            found.add(match.group(0).strip())

    for match in intl_pattern.finditer(text):
        digits = re.sub(r'\D', '', match.group(0))
        if len(digits) >= 10:
            found.add(match.group(0).strip())

    return list(found)


def extract_mentions(text: str) -> List[str]:
    """Extracts Telegram @mentions from text."""
    if not text:
        return []
    pattern = re.compile(r'@[a-zA-Z0-9_]{4,32}\b')
    return list(set(pattern.findall(text)))
