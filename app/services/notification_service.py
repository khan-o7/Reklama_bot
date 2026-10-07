import asyncio
from datetime import datetime
from typing import Dict, Any, List
from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest

from app.config.settings import settings
from app.utils.logger import logger


class NotificationService:
    @staticmethod
    def format_admin_alert(
        message: Message,
        analysis: Dict[str, Any],
        deleted: bool
    ) -> str:
        """Formats standard alert template according to specification."""
        user = message.from_user
        full_name = user.full_name if user else "Noma'lum"
        if user and user.username:
            full_name += f" (@{user.username})"

        user_id = user.id if user else "Noma'lum"
        group_title = message.chat.title or "Noma'lum guruh"
        chat_id = message.chat.id
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        msg_type = analysis.get("message_type", "TEXT")
        links = analysis.get("links", [])
        links_str = ", ".join(links) if links else "Mavjud emas"
        score = analysis.get("score", 0)
        reasons_list = analysis.get("reasons", [])
        reasons_str = "; ".join(reasons_list) if reasons_list else "Belgilanmagan"

        status_text = "🗑 Xabar guruhdan o‘chirildi." if deleted else "⚠️ Xabarni o‘chirishda xatolik yuz berdi."

        alert_text = (
            f"🚨 <b>REKLAMA ANIQLANDI</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {full_name}\n"
            f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
            f"👥 <b>Guruh:</b> {group_title}\n"
            f"💬 <b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"📅 <b>Vaqt:</b> {now_str}\n"
            f"📦 <b>Xabar turi:</b> {msg_type}\n"
            f"🔗 <b>Reklama linki:</b> {links_str}\n"
            f"📊 <b>Advertisement Score:</b> {score}\n"
            f"📝 <b>Sabablar:</b> {reasons_str}\n\n"
            f"{status_text}"
        )
        return alert_text

    @staticmethod
    async def send_to_admins(
        bot: Bot,
        message: Message,
        analysis: Dict[str, Any],
        deleted: bool
    ) -> None:
        """Sends rich alert and original message copy to all registered admins."""
        alert_text = NotificationService.format_admin_alert(message, analysis, deleted)
        admin_ids = settings.all_admin_ids

        for admin_id in admin_ids:
            for attempt in range(1, 3):
                try:
                    # 1. Send text alert
                    await bot.send_message(
                        chat_id=admin_id,
                        text=alert_text,
                        parse_mode="HTML"
                    )

                    # 2. Try copying original message so admin sees exact media & formatting
                    try:
                        await bot.copy_message(
                            chat_id=admin_id,
                            from_chat_id=message.chat.id,
                            message_id=message.message_id
                        )
                    except Exception as copy_err:
                        # Fallback if original was already deleted or forward restricted:
                        logger.debug(f"Direct copy failed for admin {admin_id}: {copy_err}. Falling back to content re-send.")
                        await NotificationService._fallback_send_content(bot, admin_id, message)
                    break
                except TelegramRetryAfter as e:
                    logger.warning(f"Flood limit when notifying admin {admin_id}. Retrying after {e.retry_after}s.")
                    await asyncio.sleep(e.retry_after)
                except TelegramForbiddenError:
                    logger.debug(f"Bot was blocked by admin {admin_id} or private chat not started.")
                    break
                except Exception as e:
                    if attempt < 2:
                        await asyncio.sleep(1.5)
                    else:
                        logger.warning(f"Could not deliver notification to admin {admin_id}: {e}")

    @staticmethod
    async def _fallback_send_content(bot: Bot, admin_id: int, message: Message) -> None:
        """Reconstructs and sends original media or text if copy_message failed."""
        try:
            caption = message.caption or ""
            caption_prefix = "<i>[Original xabar mazmuni]</i>\n\n"

            if message.text:
                await bot.send_message(chat_id=admin_id, text=f"{caption_prefix}{message.text}")
            elif message.photo:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=message.photo[-1].file_id,
                    caption=f"{caption_prefix}{caption}"
                )
            elif message.video:
                await bot.send_video(
                    chat_id=admin_id,
                    video=message.video.file_id,
                    caption=f"{caption_prefix}{caption}"
                )
            elif message.document:
                await bot.send_document(
                    chat_id=admin_id,
                    document=message.document.file_id,
                    caption=f"{caption_prefix}{caption}"
                )
            elif message.animation:
                await bot.send_animation(
                    chat_id=admin_id,
                    animation=message.animation.file_id,
                    caption=f"{caption_prefix}{caption}"
                )
            elif message.audio:
                await bot.send_audio(
                    chat_id=admin_id,
                    audio=message.audio.file_id,
                    caption=f"{caption_prefix}{caption}"
                )
            elif message.voice:
                await bot.send_voice(
                    chat_id=admin_id,
                    voice=message.voice.file_id,
                    caption=f"{caption_prefix}{caption}"
                )
            elif message.video_note:
                await bot.send_video_note(
                    chat_id=admin_id,
                    video_note=message.video_note.file_id
                )
        except Exception as e:
            logger.debug(f"Fallback content send failed for admin {admin_id}: {e}")
