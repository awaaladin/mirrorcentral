from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.deps import current_admin
from app.admin.templating import render
from app.db.session import get_session
from app.models.admin_user import AdminUser
from app.models.client_profile import ClientProfile
from app.models.enhance_job import EnhanceJob
from app.models.enhance_usage import EnhanceUsage
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(tags=["admin-users"])

PAGE_SIZE = 25


@router.get("/admin/users")
async def list_users(
    request: Request,
    admin: AdminUser = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
):
    q = request.query_params.get("q", "").strip()
    page = max(int(request.query_params.get("page") or "1"), 1)

    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q}%"))
        count_stmt = count_stmt.where(User.email.ilike(f"%{q}%"))

    total = (await session.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    users = (await session.execute(stmt)).scalars().all()

    return render(
        request,
        "users_list.html",
        {"users": users, "q": q, "page": page, "total": total, "page_size": PAGE_SIZE},
        admin=admin,
        active="users",
    )


@router.get("/admin/users/{user_id}")
async def user_detail(
    user_id: uuid.UUID,
    request: Request,
    admin: AdminUser = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if user is None:
        return render(request, "not_found.html", {"kind": "User"}, admin=admin, active="users", status_code=404)

    subscription = (
        await session.execute(select(Subscription).where(Subscription.user_id == user_id))
    ).scalar_one_or_none()

    usage_rows = (
        await session.execute(
            select(EnhanceUsage)
            .where(EnhanceUsage.user_id == user_id)
            .order_by(EnhanceUsage.billing_period.desc())
        )
    ).scalars().all()

    recent_jobs = (
        await session.execute(
            select(EnhanceJob)
            .where(EnhanceJob.user_id == user_id)
            .order_by(EnhanceJob.created_at.desc())
            .limit(10)
        )
    ).scalars().all()

    clients = (
        await session.execute(select(ClientProfile).where(ClientProfile.owner_user_id == user_id))
    ).scalars().all()

    return render(
        request,
        "user_detail.html",
        {
            "user": user,
            "subscription": subscription,
            "usage_rows": usage_rows,
            "recent_jobs": recent_jobs,
            "clients": clients,
        },
        admin=admin,
        active="users",
    )
