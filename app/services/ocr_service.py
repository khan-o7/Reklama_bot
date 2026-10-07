import io
import os
import shutil
from typing import Optional, Union
from aiogram import Bot
from aiogram.types import PhotoSize
from PIL import Image

from app.config.settings import settings
from app.utils.logger import logger

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


class OCRService:
    """
    Asynchronous Optical Character Recognition (OCR) Service for Telegram Images.
    Extracts text from images using pytesseract with resilient fallbacks.
    """
    _tesseract_available: Optional[bool] = None

    @classmethod
    def is_available(cls) -> bool:
        """Checks if pytesseract and the underlying tesseract binary are available."""
        if not settings.OCR_ENABLED:
            return False

        if not HAS_PYTESSERACT:
            return False

        if cls._tesseract_available is not None:
            return cls._tesseract_available

        # Configure custom binary path if provided in settings or common Windows locations
        if settings.TESSERACT_CMD and os.path.exists(settings.TESSERACT_CMD):
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
            cls._tesseract_available = True
            return True

        common_win_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        ]
        for path in common_win_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                cls._tesseract_available = True
                return True

        # Check if 'tesseract' is in PATH
        if shutil.which("tesseract"):
            cls._tesseract_available = True
            return True

        logger.debug("Tesseract OCR binary not found on system PATH. OCR text extraction will be skipped.")
        cls._tesseract_available = False
        return False

    @classmethod
    def extract_text_from_bytes(cls, image_bytes: bytes) -> str:
        """Extracts text from raw image bytes synchronously."""
        if not cls.is_available():
            return ""

        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Try multiple languages if installed, fallback to default
            try:
                text = pytesseract.image_to_string(image, lang="uzb+rus+eng")
            except Exception:
                try:
                    text = pytesseract.image_to_string(image, lang="rus+eng")
                except Exception:
                    text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.debug(f"OCR extraction failed: {e}")
            return ""

    @classmethod
    async def extract_text_from_photo(
        cls,
        bot: Optional[Bot],
        photos: list[PhotoSize]
    ) -> str:
        """
        Downloads the highest resolution photo from Telegram and runs OCR.
        """
        if not bot or not photos:
            return ""

        if not cls.is_available():
            return ""

        try:
            # Telegram provides photo sizes sorted from smallest to largest
            highest_res = photos[-1]
            file_io = io.BytesIO()
            await bot.download(highest_res.file_id, destination=file_io)
            image_bytes = file_io.getvalue()
            return cls.extract_text_from_bytes(image_bytes)
        except Exception as e:
            logger.debug(f"Failed to download and OCR photo from Telegram: {e}")
            return ""
