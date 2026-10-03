from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.app_release import AppRelease
from app.models.enums import AppPlatform
from app.schemas.app_releases import AppReleasePublic

# No auth dependency on purpose: the app needs to check for updates before (and regardless of)
# any sign-in, same reasoning as the public shade catalog.
router = APIRouter(prefix="/app", tags=["app-releases"])


@router.get("/version", response_model=AppReleasePublic)
async def get_latest_version(
    platform: AppPlatform = AppPlatform.ANDROID,
    session: AsyncSession = Depends(get_session),
) -> AppRelease:
    result = await session.execute(
        select(AppRelease)
        .where(AppRelease.platform == platform)
        .order_by(AppRelease.version_code.desc())
        .limit(1)
    )
    release = result.scalar_one_or_none()
    if release is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No release published yet.")
    return release
