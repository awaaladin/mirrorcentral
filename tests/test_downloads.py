import pytest
from sqlalchemy import func, select

from app.models.app_release import AppRelease
from app.models.download_event import DownloadEvent
from app.models.enums import AppPlatform

pytestmark = pytest.mark.anyio

APK = "https://example.test/mirror-9.9.9.apk"
BROWSER = {"user-agent": "Mozilla/5.0 (Linux; Android 13) Chrome/120 Mobile Safari/537.36"}


async def _release(session_factory) -> None:
    async with session_factory() as session:
        session.add(AppRelease(platform=AppPlatform.ANDROID, version_code=99, version_name="9.9.9", download_url=APK))
        await session.commit()


async def _count(session_factory) -> int:
    async with session_factory() as session:
        return (await session.execute(select(func.count()).select_from(DownloadEvent))).scalar_one()


async def test_version_link_goes_through_the_counter_and_download_redirects(client, session_factory) -> None:
    await _release(session_factory)
    link = client.get("/app/version", headers=BROWSER).json()["download_url"]
    assert "/app/download" in link and "src=web" in link
    assert "src=app" in client.get("/app/version", headers={"user-agent": "okhttp/4.12.0"}).json()["download_url"]

    response = client.get("/app/download?platform=android&src=web", headers=BROWSER, follow_redirects=False)
    assert response.status_code == 302 and response.headers["location"] == APK
    assert await _count(session_factory) == 1


async def test_crawlers_and_resumed_downloads_are_not_counted(client, session_factory) -> None:
    await _release(session_factory)
    for headers in ({"user-agent": "WhatsApp/2.23"}, {"user-agent": "Googlebot/2.1"}, {**BROWSER, "range": "bytes=100-"}):
        assert client.get("/app/download", headers=headers, follow_redirects=False).status_code == 302
    assert await _count(session_factory) == 0
