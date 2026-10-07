import hashlib
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
from aiogram import Bot
from aiogram.types import Message

from app.services.ocr_service import OCRService
from app.utils.logger import logger


class ContentExtractor:
    """
    Universal Content Parser and Deduplication Engine for Telegram Updates.
    
    Supports:
    - message, edited_message, channel_post, edited_channel_post
    - Text, Caption, Photo extraction & OCR integration
    - Content hashing and edit change tracking
    """
    _seen_hashes: "OrderedDict[Tuple[int, int], str]" = OrderedDict()
    MAX_SEEN_CACHE = 10000

    @classmethod
    def compute_hash(
        cls,
        text: str = "",
        caption: str = "",
        ocr_text: str = "",
        photo_id: str = ""
    ) -> str:
        """Computes a deterministic SHA-256 hash for message content components."""
        clean_text = text.strip()
        clean_caption = caption.strip()
        clean_ocr = ocr_text.strip()
        clean_photo = photo_id.strip()
        payload = f"T:{clean_text}|C:{clean_caption}|O:{clean_ocr}|P:{clean_photo}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def get_cached_hash(cls, chat_id: int, message_id: int) -> Optional[str]:
        """Retrieves the previous content hash for a message."""
        return cls._seen_hashes.get((chat_id, message_id))

    @classmethod
    def set_cached_hash(cls, chat_id: int, message_id: int, content_hash: str) -> None:
        """Stores or updates the content hash for a message."""
        key = (chat_id, message_id)
        if key in cls._seen_hashes:
            cls._seen_hashes.move_to_end(key)
        cls._seen_hashes[key] = content_hash
        while len(cls._seen_hashes) > cls.MAX_SEEN_CACHE:
            cls._seen_hashes.popitem(last=False)

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the seen hashes cache (useful for testing)."""
        cls._seen_hashes.clear()

    @classmethod
    async def extract_message_content(
        cls,
        message: Message,
        bot: Optional[Bot] = None,
        is_edited: bool = False,
        update_type: str = "message",
        ocr_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extracts, combines, and hashes message content across text, caption, and photo OCR.
        
        Returns unified content payload:
        {
            "text": str,
            "caption": str,
            "ocr_text": str,
            "combined_text": str,
            "has_photo": bool,
            "is_edited": bool,
            "message_id": int,
            "chat_id": int,
            "user_id": int,
            "content_hash": str,
            "is_duplicate": bool,
            "update_type": str
        }
        """
        text = message.text or ""
        caption = message.caption or ""
        has_photo = bool(message.photo)
        photo_id = message.photo[-1].file_id if has_photo else ""

        # 1. OCR Extraction for Photos
        ocr_text = ""
        if ocr_override is not None:
            ocr_text = ocr_override.strip()
        elif has_photo and bot:
            ocr_text = await OCRService.extract_text_from_photo(bot, message.photo)
            if ocr_text:
                logger.info(f"📸 OCR matn aniqlandi | chat={message.chat.id} msg={message.message_id}: '{ocr_text[:80]}'")

        # 2. Combine textual components
        parts = []
        if text.strip():
            parts.append(text.strip())
        if caption.strip():
            parts.append(caption.strip())
        if ocr_text.strip():
            parts.append(ocr_text.strip())

        combined_text = " ".join(parts).strip()

        # 3. Detect edit state
        effective_is_edited = is_edited or bool(message.edit_date)

        # 4. Extract IDs
        message_id = message.message_id
        chat_id = message.chat.id
        user_id = 0
        if message.from_user:
            user_id = message.from_user.id
        elif message.sender_chat:
            user_id = message.sender_chat.id

        # 5. Content Hashing & Deduplication
        content_hash = cls.compute_hash(text=text, caption=caption, ocr_text=ocr_text, photo_id=photo_id)
        is_duplicate = False

        if effective_is_edited:
            old_hash = cls.get_cached_hash(chat_id, message_id)
            if old_hash is not None and old_hash == content_hash:
                is_duplicate = True
            else:
                cls.set_cached_hash(chat_id, message_id, content_hash)
        else:
            cls.set_cached_hash(chat_id, message_id, content_hash)

        return {
            "text": text,
            "caption": caption,
            "ocr_text": ocr_text,
            "combined_text": combined_text,
            "has_photo": has_photo,
            "is_edited": effective_is_edited,
            "message_id": message_id,
            "chat_id": chat_id,
            "user_id": user_id,
            "content_hash": content_hash,
            "is_duplicate": is_duplicate,
            "update_type": update_type
        }
