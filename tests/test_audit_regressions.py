import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from aiogram.types import Message, Chat, User, PhotoSize

from app.services.content_extractor import ContentExtractor
from app.services.advertisement_detector import AdvertisementDetector


def make_mock_message(
    text: str = "",
    caption: str = "",
    is_photo: bool = False,
    chat_type: str = "supergroup",
    chat_id: int = -1001234567890,
    message_id: int = 101,
    user_id: int = 999001,
    is_edited: bool = False
) -> Message:
    msg = MagicMock(spec=Message)
    msg.message_id = message_id
    msg.text = text if text else None
    msg.caption = caption if caption else None
    msg.entities = []
    msg.caption_entities = []

    chat = MagicMock(spec=Chat)
    chat.id = chat_id
    chat.type = chat_type
    chat.title = "Test Chat"
    chat.username = "testchat"
    msg.chat = chat

    if chat_type == "channel":
        msg.from_user = None
        sender_chat = MagicMock(spec=Chat)
        sender_chat.id = chat_id
        sender_chat.title = "Test Channel"
        msg.sender_chat = sender_chat
    else:
        user = MagicMock(spec=User)
        user.id = user_id
        user.username = "testuser"
        user.first_name = "Test"
        user.last_name = "User"
        user.full_name = "Test User"
        user.is_bot = False
        msg.from_user = user
        msg.sender_chat = None

    if is_photo:
        p1 = MagicMock(spec=PhotoSize)
        p1.file_id = f"photo_file_{message_id}_small"
        p2 = MagicMock(spec=PhotoSize)
        p2.file_id = f"photo_file_{message_id}_large"
        msg.photo = [p1, p2]
    else:
        msg.photo = None

    msg.video = None
    msg.document = None
    msg.animation = None
    msg.audio = None
    msg.voice = None
    msg.video_note = None
    msg.sticker = None

    msg.edit_date = datetime.now(timezone.utc) if is_edited else None
    return msg


@pytest.fixture(autouse=True)
def clean_extractor_cache():
    ContentExtractor.clear_cache()
    yield
    ContentExtractor.clear_cache()


# --------------------------------------------------------------------------
# 1. Oddiy text -> reklama emas
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_01_plain_text_not_ad():
    msg = make_mock_message(text="Salom do'stlar, ertaga dars soat nechada boshlanadi?")
    content = await ContentExtractor.extract_message_content(msg, update_type="message")

    assert content["has_photo"] is False
    assert content["is_edited"] is False
    assert content["combined_text"] == "Salom do'stlar, ertaga dars soat nechada boshlanadi?"

    analysis = AdvertisementDetector.analyze_message(msg, custom_text=content["combined_text"])
    assert analysis["is_ad"] is False
    assert analysis["score"] < 40


# --------------------------------------------------------------------------
# 2. Oddiy text -> reklama
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_02_plain_text_ad():
    msg = make_mock_message(text="🔥 Yangi aksiya! 50% chegirma bilan mahsulot sotiladi. Buyurtma berish uchun @shop_admin ga yozing!")
    content = await ContentExtractor.extract_message_content(msg, update_type="message")

    analysis = AdvertisementDetector.analyze_message(msg, custom_text=content["combined_text"])
    assert analysis["is_ad"] is True
    assert analysis["score"] >= 40
    assert len(analysis["matched_keywords"]) > 0


# --------------------------------------------------------------------------
# 3. Photo -> caption yo'q
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_03_photo_no_caption():
    msg = make_mock_message(is_photo=True, caption="")
    content = await ContentExtractor.extract_message_content(msg, ocr_override="", update_type="message")

    assert content["has_photo"] is True
    assert content["caption"] == ""
    assert content["ocr_text"] == ""
    assert content["combined_text"] == ""


# --------------------------------------------------------------------------
# 4. Photo + oddiy caption
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_04_photo_normal_caption():
    msg = make_mock_message(is_photo=True, caption="Tog'dagi go'zal tabiat manzarasi")
    content = await ContentExtractor.extract_message_content(msg, ocr_override="", update_type="message")

    assert content["has_photo"] is True
    assert content["caption"] == "Tog'dagi go'zal tabiat manzarasi"
    assert content["combined_text"] == "Tog'dagi go'zal tabiat manzarasi"

    analysis = AdvertisementDetector.analyze_message(msg, custom_text=content["combined_text"])
    assert analysis["is_ad"] is False


# --------------------------------------------------------------------------
# 5. Photo + reklama caption
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_05_photo_ad_caption():
    msg = make_mock_message(is_photo=True, caption="🔥 Yangi mahsulot sotiladi! Buyurtma uchun lichkaga yozing @admin_shop")
    content = await ContentExtractor.extract_message_content(msg, ocr_override="", update_type="message")

    assert content["has_photo"] is True
    assert "sotiladi" in content["combined_text"]

    analysis = AdvertisementDetector.analyze_message(msg, custom_text=content["combined_text"])
    assert analysis["is_ad"] is True
    assert analysis["score"] >= 40


# --------------------------------------------------------------------------
# 6. Photo + OCR reklama
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_06_photo_ocr_ad():
    msg = make_mock_message(is_photo=True, caption="")
    # Image itself has advertising text recognized by OCR
    ocr_text = "50% CHEGIRMA! Barcha mahsulotlar arzon narxda sotiladi. Tel: +998901234567"
    content = await ContentExtractor.extract_message_content(msg, ocr_override=ocr_text, update_type="message")

    assert content["has_photo"] is True
    assert content["ocr_text"] == ocr_text
    assert "CHEGIRMA" in content["combined_text"]

    analysis = AdvertisementDetector.analyze_message(msg, custom_text=content["combined_text"])
    assert analysis["is_ad"] is True
    assert analysis["score"] >= 40


# --------------------------------------------------------------------------
# 7. Photo + OCR reklama + caption reklama
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_07_photo_ocr_ad_and_caption_ad():
    msg = make_mock_message(is_photo=True, caption="Buyurtma uchun hoziroq bog'laning: @fast_order_bot")
    ocr_text = "70% AKSIYA NARXIDA MAHSULOTLAR SOTILADI"
    content = await ContentExtractor.extract_message_content(msg, ocr_override=ocr_text, update_type="message")

    assert "Buyurtma uchun" in content["combined_text"]
    assert "AKSIYA" in content["combined_text"]

    analysis = AdvertisementDetector.analyze_message(msg, custom_text=content["combined_text"])
    assert analysis["is_ad"] is True
    assert analysis["score"] >= 60


# --------------------------------------------------------------------------
# 8. Text edit -> reklama bo'lmagan holat
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_08_text_edit_not_ad():
    # 1st version
    msg1 = make_mock_message(message_id=201, text="Salom barchaga", is_edited=False)
    content1 = await ContentExtractor.extract_message_content(msg1, update_type="message")
    assert content1["is_duplicate"] is False

    # 2nd version (edited harmless text)
    msg2 = make_mock_message(message_id=201, text="Salom hammaga, bugun havo juda yaxshi", is_edited=True)
    content2 = await ContentExtractor.extract_message_content(msg2, is_edited=True, update_type="edited_message")
    assert content2["is_duplicate"] is False
    assert content2["is_edited"] is True

    analysis = AdvertisementDetector.analyze_message(msg2, custom_text=content2["combined_text"])
    assert analysis["is_ad"] is False


# --------------------------------------------------------------------------
# 9. Text edit -> reklama holatiga o'tish
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_09_text_edit_becomes_ad():
    # Step 1: User sends innocent message
    msg1 = make_mock_message(message_id=202, text="Ertaga uchrashuv bo'ladimi?", is_edited=False)
    content1 = await ContentExtractor.extract_message_content(msg1, update_type="message")
    analysis1 = AdvertisementDetector.analyze_message(msg1, custom_text=content1["combined_text"])
    assert analysis1["is_ad"] is False

    # Step 2: User sneaks in an advertisement by editing the message
    msg2 = make_mock_message(
        message_id=202,
        text="🔥 DIQQAT! Sifatli kiyimlar sotiladi. Zakaz bering: @moda_admin yoki +998901234567",
        is_edited=True
    )
    content2 = await ContentExtractor.extract_message_content(msg2, is_edited=True, update_type="edited_message")
    assert content2["is_duplicate"] is False
    assert content2["is_edited"] is True

    analysis2 = AdvertisementDetector.analyze_message(msg2, custom_text=content2["combined_text"])
    assert analysis2["is_ad"] is True
    assert analysis2["score"] >= 40


# --------------------------------------------------------------------------
# 10. Text edit -> reklamadan oddiy matnga o'tish
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_10_text_edit_ad_becomes_normal_text():
    # Step 1: Advertisement
    msg1 = make_mock_message(message_id=203, text="Kanalimizga obuna bo'ling: https://t.me/kanal reklama", is_edited=False)
    content1 = await ContentExtractor.extract_message_content(msg1, update_type="message")
    analysis1 = AdvertisementDetector.analyze_message(msg1, custom_text=content1["combined_text"])
    assert analysis1["is_ad"] is True

    # Step 2: User removes the ad content
    msg2 = make_mock_message(message_id=203, text="Kechirasiz adashib yozibman, hammaga xayrli kun", is_edited=True)
    content2 = await ContentExtractor.extract_message_content(msg2, is_edited=True, update_type="edited_message")
    assert content2["is_duplicate"] is False

    analysis2 = AdvertisementDetector.analyze_message(msg2, custom_text=content2["combined_text"])
    assert analysis2["is_ad"] is False


# --------------------------------------------------------------------------
# 11. Photo caption edit -> reklama bo'lmagan holat
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_11_photo_caption_edit_not_ad():
    msg1 = make_mock_message(message_id=301, is_photo=True, caption="Do'stlar bilan sayohat", is_edited=False)
    content1 = await ContentExtractor.extract_message_content(msg1, ocr_override="", update_type="message")
    assert content1["is_duplicate"] is False

    msg2 = make_mock_message(message_id=301, is_photo=True, caption="Toshkent viloyatida sayohat", is_edited=True)
    content2 = await ContentExtractor.extract_message_content(msg2, is_edited=True, ocr_override="", update_type="edited_message")
    assert content2["is_duplicate"] is False

    analysis = AdvertisementDetector.analyze_message(msg2, custom_text=content2["combined_text"])
    assert analysis["is_ad"] is False


# --------------------------------------------------------------------------
# 12. Photo caption edit -> reklama holatiga o'tish
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_12_photo_caption_edit_becomes_ad():
    # Innocent photo caption initially
    msg1 = make_mock_message(message_id=302, is_photo=True, caption="Chiroyli soat rasmi", is_edited=False)
    content1 = await ContentExtractor.extract_message_content(msg1, ocr_override="", update_type="message")
    analysis1 = AdvertisementDetector.analyze_message(msg1, custom_text=content1["combined_text"])
    assert analysis1["is_ad"] is False

    # Sneaky caption edit into advertisement
    msg2 = make_mock_message(
        message_id=302,
        is_photo=True,
        caption="🔥 Asl shveytsariya soatlari sotiladi! Narxi arzon, buyurtma uchun yozing: @watch_shop",
        is_edited=True
    )
    content2 = await ContentExtractor.extract_message_content(msg2, is_edited=True, ocr_override="", update_type="edited_message")
    assert content2["is_duplicate"] is False
    assert content2["is_edited"] is True

    analysis2 = AdvertisementDetector.analyze_message(msg2, custom_text=content2["combined_text"])
    assert analysis2["is_ad"] is True
    assert analysis2["score"] >= 40


# --------------------------------------------------------------------------
# 13. Channel post
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_13_channel_post():
    msg = make_mock_message(
        chat_type="channel",
        chat_id=-1009876543210,
        text="Kanalimizda reklama joylashtirish narxi: 100 000 so'm. Admin: @reklama_menejer"
    )
    content = await ContentExtractor.extract_message_content(msg, update_type="channel_post")

    assert content["update_type"] == "channel_post"
    assert content["user_id"] == -1009876543210

    analysis = AdvertisementDetector.analyze_message(msg, custom_text=content["combined_text"])
    assert analysis["is_ad"] is True
    assert analysis["score"] >= 40


# --------------------------------------------------------------------------
# 14. Edited channel post
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_14_edited_channel_post():
    msg1 = make_mock_message(
        message_id=401,
        chat_type="channel",
        chat_id=-1009876543210,
        text="Bugungi rasmiy yangiliklar kanali",
        is_edited=False
    )
    content1 = await ContentExtractor.extract_message_content(msg1, update_type="channel_post")
    analysis1 = AdvertisementDetector.analyze_message(msg1, custom_text=content1["combined_text"])
    assert analysis1["is_ad"] is False

    # Channel post edited into promotional channel ad
    msg2 = make_mock_message(
        message_id=401,
        chat_type="channel",
        chat_id=-1009876543210,
        text="🔥 Yangi kanalimizga obuna bo'ling va pul ishlang: https://t.me/crypto_invest daromad",
        is_edited=True
    )
    content2 = await ContentExtractor.extract_message_content(msg2, is_edited=True, update_type="edited_channel_post")
    assert content2["is_duplicate"] is False
    assert content2["update_type"] == "edited_channel_post"

    analysis2 = AdvertisementDetector.analyze_message(msg2, custom_text=content2["combined_text"])
    assert analysis2["is_ad"] is True
    assert analysis2["score"] >= 40
