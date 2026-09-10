from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from app.db.types import pg_enum
from app.models.enums import EnhanceJobStatus


class EnhanceJob(SQLModel, table=True):
    __tablename__ = "enhance_jobs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    look_id: uuid.UUID = Field(foreign_key="makeup_looks.id", nullable=False, index=True)
    status: EnhanceJobStatus = Field(
        default=EnhanceJobStatus.QUEUED,
        sa_column=Column(pg_enum(EnhanceJobStatus, "enhance_job_status"), nullable=False),
    )
    result_url: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
