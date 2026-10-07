import re
from typing import List, Set
from urllib.parse import urlparse

# Regular expression matching general URLs, t.me links, telegram links, instagram, wa.me, etc.
URL_REGEX = re.compile(
    r'(?i)\b((?:https?://|ftp://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))\)|[^\s`!()\[\]{};:\'\".,<>?«»“”‘’]))'
)

# Telegram specific links: t.me/xxx, telegram.me/xxx
TELEGRAM_LINK_REGEX = re.compile(
    r'(?i)\b(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me|telegram\.dog)/([a-zA-Z0-9_+]{3,})\b'
)


def extract_links(text: str) -> List[str]:
    """Extracts all URLs and Telegram links from text via regex."""
    if not text:
        return []
    links: Set[str] = set()

    for match in URL_REGEX.finditer(text):
        url = match.group(0).strip(".,!?:;\"'()[]{}")
        # Ensure schema
        if not url.startswith(("http://", "https://", "ftp://")):
            url_with_scheme = "http://" + url
        else:
            url_with_scheme = url
        links.add(url_with_scheme)

    for match in TELEGRAM_LINK_REGEX.finditer(text):
        tg_url = match.group(0)
        if not tg_url.startswith(("http://", "https://")):
            tg_url = "https://" + tg_url
        links.add(tg_url)

    return list(links)


def extract_domain(url: str) -> str:
    """Extracts lowercase normalized domain from a URL."""
    if not url:
        return ""
    if not url.startswith(("http://", "https://", "ftp://")):
        url = "http://" + url
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove port if present
        if ":" in domain:
            domain = domain.split(":")[0]
        # Remove leading www.
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def is_domain_whitelisted(url: str, whitelist_domains: List[str]) -> bool:
    """
    Checks if a URL belongs to a whitelisted domain or its subdomains.
    Example: 'my.gov.uz' matches 'gov.uz'.
    """
    domain = extract_domain(url)
    if not domain:
        return False

    for allowed in whitelist_domains:
        allowed = allowed.strip().lower()
        if allowed.startswith("www."):
            allowed = allowed[4:]
        if not allowed:
            continue
        if domain == allowed or domain.endswith("." + allowed):
            return True
    return False
