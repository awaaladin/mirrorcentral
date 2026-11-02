"""What each account can use, and its monthly allowances. The app itself is free; this is the
server-side source of truth, read from subscriptions and users.unlocked_at rather than
users.account_type, which no longer decides anything.

    free               10 new photos and 3 Showroom analyses a month; shared images carry a watermark
    personal ("solo")  unlimited photos, more Showroom, no watermark
    studio (Pro)       as Personal with a larger Showroom allowance, plus Client Mode (not on sale)
    one-time buyers    (users.unlocked_at, from when Solo was sold as a one-time payment) keep
                       unlimited photos and no watermark for good; Showroom as on free

Makeup is painted on the phone, so the photo limit and the watermark are the app's to apply (from a
signed license and POST /usage/photo). Showroom runs here, so its count is enforced here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import SubscriptionPlan, SubscriptionStatus
from app.models.usage_event import UsageEvent
from app.models.user import User
from app.services.billing import aware_utc, latest_subscription

PHOTO = "photo"
SHOWROOM = "showroom"


async def active_plan(session: AsyncSession, user_id: uuid.UUID) -> SubscriptionPlan | None:
    subscription = await latest_subscription(session, user_id)
    if subscription is None or subscription.status != SubscriptionStatus.ACTIVE:
        return None
    renews_at = aware_utc(subscription.renews_at)
    if renews_at is None or renews_at <= datetime.now(UTC):
        return None
    return subscription.plan


@dataclass(frozen=True)
class Access:
    plan: SubscriptionPlan | None
    lifetime_unlock: bool = False

    @property
    def is_paid(self) -> bool:
        return self.plan is not None or self.lifetime_unlock

    @property
    def photo_limit(self) -> int | None:
        """None = unlimited."""
        return None if self.is_paid else get_settings().free_photos_per_month

    @property
    def showroom_limit(self) -> int:
        settings = get_settings()
        if self.plan == SubscriptionPlan.STUDIO:
            return settings.studio_showroom_per_month
        if self.plan == SubscriptionPlan.SOLO:
            return settings.personal_showroom_per_month
        return settings.free_showroom_per_month

    @property
    def client_mode(self) -> bool:
        return self.plan == SubscriptionPlan.STUDIO


async def access_for(session: AsyncSession, user: User) -> Access:
    return Access(await active_plan(session, user.id), user.unlocked_at is not None)


def _period() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


async def used_this_month(session: AsyncSession, user_id: uuid.UUID, kind: str) -> int:
    result = await session.execute(
        select(func.count()).select_from(UsageEvent)
        .where(UsageEvent.user_id == user_id, UsageEvent.kind == kind, UsageEvent.period == _period())
    )
    return result.scalar_one()


async def claim(session: AsyncSession, user_id: uuid.UUID, kind: str, key: str, limit: int | None, paid: bool) -> bool:
    """Counts one use against this month's allowance. The same key twice (the same photo opened
    again) is free. Two simultaneous first uses can each pass the count check, so the limit can
    be overrun by one under a race; that's an accepted cost for not locking. Commits."""
    period = _period()
    existing = await session.execute(
        select(UsageEvent.id).where(
            UsageEvent.user_id == user_id, UsageEvent.kind == kind, UsageEvent.period == period, UsageEvent.key == key
        )
    )
    if existing.first() is not None:
        return True
    if limit is not None and await used_this_month(session, user_id, kind) >= limit:
        return False
    session.add(UsageEvent(user_id=user_id, kind=kind, period=period, key=key, paid=paid))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()  # The same key landed concurrently; it's counted once either way.
    return True


async def release(session: AsyncSession, user_id: uuid.UUID, kind: str, key: str) -> None:
    """Gives a use back, e.g. when the Showroom analysis it paid for failed. Commits."""
    await session.execute(
        delete(UsageEvent).where(
            UsageEvent.user_id == user_id, UsageEvent.kind == kind, UsageEvent.period == _period(), UsageEvent.key == key
        )
    )
    await session.commit()


async def free_showroom_today(session: AsyncSession) -> int:
    """Free Showroom analyses across every account today, for the daily spending ceiling."""
    midnight = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(func.count()).select_from(UsageEvent)
        .where(UsageEvent.kind == SHOWROOM, UsageEvent.paid.is_(False), UsageEvent.created_at >= midnight)
    )
    return result.scalar_one()
