from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

from app.db.types import pg_enum
from app.models.enums import AppPlatform


class AppRelease(SQLModel, table=True):
    """A published app build the landing page can link to and the Android app can check
    against. Admin-managed (see app/admin/routes/releases.py) - there's no self-service way
    to publish one, same reasoning as AdminUser."""

    __tablename__ = "app_releases"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    platform: AppPlatform = Field(
        default=AppPlatform.ANDROID,
        sa_column=Column(pg_enum(AppPlatform, "app_platform"), nullable=False),
    )
    version_code: int = Field(nullable=False, index=True)
    version_name: str = Field(nullable=False, max_length=50)
    download_url: str = Field(nullable=False, max_length=2048)
    release_notes: str = Field(default="", nullable=False)
    is_mandatory: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
