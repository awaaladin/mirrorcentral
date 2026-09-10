from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.deps import current_admin
from app.admin.templating import render
from app.config import get_settings
from app.db.session import get_session
from app.models.admin_user import AdminUser
from app.models.enhance_job import EnhanceJob
from app.models.enhance_usage import EnhanceUsage
from app.models.enums import EnhanceJobStatus, SubscriptionPlan, SubscriptionStatus
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(tags=["admin-dashboard"])


@router.get("/admin/")
async def dashboard(
    request: Request,
    admin: AdminUser = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
):
    settings = get_settings()
    now = datetime.now(UTC)
    period = now.strftime("%Y-%m")
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = (await session.execute(select(func.count()).select_from(User))).scalar_one()

    plan_count_rows = (
        await session.execute(
            select(Subscription.plan, func.count())
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .group_by(Subscription.plan)
        )
    ).all()
    plan_counts = {plan.value: count for plan, count in plan_count_rows}

    jobs_today = (
        await session.execute(
            select(func.count()).select_from(EnhanceJob).where(EnhanceJob.created_at >= today_start)
        )
    ).scalar_one()

    failed_jobs = (
        await session.execute(
            select(func.count()).select_from(EnhanceJob).where(EnhanceJob.status == EnhanceJobStatus.FAILED)
        )
    ).scalar_one()

    active_plans_by_user = dict(
        (
            await session.execute(
                select(Subscription.user_id, Subscription.plan).where(
                    Subscription.status == SubscriptionStatus.ACTIVE
                )
            )
        ).all()
    )

    usage_rows = (
        await session.execute(select(EnhanceUsage).where(EnhanceUsage.billing_period == period))
    ).scalars().all()

    near_cap = []
    for usage in usage_rows:
        plan = active_plans_by_user.get(usage.user_id, SubscriptionPlan.SOLO)
        cap = settings.plan_monthly_cap(plan.value)
        if cap and usage.render_count / cap >= 0.8:
            near_cap.append((usage, cap))
    near_cap.sort(key=lambda pair: pair[0].render_count / pair[1], reverse=True)

    return render(
        request,
        "dashboard.html",
        {
            "total_users": total_users,
            "plan_counts": plan_counts,
            "jobs_today": jobs_today,
            "failed_jobs": failed_jobs,
            "near_cap": near_cap[:10],
            "period": period,
        },
        admin=admin,
        active="dashboard",
    )
