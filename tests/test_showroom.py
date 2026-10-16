from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routes import showroom as showroom_route
from app.config import get_settings
from app.services import showroom as showroom_service
from app.services.showroom import FaceAnalysis, ShowroomUnavailable


def _auth_headers(client: TestClient) -> dict[str, str]:
    token = client.post("/auth/register", json={"email": "s@example.com", "password": "correct-horse-1"}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def _png() -> dict:
    return {"image": ("face.png", b"\x89PNG fake", "image/png")}


def test_requires_auth(client: TestClient) -> None:
    assert client.post("/showroom/analyze", files=_png()).status_code in (401, 403)


def test_rejects_non_image(client: TestClient) -> None:
    r = client.post("/showroom/analyze", files={"image": ("a.txt", b"hi", "text/plain")}, headers=_auth_headers(client))
    assert r.status_code == 415


def test_returns_analysis(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake(data: bytes, media_type: str) -> FaceAnalysis:
        return FaceAnalysis(skin_depth=8, undertone="warm", skin_hex="#5A3825", lip_hex="#7A3B3B", face_shape="oval")

    monkeypatch.setattr(showroom_route, "analyze_face", fake)
    r = client.post("/showroom/analyze", files=_png(), headers=_auth_headers(client))
    assert r.status_code == 200
    assert r.json()["skin_depth"] == 8


def test_unconfigured_is_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake(data: bytes, media_type: str) -> FaceAnalysis:
        raise ShowroomUnavailable("nope", configured=False)

    monkeypatch.setattr(showroom_route, "analyze_face", fake)
    assert client.post("/showroom/analyze", files=_png(), headers=_auth_headers(client)).status_code == 503


@pytest.mark.anyio
async def test_service_parses_gemini_and_drops_bad_hex(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    get_settings.cache_clear()
    payload = (
        '{"skin_depth":7,"undertone":"olive","skin_hex":"#6B4A33","lip_hex":"#8A4B4B","face_shape":"round",'
        '"suggestions":[{"category":"lipstick","name":"Brick","hex":"#9C3B2E"},'
        '{"category":"blush","name":"Bad","hex":"red"}]}'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "test-key"
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": payload}]}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
        result = await showroom_service.analyze_face(b"x", "image/png", client=c)
    get_settings.cache_clear()
    assert [s.name for s in result.suggestions] == ["Brick"]
