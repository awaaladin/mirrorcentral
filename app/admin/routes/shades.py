from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.deps import (
    current_admin,
    flash,
    get_or_create_csrf_token,
    record_audit,
    require_role,
    validate_csrf,
)
from app.admin.templating import render
from app.db.session import get_session
from app.models.admin_user import AdminUser
from app.models.enums import AdminRole, ShadeCategory, ShadeFinish
from app.models.shade_item import ShadeItem

router = APIRouter(tags=["admin-shades"])


@router.get("/admin/shades")
async def list_shades(
    request: Request,
    admin: AdminUser = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
):
    shades = (
        await session.execute(select(ShadeItem).order_by(ShadeItem.category, ShadeItem.name))
    ).scalars().all()
    csrf_token = get_or_create_csrf_token(request)
    return render(
        request, "shades_list.html", {"shades": shades, "csrf_token": csrf_token}, admin=admin, active="shades"
    )


@router.get("/admin/shades/new")
async def new_shade_form(
    request: Request,
    admin: AdminUser = Depends(require_role(AdminRole.OWNER, AdminRole.SUPPORT)),
) -> HTMLResponse:
    csrf_token = get_or_create_csrf_token(request)
    return render(
        request,
        "shade_form.html",
        {"shade": None, "categories": list(ShadeCategory), "finishes": list(ShadeFinish), "csrf_token": csrf_token},
        admin=admin,
        active="shades",
    )


@router.post("/admin/shades/new")
async def create_shade(
    request: Request,
    name: str = Form(...),
    hex_color: str = Form(...),
    category: str = Form(...),
    finish: str = Form(...),
    csrf_token: str = Form(...),
    admin: AdminUser = Depends(require_role(AdminRole.OWNER, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if not validate_csrf(request, csrf_token):
        flash(request, "Your session expired — please try again.", "error")
        return RedirectResponse("/admin/shades/new", status_code=303)

    shade = ShadeItem(
        name=name.strip(),
        hex_color=hex_color.strip(),
        category=ShadeCategory(category),
        finish=ShadeFinish(finish),
    )
    session.add(shade)
    await session.flush()
    await record_audit(
        session, admin=admin, action="shade.create", target_type="shade_item", target_id=str(shade.id),
        detail={"name": shade.name},
    )
    await session.commit()

    flash(request, f'Added shade "{shade.name}".')
    return RedirectResponse("/admin/shades", status_code=303)


@router.get("/admin/shades/{shade_id}/edit")
async def edit_shade_form(
    shade_id: uuid.UUID,
    request: Request,
    admin: AdminUser = Depends(require_role(AdminRole.OWNER, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    shade = await session.get(ShadeItem, shade_id)
    if shade is None:
        return render(request, "not_found.html", {"kind": "Shade"}, admin=admin, active="shades", status_code=404)
    csrf_token = get_or_create_csrf_token(request)
    return render(
        request,
        "shade_form.html",
        {"shade": shade, "categories": list(ShadeCategory), "finishes": list(ShadeFinish), "csrf_token": csrf_token},
        admin=admin,
        active="shades",
    )


@router.post("/admin/shades/{shade_id}/edit")
async def update_shade(
    shade_id: uuid.UUID,
    request: Request,
    name: str = Form(...),
    hex_color: str = Form(...),
    category: str = Form(...),
    finish: str = Form(...),
    csrf_token: str = Form(...),
    admin: AdminUser = Depends(require_role(AdminRole.OWNER, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if not validate_csrf(request, csrf_token):
        flash(request, "Your session expired — please try again.", "error")
        return RedirectResponse(f"/admin/shades/{shade_id}/edit", status_code=303)

    shade = await session.get(ShadeItem, shade_id)
    if shade is None:
        flash(request, "Shade not found.", "error")
        return RedirectResponse("/admin/shades", status_code=303)

    shade.name = name.strip()
    shade.hex_color = hex_color.strip()
    shade.category = ShadeCategory(category)
    shade.finish = ShadeFinish(finish)
    session.add(shade)

    await record_audit(
        session, admin=admin, action="shade.update", target_type="shade_item", target_id=str(shade.id),
        detail={"name": shade.name},
    )
    await session.commit()

    flash(request, f'Updated shade "{shade.name}".')
    return RedirectResponse("/admin/shades", status_code=303)


@router.post("/admin/shades/{shade_id}/delete")
async def delete_shade(
    shade_id: uuid.UUID,
    request: Request,
    csrf_token: str = Form(...),
    admin: AdminUser = Depends(require_role(AdminRole.OWNER, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if not validate_csrf(request, csrf_token):
        flash(request, "Your session expired — please try again.", "error")
        return RedirectResponse("/admin/shades", status_code=303)

    shade = await session.get(ShadeItem, shade_id)
    if shade is not None:
        await record_audit(
            session, admin=admin, action="shade.delete", target_type="shade_item", target_id=str(shade.id),
            detail={"name": shade.name},
        )
        await session.delete(shade)
        await session.commit()
        flash(request, f'Deleted shade "{shade.name}".')
    return RedirectResponse("/admin/shades", status_code=303)
