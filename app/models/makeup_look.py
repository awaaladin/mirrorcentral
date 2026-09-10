from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON as SAJSON
from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class MakeupLook(SQLModel, table=True):
    """A saved makeup style for one source photo.

    `layers` holds the free-form makeup layer selections (lip_color, foundation_shade,
    eyeshadow_color, blush_color, eyebrow_style, lash_style, gele_style) as JSON —
    validated at the API layer (see the /clients/{id}/looks schemas) rather than
    constrained by the DB schema, so new layer types don't require a migration.
    """

    __tablename__ = "makeup_looks"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client_profile_id: uuid.UUID = Field(foreign_key="client_profiles.id", nullable=False, index=True)
    source_photo_url: str = Field(nullable=False)
    layers: dict[str, Any] = Field(default_factory=dict, sa_column=Column(SAJSON, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
