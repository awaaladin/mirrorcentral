from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.app_release import AppRelease
from app.models.crash_report import CrashReport
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


log = logging.getLogger(__name__)


class CrashReportIn(BaseModel):
    kind: str = Field(max_length=20)
    summary: str = Field(default="", max_length=500)
    trace: str = Field(default="", max_length=20_000)
    app_version: str = Field(default="", max_length=20)
    version_code: int = 0
    device: str = Field(default="", max_length=120)
    android_sdk: int = 0
    abis: list[str] = Field(default_factory=list, max_length=8)
    ram_mb: int = 0
    pss_kb: int = 0


@router.post("/crash-reports", status_code=status.HTTP_204_NO_CONTENT)
async def report_crash(report: CrashReportIn, session: AsyncSession = Depends(get_session)) -> None:
    """Why the app closed on a phone, sent on the next launch. No auth: crashes happen before
    sign-in too. Holds no photos or account details (see CrashReporter.kt in the app)."""
    data = report.model_dump()
    data["abis"] = ",".join(report.abis)[:120]
    session.add(CrashReport(**data))
    await session.commit()
    log.warning("app crash report: %s %s on %s (%s)", report.kind, report.app_version, report.device, report.summary[:200])
