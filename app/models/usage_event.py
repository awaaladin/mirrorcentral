from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel, UniqueConstraint


class UsageEvent(SQLModel, table=True):
    """One counted use of a monthly allowance (see app/services/entitlements.py): a new photo in the
    studio (key = the app's id for that photo, so reopening it is free) or a Showroom analysis.
    `period` is the "YYYY-MM" month it counts against."""

    __tablename__ = "usage_events"
    __table_args__ = (UniqueConstraint("user_id", "kind", "period", "key", name="uq_usage_event"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    kind: str = Field(nullable=False, max_length=16)
    period: str = Field(nullable=False, max_length=7, index=True)
    key: str = Field(nullable=False, max_length=64)
    # Whether a paid plan made this use; the daily ceiling on free Showroom counts only unpaid ones.
    paid: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
