import pytest
from sqlalchemy import select

from app.models.crash_report import CrashReport

pytestmark = pytest.mark.anyio


async def test_crash_report_is_stored_without_sign_in(client, session_factory) -> None:
    response = client.post(
        "/app/crash-reports",
        json={
            "kind": "native_crash",
            "summary": "crash signal 11 (SIGSEGV)",
            "app_version": "0.4.1",
            "version_code": 8,
            "device": "INFINIX X6525",
            "android_sdk": 33,
            "abis": ["arm64-v8a", "armeabi-v7a"],
            "ram_mb": 3700,
        },
    )
    assert response.status_code == 204
    async with session_factory() as session:
        report = (await session.execute(select(CrashReport))).scalar_one()
    assert (report.kind, report.device, report.abis) == ("native_crash", "INFINIX X6525", "arm64-v8a,armeabi-v7a")


def test_oversized_report_is_refused(client) -> None:
    response = client.post("/app/crash-reports", json={"kind": "crash", "trace": "x" * 30_000})
    assert response.status_code == 422
