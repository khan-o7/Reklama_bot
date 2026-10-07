import time
from typing import Set, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.list_repo import ListRepository
from app.database.repositories.setting_repo import SettingRepository
from app.utils.logger import logger


class CacheService:
    """
    High-performance in-memory cache for Whitelist, Blacklist, and Group Settings.
    Ensures message checks are near 0ms without spamming the database on every chat message.
    """
    _instance: Optional["CacheService"] = None

    def __init__(self):
        self.whitelist_domains: Set[str] = {
            "gov.uz", "edu.uz", "customs.uz", "my.gov.uz", "lex.uz", "dtm.uz"
        }
        self.blacklist_words: Set[str] = set()
        self.blacklist_domains: Set[str] = set()
        self.blacklist_usernames: Set[str] = set()
        self.group_settings: Dict[int, Dict[str, str]] = {}
        self.last_sync: float = 0
        self.ttl: float = 60.0  # Sync with DB every 60 seconds

    @classmethod
    def get_instance(cls) -> "CacheService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def sync_with_db(self, session: AsyncSession, force: bool = False) -> None:
        """Syncs in-memory sets with database if TTL expired or forced."""
        now = time.time()
        if not force and (now - self.last_sync) < self.ttl:
            return

        try:
            # 1. Sync Whitelist
            wl_items = await ListRepository.get_all_whitelist(session)
            new_wl = {"gov.uz", "edu.uz", "customs.uz", "my.gov.uz", "lex.uz", "dtm.uz"}
            for item in wl_items:
                new_wl.add(item.value.lower())
            self.whitelist_domains = new_wl

            # 2. Sync Blacklist
            bl_items = await ListRepository.get_all_blacklist(session)
            words = set()
            domains = set()
            usernames = set()
            for item in bl_items:
                val = item.value.lower()
                if item.type == "word":
                    words.add(val)
                elif item.type == "domain":
                    domains.add(val)
                elif item.type == "username":
                    usernames.add(val.lstrip("@"))
            self.blacklist_words = words
            self.blacklist_domains = domains
            self.blacklist_usernames = usernames

            self.last_sync = now
            logger.debug(
                f"Cache synchronized: WL={len(self.whitelist_domains)}, "
                f"BL_words={len(self.blacklist_words)}, BL_domains={len(self.blacklist_domains)}"
            )
        except Exception as e:
            logger.error(f"Error synchronizing cache with DB: {e}")

    def invalidate(self) -> None:
        """Invalidates cache so next check refreshes immediately."""
        self.last_sync = 0

    def get_whitelist(self) -> List[str]:
        return list(self.whitelist_domains)

    def get_blacklist_words(self) -> Set[str]:
        return self.blacklist_words

    def get_blacklist_domains(self) -> Set[str]:
        return self.blacklist_domains

    def get_blacklist_usernames(self) -> Set[str]:
        return self.blacklist_usernames


cache = CacheService.get_instance()
