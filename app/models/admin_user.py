from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from app.db.types import pg_enum
from app.models.enums import AdminRole


class AdminUser(SQLModel, table=True):
    """A Mirror staff account for the admin console — distinct from `User` (app
    customers), so a customer account can never accidentally gain admin access."""

    __tablename__ = "admin_users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False, max_length=255)
    password_hash: str = Field(nullable=False)
    role: AdminRole = Field(
        default=AdminRole.SUPPORT,
        sa_column=Column(pg_enum(AdminRole, "admin_role"), nullable=False),
    )
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    last_login_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
