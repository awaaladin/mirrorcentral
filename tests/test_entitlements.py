from __future__ import annotations

import base64
import json
import re
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from unittest import mock

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.config import get_settings
from app.models.enums import SubscriptionPlan, SubscriptionStatus
from app.models.subscription import Subscription
from app.models.user import User
from app.services import mailer
from app.services.showroom import FaceAnalysis, ShowroomUnavailable

CLIENT = {"name": "Bride", "notes": "", "tag": "client"}
PHOTO = {"image": ("face.jpg", b"jpeg-bytes", "image/jpeg")}
ANALYSIS = FaceAnalysis.model_construct()

Subscribe = Callable[..., Awaitable[None]]
Patch = Callable[..., Awaitable[None]]


@pytest.fixture(autouse=True)
def _capture_codes(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """No SMTP in these tests: keep the confirmation code each email would have carried."""
    codes: dict[str, str] = {}
    monkeypatch.setattr(mailer, "send_welcome", lambda email, code: codes.__setitem__(email, code) or True)
    monkeypatch.setattr(mailer, "send_verification_code", lambda email, code: codes.__setitem__(email, code) or True)
    return codes


def _register(client: TestClient, email: str = "artist@example.com", **extra: str) -> tuple[str, dict[str, str]]:
    body = client.post("/auth/register", json={"email": email, "password": "correct-horse-1", **extra}).json()
    return body["user"]["id"], {"Authorization": f"Bearer {body['access_token']}"}


def _verified(client: TestClient, codes: dict[str, str], email: str = "artist@example.com") -> tuple[str, dict[str, str]]:
    user_id, headers = _register(client, email)
    assert client.post("/auth/email/verify", json={"code": codes[email]}, headers=headers).status_code == 200
    return user_id, headers


@pytest.fixture
def subscribe(session_factory) -> Subscribe:
    async def _subscribe(user_id: str, plan: SubscriptionPlan, days: int = 30) -> None:
        async with session_factory() as session:
            session.add(Subscription(
                user_id=uuid.UUID(user_id), plan=plan, status=SubscriptionStatus.ACTIVE,
                renews_at=datetime.now(UTC) + timedelta(days=days),
            ))
            await session.commit()
    return _subscribe


@pytest.fixture
def patch_user(session_factory) -> Patch:
    async def _patch(user_id: str, **fields: object) -> None:
        async with session_factory() as session:
            user = await session.get(User, uuid.UUID(user_id))
            for name, value in fields.items():
                setattr(user, name, value)
            session.add(user)
            await session.commit()
    return _patch


def _analyze(client: TestClient, headers: dict[str, str], analyze: mock.AsyncMock | None = None):
    with mock.patch("app.api.routes.showroom.analyze_face", analyze or mock.AsyncMock(return_value=ANALYSIS)):
        return client.post("/showroom/analyze", files=PHOTO, headers=headers)


def _photo(client: TestClient, headers: dict[str, str], n: int) -> dict:
    return client.post("/usage/photo", json={"photo_id": f"photo-{n:012d}"}, headers=headers).json()


# --- sign-up and email confirmation

def test_signup_cannot_choose_pro(client: TestClient) -> None:
    body = client.post(
        "/auth/register", json={"email": "a@example.com", "password": "correct-horse-1", "account_type": "business"}
    ).json()
    assert body["user"]["account_type"] == "consumer"
    assert body["user"]["email_verified"] is False


def test_welcome_email_carries_a_working_code(client: TestClient, _capture_codes: dict[str, str]) -> None:
    _, headers = _register(client)
    assert re.fullmatch(r"\d{6}", _capture_codes["artist@example.com"])
    assert client.post("/auth/email/verify", json={"code": _capture_codes["artist@example.com"]}, headers=headers).status_code == 200
    assert client.get("/usage", headers=headers).json()["email_verified"] is True


def test_wrong_codes_run_out(client: TestClient, _capture_codes: dict[str, str]) -> None:
    _, headers = _register(client)
    real = _capture_codes["artist@example.com"]
    wrong = "000000" if real != "000000" else "111111"
    for _ in range(5):
        assert client.post("/auth/email/verify", json={"code": wrong}, headers=headers).status_code == 400
    # Five wrong guesses use the code up, even for the right one; a new code is needed.
    assert client.post("/auth/email/verify", json={"code": real}, headers=headers).status_code == 400
    assert client.post("/auth/email/send", headers=headers).json() == {"email_verified": False}
    fresh = _capture_codes["artist@example.com"]
    assert client.post("/auth/email/verify", json={"code": fresh}, headers=headers).status_code == 200


async def test_expired_code_is_refused(client: TestClient, _capture_codes: dict[str, str], patch_user: Patch) -> None:
    user_id, headers = _register(client)
    await patch_user(user_id, email_code_expires_at=datetime.now(UTC) - timedelta(minutes=1))
    assert client.post("/auth/email/verify", json={"code": _capture_codes["artist@example.com"]}, headers=headers).status_code == 400


# --- free allowances

def test_free_photos_need_a_confirmed_email(client: TestClient) -> None:
    _, headers = _register(client)
    assert _photo(client, headers, 1) == {"allowed": False, "reason": "verify_email", "photos": {"used": 0, "limit": 10}}


def test_ten_free_photos_a_month(client: TestClient, _capture_codes: dict[str, str]) -> None:
    _, headers = _verified(client, _capture_codes)
    for n in range(10):
        assert _photo(client, headers, n)["allowed"] is True
    assert _photo(client, headers, 3)["allowed"] is True  # reopening a counted photo is free
    eleventh = _photo(client, headers, 10)
    assert eleventh == {"allowed": False, "reason": "limit", "photos": {"used": 10, "limit": 10}}


def test_showroom_needs_a_confirmed_email(client: TestClient) -> None:
    _, headers = _register(client)
    response = _analyze(client, headers)
    assert response.status_code == 403
    assert response.headers["x-mirror-reason"] == "verify_email"


def test_three_free_showroom_analyses_and_failures_are_free(client: TestClient, _capture_codes: dict[str, str]) -> None:
    _, headers = _verified(client, _capture_codes)
    failing = mock.AsyncMock(side_effect=ShowroomUnavailable("down"))
    assert _analyze(client, headers, failing).status_code in (502, 503)  # given back
    for used in (1, 2, 3):
        response = _analyze(client, headers)
        assert response.status_code == 200
        assert (response.headers["x-mirror-used"], response.headers["x-mirror-limit"]) == (str(used), "3")
    fourth = _analyze(client, headers)
    assert fourth.status_code == 429 and fourth.headers["x-mirror-reason"] == "limit"


def test_daily_ceiling_on_free_showroom(client: TestClient, _capture_codes: dict[str, str], monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "free_showroom_daily_total", 1)
    _, first = _verified(client, _capture_codes, "a@example.com")
    _, second = _verified(client, _capture_codes, "b@example.com")
    assert _analyze(client, first).status_code == 200
    busy = _analyze(client, second)
    assert busy.status_code == 503 and busy.headers["x-mirror-reason"] == "busy"


# --- paid plans

async def test_personal_is_unlimited_photos_and_more_showroom(client: TestClient, subscribe: Subscribe, monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "free_showroom_daily_total", 0)  # paid use isn't held to it
    user_id, headers = _register(client)  # paying doesn't need a code
    await subscribe(user_id, SubscriptionPlan.SOLO)
    for n in range(15):
        assert _photo(client, headers, n)["allowed"] is True
    response = _analyze(client, headers)
    assert response.status_code == 200 and response.headers["x-mirror-limit"] == "30"
    assert client.post("/clients", json=CLIENT, headers=headers).status_code == 403


async def test_studio_gets_client_mode(client: TestClient, subscribe: Subscribe) -> None:
    user_id, headers = _register(client)
    await subscribe(user_id, SubscriptionPlan.STUDIO)
    assert client.post("/clients", json=CLIENT, headers=headers).status_code == 201
    assert _analyze(client, headers).headers["x-mirror-limit"] == "100"


async def test_lapsed_plan_falls_back_to_free(client: TestClient, subscribe: Subscribe) -> None:
    user_id, headers = _register(client)
    await subscribe(user_id, SubscriptionPlan.STUDIO, days=-1)
    assert client.post("/clients", json=CLIENT, headers=headers).status_code == 403
    assert _photo(client, headers, 1)["reason"] == "verify_email"
    assert client.get("/clients", headers=headers).status_code == 200  # their data stays reachable


async def test_earlier_one_time_buyers_keep_unlimited_photos(client: TestClient, patch_user: Patch) -> None:
    user_id, headers = _register(client)
    await patch_user(user_id, unlocked_at=datetime.now(UTC))
    for n in range(12):
        assert _photo(client, headers, n)["allowed"] is True
    usage = client.get("/usage", headers=headers).json()
    assert usage["paid"] is True and usage["photos"]["limit"] is None and usage["showroom"]["limit"] == 3


def test_personal_is_on_sale_and_studio_is_not(client: TestClient) -> None:
    available = {plan["plan"]: plan["available"] for plan in client.get("/billing/plans").json()}
    assert available == {"solo": True, "studio": False}
    _, headers = _register(client)
    assert client.post("/billing/checkout", json={"plan": "studio"}, headers=headers).status_code == 409


# --- licenses

def _padded(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _license_claims(license_: str, key: ec.EllipticCurvePrivateKey) -> dict:
    payload, signature = license_.split(".")
    key.public_key().verify(_padded(signature), payload.encode(), ec.ECDSA(hashes.SHA256()))
    return json.loads(_padded(payload))


@pytest.fixture
def license_key(monkeypatch: pytest.MonkeyPatch) -> ec.EllipticCurvePrivateKey:
    key = ec.generate_private_key(ec.SECP256R1())
    der = key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    monkeypatch.setattr(get_settings(), "license_private_key", base64.b64encode(der).decode())
    return key


async def test_personal_license_lapses_without_check_ins(client: TestClient, subscribe: Subscribe, license_key) -> None:
    user_id, headers = _register(client)
    request = {"device_id": "device-12345"}
    assert client.post("/billing/license", json=request, headers=headers).json() == {"license": None}

    await subscribe(user_id, SubscriptionPlan.SOLO)
    claims = _license_claims(client.post("/billing/license", json=request, headers=headers).json()["license"], license_key)
    assert (claims["sub"], claims["plan"], claims["did"]) == (user_id, "solo", "device-12345")
    assert claims["exp"] <= (datetime.now(UTC) + timedelta(days=14, seconds=5)).timestamp()


async def test_earlier_one_time_license_lasts(client: TestClient, patch_user: Patch, license_key) -> None:
    user_id, headers = _register(client)
    await patch_user(user_id, unlocked_at=datetime.now(UTC))
    license_ = client.post("/billing/license", json={"device_id": "device-12345"}, headers=headers).json()["license"]
    claims = _license_claims(license_, license_key)
    assert claims["plan"] == "solo"
    assert claims["exp"] > (datetime.now(UTC) + timedelta(days=36000)).timestamp()
