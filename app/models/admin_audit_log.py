from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON as SAJSON
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class AdminAuditLog(SQLModel, table=True):
    """An immutable record of every state-changing action taken in the admin console.

    Never updated or deleted after creation — the admin UI only ever appends rows here,
    so it stays a trustworthy record of who did what, independent of what the affected
    row looks like now.
    """

    __tablename__ = "admin_audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    admin_user_id: uuid.UUID = Field(foreign_key="admin_users.id", nullable=False, index=True)
    action: str = Field(nullable=False, max_length=100)
    target_type: str = Field(nullable=False, max_length=50)
    target_id: str = Field(nullable=False, max_length=100)
    detail: dict[str, Any] = Field(default_factory=dict, sa_column=Column(SAJSON, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
