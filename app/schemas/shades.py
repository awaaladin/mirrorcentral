from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import ShadeCategory, ShadeFinish


class ShadePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    hex_color: str
    category: ShadeCategory
    finish: ShadeFinish
