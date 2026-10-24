from __future__ import annotations

import html
import json
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import get_settings
from app.db.session import get_session
from app.models.enums import PaymentStatus, SubscriptionPlan, SubscriptionStatus
from app.models.payment import Payment
from app.models.user import User
from app.services import paystack
from app.services.billing import (
    apply_paystack_transaction,
    aware_utc,
    is_ours,
    latest_subscription,
    make_reference,
    payment_by_reference,
    paystack_metadata,
    plan_label,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


class PlanPublic(BaseModel):
    plan: SubscriptionPlan
    name: str
    price_ngn: int
    period_days: int
    # False = shown (so people know it's coming and roughly what it costs) but not
    # purchasable yet - see Settings.studio_plan_available.
    available: bool


class CheckoutRequest(BaseModel):
    plan: SubscriptionPlan


class CheckoutResponse(BaseModel):
    reference: str
    authorization_url: str


class PaymentPublic(BaseModel):
    reference: str
    plan: SubscriptionPlan
    status: PaymentStatus


class SubscriptionPublic(BaseModel):
    plan: SubscriptionPlan | None
    active: bool
    renews_at: datetime | None


@router.get("/plans", response_model=list[PlanPublic])
async def list_plans() -> list[PlanPublic]:
    settings = get_settings()
    return [
        PlanPublic(plan=plan, name=plan_label(plan), price_ngn=settings.plan_price_ngn(plan.value),
                   period_days=settings.plan_period_days, available=settings.plan_available(plan.value))
        for plan in SubscriptionPlan
    ]


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    request: CheckoutRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CheckoutResponse:
    """Starts a Paystack checkout for one prepaid period. The app opens authorization_url in a
    browser; Paystack sends the payer back to /billing/return when they're done."""
    settings = get_settings()
    if not settings.plan_available(request.plan.value):
        raise HTTPException(status.HTTP_409_CONFLICT, "This plan's pricing is still being reviewed - not available to buy yet.")
    payment = Payment(
        reference=make_reference("PRO"),
        user_id=user.id,
        plan=request.plan,
        amount_kobo=settings.plan_price_ngn(request.plan.value) * 100,
    )
    try:
        data = await paystack.initialize_transaction(
            email=user.email,
            amount_kobo=payment.amount_kobo,
            reference=payment.reference,
            callback_url=f"{settings.public_base_url.rstrip('/')}/billing/return",
            metadata=paystack_metadata("PRO", plan_label(request.plan), user_id=str(user.id), plan=request.plan.value),
        )
    except paystack.PaystackNotConfigured:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Payments aren't available right now.")
    except paystack.PaystackError as exc:
        log.error("Paystack initialize failed for %s: %s", payment.reference, exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Payment couldn't be started. Please try again.")

    payment.authorization_url = data["authorization_url"]
    session.add(payment)
    await session.commit()
    return CheckoutResponse(reference=payment.reference, authorization_url=payment.authorization_url)


async def _verify(session: AsyncSession, payment: Payment) -> Payment:
    if payment.status != PaymentStatus.PENDING:
        return payment
    try:
        data = await paystack.verify_transaction(payment.reference)
    except paystack.PaystackError as exc:
        log.warning("Paystack verify failed for %s: %s", payment.reference, exc)
        return payment
    return await apply_paystack_transaction(session, payment, data)


@router.post("/verify/{reference}", response_model=PaymentPublic)
async def verify(
    reference: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PaymentPublic:
    payment = await payment_by_reference(session, reference)
    if payment is None or payment.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found.")
    payment = await _verify(session, payment)
    return PaymentPublic(reference=payment.reference, plan=payment.plan, status=payment.status)


@router.get("/subscription", response_model=SubscriptionPublic)
async def my_subscription(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionPublic:
    subscription = await latest_subscription(session, user.id)
    if subscription is None:
        return SubscriptionPublic(plan=None, active=False, renews_at=None)
    renews_at = aware_utc(subscription.renews_at)
    active = (
        subscription.status == SubscriptionStatus.ACTIVE and renews_at is not None and renews_at > datetime.now(UTC)
    )
    return SubscriptionPublic(plan=subscription.plan, active=active, renews_at=renews_at)


@router.get("/return", response_class=HTMLResponse, include_in_schema=False)
async def payment_return(reference: str = "", session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    """Where Paystack's checkout sends the payer's browser. Confirms the payment with Paystack
    (no login needed: it only ever applies what Paystack itself reports) and says what to do next."""
    payment = await payment_by_reference(session, reference) if reference else None
    if payment is not None:
        payment = await _verify(session, payment)

    if payment is not None and payment.status == PaymentStatus.SUCCESS:
        title, message = "Payment received", "Mirror Pro is active on your account. You can go back to the Mirror app."
    elif payment is not None and payment.status == PaymentStatus.FAILED:
        title, message = "Payment not accepted", "Please contact support with your reference."
    else:
        title, message = "Payment not confirmed yet", "If you paid, Pro will switch on within a few minutes."
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} | Mirror</title>
<style>body{{font-family:system-ui,sans-serif;max-width:28rem;margin:4rem auto;padding:0 1rem;text-align:center;color:#2b1d1a}}
code{{background:#f4ece8;padding:.15rem .4rem;border-radius:.3rem}}</style></head>
<body><h1>{title}</h1><p>{message}</p><p>Reference: <code>{html.escape(reference)}</code></p></body></html>"""
    return HTMLResponse(page)


@router.post("/paystack/webhook", include_in_schema=False)
async def paystack_webhook(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    raw = await request.body()
    if not paystack.verify_webhook_signature(raw, request.headers.get("x-paystack-signature")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid signature.")
    try:
        payload = json.loads(raw)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid JSON.")

    data = payload.get("data") or {}
    reference = data.get("reference")
    if payload.get("event") == "charge.success" and is_ours(reference):
        payment = await payment_by_reference(session, reference)
        if payment is not None:
            await apply_paystack_transaction(session, payment, data)
    # Anything else (another app's reference, an event we don't act on) is acknowledged so
    # Paystack doesn't keep retrying it.
    return {"received": True}
