from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import EyebrowStyle, GeleStyle, LashStyle


class MakeupLookLayers(BaseModel):
    """Free-form-by-design (see MakeupLook.layers docstring): color/shade fields are
    plain strings (a shade id or a hex code — the app decides which), while the style
    fields are validated against the app's closed style vocabularies."""

    lip_color: str | None = None
    foundation_shade: str | None = None
    eyeshadow_color: str | None = None
    blush_color: str | None = None
    eyebrow_style: EyebrowStyle | None = None
    lash_style: LashStyle | None = None
    gele_style: GeleStyle | None = None


class MakeupLookCreate(BaseModel):
    source_photo_url: str
    layers: MakeupLookLayers = MakeupLookLayers()


class MakeupLookUpdate(BaseModel):
    source_photo_url: str | None = None
    layers: MakeupLookLayers | None = None


class MakeupLookPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_profile_id: uuid.UUID
    source_photo_url: str
    layers: dict[str, object]
    created_at: datetime
