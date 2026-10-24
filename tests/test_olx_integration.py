import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.olx_category_mapper import OlxCategoryMapper, OlxCategoryMapping
from app.services.olx_service import OlxService
from app.config.settings import settings
from app.database.models.advertising_request import AdvertisingRequest
from app.database.models.advertisement_answer import AdvertisementAnswer
from app.database.models.advertisement_media import AdvertisementMedia


def test_olx_category_mapper_mappings():
    """Verify that all major categories map to appropriate OLX categories and search terms."""
    # Real estate
    re_map = OlxCategoryMapper.get_olx_category("real_estate", "novostroyka")
    assert "Квартиры" in re_map.search_terms or "Новостройки" in re_map.search_terms
    assert "Ko‘chmas mulk" in re_map.category_name_uz

    # Furniture
    furn_map = OlxCategoryMapper.get_olx_category("furniture", "sofa")
    assert "Мебель" in furn_map.category_name_ru
    assert any("Диван" in t for t in furn_map.search_terms)

    # Curtains
    curt_map = OlxCategoryMapper.get_olx_category("curtains_blinds", None)
    assert any("Шторы" in t or "Pardalar" in t for t in curt_map.search_terms)

    # Electronics
    phone_map = OlxCategoryMapper.get_olx_category("electronics_other", "phones")
    assert any("Телефоны" in t or "Telefonlar" in t for t in phone_map.search_terms)


def test_olx_category_mapper_payload_normalization():
    """Verify advert payload satisfies OLX minimum constraints (16+ chars title, 80+ chars desc)."""
    answers = {
        "title": "Uy",  # Short title < 16 chars
        "description": "Zo'r xonadon",  # Short description < 80 chars
        "price": "50 000 y.e.",
        "currency": "USD",
        "city_district": "Toshkent, Yunusobod",
        "phone": "+998901234567",
        "condition": "Yangi",
        "rooms": "3",
        "floor": "4"
    }

    data = OlxCategoryMapper.prepare_advert_data(
        category_id="real_estate",
        subcategory_id="secondary_apt",
        answers=answers
    )

    assert len(data["title"]) >= 16
    assert len(data["title"]) <= 70
    assert len(data["description"]) >= 80
    assert data["price"] == 50000
    assert data["currency"] == "USD"
    assert data["city_district"] == "Toshkent, Yunusobod"
    assert data["phone"] == "+998901234567"
    assert data["condition"] == "yangi"
    assert "Rooms: 3" in data["description"] or "rooms: 3" in data["description"].lower()


def test_olx_service_session_status_missing(tmp_path):
    """Verify session status returns is_valid=False when file does not exist."""
    fake_path = tmp_path / "non_existent_session.json"
    with patch.object(OlxService, "get_session_file_path", return_value=fake_path):
        status = OlxService.get_session_status()
        assert status["exists"] is False
        assert status["is_valid"] is False


def test_olx_service_session_status_valid(tmp_path):
    """Verify session status correctly identifies valid storage_state JSON."""
    fake_path = tmp_path / "olx_session.json"
    sample_data = {
        "cookies": [
            {"name": "user_name", "value": "Test User", "domain": ".olx.uz"}
        ],
        "origins": [
            {"origin": "https://www.olx.uz", "localStorage": [{"name": "token", "value": "xyz"}]}
        ]
    }
    fake_path.write_text(json.dumps(sample_data), encoding="utf-8")

    with patch.object(OlxService, "get_session_file_path", return_value=fake_path):
        status = OlxService.get_session_status()
        assert status["exists"] is True
        assert status["is_valid"] is True
        assert status["cookies_count"] == 1


def test_olx_service_save_session_json(tmp_path):
    """Verify session json saving and validation."""
    fake_path = tmp_path / "saved_session.json"
    with patch.object(OlxService, "get_session_file_path", return_value=fake_path):
        # Invalid format
        ok, err = OlxService.save_session_json('{"invalid": 123}')
        assert ok is False

        # Valid format
        ok, msg = OlxService.save_session_json('{"cookies": [], "origins": []}')
        assert ok is True
        assert fake_path.exists()


@pytest.mark.asyncio
async def test_olx_service_publish_disabled_setting():
    """Verify when OLX_ENABLED is False, publish returns early."""
    mock_session = AsyncMock()
    fake_req = MagicMock(spec=AdvertisingRequest)
    fake_req.id = 999
    fake_req.request_number = "REQ-TEST-001"

    with patch.object(settings, "OLX_ENABLED", False):
        with patch("app.database.repositories.ad_request_repo.AdvertisingRequestRepository.update_olx_status", new_callable=AsyncMock) as mock_update:
            success, url, err = await OlxService.publish_request_to_olx(None, mock_session, fake_req)
            assert success is False
            assert "o‘chirilgan" in err
            mock_update.assert_awaited()


def test_user_product_price_not_bot_fee():
    """Verify that user's item price (6,500,000 so'm) is used, NOT the bot tariff (100,000 so'm)."""
    answers = {
        "title": "Iphone 14 pro",
        "brand": "Apple",
        "model": "14 pro",
        "storage": "128 GB",
        "price": "6500000",
        "currency": "so‘m",
        "phone": "944444444",
        "location": "Chilonzor"
    }
    preview_text = "📱 <b>TELEFON — IPHONE 14 PRO</b>\n💰 <b>Narxi:</b> 6 500 000 so‘m\n📞 <b>Aloqa:</b> 944444444"

    data = OlxCategoryMapper.prepare_advert_data(
        category_id="electronics_other",
        subcategory_id="smartphones",
        answers=answers,
        preview_text=preview_text
    )

    # Must be user's selling price, NOT bot tariff
    assert data["price"] == 6500000
    assert data["currency"] == "UZS"
    assert data["phone"] == "944444444"
    assert data["city_district"] == "Chilonzor"
    assert "Apple" in data["title"] or "14 pro" in data["title"]
    assert len(data["title"]) >= 16


def test_preview_text_fallback_extraction():
    """Verify that when answers dict is empty, fields are extracted from preview_text."""
    preview_text = (
        "🏠 <b>Yunusobodda 3 xonali shinam xonadon</b>\n\n"
        "📍 <b>Manzil:</b> Yunusobod 14-mavze\n"
        "💰 <b>Narxi:</b> 55 000 y.e. (USD)\n"
        "📞 <b>Aloqa:</b> +998901234567\n"
        "Barcha qulayliklari bilan jihozlangan ajoyib xonadon sotiladi."
    )

    data = OlxCategoryMapper.prepare_advert_data(
        category_id="real_estate",
        subcategory_id="secondary_apt",
        answers={},
        preview_text=preview_text
    )

    assert data["price"] == 55000
    assert data["currency"] == "USD"
    assert "+998901234567" in data["phone"]
    assert "Yunusobod" in data["city_district"]
    assert "Yunusobod" in data["title"]


def test_advertising_request_product_properties():
    """Verify AdvertisingRequest model properties return product details, not ad fee."""
    req = AdvertisingRequest(
        id=10,
        request_number="REQ-2026-000010",
        user_id=1,
        category_id="electronics_other",
        subcategory_id="smartphones",
        price=150000,  # Bot advertising fee
        currency="UZS",
        preview_text="📱 <b>TELEFON — IPHONE 14 PRO</b>\n💰 <b>Narxi:</b> 6 500 000 so‘m\n📞 <b>Aloqa:</b> 944444444",
        status="PUBLISHED"
    )
    ans_price = AdvertisementAnswer(request_id=10, field_id="price", value="6500000")
    ans_curr = AdvertisementAnswer(request_id=10, field_id="currency", value="so‘m")
    ans_phone = AdvertisementAnswer(request_id=10, field_id="phone", value="944444444")
    req.answers = [ans_price, ans_curr, ans_phone]

    # Product price must be 6,500,000, while req.price is 150,000 (ad fee)
    assert req.product_price == 6500000
    assert req.price == 150000
    assert req.product_currency == "UZS"
    assert req.product_phone == "944444444"


def test_olx_template_rendering_safety():
    """Verify olx.html renders with data attributes and no quote-breaking onclick strings."""
    from jinja2 import Environment, FileSystemLoader
    from app.database.models.user import User
    from datetime import datetime

    env = Environment(loader=FileSystemLoader("app/web/templates"))
    template = env.get_template("olx.html")

    user = User(id=1, first_name="Ali", username="alisher")
    req = AdvertisingRequest(
        id=77,
        request_number="REQ-2026-000077",
        user_id=1,
        category_id="electronics_other",
        subcategory_id="smartphones",
        price=100000,
        currency="UZS",
        preview_text='📱 "iPhone 15 Pro Max" 256GB\nNarxi: 1200$\nTel: +998901234567\nBarcha holatlari "ideal"!\n<script>alert("xss")</script>',
        status="PUBLISHED",
        olx_status="FAILED",
        olx_error="Traceback (most recent call last):\n  File 'olx_service.py', line 55:\n    Exception: 'selector' not found",
        created_at=datetime.now()
    )
    req.user = user

    rendered = template.render(
        request={"url_for": lambda *a, **kw: "#"},
        current_admin="admin",
        active_page="olx",
        session_status={"valid": True, "status": "CONNECTED", "user": "test_user"},
        auto_post_enabled=True,
        metrics={"total_requests": 1, "olx_published": 0, "olx_pending": 0, "olx_failed": 1},
        requests=[req],
        current_olx_filter=None,
        message=None
    )

    # Must contain safe data attributes and helper calls
    assert 'onclick="openDetailsFromButton(this)"' in rendered
    assert 'data-req-id="77"' in rendered
    assert 'data-title="iPhone 15 Pro Max' in rendered
    assert 'onclick="showErrorModalById(\'olx-error-77\')"' in rendered
    assert '<div id="preview-text-77" class="hidden">' in rendered
    assert '<div id="olx-error-77" class="hidden">' in rendered
    # Must NOT have unsafe inline openDetailsModal with quote parameters inside button
    assert 'onclick="openDetailsModal(77,' not in rendered

    # Edit & Delete buttons and modals
    assert 'onclick="openEditModalFromButton(this)"' in rendered
    assert 'id="btn-edit-77"' in rendered
    assert 'onclick="openDeleteModal(\'77\'' in rendered
    assert 'id="btn-delete-77"' in rendered
    assert 'id="editModal"' in rendered
    assert 'id="deleteConfirmModal"' in rendered


@pytest.mark.asyncio
async def test_ad_request_update_and_delete_repo():
    from tests.test_commercial_workflow import get_test_session
    from app.database.repositories.user_repo import UserRepository
    from app.database.repositories.ad_request_repo import AdvertisingRequestRepository

    async with get_test_session() as session:
        # Create test user
        user = await UserRepository.get_or_create(
            session,
            telegram_id=98765432999,
            username="olx_crud_tester",
            first_name="OLX",
            last_name="Tester"
        )
        assert user.id is not None

        # Create advertising request
        req = await AdvertisingRequestRepository.create(
            session=session,
            user_id=user.id,
            category_id="electronics_other",
            subcategory_id="smartphones"
        )
        assert req.id is not None
        req_id = req.id

        # Update request content
        updated = await AdvertisingRequestRepository.update_request_content(
            session=session,
            request_id=req_id,
            title="Samsung Galaxy S24 Ultra 512GB Grey",
            price=12500000,
            currency="UZS",
            phone="+998901234567",
            location="Toshkent, Mirzo Ulugbek",
            condition="used",
            preview_text="Samsung Galaxy S24 Ultra 512GB yangidek, karobka-dokument bor."
        )

        assert updated is not None
        assert updated.product_title == "Samsung Galaxy S24 Ultra 512GB Grey"
        assert updated.product_price == 12500000
        assert updated.product_currency == "UZS"
        assert updated.product_phone == "+998901234567"
        assert updated.product_location == "Toshkent, Mirzo Ulugbek"
        assert "Samsung Galaxy S24" in updated.preview_text

        # Delete request
        deleted = await AdvertisingRequestRepository.delete_by_id(session, req_id)
        assert deleted is True

        # Verify it is deleted
        found = await AdvertisingRequestRepository.get_by_id(session, req_id)
        assert found is None


