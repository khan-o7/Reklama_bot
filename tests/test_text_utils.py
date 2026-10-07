import pytest
from app.utils.text_utils import cyrillic_to_latin, normalize_text, extract_phone_numbers, extract_mentions


def test_cyrillic_to_latin():
    assert cyrillic_to_latin("сотилади") == "sotiladi"
    assert cyrillic_to_latin("акция") == "aksiya"
    assert cyrillic_to_latin("канал") == "kanal"
    assert cyrillic_to_latin("реклама") == "reklama"


def test_extract_phone_numbers():
    text = "Murojaat uchun: +998 90 123 45 67 yoki 998935554433"
    phones = extract_phone_numbers(text)
    assert len(phones) >= 1


def test_extract_mentions():
    text = "Savollar bo'lsa @admin_support yoki @test_channel ga yozing"
    mentions = extract_mentions(text)
    assert "@admin_support" in mentions
    assert "@test_channel" in mentions
