from fastapi import APIRouter, Request, Depends, responses
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.web.auth import get_current_admin
from app.database.models.admin_user import AdminUser
from app.database.repositories.group_repo import GroupRepository
from app.database.repositories.user_repo import UserRepository
from app.database.repositories.ad_repo import AdvertisementRepository
from app.database.repositories.warning_repo import WarningRepository
from app.database.repositories.list_repo import ListRepository
from app.database.repositories.setting_repo import SettingRepository
from app.database.repositories.audit_repo import AuditRepository

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/", response_class=responses.HTMLResponse)
async def dashboard_page(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    total_groups = await GroupRepository.get_total_count(session)
    total_users = await UserRepository.get_total_count(session)
    today_ads = await AdvertisementRepository.count_today(session)
    today_deleted = await AdvertisementRepository.count_today_deleted(session)
    today_warnings = await WarningRepository.count_today_by_type(session, "warning")
    today_muted = await WarningRepository.count_today_by_type(session, "mute")
    today_banned = await WarningRepository.count_today_by_type(session, "ban")

    chart_data = await AdvertisementRepository.get_chart_data_7_days(session)
    top_offenders = await UserRepository.get_top_offenders(session, limit=5)
    recent_ads = await AdvertisementRepository.get_recent(session, limit=10)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "current_admin": current_admin,
            "active_page": "dashboard",
            "total_groups": total_groups,
            "total_users": total_users,
            "today_ads": today_ads,
            "today_deleted": today_deleted,
            "today_warnings": today_warnings,
            "today_muted": today_muted,
            "today_banned": today_banned,
            "chart_data": chart_data,
            "top_offenders": top_offenders,
            "recent_ads": recent_ads,
        }
    )


@router.get("/groups", response_class=responses.HTMLResponse)
async def groups_page(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    groups = await GroupRepository.get_all(session, limit=100)
    return templates.TemplateResponse(
        request=request,
        name="groups.html",
        context={
            "current_admin": current_admin,
            "active_page": "groups",
            "groups": groups,
        }
    )


@router.get("/users", response_class=responses.HTMLResponse)
async def users_page(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    users = await UserRepository.get_recent_users(session, limit=100)
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={
            "current_admin": current_admin,
            "active_page": "users",
            "users": users,
        }
    )


@router.get("/ads", response_class=responses.HTMLResponse)
async def ads_page(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    ads = await AdvertisementRepository.get_recent(session, limit=100)
    return templates.TemplateResponse(
        request=request,
        name="ads.html",
        context={
            "current_admin": current_admin,
            "active_page": "ads",
            "ads": ads,
        }
    )


@router.get("/warnings", response_class=responses.HTMLResponse)
async def warnings_page(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    warnings = await WarningRepository.get_recent(session, limit=100)
    return templates.TemplateResponse(
        request=request,
        name="warnings.html",
        context={
            "current_admin": current_admin,
            "active_page": "warnings",
            "warnings": warnings,
        }
    )


@router.get("/lists", response_class=responses.HTMLResponse)
async def lists_page(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    whitelist = await ListRepository.get_all_whitelist(session)
    blacklist = await ListRepository.get_all_blacklist(session)
    return templates.TemplateResponse(
        request=request,
        name="lists.html",
        context={
            "current_admin": current_admin,
            "active_page": "lists",
            "whitelist": whitelist,
            "blacklist": blacklist,
        }
    )


@router.get("/settings", response_class=responses.HTMLResponse)
async def settings_page(
    request: Request,
    message: str = None,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    settings_dict = await SettingRepository.get_all_group_settings(session, None)
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "current_admin": current_admin,
            "active_page": "settings",
            "settings_dict": settings_dict,
            "message": message,
        }
    )


@router.get("/logs", response_class=responses.HTMLResponse)
async def logs_page(
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    logs = await AuditRepository.get_recent(session, limit=100)
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={
            "current_admin": current_admin,
            "active_page": "logs",
            "logs": logs,
        }
    )
