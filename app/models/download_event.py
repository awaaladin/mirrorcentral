from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class DownloadEvent(SQLModel, table=True):
    """One counted download of the Android app (see GET /app/download). Holds no IP address,
    user agent or account: only which build, whether it came from the website or the in-app update
    prompt, and when."""

    __tablename__ = "mirror_downloads"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    version_code: int = Field(nullable=False, index=True)
    source: str = Field(default="web", nullable=False, max_length=8)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True))
