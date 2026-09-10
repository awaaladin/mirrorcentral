from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.deps import SESSION_KEY, flash, get_or_create_csrf_token, validate_csrf
from app.admin.templating import render
from app.core.security import verify_password
from app.db.session import get_session
from app.models.admin_user import AdminUser

router = APIRouter(tags=["admin-auth"])


@router.get("/admin/login", response_model=None)
async def login_form(request: Request) -> Response:
    if request.session.get(SESSION_KEY):
        return RedirectResponse("/admin/", status_code=303)
    csrf_token = get_or_create_csrf_token(request)
    next_path = request.query_params.get("next", "/admin/")
    return render(request, "login.html", {"csrf_token": csrf_token, "next_path": next_path})


@router.post("/admin/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    next_path: str = Form("/admin/"),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if not validate_csrf(request, csrf_token):
        flash(request, "Your session expired — please try again.", "error")
        return RedirectResponse("/admin/login", status_code=303)

    email_normalized = email.strip().lower()
    result = await session.execute(select(AdminUser).where(AdminUser.email == email_normalized))
    admin = result.scalar_one_or_none()

    if admin is None or not admin.is_active or not verify_password(password, admin.password_hash):
        flash(request, "Incorrect email or password.", "error")
        return RedirectResponse("/admin/login", status_code=303)

    admin.last_login_at = datetime.now(UTC)
    session.add(admin)
    await session.commit()

    request.session[SESSION_KEY] = str(admin.id)
    safe_next = next_path if next_path.startswith("/admin") else "/admin/"
    return RedirectResponse(safe_next, status_code=303)


@router.post("/admin/logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)
