from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.deps import (
    flash,
    get_or_create_csrf_token,
    record_audit,
    require_role,
    validate_csrf,
)
from app.admin.templating import render
from app.core.security import hash_password
from app.db.session import get_session
from app.models.admin_user import AdminUser
from app.models.enums import AdminRole

router = APIRouter(tags=["admin-admins"])


@router.get("/admin/admins")
async def list_admins(
    request: Request,
    admin: AdminUser = Depends(require_role(AdminRole.OWNER)),
    session: AsyncSession = Depends(get_session),
):
    admins = (await session.execute(select(AdminUser).order_by(AdminUser.created_at))).scalars().all()
    csrf_token = get_or_create_csrf_token(request)
    return render(
        request,
        "admins_list.html",
        {"admins": admins, "roles": list(AdminRole), "csrf_token": csrf_token},
        admin=admin,
        active="admins",
    )


@router.post("/admin/admins")
async def create_admin_account(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    csrf_token: str = Form(...),
    admin: AdminUser = Depends(require_role(AdminRole.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if not validate_csrf(request, csrf_token):
        flash(request, "Your session expired — please try again.", "error")
        return RedirectResponse("/admin/admins", status_code=303)

    email_normalized = email.strip().lower()
    existing = (
        await session.execute(select(AdminUser).where(AdminUser.email == email_normalized))
    ).scalar_one_or_none()
    if existing:
        flash(request, "An admin with that email already exists.", "error")
        return RedirectResponse("/admin/admins", status_code=303)

    new_admin = AdminUser(email=email_normalized, password_hash=hash_password(password), role=AdminRole(role))
    session.add(new_admin)
    await session.flush()
    await record_audit(
        session, admin=admin, action="admin_user.create", target_type="admin_user", target_id=str(new_admin.id),
        detail={"email": email_normalized, "role": role},
    )
    await session.commit()

    flash(request, f"Created admin account for {email_normalized}.")
    return RedirectResponse("/admin/admins", status_code=303)


@router.post("/admin/admins/{admin_id}/toggle-active")
async def toggle_admin_active(
    admin_id: uuid.UUID,
    request: Request,
    csrf_token: str = Form(...),
    admin: AdminUser = Depends(require_role(AdminRole.OWNER)),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if not validate_csrf(request, csrf_token):
        flash(request, "Your session expired — please try again.", "error")
        return RedirectResponse("/admin/admins", status_code=303)

    target = await session.get(AdminUser, admin_id)
    if target is None:
        flash(request, "Admin not found.", "error")
        return RedirectResponse("/admin/admins", status_code=303)
    if target.id == admin.id:
        flash(request, "You can't deactivate your own account.", "error")
        return RedirectResponse("/admin/admins", status_code=303)

    target.is_active = not target.is_active
    session.add(target)
    await record_audit(
        session, admin=admin, action="admin_user.toggle_active", target_type="admin_user", target_id=str(target.id),
        detail={"is_active": target.is_active},
    )
    await session.commit()

    flash(request, f"{'Activated' if target.is_active else 'Deactivated'} {target.email}.")
    return RedirectResponse("/admin/admins", status_code=303)
