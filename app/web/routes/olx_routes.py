from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, responses, status
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.web.auth import get_current_admin
from app.database.models.admin_user import AdminUser
from app.database.repositories.ad_request_repo import AdvertisingRequestRepository
from app.database.repositories.setting_repo import SettingRepository
from app.database.repositories.audit_repo import AuditRepository
from app.services.olx_service import OlxService
from app.config.settings import settings

class OlxUpdateRequest(BaseModel):
    title: Optional[str] = None
    price: Optional[int] = None
    currency: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None
    preview_text: Optional[str] = None

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/olx", response_class=responses.HTMLResponse)
async def olx_dashboard_page(
    request: Request,
    olx_status: Optional[str] = None,
    message: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    session_status = OlxService.get_session_status()
    metrics = await AdvertisingRequestRepository.get_olx_metrics(session)

    # Check auto-post setting from DB or settings
    db_auto_post = await SettingRepository.get_setting(session, None, "olx_auto_post")
    if db_auto_post is not None:
        auto_post_enabled = db_auto_post.lower() in ("true", "1", "yes")
    else:
        auto_post_enabled = getattr(settings, "OLX_AUTO_POST", True)

    # Fetch requests
    requests_list = await AdvertisingRequestRepository.get_all_requests_with_details(
        session,
        limit=100,
        olx_status=olx_status
    )

    return templates.TemplateResponse(
        request=request,
        name="olx.html",
        context={
            "current_admin": current_admin,
            "active_page": "olx",
            "session_status": session_status,
            "auto_post_enabled": auto_post_enabled,
            "metrics": metrics,
            "requests": requests_list,
            "current_olx_filter": olx_status,
            "message": message,
        }
    )


@router.post("/api/olx/push/{request_id}")
async def api_olx_push(
    request_id: int,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    req = await AdvertisingRequestRepository.get_by_id(session, request_id)
    if not req:
        return {"success": False, "message": f"So‘rov topilmadi: {request_id}"}

    success, url, err = await OlxService.publish_request_to_olx(None, session, req)
    if success:
        await AuditRepository.create(
            session,
            event_type="olx_manual_push_success",
            details=f"Admin {current_admin.username} pushed req {req.request_number} to OLX: {url}"
        )
        return {
            "success": True,
            "message": f"E’lon OLX.uz ga muvaffaqiyatli joylashtirildi!",
            "url": url
        }
    else:
        await AuditRepository.create(
            session,
            event_type="olx_manual_push_failed",
            details=f"Admin {current_admin.username} failed to push req {req.request_number}: {err}"
        )
        return {
            "success": False,
            "message": err or "OLX ga e’lon joylashda xatolik yuz berdi."
        }


@router.post("/api/olx/upload-session")
async def api_olx_upload_session(
    session_file: Optional[UploadFile] = File(None),
    session_json: Optional[str] = Form(None),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    content = ""
    if session_file and session_file.filename:
        file_bytes = await session_file.read()
        content = file_bytes.decode("utf-8", errors="ignore")
    elif session_json and session_json.strip():
        content = session_json.strip()

    if not content:
        return responses.RedirectResponse(
            url="/olx?message=Hech+qanday+fayl+yoki+matn+yuborilmadi",
            status_code=status.HTTP_303_SEE_OTHER
        )

    ok, msg = OlxService.save_session_json(content)
    if ok:
        await AuditRepository.create(
            session,
            event_type="olx_session_uploaded",
            details=f"Session uploaded by {current_admin.username}"
        )
        redirect_msg = "OLX+sessiyasi+muvaffaqiyatli+saqlandi"
    else:
        redirect_msg = f"Sessiyani+saqlashda+xatolik:+{msg}"

    return responses.RedirectResponse(
        url=f"/olx?message={redirect_msg}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/api/olx/toggle-auto-post")
async def api_olx_toggle_auto_post(
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    db_val = await SettingRepository.get_setting(session, None, "olx_auto_post")
    if db_val is not None:
        current_state = db_val.lower() in ("true", "1", "yes")
    else:
        current_state = getattr(settings, "OLX_AUTO_POST", True)

    new_state = not current_state
    new_str = "true" if new_state else "false"

    await SettingRepository.set_setting(session, None, "olx_auto_post", new_str)
    settings.OLX_AUTO_POST = new_state

    await AuditRepository.create(
        session,
        event_type="olx_toggle_auto_post",
        details=f"Auto post set to {new_state} by {current_admin.username}"
    )

    state_word = "yoqildi" if new_state else "o‘chirildi"
    return responses.RedirectResponse(
        url=f"/olx?message=OLX+avto-e'lon+{state_word}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/api/olx/update/{request_id}")
async def api_olx_update(
    request_id: int,
    payload: OlxUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    req = await AdvertisingRequestRepository.update_request_content(
        session=session,
        request_id=request_id,
        title=payload.title,
        price=payload.price,
        currency=payload.currency,
        phone=payload.phone,
        location=payload.location,
        condition=payload.condition,
        preview_text=payload.preview_text
    )
    if not req:
        return {"success": False, "message": f"So‘rov topilmadi: {request_id}"}

    await AuditRepository.create(
        session,
        event_type="olx_ad_updated",
        details=f"Admin {current_admin.username} updated req {req.request_number} (title: {payload.title}, price: {payload.price})"
    )
    return {
        "success": True,
        "message": f"{req.request_number} e’loni muvaffaqiyatli tahrirlandi!",
        "request": {
            "id": req.id,
            "request_number": req.request_number,
            "product_title": req.product_title,
            "product_price": req.product_price,
            "product_currency": req.product_currency,
            "product_phone": req.product_phone,
            "product_location": req.product_location,
            "preview_text": req.preview_text
        }
    }


@router.post("/api/olx/delete/{request_id}")
async def api_olx_delete(
    request_id: int,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db)
):
    req = await AdvertisingRequestRepository.get_by_id(session, request_id)
    if not req:
        return {"success": False, "message": f"So‘rov topilmadi: {request_id}"}

    req_num = req.request_number
    ok = await AdvertisingRequestRepository.delete_by_id(session, request_id)
    if ok:
        await AuditRepository.create(
            session,
            event_type="olx_ad_deleted",
            details=f"Admin {current_admin.username} deleted req {req_num} (ID: {request_id})"
        )
        return {
            "success": True,
            "message": f"{req_num} e’loni bazadan muvaffaqiyatli o‘chirildi!"
        }
    else:
        return {"success": False, "message": "O‘chirishda xatolik yuz berdi."}

