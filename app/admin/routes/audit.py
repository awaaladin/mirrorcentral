from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.deps import current_admin
from app.admin.templating import render
from app.db.session import get_session
from app.models.admin_audit_log import AdminAuditLog
from app.models.admin_user import AdminUser

router = APIRouter(tags=["admin-audit"])


@router.get("/admin/audit-log")
async def audit_log(
    request: Request,
    admin: AdminUser = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(AdminAuditLog, AdminUser)
        .join(AdminUser, AdminUser.id == AdminAuditLog.admin_user_id)
        .order_by(AdminAuditLog.created_at.desc())
        .limit(200)
    )
    rows = (await session.execute(stmt)).all()
    return render(request, "audit_log.html", {"rows": rows}, admin=admin, active="audit_log")
