import pytest
from unittest.mock import MagicMock
from aiogram.types import Message, Chat, User, MessageEntity
from aiogram.enums import MessageEntityType
from app.services.advertisement_detector import AdvertisementDetector


def create_mock_message(
    text: str = None,
    caption: str = None,
    entities: list = None,
    caption_entities: list = None,
    is_photo: bool = False
) -> Message:
    msg = MagicMock(spec=Message)
    msg.text = text
    msg.caption = caption
    msg.entities = entities or []
    msg.caption_entities = caption_entities or []
    msg.photo = [MagicMock()] if is_photo else None
    msg.video = None
    msg.document = None
    msg.animation = None
    msg.audio = None
    msg.voice = None
    msg.video_note = None
    msg.sticker = None
    msg.chat = MagicMock(spec=Chat, id=-100123456789, title="Test Group")
    msg.from_user = MagicMock(spec=User, id=987654321, first_name="Ali", username="ali_uz")
    return msg


def test_url_detection():
    msg = create_mock_message(text="Ajoyib mahsulotlar https://super-shop.com saytida!")
    res = AdvertisementDetector.analyze_message(msg)
    assert res["is_ad"] is True
    assert res["score"] >= 40
    assert "external_url" in res["reasons"]
    assert any("super-shop.com" in l for l in res["links"])


def test_keyword_detection():
    # Uzbek Cyrillic keywords: сотилади (+20) + акция (+20) = 40 points
    msg = create_mock_message(text="Telefonlar сотилади! Yangi акция boshlandi!")
    res = AdvertisementDetector.analyze_message(msg)
    assert res["is_ad"] is True
    assert res["score"] >= 40
    assert any("keywords" in r for r in res["reasons"])


def test_phone_detection():
    # Phone (+15) + "zakaz" (+15) + "sotiladi" (+20) = 50 points
    msg = create_mock_message(text="Zakaz uchun sotiladi telefon: +998 90 123 45 67")
    res = AdvertisementDetector.analyze_message(msg)
    assert res["is_ad"] is True
    assert res["score"] >= 40
    assert "phone_number" in res["reasons"]


def test_whitelist():
    # Whitelisted domain (gov.uz)
    msg = create_mock_message(text="Mana rasmiy davlat portali: https://my.gov.uz")
    whitelist = ["gov.uz", "edu.uz"]
    res = AdvertisementDetector.analyze_message(msg, whitelist_domains=whitelist)
    # Whitelisted url gives 0 points and false positive mitigation ensures is_ad is False
    assert res["is_ad"] is False
    assert res["score"] < 40


def test_blacklist():
    # Normal looking message containing blacklisted word
    msg = create_mock_message(text="Salom hammaga, bugun 1xbet haqida gaplashamiz")
    blacklist_words = {"1xbet"}
    res = AdvertisementDetector.analyze_message(msg, blacklist_words=blacklist_words)
    assert res["is_ad"] is True
    assert res["score"] == 100
    assert any("blacklist_word" in r for r in res["reasons"])


def test_score():
    # Composite score: "reklama" (+40) -> immediately reaches threshold
    msg = create_mock_message(text="Kanalimizda yangi reklama berildi")
    res = AdvertisementDetector.analyze_message(msg)
    assert res["score"] >= 40
    assert res["is_ad"] is True


def test_false_positive():
    whitelist = ["gov.uz", "edu.uz"]

    # 1. "Bugun gov.uz saytidan ma'lumot oldim"
    msg1 = create_mock_message(text="Bugun gov.uz saytidan ma'lumot oldim")
    res1 = AdvertisementDetector.analyze_message(msg1, whitelist_domains=whitelist)
    assert res1["is_ad"] is False

    # 2. "Mana universitet sayti https://edu.uz"
    msg2 = create_mock_message(text="Mana universitet sayti https://edu.uz")
    res2 = AdvertisementDetector.analyze_message(msg2, whitelist_domains=whitelist)
    assert res2["is_ad"] is False

    # 3. "Telefonim buzilib qoldi"
    msg3 = create_mock_message(text="Telefonim buzilib qoldi, usta bormi?")
    res3 = AdvertisementDetector.analyze_message(msg3)
    assert res3["is_ad"] is False

    # 4. "Bugun soat 18:00 da yig‘ilish"
    msg4 = create_mock_message(text="Bugun soat 18:00 da yig‘ilish bo‘ladi")
    res4 = AdvertisementDetector.analyze_message(msg4)
    assert res4["is_ad"] is False


def test_media_caption_detection():
    # Photo with commercial caption
    caption = "Telefonlar sotiladi. Narxi 2 000 000 so‘m. Murojaat uchun: +998 90 123 45 67"
    msg = create_mock_message(caption=caption, is_photo=True)
    res = AdvertisementDetector.analyze_message(msg)
    assert res["is_ad"] is True
    assert res["message_type"] == "PHOTO"
    assert res["score"] >= 40


def test_russian_ad_detection():
    # Russian commercial message: скидки (+15) + пишите нам (+20) + combo (+20) = 55
    msg = create_mock_message(text="Большие скидки на все товары! Напишите нам в личку для заказа.")
    res = AdvertisementDetector.analyze_message(msg)
    assert res["is_ad"] is True
    assert res["score"] >= 40


def test_english_ad_detection():
    # English commercial message: special offer (+30) + order now (+30) = 60
    msg = create_mock_message(text="Special offer! Order now and get a great discount.")
    res = AdvertisementDetector.analyze_message(msg)
    assert res["is_ad"] is True
    assert res["score"] >= 40


def test_combination_vs_casual():
    # 1. Casual: "Bugun chegirma bor" (single sales term, no CTA, no contact, no URL) -> not an ad
    msg_casual = create_mock_message(text="Bugun do‘konda chegirma bor ekan")
    res_casual = AdvertisementDetector.analyze_message(msg_casual)
    assert res_casual["is_ad"] is False
    assert res_casual["score"] < 40

    # 2. Strong Combo: "🔥 50% chegirma! Hoziroq buyurtma bering. Batafsil: https://t.me/kanal"
    msg_combo = create_mock_message(text="🔥 50% chegirma! Hoziroq buyurtma bering. Batafsil: https://t.me/kanal")
    res_combo = AdvertisementDetector.analyze_message(msg_combo)
    assert res_combo["is_ad"] is True
    assert res_combo["score"] >= 80


def test_dataset_lexicon_phrases():
    # Test commercial phrase combinations from advertising_keywords.json
    msg1 = create_mock_message(text="Sotuvda mavjud bo'lgan mahsulotlar uchun admin ga murojaat qiling")
    res1 = AdvertisementDetector.analyze_message(msg1)
    assert res1["is_ad"] is True
    assert res1["score"] >= 40

    # Test crypto signal from dataset
    msg2 = create_mock_message(text="Trading signals and guaranteed profit for all crypto users")
    res2 = AdvertisementDetector.analyze_message(msg2)
    assert res2["is_ad"] is True
    assert res2["score"] >= 40

    # Test Cyrillic Uzbek phrase from dataset
    msg3 = create_mock_message(text="Маҳсулот сотамиз, буюртма қилинг ва чегирма билан олинг")
    res3 = AdvertisementDetector.analyze_message(msg3)
    assert res3["is_ad"] is True
    assert res3["score"] >= 40
