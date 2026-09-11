from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ClientTag


class ClientProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    notes: str = ""
    tag: ClientTag = ClientTag.SELF


class ClientProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    notes: str | None = None
    tag: ClientTag | None = None


class ClientProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_user_id: uuid.UUID
    name: str
    notes: str
    tag: ClientTag
