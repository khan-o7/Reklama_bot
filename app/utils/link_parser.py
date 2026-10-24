import ipaddress
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


def is_private_ip(domain_or_ip: str) -> bool:
    """
    Checks if the host is a private/local IPv4/IPv6 address (RFC 1918, loopback, link-local).
    E.g., 192.168.x.x, 10.x.x.x, 172.16-31.x.x, 127.0.0.1, localhost.
    """
    if not domain_or_ip:
        return False
    if domain_or_ip.lower() == "localhost":
        return True
    try:
        ip = ipaddress.ip_address(domain_or_ip)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def extract_domain(url: str) -> str:
    """Extracts lowercase normalized domain from a URL or network path."""
    if not url:
        return ""
    # Normalize backslashes for Windows UNC / intranet paths (e.g. \\192.168.1.1\share)
    clean_url = url.replace("\\", "/").strip()
    if clean_url.startswith("//"):
        clean_url = clean_url.lstrip("/")
    if not clean_url.startswith(("http://", "https://", "ftp://")):
        clean_url = "http://" + clean_url
    try:
        parsed = urlparse(clean_url)
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
    Checks if a URL belongs to a whitelisted domain, its subdomains, or a private/internal LAN IP.
    Example: 'my.gov.uz' matches 'gov.uz', '192.168.224.209' is internal private network.
    """
    domain = extract_domain(url)
    if not domain:
        return False

    # Automatically whitelist private intranet and local network addresses
    if is_private_ip(domain):
        return True

    for allowed in whitelist_domains:
        allowed = allowed.strip().lower()
        if allowed.startswith("www."):
            allowed = allowed[4:]
        if not allowed:
            continue
        if domain == allowed or domain.endswith("." + allowed):
            return True
    return False
