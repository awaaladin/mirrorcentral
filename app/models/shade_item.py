from __future__ import annotations

import uuid

from sqlalchemy import Column
from sqlmodel import Field, SQLModel

from app.db.types import pg_enum
from app.models.enums import ShadeCategory, ShadeFinish


class ShadeItem(SQLModel, table=True):
    """A single selectable makeup color in the shade library, e.g. one lipstick shade."""

    __tablename__ = "shade_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False, max_length=255)
    hex_color: str = Field(nullable=False, max_length=9)
    category: ShadeCategory = Field(sa_column=Column(pg_enum(ShadeCategory, "shade_category"), nullable=False))
    finish: ShadeFinish = Field(sa_column=Column(pg_enum(ShadeFinish, "shade_finish"), nullable=False))
