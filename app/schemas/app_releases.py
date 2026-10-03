from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AppPlatform


class AppReleaseCreate(BaseModel):
    platform: AppPlatform = AppPlatform.ANDROID
    version_code: int
    version_name: str
    download_url: str
    release_notes: str = ""
    is_mandatory: bool = False


class AppReleasePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    platform: AppPlatform
    version_code: int
    version_name: str
    download_url: str
    release_notes: str
    is_mandatory: bool
    created_at: datetime


class DeviceTokenRegister(BaseModel):
    token: str
    platform: AppPlatform = AppPlatform.ANDROID
