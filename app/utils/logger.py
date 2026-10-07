import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from app.config.settings import settings


class CustomFormatter(logging.Formatter):
    """Custom formatter with optional ANSI colors for console output."""
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_color: bool = True):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.use_color = use_color and sys.platform != "win32" or "WT_SESSION" in os.environ

    def format(self, record: logging.LogRecord) -> str:
        orig_levelname = record.levelname
        if self.use_color and record.levelno in self.COLORS:
            color = self.COLORS[record.levelno]
            record.levelname = f"{color}{orig_levelname}{self.RESET}"
        formatted = super().format(record)
        record.levelname = orig_levelname
        return formatted


def setup_logger(name: str = "defender_bot") -> logging.Logger:
    """Configures and returns application logger with console and rotating file handlers."""
    log_level_name = getattr(settings, "LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "bot.log")

    app_logger = logging.getLogger(name)
    app_logger.setLevel(log_level)

    # Avoid duplicate handlers if setup_logger called multiple times
    if not app_logger.handlers:
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(CustomFormatter(use_color=True))
        app_logger.addHandler(console_handler)

        # Rotating File Handler (10MB max, 5 backup files)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        app_logger.addHandler(file_handler)

    # Suppress verbose 3rd party logs
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return app_logger


logger = setup_logger()
