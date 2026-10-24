import os
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram Bot
    BOT_TOKEN: str = Field(
        default="1234567890:TEST_TOKEN_DEFAULT_DEFENDER_BOT",
        description="Telegram Bot Token from @BotFather"
    )
    OWNER_ID: int = Field(
        default=123456789,
        description="Telegram ID of the bot owner"
    )
    ADMINS: Union[str, List[int]] = Field(default="", description="Comma-separated Telegram IDs of admins")
    ADMIN_USERNAME: str = Field(default="ads_bot_service", description="Username of admin for contact buttons")
    AD_PAYMENT_CARD: str = Field(default="5614683515901387", description="Card number for ad payments")
    AD_CARDHOLDER_NAME: str = Field(default="ALISHER USMONOV", description="Cardholder name for ad payments")
    AD_PAYMENT_INSTRUCTIONS: str = Field(
        default="To‘lovni amalga oshirgach, to‘lov chekini ushbu botga yuboring.\nEslatma: Reklama to‘lov administrator tomonidan tasdiqlangandan keyingina joylashtiriladi.",
        description="Payment instructions shown to advertiser"
    )
    AD_PRICE: str = Field(default="150 000 so‘m", description="Standard price for ad placement")
    MIN_AD_PRICE: int = Field(default=1000, description="Minimum price in UZS")
    MAX_AD_PRICE: int = Field(default=100_000_000, description="Maximum price in UZS")
    TARGET_GROUP_ID: Union[str, int, None] = Field(default=None, description="Explicit target group ID to moderate")
    AD_PUBLISH_CHANNEL_ID: Union[str, int, None] = Field(default=None, description="Optional separate destination chat ID for publishing")
    TELEGRAM_PROXY: str = Field(default="", description="Optional HTTP/SOCKS5 proxy for Telegram API requests")
    REDIS_URL: str = Field(default="", description="Optional Redis URL for caching/coordination")
    SCHEDULER_INTERVAL_SECONDS: int = Field(default=30, description="Seconds interval for background tasks")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/defender_bot",
        description="Async SQLAlchemy database connection URL"
    )

    # Moderation Rules
    WARNING_DELETE_SECONDS: int = Field(default=0, description="Seconds before auto-deleting warning message (0 to keep)")
    ADVERTISEMENT_THRESHOLD: int = Field(default=40, description="Minimum score to flag as advertisement")
    AUTO_MUTE: bool = Field(default=False, description="Enable automatic mute escalation")
    AUTO_BAN: bool = Field(default=False, description="Enable automatic ban escalation")
    FILTER_ADMINS: bool = Field(default=False, description="Whether to filter group admins too")

    # OCR Settings
    OCR_ENABLED: bool = Field(default=True, description="Enable image OCR detection for photos")
    TESSERACT_CMD: str = Field(default="", description="Path to tesseract executable if not in PATH")

    # Escalation Actions
    FIRST_ACTION: str = Field(default="warning", description="Action for 1st offense (warning)")
    SECOND_ACTION: str = Field(default="warning", description="Action for 2nd offense")
    THIRD_ACTION: str = Field(default="warning", description="Action for 3rd offense")
    FOURTH_ACTION: str = Field(default="warning", description="Action for 4th offense")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")

    # Web Admin Panel
    WEB_ADMIN_ENABLED: bool = Field(default=True, description="Enable FastAPI admin dashboard")
    WEB_ADMIN_HOST: str = Field(default="0.0.0.0", description="Admin panel binding host")
    WEB_ADMIN_PORT: int = Field(default=8090, description="Admin panel port")
    WEB_ADMIN_SECRET_KEY: str = Field(
        default="super-secret-random-key-change-this-in-production-123456789",
        description="JWT session secret key"
    )
    WEB_ADMIN_USERNAME: str = Field(default="admin", description="Web admin initial login")
    WEB_ADMIN_PASSWORD: str = Field(default="admin12345", description="Web admin initial password")

    # OLX.uz Integration
    OLX_ENABLED: bool = Field(default=True, description="Enable OLX automatic posting and management")
    OLX_AUTO_POST: bool = Field(default=True, description="Automatically post advertisements to OLX upon approval")
    OLX_SESSION_FILE: str = Field(default="app/data/olx_session.json", description="Path to OLX Playwright session state JSON")
    OLX_HEADLESS: bool = Field(default=True, description="Whether to run OLX Playwright browser in headless mode")
    OLX_DEFAULT_CITY: str = Field(default="Toshkent", description="Default city for OLX advert placement")
    OLX_DEFAULT_PHONE: str = Field(default="", description="Default contact phone for OLX adverts if user did not specify")

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
            ".env"
        ),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("ADMINS", mode="before")
    @classmethod
    def parse_admins(cls, v: Union[str, List[int], int]) -> List[int]:
        if isinstance(v, list):
            return [int(x) for x in v]
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return []

    @property
    def all_admin_ids(self) -> List[int]:
        """Combines OWNER_ID and ADMINS list ensuring uniqueness."""
        admin_set = set(self.ADMINS if isinstance(self.ADMINS, list) else [])
        admin_set.add(self.OWNER_ID)
        return list(admin_set)

    @property
    def target_group_id_int(self) -> Union[int, None]:
        if not self.TARGET_GROUP_ID:
            return None
        try:
            return int(str(self.TARGET_GROUP_ID).strip())
        except (ValueError, TypeError):
            return None

    @property
    def publish_channel_id_int(self) -> Union[int, None]:
        if not self.AD_PUBLISH_CHANNEL_ID:
            return None
        try:
            return int(str(self.AD_PUBLISH_CHANNEL_ID).strip())
        except (ValueError, TypeError):
            return None

    @property
    def sync_database_url(self) -> str:
        """Returns standard psycopg/postgresql URL for synchronous Alembic migrations."""
        url = self.DATABASE_URL
        if "+asyncpg" in url:
            return url.replace("+asyncpg", "")
        return url


settings = Settings()
