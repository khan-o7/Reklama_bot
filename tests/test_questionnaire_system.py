import pytest
from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config.settings import settings
from app.services.questionnaire.schema import FieldType, QuestionField
from app.services.questionnaire.definitions import get_categories
from app.services.questionnaire.engine import QuestionnaireEngine
from app.services.questionnaire.preview_generator import AdvertisementPreviewGenerator
from app.bot.handlers.questionnaire_handler import get_start_menu_keyboard
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.ad_request_repo import AdvertisingRequestRepository
from app.services.publication_service import PublicationService


@asynccontextmanager
async def get_test_session():
    test_engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await test_engine.dispose()


def test_start_menu_has_exact_7_buttons():
    """Verify Section 4: Start menu displays the exact required 7 inline buttons."""
    kb = get_start_menu_keyboard(is_admin=False)
    assert len(kb.inline_keyboard) == 7

    button_texts = [row[0].text for row in kb.inline_keyboard]
    assert any("ko‘chmas mulk" in t.lower() for t in button_texts)
    assert any("mebel" in t.lower() for t in button_texts)
    assert any("jalyuzi" in t.lower() for t in button_texts)
    assert any("boshqa mahsulotlar" in t.lower() for t in button_texts)
    assert any("mening e’lonlarim" in t.lower() for t in button_texts)
    assert any("tartibi" in t.lower() for t in button_texts)
    assert any("yordam" in t.lower() for t in button_texts)


def test_all_categories_and_subcategories_defined():
    """Verify Sections 6, 7, 8, 9: Categories A, B, C, D and subcategories are defined."""
    cats = get_categories()
    assert "real_estate" in cats
    assert "furniture" in cats
    assert "curtains_blinds" in cats
    assert "electronics_other" in cats

    re_sub = cats["real_estate"].subcategories
    assert "novostroyka" in re_sub
    assert "secondary_apt" in re_sub
    assert "house" in re_sub
    assert "land" in re_sub
    assert "commercial" in re_sub
    assert "rent" in re_sub

    furn_sub = cats["furniture"].subcategories
    assert "sofa" in furn_sub
    assert "bed" in furn_sub
    assert "kitchen" in furn_sub
    assert "custom_furniture" in furn_sub

    curt_sub = cats["curtains_blinds"].subcategories
    assert "vertical_blinds" in curt_sub
    assert "roller_blinds" in curt_sub
    assert "zebra_blinds" in curt_sub
    assert "classic_curtains" in curt_sub

    elec_sub = cats["electronics_other"].subcategories
    expected_11 = [
        "smartphones", "computers", "tv_audio", "home_appliances", "hvac",
        "construction", "tools", "auto_parts", "clothing", "services", "other_goods"
    ]
    for sub_id in expected_11:
        assert sub_id in elec_sub, f"Subcategory {sub_id} must be in electronics_other"
    assert len(elec_sub) == 11
    assert len(cats["electronics_other"].common_fields) == 0, "electronics_other common_fields must be empty for specialized questionnaires"



def test_conditional_fields_logic():
    """Verify conditional fields appear only when their prerequisite answer matches."""
    cats = get_categories()

    # Furniture: 'defects' field condition
    furn_fields = cats["furniture"].common_fields
    defects_field = next(f for f in furn_fields if f.id == "defects")
    assert defects_field.is_applicable({"condition": "Ishlatilgan"}) is True
    assert defects_field.is_applicable({"condition": "Yangi"}) is False

    # Furniture: 'lead_time' field condition
    lead_time_field = next(f for f in furn_fields if f.id == "lead_time")
    assert lead_time_field.is_applicable({"ready_or_custom": "Buyurtma asosida"}) is True
    assert lead_time_field.is_applicable({"ready_or_custom": "Tayyor mahsulot"}) is False

    # Real Estate: Land subcategory does NOT ask apartment floor or rooms
    land_fields = QuestionnaireEngine.get_applicable_fields("real_estate", "land", {})
    land_ids = [f.id for f in land_fields]
    assert "land_area" in land_ids
    assert "land_use" in land_ids
    assert "floor" not in land_ids
    assert "rooms" not in land_ids


def test_validation_rules():
    """Verify QuestionnaireEngine.validate_input for price, phone, integer, decimals, single_select."""
    price_field = QuestionField(
        id="price",
        label="Narx",
        prompt="Narx:",
        field_type=FieldType.PRICE,
        required=True,
        validation_rules={"min": 1000}
    )
    ok, val, err = QuestionnaireEngine.validate_input(price_field, "650 000 000 so'm")
    assert ok is True
    assert val == 650000000

    ok_zero, _, err_zero = QuestionnaireEngine.validate_input(price_field, "0")
    assert ok_zero is False
    assert "noldan katta" in err_zero

    # Phone validation
    phone_field = QuestionField(
        id="phone",
        label="Telefon",
        prompt="Tel:",
        field_type=FieldType.PHONE,
        required=True
    )
    ok_phone, val_phone, _ = QuestionnaireEngine.validate_input(phone_field, "+998 90 123-45-67")
    assert ok_phone is True
    assert val_phone == "+998901234567"

    ok_bad_phone, _, err_bad_phone = QuestionnaireEngine.validate_input(phone_field, "not_a_phone")
    assert ok_bad_phone is False
    assert "noto‘g‘ri" in err_bad_phone

    # Decimal validation
    decimal_field = QuestionField(
        id="area",
        label="Maydon",
        prompt="Maydon:",
        field_type=FieldType.DECIMAL,
        required=True
    )
    ok_dec, val_dec, _ = QuestionnaireEngine.validate_input(decimal_field, "68,75")
    assert ok_dec is True
    assert val_dec == 68.75


def test_back_navigation_and_next_field():
    """Verify Back navigation and Next field calculation without losing progress."""
    answers = {
        "deal_type": "Sotiladi",
        "title": "3 xonali xonadon",
        "city_district": "Toshkent, Mirzo Ulug‘bek"
    }
    next_f, idx, total = QuestionnaireEngine.get_next_field("real_estate", "novostroyka", answers, current_field_id="deal_type")
    assert next_f is not None
    assert next_f.id != "deal_type"

    prev_f = QuestionnaireEngine.get_previous_field("real_estate", "novostroyka", answers, current_field_id="title")
    assert prev_f is not None
    assert prev_f.id == "deal_type"


def test_preview_generator_cleanliness():
    """Verify Section 12: Previews are clean, formatted in Uzbek Latin, with no 'None' or 'null'."""
    re_answers = {
        "deal_type": "Sotiladi",
        "title": "2 xonali novostroyka",
        "complex_name": "Yunusobod Plaza",
        "rooms": "2 xona",
        "total_area": 65.0,
        "floor": 5,
        "total_floors": 12,
        "repair_status": "To‘liq ta’mirlangan",
        "price": 650000000,
        "currency": "so‘m",
        "city_district": "Toshkent, Yunusobod",
        "phone": "+998901234567",
        "description": "Juda shinam va yorug‘ xonadon"
    }
    preview = AdvertisementPreviewGenerator.generate_preview("real_estate", "novostroyka", re_answers)
    assert "None" not in preview
    assert "null" not in preview
    assert "SOTILADI" in preview
    assert "Yunusobod Plaza" in preview
    assert "650 000 000 so‘m" in preview
    assert "+998901234567" in preview


@pytest.mark.asyncio
async def test_request_lifecycle_persistence():
    """Verify PostgreSQL persistence for AdvertisingRequest, answers, media, and state recovery."""
    async with get_test_session() as session:
        # Create user
        user = await UserRepository.get_or_create(
            session=session,
            telegram_id=777888999,
            username="reklama_tester",
            first_name="Jasur"
        )

        # 1. Create request
        req = await AdvertisingRequestRepository.create(
            session=session,
            user_id=user.id,
            category_id="furniture",
            subcategory_id="sofa"
        )
        assert req.id is not None
        assert req.request_number.startswith("REQ-")
        assert req.status == "COLLECTING_INFORMATION"

        # 2. Save answers
        await AdvertisingRequestRepository.save_answer(session, req.id, "title", "Yumshoq divan")
        await AdvertisingRequestRepository.save_answer(session, req.id, "price", 3500000)

        # 3. Add media
        await AdvertisingRequestRepository.add_media(
            session=session,
            request_id=req.id,
            file_id="tg_file_sofa_123",
            media_type="PHOTO"
        )

        # 4. Verify fetch
        ans_dict = await AdvertisingRequestRepository.get_answers_dict(session, req.id)
        assert ans_dict["title"] == "Yumshoq divan"
        assert ans_dict["price"] == 3500000

        media_items = await AdvertisingRequestRepository.get_media_items(session, req.id)
        assert len(media_items) == 1
        assert media_items[0].file_id == "tg_file_sofa_123"

        # 5. Set Price
        await AdvertisingRequestRepository.set_price(
            session=session,
            request_id=req.id,
            price=75000,
            card_number="8600111122223333",
            cardholder="Defender Admin",
            admin_id=5976376745
        )
        reloaded = await AdvertisingRequestRepository.get_by_id(session, req.id)
        assert reloaded.price == 75000
        assert reloaded.status == "AWAITING_PAYMENT"

        # 6. Publish request
        mock_bot = MagicMock()
        mock_sent = MagicMock()
        mock_sent.message_id = 445566
        mock_bot.send_photo = AsyncMock(return_value=mock_sent)

        reloaded.published_chat_id = -1002285646035
        reloaded.preview_text = "Divan sotiladi"
        pub_ok, sent_id, msg = await PublicationService.publish_advertising_request(
            bot=mock_bot,
            session=session,
            req=reloaded
        )
        assert pub_ok is True
        assert sent_id == 445566
        assert reloaded.status == "PUBLISHED"
        assert PublicationService.is_bot_published(-1002285646035, 445566) is True


@pytest.mark.asyncio
async def test_validate_active_request_missing_safe_handling():
    """Verify that validate_active_request handles non-existent request_id without raising ForeignKeyViolationError."""
    from app.bot.handlers.questionnaire_handler import validate_active_request
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey

    storage = MemoryStorage()
    key = StorageKey(bot_id=1, chat_id=123, user_id=123)
    state = FSMContext(storage=storage, key=key)
    # Stale request_id that does not exist in DB
    await state.update_data(request_id=999999, category_id="real_estate", subcategory_id="apartment_sale")

    async with get_test_session() as session:
        mock_cb = MagicMock()
        mock_cb.answer = AsyncMock()
        mock_cb.message = MagicMock()
        mock_cb.message.answer = AsyncMock()

        result = await validate_active_request(session, state, mock_cb)
        assert result is None
        mock_cb.answer.assert_called_once()
        # State should be cleared
        cleared_data = await state.get_data()
        assert "request_id" not in cleared_data


@pytest.mark.asyncio
async def test_album_middleware_grouping():
    """Verify that AlbumMiddleware collects messages with identical media_group_id."""
    from app.bot.middlewares.album_middleware import AlbumMiddleware
    from aiogram.types import Message

    middleware = AlbumMiddleware(latency=0.05)
    handler = AsyncMock(return_value="OK")

    msg1 = MagicMock(spec=Message)
    msg1.media_group_id = "test_group_123"

    msg2 = MagicMock(spec=Message)
    msg2.media_group_id = "test_group_123"

    # Simulate near-simultaneous arrivals
    import asyncio
    async def send_msg2():
        await asyncio.sleep(0.01)
        data2 = {}
        await middleware(handler, msg2, data2)

    data1 = {}
    task = asyncio.create_task(send_msg2())
    res = await middleware(handler, msg1, data1)
    await task

    assert res == "OK"
    handler.assert_called_once()
    passed_data = handler.call_args[0][1]
    assert "album" in passed_data
    assert len(passed_data["album"]) == 2


@pytest.mark.asyncio
async def test_handle_media_answer_with_album():
    """Verify that handle_media_answer saves all media items when an album is received."""
    from app.bot.handlers.questionnaire_handler import handle_media_answer, QuestionnaireStates
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey
    from aiogram.types import PhotoSize

    storage = MemoryStorage()
    key = StorageKey(bot_id=1, chat_id=123, user_id=123)
    state = FSMContext(storage=storage, key=key)

    async with get_test_session() as session:
        # Create user & request
        user = await UserRepository.get_or_create(session, 888777, "photo_user")
        req = await AdvertisingRequestRepository.create(session, user.id, "furniture", "sofa")
        await state.set_state(QuestionnaireStates.answering_questions)
        await state.update_data(request_id=req.id, category_id="furniture", subcategory_id="sofa", current_field_id="media")

        # Create 2 mock messages in an album
        p1 = PhotoSize(file_id="photo_id_1", file_unique_id="u1", width=100, height=100, file_size=5000)
        p2 = PhotoSize(file_id="photo_id_2", file_unique_id="u2", width=100, height=100, file_size=6000)

        msg1 = MagicMock()
        msg1.photo = [p1]
        msg1.video = None
        msg1.caption = "Photo 1"
        msg1.answer = AsyncMock()

        msg2 = MagicMock()
        msg2.photo = [p2]
        msg2.video = None
        msg2.caption = "Photo 2"
        msg2.answer = AsyncMock()

        await handle_media_answer(
            message=msg1,
            state=state,
            session=session,
            album=[msg1, msg2]
        )

        # Check DB
        items = await AdvertisingRequestRepository.get_media_items(session, req.id)
        assert len(items) == 2
        assert items[0].file_id == "photo_id_1"
        assert items[1].file_id == "photo_id_2"

        # Check response
        msg1.answer.assert_called_once()
        sent_text = msg1.answer.call_args[0][0]
        assert "2 ta" in sent_text


@pytest.mark.asyncio
async def test_start_with_ad_deep_link_opens_categories_directly():
    """Verify entering bot with /start ad_... or /start new_ad opens questionnaire categories without price screen."""
    from app.bot.handlers.start import handle_start
    from aiogram.filters import CommandObject

    async with get_test_session() as session:
        user = MagicMock()
        user.id = 777666555
        user.username = "test_advertiser"
        user.first_name = "Advertiser"
        user.last_name = None

        chat = MagicMock()
        chat.id = 777666555
        chat.type = "private"

        message = MagicMock()
        message.from_user = user
        message.chat = chat
        message.answer = AsyncMock()

        state = MagicMock()
        state.clear = AsyncMock()
        state.set_state = AsyncMock()

        command = CommandObject(prefix="/", command="start", args="ad_123")

        await handle_start(message, session, state, command=command)

        # State should be cleared and set to selecting_category
        state.clear.assert_called_once()
        state.set_state.assert_called_once()

        # Should answer with categories keyboard and no price mentions
        assert message.answer.call_count == 2
        categories_msg = message.answer.call_args_list[1]
        text = categories_msg[0][0]
        kb = categories_msg[1]["reply_markup"]

        assert "Yangi reklama yaratish" in text
        assert "toifani tanlang" in text.lower() or "turini tanlang" in text.lower()
        # Verify 4 categories are present
        assert len(kb.inline_keyboard) == 4
        assert kb.inline_keyboard[0][0].callback_data.startswith("cat:")


def test_electronics_11_categories_distinct_fields_and_conditional_logic():
    """
    Verify all 11 subcategories of electronics_other have dedicated, distinct field schemas
    and properly evaluate conditional logic (OLX-style requirements).
    """
    # 1. Smartphones
    phone_fields = QuestionnaireEngine.get_applicable_fields("electronics_other", "smartphones", {})
    phone_ids = [f.id for f in phone_fields]
    assert "brand" in phone_ids
    assert "model" in phone_ids
    assert "storage" in phone_ids
    assert "battery_health" in phone_ids
    assert "sim_config" in phone_ids
    assert "repaired_status" in phone_ids
    assert "cpu" not in phone_ids
    assert "unit_of_measure" not in phone_ids
    assert "service_area" not in phone_ids

    # 2. Computers & Laptops
    laptop_fields = QuestionnaireEngine.get_applicable_fields(
        "electronics_other", "computers", {"device_type": "Noutbuk"}
    )
    laptop_ids = [f.id for f in laptop_fields]
    assert "cpu" in laptop_ids
    assert "ram" in laptop_ids
    assert "storage" in laptop_ids
    assert "gpu" in laptop_ids
    assert "battery_status" in laptop_ids

    desktop_fields = QuestionnaireEngine.get_applicable_fields(
        "electronics_other", "computers", {"device_type": "Statsionar kompyuter"}
    )
    desktop_ids = [f.id for f in desktop_fields]
    assert "cpu" in desktop_ids
    assert "ram" in desktop_ids
    assert "battery_status" not in desktop_ids  # Never ask battery for desktop PC!

    monitor_fields = QuestionnaireEngine.get_applicable_fields(
        "electronics_other", "computers", {"device_type": "Monitor"}
    )
    monitor_ids = [f.id for f in monitor_fields]
    assert "screen_size" in monitor_ids
    assert "cpu" not in monitor_ids  # Monitor does not require CPU
    assert "ram" not in monitor_ids  # Monitor does not require RAM

    # 3. TV & Audio
    tv_fields = QuestionnaireEngine.get_applicable_fields(
        "electronics_other", "tv_audio", {"device_type": "Televizor"}
    )
    tv_ids = [f.id for f in tv_fields]
    assert "screen_size" in tv_ids
    assert "screen_tech" in tv_ids
    assert "resolution" in tv_ids
    assert "smart_tv" in tv_ids

    speaker_fields = QuestionnaireEngine.get_applicable_fields(
        "electronics_other", "tv_audio", {"device_type": "Kolonka"}
    )
    speaker_ids = [f.id for f in speaker_fields]
    assert "audio_power" in speaker_ids
    assert "screen_size" not in speaker_ids  # Speaker hides TV screen size!
    assert "smart_tv" not in speaker_ids

    # 4. Home Appliances
    washer_fields = QuestionnaireEngine.get_applicable_fields(
        "electronics_other", "home_appliances", {"appliance_type": "Kir yuvish mashinasi"}
    )
    washer_ids = [f.id for f in washer_fields]
    assert "capacity" in washer_ids
    assert "spin_speed" in washer_ids
    assert "installation" in washer_ids

    fridge_fields = QuestionnaireEngine.get_applicable_fields(
        "electronics_other", "home_appliances", {"appliance_type": "Muzlatgich"}
    )
    fridge_ids = [f.id for f in fridge_fields]
    assert "capacity" in fridge_ids
    assert "spin_speed" not in fridge_ids  # Fridge hides washing machine spin speed!

    # 5. HVAC
    hvac_fields = QuestionnaireEngine.get_applicable_fields("electronics_other", "hvac", {})
    hvac_ids = [f.id for f in hvac_fields]
    assert "hvac_type" in hvac_ids
    assert "capacity_power" in hvac_ids
    assert "recommended_area" in hvac_ids
    assert "inverter" in hvac_ids
    assert "freon_type" in hvac_ids
    assert "dismantling" in hvac_ids

    # 6. Construction Materials
    const_fields = QuestionnaireEngine.get_applicable_fields("electronics_other", "construction", {})
    const_ids = [f.id for f in const_fields]
    assert "material_type" in const_ids
    assert "unit_of_measure" in const_ids
    assert "stock_quantity" in const_ids
    assert "min_order" in const_ids
    assert "wholesale" in const_ids
    assert "loading_service" in const_ids

    # 7. Tools
    tools_sale_fields = QuestionnaireEngine.get_applicable_fields(
        "electronics_other", "tools", {"deal_type": "Sotiladi"}
    )
    tools_sale_ids = [f.id for f in tools_sale_fields]
    assert "tool_type" in tools_sale_ids
    assert "power_specs" in tools_sale_ids
    assert "rental_terms" not in tools_sale_ids

    tools_rent_fields = QuestionnaireEngine.get_applicable_fields(
        "electronics_other", "tools", {"deal_type": "Ijaraga beriladi (Prokat)"}
    )
    tools_rent_ids = [f.id for f in tools_rent_fields]
    assert "rental_terms" in tools_rent_ids  # Rent requires rental terms!

    # 8. Auto Parts
    auto_fields = QuestionnaireEngine.get_applicable_fields("electronics_other", "auto_parts", {})
    auto_ids = [f.id for f in auto_fields]
    assert "part_category" in auto_ids
    assert "car_brand" in auto_ids
    assert "car_model" in auto_ids
    assert "part_originality" in auto_ids
    assert "part_number" in auto_ids

    # 9. Clothing
    cloth_fields = QuestionnaireEngine.get_applicable_fields("electronics_other", "clothing", {})
    cloth_ids = [f.id for f in cloth_fields]
    assert "clothing_type" in cloth_ids
    assert "size" in cloth_ids
    assert "color" in cloth_ids
    assert "material" in cloth_ids
    assert "sale_type" in cloth_ids
    assert "return_policy" in cloth_ids

    # 10. Services
    serv_fields = QuestionnaireEngine.get_applicable_fields("electronics_other", "services", {})
    serv_ids = [f.id for f in serv_fields]
    assert "service_type" in serv_ids
    assert "service_scope" in serv_ids
    assert "service_area" in serv_ids
    assert "pricing_type" in serv_ids
    assert "home_visit" in serv_ids
    assert "working_hours" in serv_ids
    assert "condition" not in serv_ids  # Services do not ask physical condition

    # 11. Other Goods
    other_fields = QuestionnaireEngine.get_applicable_fields("electronics_other", "other_goods", {})
    other_ids = [f.id for f in other_fields]
    assert "title" in other_ids
    assert "item_type" in other_ids
    assert "unit_of_measure" in other_ids
    assert "condition" in other_ids


def test_electronics_11_categories_dedicated_previews():
    """
    Verify all 11 subcategories produce dedicated, OLX-style preview formats
    with no generic templates, correct unit pricing, and no empty/None fields.
    """
    # 1. Smartphones
    p1 = AdvertisementPreviewGenerator.generate_preview(
        "electronics_other", "smartphones",
        {
            "title": "iPhone 15 Pro Max",
            "brand": "Apple",
            "model": "15 Pro Max",
            "storage": "256 GB",
            "ram": "8 GB",
            "color": "Natural Titanium",
            "condition": "Ideal",
            "battery_health": "95%",
            "sim_config": "1 SIM + eSIM",
            "repaired_status": "Ochilmagan (zavod)",
            "accessories": "Karobka, kabel",
            "price": 1150,
            "currency": "USD",
            "price_negotiable": "Ha, kelishiladi",
            "location": "Toshkent, Chilonzor",
            "phone": "+998901234567"
        }
    )
    assert "📱 <b>TELEFON — IPHONE 15 PRO MAX</b>" in p1
    assert "Apple 15 Pro Max" in p1
    assert "256 GB" in p1
    assert "95%" in p1
    assert "1 150 USD (kelishiladi)" in p1
    assert "None" not in p1

    # 2. Computers
    p2 = AdvertisementPreviewGenerator.generate_preview(
        "electronics_other", "computers",
        {
            "device_type": "Noutbuk",
            "title": "Lenovo Legion 5",
            "brand_model": "Lenovo Legion 5 15ACH6H",
            "cpu": "AMD Ryzen 7 5800H",
            "ram": "16 GB",
            "storage": "1 TB SSD",
            "gpu": "RTX 3060 6GB",
            "screen_size": "15.6 FHD 165Hz",
            "battery_status": "85% salomatlik",
            "condition": "Ideal",
            "price": 8500000,
            "currency": "so‘m",
            "price_negotiable": "Qat’iy narx",
            "location": "Toshkent, Yunusobod",
            "phone": "+998909876543"
        }
    )
    assert "💻 <b>NOUTBUK — LENOVO LEGION 5</b>" in p2
    assert "AMD Ryzen 7 5800H" in p2
    assert "16 GB" in p2
    assert "1 TB SSD" in p2
    assert "8 500 000 so‘m" in p2
    assert "None" not in p2

    # 3. TV & Audio
    p3 = AdvertisementPreviewGenerator.generate_preview(
        "electronics_other", "tv_audio",
        {
            "device_type": "Televizor",
            "title": "Samsung 55 Crystal UHD",
            "brand": "Samsung",
            "model": "55CU7100",
            "screen_size": "55 dyuym",
            "screen_tech": "LED",
            "resolution": "4K UHD",
            "smart_tv": "Smart TV bor",
            "condition": "Yangi",
            "price": 4500000,
            "currency": "so‘m",
            "location": "Samarqand",
            "phone": "+998931112233"
        }
    )
    assert "📺 <b>TELEVIZOR — SAMSUNG 55 CRYSTAL UHD</b>" in p3
    assert "55 dyuym" in p3
    assert "4K UHD" in p3
    assert "Smart TV bor" in p3
    assert "4 500 000 so‘m" in p3

    # 4. Home Appliances
    p4 = AdvertisementPreviewGenerator.generate_preview(
        "electronics_other", "home_appliances",
        {
            "appliance_type": "Kir yuvish mashinasi",
            "title": "LG Inverter 8kg",
            "brand_model": "LG F2J3HS2W",
            "capacity": "8 kg yuklama",
            "spin_speed": "1200 ayl/daq",
            "condition": "Yangi",
            "price": 4200000,
            "currency": "so‘m",
            "location": "Toshkent",
            "phone": "+998901234567"
        }
    )
    assert "🧊 <b>KIR YUVISH MASHINASI — LG INVERTER 8KG</b>" in p4
    assert "8 kg yuklama" in p4
    assert "1200 ayl/daq" in p4

    # 5. HVAC
    p5 = AdvertisementPreviewGenerator.generate_preview(
        "electronics_other", "hvac",
        {
            "hvac_type": "Konditsioner",
            "title": "Shivaki 12 Inverter",
            "brand_model": "Shivaki Grand 12",
            "capacity_power": "12 000 BTU",
            "recommended_area": "35 m² gacha",
            "inverter": "Inverterli",
            "condition": "Yangi",
            "installation": "O‘rnatish mavjud",
            "price": 400,
            "currency": "USD",
            "location": "Buxoro",
            "phone": "+998971234567"
        }
    )
    assert "❄️ <b>KONDITSIONER — SHIVAKI 12 INVERTER</b>" in p5
    assert "12 000 BTU" in p5
    assert "Inverterli" in p5
    assert "O‘rnatish mavjud" in p5

    # 6. Construction Materials (must format unit price with unit of measure!)
    p6 = AdvertisementPreviewGenerator.generate_preview(
        "electronics_other", "construction",
        {
            "title": "Qizilqum Sement M500",
            "material_type": "Sement va qorishmalar",
            "brand_manufacturer": "Qizilqumsement",
            "grade_model": "M-500",
            "unit_of_measure": "qop",
            "price": 65000,
            "currency": "so‘m",
            "price_negotiable": "Ha, kelishiladi",
            "stock_quantity": "2000 qop",
            "location": "Toshkent, Bektemir",
            "phone": "+998905554433"
        }
    )
    assert "🧱 <b>QURILISH MATERIALI — QIZILQUM SEMENT M500</b>" in p6
    assert "65 000 so‘m / qop (kelishiladi)" in p6
    assert "Qizilqumsement" in p6

    # 7. Tools (Prokat / Ijara format)
    p7 = AdvertisementPreviewGenerator.generate_preview(
        "electronics_other", "tools",
        {
            "deal_type": "Ijaraga beriladi (Prokat)",
            "title": "Bosch GBH 2-26 Perforator",
            "tool_type": "Elektr asboblari",
            "brand_model": "Bosch GBH 2-26",
            "power_specs": "800W",
            "rental_terms": "Kunlik 70 000 so‘m, pasport garovga",
            "condition": "Yaxshi",
            "price": 70000,
            "currency": "so‘m",
            "location": "Toshkent",
            "phone": "+998903332211"
        }
    )
    assert "🛠 <b>IJARAGA BERILADI (PROKAT) — BOSCH GBH 2-26 PERFORATOR</b>" in p7
    assert "Ijara narxi" in p7
    assert "70 000 so‘m" in p7
    assert "Kunlik 70 000 so‘m, pasport garovga" in p7

    # 8. Auto Parts
    p8 = AdvertisementPreviewGenerator.generate_preview(
        "electronics_other", "auto_parts",
        {
            "title": "Gentra Old o‘ng fara",
            "part_category": "Kuzov va optika",
            "car_brand": "Chevrolet",
            "car_model": "Gentra",
            "year_range": "2018-2023",
            "part_originality": "Original (OEM)",
            "part_number": "96473218",
            "condition": "Ideal",
            "price": 650000,
            "currency": "so‘m",
            "location": "Sergeli moshina bozori",
            "phone": "+998991112233"
        }
    )
    assert "🚗 <b>AVTO EHTIYOT QISM — GENTRA OLD O‘NG FARA</b>" in p8
    assert "Chevrolet Gentra (2018-2023)" in p8
    assert "96473218" in p8
    assert "Original (OEM)" in p8

    # 9. Clothing
    p9 = AdvertisementPreviewGenerator.generate_preview(
        "electronics_other", "clothing",
        {
            "title": "Erkaklar charm kurtkasi",
            "clothing_type": "Erkaklar kiyimi",
            "brand": "Zara",
            "size": "L, XL",
            "color": "Qora",
            "material": "Tabiiy charm",
            "condition": "Yangi (etiketkali)",
            "sale_type": "Chakana",
            "price": 1200000,
            "currency": "so‘m",
            "location": "Toshkent",
            "phone": "+998901234567"
        }
    )
    assert "👔 <b>KIYIM-KECHAK — ERKAKLAR CHARM KURTKASI</b>" in p9
    assert "L, XL" in p9
    assert "Tabiiy charm" in p9
    assert "1 200 000 so‘m" in p9

    # 10. Services
    p10 = AdvertisementPreviewGenerator.generate_preview(
        "electronics_other", "services",
        {
            "title": "Professional santexnika xizmatlari",
            "service_type": "Santexnika",
            "service_scope": "Quvurlar va kotyol o‘rnatish, sizishlarni bartaraf qilish",
            "service_area": "Toshkent shahri",
            "pricing_type": "Ish hajmiga qarab",
            "price": 150000,
            "currency": "so‘m",
            "home_visit": "Mijoz manziliga boriladi",
            "working_hours": "08:00 - 22:00",
            "location": "Toshkent",
            "phone": "+998907778899"
        }
    )
    assert "🛠 <b>XIZMAT — PROFESSIONAL SANTEXNIKA XIZMATLARI</b>" in p10
    assert "Quvurlar va kotyol o‘rnatish" in p10
    assert "Toshkent shahri" in p10
    assert "150 000 so‘m (Ish hajmiga qarab)" in p10
    assert "Mijoz manziliga boriladi" in p10

    # 11. Other Goods
    p11 = AdvertisementPreviewGenerator.generate_preview(
        "electronics_other", "other_goods",
        {
            "title": "Tog‘ velosipedi 26 dyuym",
            "item_type": "Sport anjomi",
            "brand_model": "Trinx M100",
            "condition": "Yaxshi",
            "quantity": "1 dona",
            "unit_of_measure": "dona",
            "price": 1400000,
            "currency": "so‘m",
            "location": "Toshkent, Olmazor",
            "phone": "+998901234567"
        }
    )
    assert "📦 <b>MAHSULOT — TOG‘ VELOSIPEDI 26 DYUYM</b>" in p11
    assert "Sport anjomi" in p11
    assert "Trinx M100" in p11
    assert "1 400 000 so‘m" in p11


