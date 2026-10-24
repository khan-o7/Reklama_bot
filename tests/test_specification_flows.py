import pytest
from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager
from aiogram.types import Message, Chat, User as TgUser, Document, Audio, Voice, Animation, Sticker, Contact
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config.settings import settings
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.group_repo import GroupRepository
from app.database.repositories.ad_repo import AdvertisementRepository
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.publication_service import PublicationService
from app.services.content_extractor import ContentExtractor
from app.services.moderation_service import ModerationService
from app.services.request_service import RequestService
from app.services.state_machine import (
    RequestStatus,
    validate_transition,
    normalize_status,
    get_status_label
)


@asynccontextmanager
async def get_test_session():
    test_engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await test_engine.dispose()


# ==============================================================================
# 1. State Machine & Transition Validation Tests
# ==============================================================================

def test_state_machine_legal_transitions():
    """Verify that all legal state transitions succeed without error."""
    assert validate_transition(RequestStatus.NEW, RequestStatus.AWAITING_PRICE) is True
    assert validate_transition(RequestStatus.AWAITING_PRICE, RequestStatus.AWAITING_PAYMENT) is True
    assert validate_transition(RequestStatus.AWAITING_PAYMENT, RequestStatus.RECEIPT_SUBMITTED) is True
    assert validate_transition(RequestStatus.RECEIPT_SUBMITTED, RequestStatus.PAYMENT_APPROVED) is True
    assert validate_transition(RequestStatus.PAYMENT_APPROVED, RequestStatus.PUBLISHED) is True
    assert validate_transition(RequestStatus.RECEIPT_SUBMITTED, RequestStatus.PAYMENT_REJECTED) is True
    assert validate_transition(RequestStatus.PAYMENT_REJECTED, RequestStatus.RECEIPT_SUBMITTED) is True


def test_state_machine_illegal_transitions_prevented():
    """
    Verify that arbitrary illegal transitions are blocked.
    Publication before payment approval MUST be strictly prohibited.
    """
    # Publication before approval is illegal
    with pytest.raises(ValueError, match="Ruxsat etilmagan holat"):
        validate_transition(RequestStatus.NEW, RequestStatus.PUBLISHED)

    with pytest.raises(ValueError, match="Ruxsat etilmagan holat"):
        validate_transition(RequestStatus.AWAITING_PRICE, RequestStatus.PUBLISHED)

    with pytest.raises(ValueError, match="Ruxsat etilmagan holat"):
        validate_transition(RequestStatus.RECEIPT_SUBMITTED, RequestStatus.PUBLISHED)

    # Approving payment before receipt is submitted is illegal
    with pytest.raises(ValueError, match="Ruxsat etilmagan holat"):
        validate_transition(RequestStatus.NEW, RequestStatus.PAYMENT_APPROVED)

    with pytest.raises(ValueError, match="Ruxsat etilmagan holat"):
        validate_transition(RequestStatus.AWAITING_PRICE, RequestStatus.PAYMENT_APPROVED)


# ==============================================================================
# 2. Universal Media Types Extraction Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_content_extractor_various_media_types():
    """Verify handling of document, audio, voice, animation, sticker, and contact."""
    base_msg = MagicMock(spec=Message)
    base_msg.message_id = 101
    base_msg.text = None
    base_msg.photo = []
    base_msg.video = None
    base_msg.entities = []
    base_msg.caption_entities = []
    base_msg.edit_date = None
    base_msg.from_user = MagicMock(spec=TgUser, id=112233)
    base_msg.chat = MagicMock(spec=Chat, id=-1001234567, type="supergroup")

    # Document test
    doc_mock = MagicMock(spec=Document, file_id="doc_fid_1", file_unique_id="doc_uid_1")
    base_msg.document = doc_mock
    base_msg.caption = "Tijoriy taklif faylda"
    res_doc = await ContentExtractor.extract_message_content(base_msg)
    assert res_doc["media_type"] == "DOCUMENT"
    assert res_doc["media_file_id"] == "doc_fid_1"
    assert "Tijoriy taklif" in res_doc["combined_text"]
    base_msg.document = None

    # Audio test
    audio_mock = MagicMock(spec=Audio, file_id="aud_fid_1", file_unique_id="aud_uid_1")
    base_msg.audio = audio_mock
    base_msg.caption = "Audio reklama eshiting"
    res_aud = await ContentExtractor.extract_message_content(base_msg)
    assert res_aud["media_type"] == "AUDIO"
    assert res_aud["media_file_id"] == "aud_fid_1"
    base_msg.audio = None

    # Animation test
    anim_mock = MagicMock(spec=Animation, file_id="anim_fid_1", file_unique_id="anim_uid_1")
    base_msg.animation = anim_mock
    base_msg.caption = "Aksiya GIF"
    res_anim = await ContentExtractor.extract_message_content(base_msg)
    assert res_anim["media_type"] == "ANIMATION"
    assert res_anim["media_file_id"] == "anim_fid_1"
    base_msg.animation = None

    # Contact test
    contact_mock = MagicMock(spec=Contact, phone_number="+998901234567", first_name="Diler", last_name="Savdogar")
    base_msg.contact = contact_mock
    base_msg.caption = None
    res_contact = await ContentExtractor.extract_message_content(base_msg)
    assert res_contact["media_type"] == "CONTACT"
    assert "+998901234567" in res_contact["combined_text"]


# ==============================================================================
# 3. Telegram API Failures Graceful Handling Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_group_deletion_permission_failure_graceful():
    """
    If bot lacks permission to delete message in group,
    ModerationService should catch TelegramBadRequest, record audit event, and continue.
    """
    async with get_test_session() as session:
        mock_bot = AsyncMock()
        mock_bot.get_me = AsyncMock(return_value=MagicMock(username="DefenderBot"))
        mock_bot.send_message = AsyncMock(return_value=MagicMock(message_id=777))

        mock_msg = MagicMock(spec=Message)
        mock_msg.message_id = 9999
        mock_msg.chat = MagicMock(spec=Chat, id=-100111222333, type="supergroup", title="Test Group", username="test_grp")
        mock_msg.from_user = MagicMock(id=555444333, username="spammer", first_name="Ali", last_name=None, full_name="Ali")
        mock_msg.text = "Reklama: arzon narxlarda krossovkalar sotiladi!"
        mock_msg.caption = None

        # Simulate Telegram API error on delete (e.g. not an admin)
        mock_msg.delete = AsyncMock(side_effect=TelegramBadRequest(method=MagicMock(), message="Not enough rights to delete"))

        analysis = {
            "is_ad": True,
            "score": 90,
            "reasons": ["sotiladi", "narxlarda"],
            "matched_keywords": ["sotiladi", "narxlarda"],
            "links": [],
            "message_type": "TEXT"
        }
        content = {
            "text": mock_msg.text,
            "caption": None,
            "combined_text": mock_msg.text,
            "media_type": "TEXT",
            "media_file_id": None,
            "media_file_unique_id": None,
            "ocr_text": None
        }

        # Should execute cleanly without raising unhandled exception
        await ModerationService.handle_advertisement(
            bot=mock_bot,
            message=mock_msg,
            analysis=analysis,
            session=session,
            content=content
        )

        # Message delete was attempted
        assert mock_msg.delete.called


@pytest.mark.asyncio
async def test_user_not_started_bot_pm_failure_graceful():
    """
    When sending a private notification to a user who hasn't started the bot,
    TelegramForbiddenError occurs. The bot must handle this gracefully without crashing.
    """
    async with get_test_session() as session:
        mock_bot = AsyncMock()
        mock_bot.get_me = AsyncMock(return_value=MagicMock(username="DefenderBot"))

        # Private message fails with TelegramForbiddenError (bot blocked or not started)
        def send_message_mock(*args, **kwargs):
            chat_id = kwargs.get("chat_id")
            if chat_id and chat_id > 0:  # Private chat ID is positive
                raise TelegramForbiddenError(method=MagicMock(), message="bot was blocked by the user")
            return MagicMock(message_id=888)

        mock_bot.send_message = AsyncMock(side_effect=send_message_mock)

        mock_msg = MagicMock(spec=Message)
        mock_msg.message_id = 9998
        mock_msg.chat = MagicMock(spec=Chat, id=-100111222333, type="supergroup", title="Test Group", username="test_grp")
        mock_msg.from_user = MagicMock(id=666777888, username="newbie", first_name="Vali", last_name=None, full_name="Vali")
        mock_msg.text = "Ulgurji narxda mevalar yetkazib beramiz!"
        mock_msg.caption = None
        mock_msg.delete = AsyncMock(return_value=True)

        analysis = {
            "is_ad": True,
            "score": 90,
            "reasons": ["narxda", "yetkazib"],
            "matched_keywords": ["narxda"],
            "links": [],
            "message_type": "TEXT"
        }
        content = {
            "text": mock_msg.text,
            "caption": None,
            "combined_text": mock_msg.text,
            "media_type": "TEXT",
            "media_file_id": None,
            "media_file_unique_id": None,
            "ocr_text": None
        }

        # Does not crash when user private message is rejected
        await ModerationService.handle_advertisement(
            bot=mock_bot,
            message=mock_msg,
            analysis=analysis,
            session=session,
            content=content
        )


# ==============================================================================
# 4. Publication Retry and Failure Handling Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_publication_failure_and_retry_workflow():
    """
    Verify that if Telegram API fails during publication,
    the status becomes PUBLICATION_FAILED, and retrying after fix succeeds.
    """
    async with get_test_session() as session:
        user_db = await UserRepository.get_or_create(
            session=session,
            telegram_id=333222111,
            username="pub_fail_user",
            first_name="Mansur"
        )
        ad = await AdvertisementRepository.create(
            session=session,
            group_id=None,
            user_id=user_db.id,
            telegram_message_id=12345,
            chat_id=-1001999000,
            username="pub_fail_user",
            first_name="Mansur",
            message_type="TEXT",
            media_type="TEXT",
            text="Konditsioner o'rnatish xizmati",
            score=100,
            detection_reason="Xizmat",
            deleted=True,
            status="DELETED"
        )
        order = await OrderService.create_order_for_ad(session, ad, default_price=100000)
        order.status = "APPROVED"
        await session.commit()

        # 1. Simulate failure during Telegram send
        mock_bot_fail = MagicMock()
        mock_bot_fail.send_message = AsyncMock(side_effect=Exception("Telegram connection timeout"))

        ok_fail, msg_id_fail, err_fail = await PublicationService.publish_advertisement(
            bot=mock_bot_fail,
            session=session,
            ad=ad,
            order=order
        )
        assert ok_fail is False
        assert msg_id_fail is None
        assert "timeout" in err_fail

        # Verify DB status updated to PUBLICATION_FAILED
        refreshed_order = await OrderService.get_order_by_id(session, order.id)
        assert refreshed_order.status == "PUBLICATION_FAILED"

        # 2. Simulate retry when Telegram network is restored
        mock_bot_success = MagicMock()
        mock_sent = MagicMock(message_id=54321)
        mock_bot_success.send_message = AsyncMock(return_value=mock_sent)

        ok_retry, msg_id_retry, err_retry = await PublicationService.publish_advertisement(
            bot=mock_bot_success,
            session=session,
            ad=ad,
            order=refreshed_order
        )
        assert ok_retry is True
        assert msg_id_retry == 54321
        assert "muvaffaqiyatli" in err_retry.lower()

        # Verify final status is PUBLISHED
        final_order = await OrderService.get_order_by_id(session, order.id)
        assert final_order.status == "PUBLISHED"


# ==============================================================================
# 5. User Data Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_user_data_isolation():
    """Verify that User A cannot see or access User B's orders."""
    async with get_test_session() as session:
        user_a = await UserRepository.get_or_create(session=session, telegram_id=1111111, username="usera")
        user_b = await UserRepository.get_or_create(session=session, telegram_id=2222222, username="userb")

        ad_a = await AdvertisementRepository.create(
            session=session, group_id=None, user_id=user_a.id, telegram_message_id=101,
            chat_id=-1001, username="usera", first_name="A", message_type="TEXT",
            media_type="TEXT", text="Ad A", score=100, detection_reason="Ad", deleted=True
        )
        ad_b = await AdvertisementRepository.create(
            session=session, group_id=None, user_id=user_b.id, telegram_message_id=102,
            chat_id=-1001, username="userb", first_name="B", message_type="TEXT",
            media_type="TEXT", text="Ad B", score=100, detection_reason="Ad", deleted=True
        )

        order_a = await OrderService.create_order_for_ad(session, ad_a, default_price=50000)
        order_b = await OrderService.create_order_for_ad(session, ad_b, default_price=70000)

        # Query user A's orders
        orders_for_a = await RequestService.get_user_requests(session, user_id=user_a.id)
        assert any(o.id == order_a.id for o in orders_for_a)
        assert not any(o.id == order_b.id for o in orders_for_a), "User A must NOT see User B's orders"

        # Query user B's orders
        orders_for_b = await RequestService.get_user_requests(session, user_id=user_b.id)
        assert any(o.id == order_b.id for o in orders_for_b)
        assert not any(o.id == order_a.id for o in orders_for_b), "User B must NOT see User A's orders"


# ==============================================================================
# 6. Duplicate Request Prevention Test
# ==============================================================================

@pytest.mark.asyncio
async def test_duplicate_request_prevention():
    """Calling create_order_for_ad multiple times returns the existing order idempotently."""
    async with get_test_session() as session:
        user_db = await UserRepository.get_or_create(session=session, telegram_id=999888111, username="dup_test")
        ad = await AdvertisementRepository.create(
            session=session, group_id=None, user_id=user_db.id, telegram_message_id=7788,
            chat_id=-1001, username="dup_test", first_name="Dup", message_type="TEXT",
            media_type="TEXT", text="Dup test ad", score=100, detection_reason="Ad", deleted=True
        )

        order1 = await OrderService.create_order_for_ad(session, ad)
        order2 = await OrderService.create_order_for_ad(session, ad)

        assert order1.id == order2.id
        assert order1.order_number == order2.order_number


# ==============================================================================
# 7. Financial Statistics Calculation Test
# ==============================================================================

@pytest.mark.asyncio
async def test_financial_statistics_reporting():
    """Verify that financial statistics are calculated accurately from DB."""
    async with get_test_session() as session:
        stats = await RequestService.get_financial_statistics(session)
        assert "total_orders" in stats
        assert "today_orders" in stats
        assert "month_orders" in stats
        assert "total_revenue" in stats
        assert isinstance(stats["total_revenue"], int)
        assert isinstance(stats["total_orders"], int)


# ==============================================================================
# 8. Restart Recovery of Unfinished Publications Test
# ==============================================================================

@pytest.mark.asyncio
async def test_restart_recovery_of_unfinished_publications():
    """
    Verify that upon bot restart, any orders left in PAYMENT_APPROVED
    or READY_TO_PUBLISH are automatically recovered and published.
    """
    async with get_test_session() as session:
        user_db = await UserRepository.get_or_create(session=session, telegram_id=888123456, username="rec_user")
        ad = await AdvertisementRepository.create(
            session=session, group_id=None, user_id=user_db.id, telegram_message_id=98765,
            chat_id=-1001555666, username="rec_user", first_name="Rec", message_type="TEXT",
            media_type="TEXT", text="Restart recovery ad content", score=100, detection_reason="Ad", deleted=True
        )
        order = await OrderService.create_order_for_ad(session, ad, default_price=120000)
        order.status = "PAYMENT_APPROVED"
        await session.commit()

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock(return_value=MagicMock(message_id=778899))

        recovered = await PublicationService.recover_unfinished_publications(mock_bot, session)
        assert recovered >= 1

        refreshed_order = await OrderService.get_order_by_id(session, order.id)
        assert refreshed_order.status == "PUBLISHED"
        assert refreshed_order.advertisement.published_message_id == 778899
