from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, SQLModel


class CrashReport(SQLModel, table=True):
    """Why the Android app closed on someone's phone, sent by the app on its next launch
    (com.mirror.app.core.crash.CrashReporter). No photos or account details, only the error,
    the app version and the phone model. Read it with SQL or the admin console's database view."""

    __tablename__ = "mirror_crash_reports"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    kind: str = Field(nullable=False, max_length=20, index=True)
    summary: str = Field(default="", nullable=False, max_length=500)
    trace: str = Field(default="", sa_column=Column(Text, nullable=False, server_default=""))
    app_version: str = Field(default="", nullable=False, max_length=20)
    version_code: int = Field(default=0, nullable=False)
    device: str = Field(default="", nullable=False, max_length=120)
    android_sdk: int = Field(default=0, nullable=False)
    abis: str = Field(default="", nullable=False, max_length=120)
    ram_mb: int = Field(default=0, nullable=False)
    pss_kb: int = Field(default=0, nullable=False)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True))
