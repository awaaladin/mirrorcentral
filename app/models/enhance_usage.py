from __future__ import annotations

import uuid

from sqlmodel import Field, SQLModel, UniqueConstraint


class EnhanceUsage(SQLModel, table=True):
    """Render-count counter for one user's billing period, used to enforce the monthly cap.

    `billing_period` is a "YYYY-MM" string naming the calendar month it covers, so a
    user has at most one row per month per the unique constraint below.
    """

    __tablename__ = "enhance_usages"
    __table_args__ = (UniqueConstraint("user_id", "billing_period", name="uq_enhance_usage_user_period"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    billing_period: str = Field(nullable=False, max_length=7, index=True)
    render_count: int = Field(default=0, nullable=False)
