from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

from app.db.types import pg_enum
from app.models.enums import PaymentStatus, SubscriptionPlan


class Payment(SQLModel, table=True):
    """One Paystack checkout for a prepaid Pro period. The reference (MIRROR-PRO-...) is what
    shows in the shared Paystack dashboard, so a row here can always be matched to it."""

    __tablename__ = "payments"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    reference: str = Field(nullable=False, max_length=100, unique=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    plan: SubscriptionPlan = Field(
        sa_column=Column(pg_enum(SubscriptionPlan, "subscription_plan"), nullable=False)
    )
    amount_kobo: int = Field(nullable=False)
    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING,
        sa_column=Column(pg_enum(PaymentStatus, "payment_status"), nullable=False),
    )
    authorization_url: str = Field(default="", max_length=2048)
    paystack_transaction_id: str | None = Field(default=None, max_length=40)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    paid_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
