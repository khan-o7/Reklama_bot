from fastapi import APIRouter, Request, Form, Depends, responses, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.database.repositories.admin_user_repo import AdminUserRepository
from app.web.auth import verify_password, create_access_token, COOKIE_NAME

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/login", response_class=responses.HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})


@router.post("/login")
async def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_db)
):
    admin_user = await AdminUserRepository.get_by_username(session, username)
    if not admin_user or not verify_password(password, admin_user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Login yoki parol noto‘g‘ri!"},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    token = create_access_token({"sub": admin_user.username})
    response = responses.RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )
    return response


@router.get("/logout")
async def logout_action():
    response = responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key=COOKIE_NAME)
    return response
