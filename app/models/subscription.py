from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from app.db.types import pg_enum
from app.models.enums import SubscriptionPlan, SubscriptionStatus


class Subscription(SQLModel, table=True):
    __tablename__ = "subscriptions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    plan: SubscriptionPlan = Field(
        sa_column=Column(pg_enum(SubscriptionPlan, "subscription_plan"), nullable=False)
    )
    status: SubscriptionStatus = Field(
        default=SubscriptionStatus.INCOMPLETE,
        sa_column=Column(pg_enum(SubscriptionStatus, "subscription_status"), nullable=False),
    )
    renews_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    paystack_subscription_code: str | None = Field(default=None, max_length=255)
