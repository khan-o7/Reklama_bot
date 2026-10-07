from fastapi import APIRouter, Form, Depends, responses, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.web.auth import get_current_admin
from app.database.models.admin_user import AdminUser
from app.database.repositories.list_repo import ListRepository
from app.database.repositories.setting_repo import SettingRepository
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.audit_repo import AuditRepository
from app.database.repositories.ad_repo import AdvertisementRepository
from app.services.cache_service import cache

router = APIRouter(prefix="/api")


@router.post("/whitelist/add")
async def api_whitelist_add(
    value: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    await ListRepository.add_to_whitelist(session, "domain", value)
    cache.invalidate()
    await cache.sync_with_db(session, force=True)
    await AuditRepository.create(session, "whitelist_added", details=f"domain: {value} by {current_admin.username}")
    return responses.RedirectResponse(url="/lists", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/whitelist/delete")
async def api_whitelist_delete(
    value: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    await ListRepository.remove_from_whitelist(session, value)
    cache.invalidate()
    await cache.sync_with_db(session, force=True)
    await AuditRepository.create(session, "whitelist_removed", details=f"domain: {value} by {current_admin.username}")
    return responses.RedirectResponse(url="/lists", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/blacklist/add")
async def api_blacklist_add(
    type: str = Form(...),
    value: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    await ListRepository.add_to_blacklist(session, type, value)
    cache.invalidate()
    await cache.sync_with_db(session, force=True)
    await AuditRepository.create(session, "blacklist_added", details=f"{type}: {value} by {current_admin.username}")
    return responses.RedirectResponse(url="/lists", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/blacklist/delete")
async def api_blacklist_delete(
    value: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    await ListRepository.remove_from_blacklist(session, value)
    cache.invalidate()
    await cache.sync_with_db(session, force=True)
    await AuditRepository.create(session, "blacklist_removed", details=f"value: {value} by {current_admin.username}")
    return responses.RedirectResponse(url="/lists", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/settings/update")
async def api_settings_update(
    delete_ads: str = Form("false"),
    warning_enabled: str = Form("false"),
    auto_mute: str = Form("false"),
    auto_ban: str = Form("false"),
    advertisement_threshold: str = Form("40"),
    warning_delete_seconds: str = Form("15"),
    first_action: str = Form("warning"),
    second_action: str = Form("mute_10m"),
    third_action: str = Form("mute_1h"),
    fourth_action: str = Form("ban"),
    warning_message: str = Form(""),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    settings_map = {
        "delete_ads": delete_ads,
        "warning_enabled": warning_enabled,
        "auto_mute": auto_mute,
        "auto_ban": auto_ban,
        "advertisement_threshold": advertisement_threshold,
        "warning_delete_seconds": warning_delete_seconds,
        "first_action": first_action,
        "second_action": second_action,
        "third_action": third_action,
        "fourth_action": fourth_action,
        "warning_message": warning_message,
    }

    for k, v in settings_map.items():
        await SettingRepository.set_setting(session, None, k, v)

    await AuditRepository.create(session, "settings_changed", details=f"Updated by {current_admin.username}")
    return responses.RedirectResponse(url="/settings?message=Sozlamalar+saqlandi", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/{user_id}/reset-warnings")
async def api_user_reset_warnings(
    user_id: int,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    await UserRepository.reset_warnings(session, user_id)
    await UserRepository.set_muted(session, user_id, False)
    await UserRepository.set_banned(session, user_id, False)
    await AuditRepository.create(session, "user_warnings_reset", user_id=user_id, details=f"By {current_admin.username}")
    return responses.RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/chart-data")
async def api_chart_data(
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    data = await AdvertisementRepository.get_chart_data_7_days(session)
    return {"data": data}
