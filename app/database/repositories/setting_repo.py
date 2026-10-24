from typing import Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.setting import Setting


class SettingRepository:
    DEFAULT_SETTINGS = {
        "enabled": "true",
        "delete_ads": "true",
        "warning_enabled": "true",
        "auto_mute": "false",
        "auto_ban": "false",
        "warning_delete_seconds": "0",
        "advertisement_threshold": "40",
        "filter_admins": "false",
        "filter_links": "true",
        "filter_photos": "true",
        "filter_videos": "true",
        "filter_documents": "true",
        "first_action": "warning",
        "second_action": "warning",
        "third_action": "warning",
        "fourth_action": "warning",
        "warning_message": (
            "⚠️ <b>REKLAMA TAQIQLANGAN</b>\n\n"
            "Hurmatli foydalanuvchi, guruhda reklama yuborish taqiqlangan.\n"
            "Reklama yoki e’lon joylashtirish bo‘yicha administratorga murojaat qiling.\n"
            "Iltimos, guruh qoidalariga rioya qiling."
        )
    }

    @staticmethod
    async def get_all_group_settings(session: AsyncSession, group_id: Optional[int]) -> Dict[str, str]:
        """Fetches all settings for a group, merging defaults with custom database values."""
        settings_dict = dict(SettingRepository.DEFAULT_SETTINGS)

        stmt = select(Setting).where(Setting.group_id == group_id)
        result = await session.execute(stmt)
        for s in result.scalars().all():
            settings_dict[s.key] = s.value

        return settings_dict

    @staticmethod
    async def get_setting(session: AsyncSession, group_id: Optional[int], key: str, default: Optional[str] = None) -> str:
        stmt = select(Setting).where(Setting.group_id == group_id, Setting.key == key)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        if setting:
            return setting.value
        return default if default is not None else SettingRepository.DEFAULT_SETTINGS.get(key, "")

    @staticmethod
    async def set_setting(session: AsyncSession, group_id: Optional[int], key: str, value: str) -> Setting:
        stmt = select(Setting).where(Setting.group_id == group_id, Setting.key == key)
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = str(value)
        else:
            setting = Setting(group_id=group_id, key=key, value=str(value))
            session.add(setting)

        await session.commit()
        await session.refresh(setting)
        return setting
