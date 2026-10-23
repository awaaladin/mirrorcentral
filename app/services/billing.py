"""Prepaid Pro through Paystack.

One Paystack account serves several apps, so every Mirror reference starts with the app code and
every transaction carries the same metadata keys. That lets the dashboard, exports and the
webhook router tell Mirror's payments apart from the other apps':

    MIRROR-PRO-20261023-4F9A2C7B1E0D    one prepaid period of a Pro plan (solo or studio)

A successful payment extends the user's subscription by `plan_period_days` (from today, or from
the current end date if they renew early) and makes the account a Pro/business account, which is
what the Android app gates Client Mode on.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import AccountType, PaymentStatus, SubscriptionPlan, SubscriptionStatus
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User

log = logging.getLogger(__name__)

APP_CODE = "MIRROR"
APP_NAME = "Mirror"


def make_reference(purpose: str, *, length: int = 12) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"{APP_CODE}-{purpose.upper()}-{stamp}-{uuid.uuid4().hex[:length].upper()}"


def is_ours(reference: str | None) -> bool:
    return (reference or "").upper().startswith(f"{APP_CODE}-")


def paystack_metadata(purpose: str, description: str, **extra: object) -> dict:
    """Metadata sent with every transaction. custom_fields show on the Paystack dashboard."""
    return {
        "app": APP_CODE,
        "app_name": APP_NAME,
        "purpose": purpose.upper(),
        **extra,
        "custom_fields": [
            {"display_name": "App", "variable_name": "app", "value": APP_NAME},
            {"display_name": "Payment for", "variable_name": "purpose", "value": description[:200]},
        ],
    }


def plan_label(plan: SubscriptionPlan) -> str:
    return f"Mirror Pro {plan.value.title()} ({get_settings().plan_period_days} days)"


async def latest_subscription(session: AsyncSession, user_id: uuid.UUID) -> Subscription | None:
    result = await session.execute(
        select(Subscription).where(Subscription.user_id == user_id).order_by(Subscription.renews_at.desc().nulls_last())
    )
    return result.scalars().first()


def aware_utc(value: datetime | None) -> datetime | None:
    # SQLite (tests) hands back naive datetimes even for timezone=True columns.
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


async def apply_paystack_transaction(session: AsyncSession, payment: Payment, data: dict) -> Payment:
    """Applies Paystack's view of a transaction to its payment. Idempotent: only a PENDING payment
    can become SUCCESS, so the webhook, the return page and the app's verify call can all report
    the same charge and the subscription is still extended once. Commits."""
    if payment.status != PaymentStatus.PENDING or data.get("status") != "success":
        return payment

    if data.get("currency", "NGN") != "NGN" or int(data.get("amount") or 0) < payment.amount_kobo:
        log.error("Paystack %s: expected %s kobo NGN, got %s %s", payment.reference, payment.amount_kobo,
                  data.get("amount"), data.get("currency"))
        payment.status = PaymentStatus.FAILED
        session.add(payment)
        await session.commit()
        return payment

    now = datetime.now(UTC)
    payment.status = PaymentStatus.SUCCESS
    payment.paid_at = now
    payment.paystack_transaction_id = str(data.get("id") or "") or None

    subscription = await latest_subscription(session, payment.user_id)
    if subscription is None:
        subscription = Subscription(user_id=payment.user_id, plan=payment.plan)
    current_end = aware_utc(subscription.renews_at)
    start = current_end if current_end and current_end > now else now
    subscription.plan = payment.plan
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.renews_at = start + timedelta(days=get_settings().plan_period_days)

    user = await session.get(User, payment.user_id)
    if user is not None and user.account_type != AccountType.BUSINESS:
        user.account_type = AccountType.BUSINESS
        session.add(user)

    session.add(payment)
    session.add(subscription)
    await session.commit()
    await session.refresh(payment)
    return payment


async def payment_by_reference(session: AsyncSession, reference: str) -> Payment | None:
    result = await session.execute(select(Payment).where(Payment.reference == reference))
    return result.scalar_one_or_none()
