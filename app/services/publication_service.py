from datetime import datetime, timezone
from typing import Optional, Tuple, Set, Any
from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.models.advertisement import Advertisement
from app.database.models.order import Order
from app.database.repositories.ad_repo import AdvertisementRepository
from app.database.repositories.order_repo import OrderRepository
from app.utils.logger import logger


class PublicationService:
    # Set of (chat_id, message_id) tuples to instantly ignore in moderation without DB hit
    _bot_published_messages: Set[Tuple[int, int]] = set()

    @classmethod
    def is_bot_published(cls, chat_id: int, message_id: int) -> bool:
        return (chat_id, message_id) in cls._bot_published_messages

    @classmethod
    def register_bot_published(cls, chat_id: int, message_id: int) -> None:
        cls._bot_published_messages.add((chat_id, message_id))
        if len(cls._bot_published_messages) > 10000:
            # Pop roughly 10%
            cls._bot_published_messages = set(list(cls._bot_published_messages)[-5000:])

    @classmethod
    async def publish_advertisement(
        cls,
        bot: Bot,
        session: AsyncSession,
        ad: Advertisement,
        order: Optional[Order] = None
    ) -> Tuple[bool, Optional[int], str]:
        """
        Publishes the approved advertisement into its original group or target chat.
        Idempotent: if already published, returns existing published_message_id.
        """
        ad_id = ad.id
        if ad.published_message_id:
            logger.info(f"ℹ️ Reklama allaqachon chop etilgan: ad_id={ad_id} msg_id={ad.published_message_id}")
            return True, ad.published_message_id, "Reklama allaqachon chop etilgan."

        order_id = order.id if order else None
        target_chat_id = (
            ad.published_chat_id
            or ad.chat_id
            or (ad.group.telegram_chat_id if ad.group else None)
            or (settings.publish_channel_id_int if hasattr(settings, "publish_channel_id_int") else None)
        )

        if not target_chat_id:
            if order_id:
                await OrderRepository.update_status(session, order_id, "PUBLICATION_FAILED")
            await AdvertisementRepository.update_status(session, ad_id, "PUBLICATION_FAILED")
            return False, None, "Guruh chat_id topilmadi."

        media_type = (ad.media_type or "TEXT").upper()
        media_file_id = ad.media_file_id
        orig_caption = ad.original_caption or ad.caption or ad.text
        orig_text = ad.original_text or ad.text

        tag = "\n\n📢 #reklama #hamkorlik"
        sent_msg_id = None

        try:
            if media_type == "PHOTO" and media_file_id:
                caption = (orig_caption or "").strip()
                full_caption = (caption + tag) if caption else "📢 #reklama #hamkorlik"
                msg = await bot.send_photo(
                    chat_id=target_chat_id,
                    photo=media_file_id,
                    caption=full_caption[:1024]
                )
                sent_msg_id = msg.message_id
            elif media_type == "VIDEO" and media_file_id:
                caption = (orig_caption or "").strip()
                full_caption = (caption + tag) if caption else "📢 #reklama #hamkorlik"
                msg = await bot.send_video(
                    chat_id=target_chat_id,
                    video=media_file_id,
                    caption=full_caption[:1024]
                )
                sent_msg_id = msg.message_id
            elif media_type == "ANIMATION" and media_file_id:
                caption = (orig_caption or "").strip()
                full_caption = (caption + tag) if caption else "📢 #reklama #hamkorlik"
                msg = await bot.send_animation(
                    chat_id=target_chat_id,
                    animation=media_file_id,
                    caption=full_caption[:1024]
                )
                sent_msg_id = msg.message_id
            elif media_type == "DOCUMENT" and media_file_id:
                caption = (orig_caption or "").strip()
                full_caption = (caption + tag) if caption else "📢 #reklama #hamkorlik"
                msg = await bot.send_document(
                    chat_id=target_chat_id,
                    document=media_file_id,
                    caption=full_caption[:1024]
                )
                sent_msg_id = msg.message_id
            elif media_type == "AUDIO" and media_file_id:
                caption = (orig_caption or "").strip()
                full_caption = (caption + tag) if caption else "📢 #reklama #hamkorlik"
                msg = await bot.send_audio(
                    chat_id=target_chat_id,
                    audio=media_file_id,
                    caption=full_caption[:1024]
                )
                sent_msg_id = msg.message_id
            elif media_type == "VOICE" and media_file_id:
                caption = (orig_caption or "").strip()
                full_caption = (caption + tag) if caption else "📢 #reklama #hamkorlik"
                msg = await bot.send_voice(
                    chat_id=target_chat_id,
                    voice=media_file_id,
                    caption=full_caption[:1024]
                )
                sent_msg_id = msg.message_id
            elif media_type == "VIDEO_NOTE" and media_file_id:
                msg = await bot.send_video_note(
                    chat_id=target_chat_id,
                    video_note=media_file_id
                )
                sent_msg_id = msg.message_id
            else:
                raw_text = (orig_text or "").strip()
                full_text = (raw_text + tag) if raw_text else "📢 #reklama #hamkorlik"
                msg = await bot.send_message(
                    chat_id=target_chat_id,
                    text=full_text
                )
                sent_msg_id = msg.message_id

            # Register so the bot doesn't detect its own ad!
            cls.register_bot_published(target_chat_id, sent_msg_id)

            # Update DB records
            await AdvertisementRepository.set_published(
                session=session,
                ad_id=ad_id,
                published_message_id=sent_msg_id,
                published_chat_id=target_chat_id
            )

            if order_id:
                await OrderRepository.update_status(session, order_id, "PUBLISHED")

            logger.info(
                f"🚀 Reklama guruhga muvaffaqiyatli chop etildi | ad_id={ad_id} "
                f"chat_id={target_chat_id} msg_id={sent_msg_id}"
            )
            return True, sent_msg_id, "Reklama muvaffaqiyatli chop etildi."

        except Exception as e:
            logger.error(f"❌ Reklamani guruhga chop etishda xatolik | ad_id={ad_id}: {e}", exc_info=True)
            if order_id:
                await OrderRepository.update_status(session, order_id, "PUBLICATION_FAILED")
            await AdvertisementRepository.update_status(session, ad_id, "PUBLICATION_FAILED")
            return False, None, f"Chop etishda xatolik: {e}"

    @classmethod
    async def publish_advertising_request(
        cls,
        bot: Bot,
        session: AsyncSession,
        req: Any
    ) -> Tuple[bool, Optional[int], str]:
        """
        Publishes structured AdvertisingRequest to the target group or channel.
        Includes all uploaded media, #reklama tag, and registers published ID.
        """
        from aiogram.types import InputMediaPhoto, InputMediaVideo
        from app.database.repositories.ad_request_repo import AdvertisingRequestRepository

        target_chat_id = (
            req.published_chat_id
            or (req.group.telegram_chat_id if req.group else None)
            or (settings.publish_channel_id_int if hasattr(settings, "publish_channel_id_int") else None)
            or (settings.target_group_id_int if hasattr(settings, "target_group_id_int") else None)
        )

        if not target_chat_id:
            return False, None, "Guruh yoki kanal chat_id topilmadi."

        tag = "\n\n📢 #reklama #hamkorlik"
        full_text = ((req.preview_text or "").strip() + tag)[:4096]

        media_items = await AdvertisingRequestRepository.get_media_items(session, req.id)
        sent_msg_id = None

        try:
            if not media_items:
                msg = await bot.send_message(
                    chat_id=target_chat_id,
                    text=full_text,
                    parse_mode="HTML"
                )
                sent_msg_id = msg.message_id
            elif len(media_items) == 1:
                m = media_items[0]
                caption_text = full_text[:1024]
                if m.media_type == "PHOTO":
                    msg = await bot.send_photo(
                        chat_id=target_chat_id,
                        photo=m.file_id,
                        caption=caption_text,
                        parse_mode="HTML"
                    )
                    sent_msg_id = msg.message_id
                elif m.media_type == "VIDEO":
                    msg = await bot.send_video(
                        chat_id=target_chat_id,
                        video=m.file_id,
                        caption=caption_text,
                        parse_mode="HTML"
                    )
                    sent_msg_id = msg.message_id
                else:
                    msg = await bot.send_message(chat_id=target_chat_id, text=full_text, parse_mode="HTML")
                    sent_msg_id = msg.message_id
            else:
                # Media group (up to 10 photos/videos)
                mg = []
                for idx, m in enumerate(media_items[:10]):
                    caption_piece = full_text[:1024] if idx == 0 else None
                    mode_piece = "HTML" if idx == 0 else None
                    if m.media_type == "PHOTO":
                        mg.append(InputMediaPhoto(media=m.file_id, caption=caption_piece, parse_mode=mode_piece))
                    elif m.media_type == "VIDEO":
                        mg.append(InputMediaVideo(media=m.file_id, caption=caption_piece, parse_mode=mode_piece))
                if mg:
                    msgs = await bot.send_media_group(chat_id=target_chat_id, media=mg)
                    sent_msg_id = msgs[0].message_id
                else:
                    msg = await bot.send_message(chat_id=target_chat_id, text=full_text, parse_mode="HTML")
                    sent_msg_id = msg.message_id

            # Register so bot does not delete its own published ad
            cls.register_bot_published(target_chat_id, sent_msg_id)

            req.published_message_id = sent_msg_id
            req.published_chat_id = target_chat_id
            req.published_at = datetime.now(timezone.utc)
            req.status = "PUBLISHED"
            await session.flush()

            logger.info(f"🚀 Reklama so‘rovi guruhga muvaffaqiyatli chop etildi | req={req.request_number} chat={target_chat_id} msg={sent_msg_id}")
            return True, sent_msg_id, "Reklama muvaffaqiyatli chop etildi."

        except Exception as e:
            logger.error(f"❌ Reklama so‘rovini chop etishda xatolik | req={req.request_number}: {e}", exc_info=True)
            req.status = "PUBLICATION_FAILED"
            await session.flush()
            return False, None, f"Chop etishda xatolik: {e}"

    @classmethod
    async def recover_unfinished_publications(cls, bot: Bot, session: AsyncSession) -> int:
        """
        Scans for orders that were approved (PAYMENT_APPROVED, APPROVED, READY_TO_PUBLISH)
        prior to restart but not yet published. Publishes them safely and idempotently.
        """
        stmt = (
            select(Order)
            .where(Order.status.in_(["PAYMENT_APPROVED", "APPROVED", "READY_TO_PUBLISH"]))
            .options(selectinload(Order.advertisement))
        )
        res = await session.execute(stmt)
        unfinished_orders = list(res.scalars().all())
        recovered_count = 0
        for order in unfinished_orders:
            if order.advertisement and not order.advertisement.published_message_id:
                logger.info(f"🔄 Tiklash jarayoni: tugallanmagan reklama chop etilmoqda: order={order.order_number}")
                ok, _, _ = await cls.publish_advertisement(bot, session, order.advertisement, order)
                if ok:
                    recovered_count += 1

        # Also recover structured AdvertisingRequests
        from app.database.models.advertising_request import AdvertisingRequest
        req_stmt = (
            select(AdvertisingRequest)
            .where(
                AdvertisingRequest.status.in_(["READY_TO_PUBLISH", "PAYMENT_APPROVED"]),
                AdvertisingRequest.published_message_id.is_(None)
            )
            .options(
                selectinload(AdvertisingRequest.group),
                selectinload(AdvertisingRequest.media_items)
            )
        )
        req_res = await session.execute(req_stmt)
        unfinished_reqs = list(req_res.scalars().all())
        for req_item in unfinished_reqs:
            logger.info(f"🔄 Tiklash jarayoni: tugallanmagan so‘rov chop etilmoqda: req={req_item.request_number}")
            ok, _, _ = await cls.publish_advertising_request(bot, session, req_item)
            if ok:
                recovered_count += 1

        return recovered_count

