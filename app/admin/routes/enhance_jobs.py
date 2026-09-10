from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
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
from app.models.enhance_job import EnhanceJob
from app.models.enums import AdminRole, EnhanceJobStatus
from app.models.user import User

router = APIRouter(tags=["admin-enhance-jobs"])


@router.get("/admin/enhance-jobs")
async def list_enhance_jobs(
    request: Request,
    admin: AdminUser = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
):
    status_filter = request.query_params.get("status") or None
    stmt = select(EnhanceJob, User).join(User, User.id == EnhanceJob.user_id)
    if status_filter:
        stmt = stmt.where(EnhanceJob.status == EnhanceJobStatus(status_filter))
    stmt = stmt.order_by(EnhanceJob.created_at.desc()).limit(200)
    rows = (await session.execute(stmt)).all()
    csrf_token = get_or_create_csrf_token(request)

    return render(
        request,
        "enhance_jobs_list.html",
        {"rows": rows, "status_filter": status_filter, "statuses": list(EnhanceJobStatus), "csrf_token": csrf_token},
        admin=admin,
        active="enhance_jobs",
    )


@router.post("/admin/enhance-jobs/{job_id}/retry")
async def retry_enhance_job(
    job_id: uuid.UUID,
    request: Request,
    csrf_token: str = Form(...),
    admin: AdminUser = Depends(require_role(AdminRole.OWNER, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Resets a failed job to `queued` in the DB.

    Doesn't itself re-enqueue an arq task — that wiring lands with the worker in a
    later phase. For now this unblocks a stuck-looking row and gets picked up once the
    worker polls queued jobs.
    """
    if not validate_csrf(request, csrf_token):
        flash(request, "Your session expired — please try again.", "error")
        return RedirectResponse("/admin/enhance-jobs", status_code=303)

    job = await session.get(EnhanceJob, job_id)
    if job is None:
        flash(request, "Job not found.", "error")
        return RedirectResponse("/admin/enhance-jobs", status_code=303)

    previous_status = job.status.value
    job.status = EnhanceJobStatus.QUEUED
    job.completed_at = None
    session.add(job)

    await record_audit(
        session,
        admin=admin,
        action="enhance_job.retry",
        target_type="enhance_job",
        target_id=str(job.id),
        detail={"previous_status": previous_status},
    )
    await session.commit()

    flash(request, "Job re-queued.")
    return RedirectResponse("/admin/enhance-jobs", status_code=303)
