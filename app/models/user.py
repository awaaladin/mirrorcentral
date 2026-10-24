from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from app.db.types import pg_enum
from app.models.enums import AccountType


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False, max_length=255)
    password_hash: str = Field(nullable=False)
    account_type: AccountType = Field(
        default=AccountType.CONSUMER,
        sa_column=Column(pg_enum(AccountType, "account_type"), nullable=False),
    )
    # Set on every /auth/register or /auth/login, carried as the "sid" claim in both the
    # access and refresh tokens minted alongside it. A later login overwrites it, so every
    # already-issued token (on whatever device had the old one) stops matching - see
    # get_current_user and /auth/refresh. One active sign-in per account at a time.
    current_session_id: str | None = Field(default=None, max_length=64)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
