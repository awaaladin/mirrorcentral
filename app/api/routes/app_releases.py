from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.app_release import AppRelease
from app.config import get_settings
from app.models.crash_report import CrashReport
from app.models.download_event import DownloadEvent
from app.models.enums import AppPlatform
from app.schemas.app_releases import AppReleasePublic

# No auth dependency on purpose: the app needs to check for updates before (and regardless of)
# any sign-in, same reasoning as the public shade catalog.
router = APIRouter(prefix="/app", tags=["app-releases"])


async def _latest_release(session: AsyncSession, platform: AppPlatform) -> AppRelease:
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


@router.get("/version", response_model=AppReleasePublic)
async def get_latest_version(
    request: Request,
    platform: AppPlatform = AppPlatform.ANDROID,
    session: AsyncSession = Depends(get_session),
) -> AppReleasePublic:
    release = await _latest_release(session, platform)
    # The website's Download button and the app's update prompt both read this link, so pointing it
    # at /app/download counts every download without either of them changing.
    source = "app" if "okhttp" in request.headers.get("user-agent", "").lower() else "web"
    counted = f"{get_settings().public_base_url}/app/download?platform={platform.value}&src={source}"
    return AppReleasePublic.model_validate(release).model_copy(update={"download_url": counted})


# Link-preview fetchers, crawlers and command-line tools aren't people downloading the app.
_NOT_PEOPLE = ("bot", "crawl", "spider", "preview", "facebookexternalhit", "whatsapp/", "telegram", "slack", "curl", "wget", "headless")


@router.get("/download")
async def download_app(
    request: Request,
    platform: AppPlatform = AppPlatform.ANDROID,
    src: str = "web",
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Counts a download, then sends the person to the APK. Keeps no IP address or user agent."""
    release = await _latest_release(session, platform)
    agent = request.headers.get("user-agent", "").lower()
    if not any(marker in agent for marker in _NOT_PEOPLE) and "range" not in request.headers:
        session.add(DownloadEvent(version_code=release.version_code, source=src if src in ("web", "app") else "web"))
        await session.commit()
    return RedirectResponse(release.download_url, status_code=status.HTTP_302_FOUND)


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
