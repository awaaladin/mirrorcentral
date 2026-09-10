from __future__ import annotations

import uuid
from datetime import UTC, datetime

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
from app.models.enums import AdminRole, SubscriptionPlan, SubscriptionStatus
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(tags=["admin-subscriptions"])


@router.get("/admin/subscriptions")
async def list_subscriptions(
    request: Request,
    admin: AdminUser = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
):
    status_filter = request.query_params.get("status") or None
    stmt = select(Subscription, User).join(User, User.id == Subscription.user_id)
    if status_filter:
        stmt = stmt.where(Subscription.status == SubscriptionStatus(status_filter))
    rows = (await session.execute(stmt.order_by(Subscription.renews_at.desc()))).all()

    return render(
        request,
        "subscriptions_list.html",
        {"rows": rows, "status_filter": status_filter, "statuses": list(SubscriptionStatus)},
        admin=admin,
        active="subscriptions",
    )


@router.get("/admin/subscriptions/{subscription_id}/edit")
async def edit_subscription_form(
    subscription_id: uuid.UUID,
    request: Request,
    admin: AdminUser = Depends(require_role(AdminRole.OWNER, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    subscription = await session.get(Subscription, subscription_id)
    if subscription is None:
        return render(
            request, "not_found.html", {"kind": "Subscription"}, admin=admin, active="subscriptions", status_code=404
        )
    user = await session.get(User, subscription.user_id)
    csrf_token = get_or_create_csrf_token(request)
    return render(
        request,
        "subscription_edit.html",
        {
            "subscription": subscription,
            "user": user,
            "plans": list(SubscriptionPlan),
            "statuses": list(SubscriptionStatus),
            "csrf_token": csrf_token,
        },
        admin=admin,
        active="subscriptions",
    )


@router.post("/admin/subscriptions/{subscription_id}/edit")
async def edit_subscription_submit(
    subscription_id: uuid.UUID,
    request: Request,
    plan: str = Form(...),
    status: str = Form(...),
    renews_at: str = Form(""),
    csrf_token: str = Form(...),
    admin: AdminUser = Depends(require_role(AdminRole.OWNER, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if not validate_csrf(request, csrf_token):
        flash(request, "Your session expired — please try again.", "error")
        return RedirectResponse(f"/admin/subscriptions/{subscription_id}/edit", status_code=303)

    subscription = await session.get(Subscription, subscription_id)
    if subscription is None:
        flash(request, "Subscription not found.", "error")
        return RedirectResponse("/admin/subscriptions", status_code=303)

    before = {
        "plan": subscription.plan.value,
        "status": subscription.status.value,
        "renews_at": subscription.renews_at.isoformat() if subscription.renews_at else None,
    }

    subscription.plan = SubscriptionPlan(plan)
    subscription.status = SubscriptionStatus(status)
    subscription.renews_at = (
        datetime.fromisoformat(renews_at).replace(tzinfo=UTC) if renews_at else None
    )
    session.add(subscription)

    await record_audit(
        session,
        admin=admin,
        action="subscription.update",
        target_type="subscription",
        target_id=str(subscription.id),
        detail={"before": before, "after": {"plan": plan, "status": status, "renews_at": renews_at or None}},
    )
    await session.commit()

    flash(request, "Subscription updated.")
    return RedirectResponse(f"/admin/users/{subscription.user_id}", status_code=303)
