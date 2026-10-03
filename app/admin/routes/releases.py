from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.deps import current_admin, flash, get_or_create_csrf_token, record_audit, require_role, validate_csrf
from app.admin.templating import render
from app.db.session import get_session
from app.models.admin_user import AdminUser
from app.models.app_release import AppRelease
from app.models.enums import AdminRole, AppPlatform
from app.services.push import notify_new_release

router = APIRouter(tags=["admin-releases"])


@router.get("/admin/releases")
async def list_releases(
    request: Request,
    admin: AdminUser = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
):
    releases = (
        await session.execute(select(AppRelease).order_by(AppRelease.created_at.desc()))
    ).scalars().all()
    csrf_token = get_or_create_csrf_token(request)
    return render(
        request, "releases_list.html", {"releases": releases, "csrf_token": csrf_token}, admin=admin, active="releases"
    )


@router.get("/admin/releases/new")
async def new_release_form(
    request: Request,
    admin: AdminUser = Depends(require_role(AdminRole.OWNER, AdminRole.SUPPORT)),
) -> HTMLResponse:
    csrf_token = get_or_create_csrf_token(request)
    return render(
        request, "release_form.html", {"platforms": list(AppPlatform), "csrf_token": csrf_token}, admin=admin, active="releases"
    )


@router.post("/admin/releases/new")
async def create_release(
    request: Request,
    platform: str = Form(...),
    version_code: int = Form(...),
    version_name: str = Form(...),
    download_url: str = Form(...),
    release_notes: str = Form(""),
    is_mandatory: bool = Form(False),
    csrf_token: str = Form(...),
    admin: AdminUser = Depends(require_role(AdminRole.OWNER, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if not validate_csrf(request, csrf_token):
        flash(request, "Your session expired — please try again.", "error")
        return RedirectResponse("/admin/releases/new", status_code=303)

    release = AppRelease(
        platform=AppPlatform(platform),
        version_code=version_code,
        version_name=version_name.strip(),
        download_url=download_url.strip(),
        release_notes=release_notes.strip(),
        is_mandatory=is_mandatory,
    )
    session.add(release)
    await session.flush()
    await record_audit(
        session, admin=admin, action="release.create", target_type="app_release", target_id=str(release.id),
        detail={"version_name": release.version_name, "version_code": release.version_code},
    )
    await session.commit()

    notified = await notify_new_release(session, release)
    flash(request, f'Published version {release.version_name} — notified {notified} device(s).')
    return RedirectResponse("/admin/releases", status_code=303)
