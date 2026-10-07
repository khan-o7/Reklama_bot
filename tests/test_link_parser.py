import pytest
from app.utils.link_parser import extract_links, extract_domain, is_domain_whitelisted


def test_extract_links():
    text = "Mana bu sayt https://example.com/test va t.me/mychannel hamda http://market.uz"
    links = extract_links(text)
    assert len(links) >= 3
    assert any("example.com" in l for l in links)
    assert any("t.me" in l for l in links)
    assert any("market.uz" in l for l in links)


def test_extract_domain():
    assert extract_domain("https://sub.gov.uz/path?q=1") == "sub.gov.uz"
    assert extract_domain("http://www.example.com") == "example.com"
    assert extract_domain("t.me/channel") == "t.me"


def test_is_domain_whitelisted():
    whitelist = ["gov.uz", "edu.uz", "customs.uz"]

    assert is_domain_whitelisted("https://my.gov.uz/services", whitelist) is True
    assert is_domain_whitelisted("http://edu.uz", whitelist) is True
    assert is_domain_whitelisted("https://sub.customs.uz/doc", whitelist) is True

    # Non-whitelisted
    assert is_domain_whitelisted("https://1xbet.com", whitelist) is False
    assert is_domain_whitelisted("https://t.me/random_channel", whitelist) is False
