"""What each purchase unlocks. The app itself is free; this is the server-side source of truth
for the paid features, and it reads subscriptions and users.unlocked_at rather than
users.account_type, which no longer decides anything.

    one-time payment (users.unlocked_at)   no watermark, forever
    studio subscription (Pro, not on sale)  no watermark, Showroom, Client Mode
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enhance_usage import EnhanceUsage
from app.models.enums import SubscriptionPlan, SubscriptionStatus
from app.services.billing import aware_utc, latest_subscription


async def active_plan(session: AsyncSession, user_id: uuid.UUID) -> SubscriptionPlan | None:
    subscription = await latest_subscription(session, user_id)
    if subscription is None or subscription.status != SubscriptionStatus.ACTIVE:
        return None
    renews_at = aware_utc(subscription.renews_at)
    if renews_at is None or renews_at <= datetime.now(UTC):
        return None
    return subscription.plan


def can_use_showroom(plan: SubscriptionPlan) -> bool:
    return plan == SubscriptionPlan.STUDIO


def can_use_client_mode(plan: SubscriptionPlan) -> bool:
    return plan == SubscriptionPlan.STUDIO


def _period() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


async def take_showroom_credit(session: AsyncSession, user_id: uuid.UUID, cap: int) -> bool:
    """Counts one analysis against this month's cap (enhance_usages is the existing per-month
    usage counter). The increment is a single conditional UPDATE so concurrent requests can't
    overrun the cap. Returns False once it's used up. Commits."""
    period = _period()
    result = await session.execute(
        update(EnhanceUsage)
        .where(EnhanceUsage.user_id == user_id, EnhanceUsage.billing_period == period, EnhanceUsage.render_count < cap)
        .values(render_count=EnhanceUsage.render_count + 1)
    )
    await session.commit()
    if result.rowcount:
        return True
    existing = await session.execute(
        select(EnhanceUsage.id).where(EnhanceUsage.user_id == user_id, EnhanceUsage.billing_period == period)
    )
    if existing.first() is not None or cap < 1:
        return False
    session.add(EnhanceUsage(user_id=user_id, billing_period=period, render_count=1))
    try:
        await session.commit()
    except IntegrityError:
        # A concurrent first request of the month created the row; go through the UPDATE path.
        await session.rollback()
        return await take_showroom_credit(session, user_id, cap)
    return True


async def refund_showroom_credit(session: AsyncSession, user_id: uuid.UUID) -> None:
    """A failed analysis shouldn't use up the month's allowance. Commits."""
    await session.execute(
        update(EnhanceUsage)
        .where(EnhanceUsage.user_id == user_id, EnhanceUsage.billing_period == _period(), EnhanceUsage.render_count > 0)
        .values(render_count=EnhanceUsage.render_count - 1)
    )
    await session.commit()
