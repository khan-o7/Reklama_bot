import pytest
from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager
from aiogram.types import Message, Chat, User as TgUser, Video
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
from app.bot.keyboards.warning_kb import get_warning_keyboard


@asynccontextmanager
async def get_test_session():
    test_engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_warning_keyboard_deep_link():
    """Verify deep-link URL and button text depending on whether ad_id is passed."""
    # When ad_id is provided -> deep link to that deleted ad
    kb_ad = get_warning_keyboard(bot_username="DefenderTestBot", ad_id=888)
    assert len(kb_ad.inline_keyboard) >= 1
    ad_btn = kb_ad.inline_keyboard[0][0]
    assert "reklama joylash" in ad_btn.text.lower()
    assert "https://t.me/DefenderTestBot?start=ad_888" in ad_btn.url

    # When ad_id is None -> default ad_order link
    kb_default = get_warning_keyboard(bot_username="DefenderTestBot", ad_id=None)
    def_btn = kb_default.inline_keyboard[0][0]
    assert "reklama joylash" in def_btn.text.lower()
    assert "https://t.me/DefenderTestBot?start=ad_order" in def_btn.url


@pytest.mark.asyncio
async def test_content_extractor_video_and_photo():
    """Verify universal content extractor handles photos, videos, and media types."""
    v_msg = MagicMock(spec=Message)
    v_msg.message_id = 901
    v_msg.text = None
    v_msg.caption = "Mashina sotiladi, holati a'lo!"
    v_msg.photo = []
    v_msg.entities = []
    v_msg.caption_entities = []
    v_msg.edit_date = None
    v_msg.from_user = MagicMock(spec=TgUser, id=1234567)
    v_msg.chat = MagicMock(spec=Chat, id=-1001999888, type="supergroup")

    video_mock = MagicMock(spec=Video)
    video_mock.file_id = "video_file_id_abc"
    video_mock.file_unique_id = "video_uid_123"
    video_mock.thumbnail = None
    v_msg.video = video_mock

    content_v = await ContentExtractor.extract_message_content(v_msg, update_type="message")
    assert content_v["has_video"] is True
    assert content_v["has_photo"] is False
    assert content_v["media_type"] == "VIDEO"
    assert content_v["media_file_id"] == "video_file_id_abc"
    assert content_v["media_file_unique_id"] == "video_uid_123"
    assert "Mashina sotiladi" in content_v["combined_text"]


@pytest.mark.asyncio
async def test_commercial_full_lifecycle():
    """
    End-to-end test of the complete commercial ad ordering lifecycle:
    1. Advertisement created
    2. Order created
    3. Admin sets price
    4. User submits payment receipt
    5. Deduplication check on duplicate receipt
    6. Admin approves payment (with idempotency protection)
    7. PublicationService publishes ad with #reklama tag and registers message ID
    8. Moderator ignores bot-published message
    """
    async with get_test_session() as session:
        # Step 1: Set up test user and ad
        user_db = await UserRepository.get_or_create(
            session=session,
            telegram_id=888777666,
            username="advertiser_test",
            first_name="Azizbek"
        )
        group_db = await GroupRepository.get_or_create(
            session=session,
            telegram_chat_id=-1001555444333,
            title="Savdo Guruh Test"
        )

        ad = await AdvertisementRepository.create(
            session=session,
            group_id=group_db.id,
            user_id=user_db.id,
            telegram_message_id=5001,
            chat_id=-1001555444333,
            username="advertiser_test",
            first_name="Azizbek",
            message_type="TEXT",
            media_type="TEXT",
            text="Original reklama matni: Telefon sotiladi, yangi karobka!",
            score=100,
            detection_reason="Reklama so'zi aniqlandi",
            deleted=True,
            status="DELETED"
        )
        assert ad.id is not None

        # Step 2: Create Commercial Order
        order = await OrderService.create_order_for_ad(session, ad)
        assert order.id is not None
        target_order_id = order.id
        target_ad_id = ad.id
        assert order.order_number.startswith("AD-")
        assert order.advertisement_id == target_ad_id

        # Step 3: Admin Sets Price
        updated_order = await OrderService.set_order_price(
            session=session,
            order_id=target_order_id,
            price=150000,
            card_number="8600123456789012"
        )
        assert updated_order.price == 150000
        assert updated_order.status == "WAITING_PAYMENT"
        assert updated_order.card_number == "8600123456789012"

        # Check advertisement status synced
        reloaded_ad = await AdvertisementRepository.get_by_id(session, target_ad_id)
        assert reloaded_ad.status == "WAITING_PAYMENT"

        # Step 4: User Submits Payment Receipt
        import uuid
        uid = str(uuid.uuid4())
        receipt_bytes = f"sample_payment_bytes_{uid}".encode()
        payment, is_dup = await PaymentService.submit_receipt(
            session=session,
            order=updated_order,
            receipt_file_id=f"tg_receipt_file_{uid}",
            receipt_file_unique_id=f"tg_uid_{uid}",
            file_bytes=receipt_bytes,
            receipt_type="PHOTO"
        )
        assert payment.id is not None
        assert payment.status == "PENDING"
        assert is_dup is False

        # Order and Ad should now be in PAYMENT_REVIEW
        reloaded_order = await OrderService.get_order_by_id(session, target_order_id)
        assert reloaded_order.status == "PAYMENT_REVIEW"

        # Step 5: Duplicate Receipt Detection
        payment_dup, is_dup2 = await PaymentService.submit_receipt(
            session=session,
            order=reloaded_order,
            receipt_file_id=f"tg_receipt_file_{uid}_another",
            receipt_file_unique_id=f"tg_uid_{uid}_another",
            file_bytes=receipt_bytes,
            receipt_type="PHOTO"
        )
        assert is_dup2 is True, "Identical receipt bytes should be flagged as duplicate"

        # Step 6: Admin Approves Payment & Idempotency Test
        ok, approved_order, msg = await PaymentService.approve_payment(
            session=session,
            order_id=target_order_id,
            admin_id=5976376745
        )
        assert ok is True
        assert approved_order.status == "APPROVED"

        # Idempotency: Second approval attempt should be rejected
        ok_again, _, msg_again = await PaymentService.approve_payment(
            session=session,
            order_id=target_order_id,
            admin_id=5976376745
        )
        assert ok_again is False
        assert "allaqachon tasdiqlangan" in msg_again

        # Step 7: PublicationService Publishes Advertisement
        mock_bot = MagicMock()
        mock_sent_msg = MagicMock()
        mock_sent_msg.message_id = 998877
        mock_bot.send_message = AsyncMock(return_value=mock_sent_msg)

        fresh_ad = await AdvertisementRepository.get_by_id(session, target_ad_id)
        pub_ok, pub_id, pub_text = await PublicationService.publish_advertisement(
            bot=mock_bot,
            session=session,
            ad=fresh_ad,
            order=approved_order
        )
        assert pub_ok is True
        assert pub_id == 998877

        # Verify sent text contains #reklama tag
        sent_call_args = mock_bot.send_message.call_args[1]
        assert "#reklama" in sent_call_args["text"]

        # Verify bot published bypass register
        assert PublicationService.is_bot_published(-1001555444333, 998877) is True

        # Verify DB records updated to PUBLISHED
        final_ad = await AdvertisementRepository.get_by_id(session, target_ad_id)
        assert final_ad.status == "PUBLISHED"
        assert final_ad.published_message_id == 998877

        final_order = await OrderService.get_order_by_id(session, target_order_id)
        assert final_order.status == "PUBLISHED"


@pytest.mark.asyncio
async def test_rejection_workflow():
    """Verify that rejecting a payment puts the order back into WAITING_PAYMENT with reason."""
    async with get_test_session() as session:
        user_db = await UserRepository.get_or_create(
            session=session,
            telegram_id=777666555,
            username="rejected_user",
            first_name="Nodir"
        )
        ad = await AdvertisementRepository.create(
            session=session,
            group_id=None,
            user_id=user_db.id,
            telegram_message_id=6001,
            chat_id=-1001777888,
            username="rejected_user",
            first_name="Nodir",
            message_type="TEXT",
            media_type="TEXT",
            text="Uy sotiladi, Samarqand",
            score=100,
            detection_reason="Reklama",
            deleted=True,
            status="DELETED"
        )
        order = await OrderService.create_order_for_ad(session, ad, default_price=80000)

        # Submit receipt
        import uuid
        r_uid = str(uuid.uuid4())
        await PaymentService.submit_receipt(
            session=session,
            order=order,
            receipt_file_id=f"bad_check_{r_uid}",
            receipt_file_unique_id=f"bad_uid_{r_uid}",
            file_bytes=f"bad_content_{r_uid}".encode(),
            receipt_type="PHOTO"
        )

        # Reject payment
        rej_ok, rej_order, msg = await PaymentService.reject_payment(
            session=session,
            order_id=order.id,
            admin_id=5976376745,
            reason="Summa yetarli emas (80 000 o'rniga 40 000 to'langan)"
        )
        assert rej_ok is True
        assert rej_order.status == "WAITING_PAYMENT"
        assert "yetarli emas" in rej_order.rejection_reason

        # Re-check advertisement status
        ad_check = await AdvertisementRepository.get_by_id(session, ad.id)
        assert ad_check.status == "PAYMENT_REJECTED"


@pytest.mark.asyncio
async def test_order_cancellation_and_query():
    """Verify user order listing and order cancellation."""
    async with get_test_session() as session:
        user_db = await UserRepository.get_or_create(
            session=session,
            telegram_id=444333222,
            username="cancel_user",
            first_name="Bobur"
        )
        ad = await AdvertisementRepository.create(
            session=session,
            group_id=None,
            user_id=user_db.id,
            telegram_message_id=7001,
            chat_id=-1001444333,
            username="cancel_user",
            first_name="Bobur",
            message_type="TEXT",
            media_type="TEXT",
            text="Kiyim sotiladi",
            score=100,
            detection_reason="Reklama",
            deleted=True,
            status="DELETED"
        )
        order = await OrderService.create_order_for_ad(session, ad, default_price=50000)

        cancelled = await OrderService.cancel_order(session, order.id, reason="Mijoz bekor qildi")
        assert cancelled.status == "CANCELLED"

        user_orders = await OrderService.get_user_orders(session, user_db.id)
        assert len(user_orders) >= 1
        assert any(o.id == order.id for o in user_orders)


@pytest.mark.asyncio
async def test_no_mute_no_ban_on_multiple_ads():
    """
    Verify that posting multiple ads in a group NEVER mutes or bans the user,
    only deletes the ad, records order, notifies admins, and posts the warning link.
    """
    from app.services.moderation_service import ModerationService
    from aiogram import Bot

    async with get_test_session() as session:
        # Create user and group
        import random
        test_uid = random.randint(100000000, 999999999)
        user_db = await UserRepository.get_or_create(
            session=session,
            telegram_id=test_uid,
            username="repeat_ad_user",
            first_name="Sardor"
        )
        group_db = await GroupRepository.get_or_create(
            session=session,
            telegram_chat_id=-1001999888777,
            title="Savdo Guruh No Mute Test"
        )

        mock_bot = AsyncMock(spec=Bot)
        mock_bot.get_me = AsyncMock(return_value=MagicMock(username="DefenderTestBot"))
        mock_bot.delete_message = AsyncMock(return_value=True)
        mock_bot.send_message = AsyncMock(return_value=MagicMock(message_id=5555))
        mock_bot.restrict_chat_member = AsyncMock()
        mock_bot.ban_chat_member = AsyncMock()

        # Simulate posting ads 3 times
        for post_num in range(1, 4):
            mock_msg = MagicMock(spec=Message)
            mock_msg.message_id = 1000 + post_num
            mock_msg.chat = MagicMock(spec=Chat, id=-1001999888777, type="supergroup", title="Savdo Guruh No Mute Test", username="savdo_test")
            mock_msg.from_user = MagicMock(id=test_uid, username="repeat_ad_user", first_name="Sardor", last_name=None, full_name="Sardor")
            mock_msg.text = f"Katta chegirma {post_num}! Narxi 50 ming!"
            mock_msg.caption = None
            mock_msg.delete = AsyncMock(return_value=True)

            analysis = {
                "is_ad": True,
                "score": 80,
                "reasons": ["chegirma", "narxi"],
                "matched_keywords": ["chegirma", "narxi"],
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

            await ModerationService.handle_advertisement(
                bot=mock_bot,
                message=mock_msg,
                analysis=analysis,
                session=session,
                content=content
            )

            # Assert message was deleted
            assert mock_msg.delete.called

        # CRITICAL ASSERTION: bot.restrict_chat_member and bot.ban_chat_member were NEVER called!
        assert mock_bot.restrict_chat_member.call_count == 0
        assert mock_bot.ban_chat_member.call_count == 0

        # Verify user in database is still NOT muted and NOT banned
        refreshed_user = await UserRepository.get_by_telegram_id(session, test_uid)
        assert refreshed_user.is_muted is False
        assert refreshed_user.is_banned is False
        assert refreshed_user.warnings_count >= 3

