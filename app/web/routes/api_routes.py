from typing import Optional, List
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
from app.database.repositories.warning_repo import WarningRepository
from app.database.repositories.group_repo import GroupRepository
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


def _parse_ids(ids: str) -> List[int]:
    result = []
    for item in (ids or "").split(","):
        cleaned = item.strip()
        if cleaned.isdigit():
            result.append(int(cleaned))
    return result


# ==========================================
# WARNINGS (OGOHLANTIRISHLAR) ENDPOINTS
# ==========================================

@router.post("/warnings/delete")
async def api_warning_delete(
    warning_id: int = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    success = await WarningRepository.delete_by_id(session, warning_id)
    if success:
        await AuditRepository.create(session, "warning_deleted", details=f"Warning ID {warning_id} deleted by {current_admin.username}")
    return responses.RedirectResponse(url="/warnings", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/warnings/bulk-delete")
async def api_warnings_bulk_delete(
    ids: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    id_list = _parse_ids(ids)
    count = await WarningRepository.delete_multiple(session, id_list)
    await AuditRepository.create(session, "warnings_bulk_deleted", details=f"{count} warnings deleted by {current_admin.username}")
    return responses.RedirectResponse(url="/warnings", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/warnings/clear-all")
async def api_warnings_clear_all(
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    count = await WarningRepository.clear_all(session)
    await AuditRepository.create(session, "warnings_cleared_all", details=f"All {count} warnings cleared by {current_admin.username}")
    return responses.RedirectResponse(url="/warnings", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/warnings/edit")
async def api_warning_edit(
    warning_id: int = Form(...),
    warning_type: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    await WarningRepository.update_warning(session, warning_id, warning_type.strip())
    await AuditRepository.create(session, "warning_edited", details=f"Warning ID {warning_id} updated to '{warning_type}' by {current_admin.username}")
    return responses.RedirectResponse(url="/warnings", status_code=status.HTTP_303_SEE_OTHER)


# ==========================================
# ADS (REKLAMALAR) ENDPOINTS
# ==========================================

@router.post("/ads/delete")
async def api_ad_delete(
    ad_id: int = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    success = await AdvertisementRepository.delete_by_id(session, ad_id)
    if success:
        await AuditRepository.create(session, "ad_deleted", details=f"Ad ID {ad_id} deleted by {current_admin.username}")
    return responses.RedirectResponse(url="/ads", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/ads/bulk-delete")
async def api_ads_bulk_delete(
    ids: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    id_list = _parse_ids(ids)
    count = await AdvertisementRepository.delete_multiple(session, id_list)
    await AuditRepository.create(session, "ads_bulk_deleted", details=f"{count} ads deleted by {current_admin.username}")
    return responses.RedirectResponse(url="/ads", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/ads/clear-all")
async def api_ads_clear_all(
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    count = await AdvertisementRepository.clear_all(session)
    await AuditRepository.create(session, "ads_cleared_all", details=f"All {count} ads cleared by {current_admin.username}")
    return responses.RedirectResponse(url="/ads", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/ads/edit")
async def api_ad_edit(
    ad_id: int = Form(...),
    status_val: str = Form(..., alias="status"),
    risk_score: int = Form(0),
    detection_reason: str = Form(""),
    text: Optional[str] = Form(None),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    await AdvertisementRepository.update_ad(
        session,
        ad_id,
        status=status_val.strip(),
        risk_score=risk_score,
        detection_reason=detection_reason.strip(),
        text=text
    )
    await AuditRepository.create(session, "ad_edited", details=f"Ad ID {ad_id} updated by {current_admin.username}")
    return responses.RedirectResponse(url="/ads", status_code=status.HTTP_303_SEE_OTHER)


# ==========================================
# USERS (FOYDALANUVCHILAR) ENDPOINTS
# ==========================================

@router.post("/users/delete")
async def api_user_delete(
    user_id: int = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    success = await UserRepository.delete_by_id(session, user_id)
    if success:
        await AuditRepository.create(session, "user_deleted", user_id=user_id, details=f"User ID {user_id} deleted by {current_admin.username}")
    return responses.RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/bulk-delete")
async def api_users_bulk_delete(
    ids: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    id_list = _parse_ids(ids)
    count = await UserRepository.delete_multiple(session, id_list)
    await AuditRepository.create(session, "users_bulk_deleted", details=f"{count} users deleted by {current_admin.username}")
    return responses.RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/bulk-reset")
async def api_users_bulk_reset(
    ids: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    id_list = _parse_ids(ids)
    count = await UserRepository.bulk_reset_warnings(session, id_list)
    await AuditRepository.create(session, "users_bulk_reset", details=f"{count} users warnings reset by {current_admin.username}")
    return responses.RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/clear-all")
async def api_users_clear_all(
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    count = await UserRepository.clear_all(session, exclude_admins=True)
    await AuditRepository.create(session, "users_cleared_all", details=f"All {count} non-admin users cleared by {current_admin.username}")
    return responses.RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/clear-all-warnings")
async def api_users_clear_all_warnings(
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    count = await UserRepository.clear_all_warnings(session)
    await AuditRepository.create(session, "users_all_warnings_cleared", details=f"All users warnings cleared by {current_admin.username}")
    return responses.RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/edit")
async def api_user_edit(
    user_id: int = Form(...),
    first_name: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
    warnings_count: int = Form(0),
    is_muted: Optional[str] = Form("false"),
    is_banned: Optional[str] = Form("false"),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    await UserRepository.update_user(
        session,
        user_id,
        first_name=first_name,
        username=username,
        warnings_count=warnings_count,
        is_muted=(is_muted == "true" or is_muted == "1"),
        is_banned=(is_banned == "true" or is_banned == "1")
    )
    await AuditRepository.create(session, "user_edited", user_id=user_id, details=f"User ID {user_id} updated by {current_admin.username}")
    return responses.RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


# ==========================================
# GROUPS (GURUHLAR) ENDPOINTS
# ==========================================

@router.post("/groups/delete")
async def api_group_delete(
    group_id: int = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    success = await GroupRepository.delete_by_id(session, group_id)
    if success:
        await AuditRepository.create(session, "group_deleted", details=f"Group ID {group_id} deleted by {current_admin.username}")
    return responses.RedirectResponse(url="/groups", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/groups/bulk-delete")
async def api_groups_bulk_delete(
    ids: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    id_list = _parse_ids(ids)
    count = await GroupRepository.delete_multiple(session, id_list)
    await AuditRepository.create(session, "groups_bulk_deleted", details=f"{count} groups deleted by {current_admin.username}")
    return responses.RedirectResponse(url="/groups", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/groups/clear-all")
async def api_groups_clear_all(
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    count = await GroupRepository.clear_all(session)
    await AuditRepository.create(session, "groups_cleared_all", details=f"All {count} groups cleared by {current_admin.username}")
    return responses.RedirectResponse(url="/groups", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/groups/edit")
async def api_group_edit(
    group_id: int = Form(...),
    title: str = Form(...),
    username: Optional[str] = Form(None),
    is_active: Optional[str] = Form("false"),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    await GroupRepository.update_group(
        session,
        group_id,
        title=title.strip(),
        username=username,
        is_active=(is_active == "true" or is_active == "1")
    )
    await AuditRepository.create(session, "group_edited", details=f"Group ID {group_id} updated by {current_admin.username}")
    return responses.RedirectResponse(url="/groups", status_code=status.HTTP_303_SEE_OTHER)

