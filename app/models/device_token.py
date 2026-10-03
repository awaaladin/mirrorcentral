from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

from app.db.types import pg_enum
from app.models.enums import AppPlatform


class DeviceToken(SQLModel, table=True):
    """A device registered to receive push notifications (app update alerts today). Not tied to
    a user account - registration happens as soon as the app gets an FCM token, before any
    sign-in, same reasoning as the public shade catalog: update alerts aren't an account feature."""

    __tablename__ = "device_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    token: str = Field(nullable=False, max_length=512, unique=True, index=True)
    platform: AppPlatform = Field(
        default=AppPlatform.ANDROID,
        sa_column=Column(pg_enum(AppPlatform, "app_platform"), nullable=False),
    )
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
