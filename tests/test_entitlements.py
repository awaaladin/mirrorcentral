from __future__ import annotations

import base64
import json
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
from app.services.showroom import FaceAnalysis, ShowroomUnavailable

CLIENT = {"name": "Bride", "notes": "", "tag": "client"}
PHOTO = {"image": ("face.jpg", b"jpeg-bytes", "image/jpeg")}
ANALYSIS = FaceAnalysis.model_construct()

Subscribe = Callable[..., Awaitable[None]]
Unlock = Callable[[str], Awaitable[None]]


def _register(client: TestClient, email: str = "artist@example.com", **extra: str) -> tuple[str, dict[str, str]]:
    body = client.post("/auth/register", json={"email": email, "password": "correct-horse-1", **extra}).json()
    return body["user"]["id"], {"Authorization": f"Bearer {body['access_token']}"}


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
def unlock(session_factory) -> Unlock:
    async def _unlock(user_id: str) -> None:
        async with session_factory() as session:
            user = await session.get(User, uuid.UUID(user_id))
            user.unlocked_at = datetime.now(UTC)
            session.add(user)
            await session.commit()
    return _unlock


def _analyze(client: TestClient, headers: dict[str, str], analyze: mock.AsyncMock | None = None):
    with mock.patch("app.api.routes.showroom.analyze_face", analyze or mock.AsyncMock(return_value=ANALYSIS)):
        return client.post("/showroom/analyze", files=PHOTO, headers=headers)


def test_signup_cannot_choose_pro(client: TestClient) -> None:
    body = client.post(
        "/auth/register", json={"email": "a@example.com", "password": "correct-horse-1", "account_type": "business"}
    ).json()
    assert body["user"]["account_type"] == "consumer"


def test_only_the_one_time_payment_is_on_sale(client: TestClient) -> None:
    available = {plan["plan"]: plan["available"] for plan in client.get("/billing/plans").json()}
    assert available == {"solo": True, "studio": False}
    _, headers = _register(client)
    assert client.post("/billing/checkout", json={"plan": "studio"}, headers=headers).status_code == 409


def test_free_account_is_refused_pro_features(client: TestClient) -> None:
    _, headers = _register(client)
    assert client.post("/clients", json=CLIENT, headers=headers).status_code == 403
    assert _analyze(client, headers).status_code == 403


async def test_unlocked_account_gets_no_pro_features(client: TestClient, unlock: Unlock) -> None:
    user_id, headers = _register(client)
    await unlock(user_id)
    assert _analyze(client, headers).status_code == 403
    assert client.post("/clients", json=CLIENT, headers=headers).status_code == 403


async def test_studio_gets_both(client: TestClient, subscribe: Subscribe) -> None:
    user_id, headers = _register(client)
    await subscribe(user_id, SubscriptionPlan.STUDIO)
    assert _analyze(client, headers).status_code == 200
    assert client.post("/clients", json=CLIENT, headers=headers).status_code == 201


async def test_lapsed_plan_is_refused(client: TestClient, subscribe: Subscribe) -> None:
    user_id, headers = _register(client)
    await subscribe(user_id, SubscriptionPlan.STUDIO, days=-1)
    assert client.post("/clients", json=CLIENT, headers=headers).status_code == 403
    assert _analyze(client, headers).status_code == 403
    assert client.get("/clients", headers=headers).status_code == 200  # their data stays reachable


async def test_showroom_monthly_cap_and_refund(client: TestClient, subscribe: Subscribe, monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "studio_plan_monthly_cap", 2)
    user_id, headers = _register(client)
    await subscribe(user_id, SubscriptionPlan.STUDIO)

    failing = mock.AsyncMock(side_effect=ShowroomUnavailable("down"))
    assert _analyze(client, headers, failing).status_code in (502, 503)  # refunded
    assert _analyze(client, headers).status_code == 200
    assert _analyze(client, headers).status_code == 200
    assert _analyze(client, headers).status_code == 429


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


async def test_one_time_license_lasts_for_good(client: TestClient, unlock: Unlock, license_key) -> None:
    user_id, headers = _register(client)
    request = {"device_id": "device-12345"}
    assert client.post("/billing/license", json=request, headers=headers).json() == {"license": None}

    await unlock(user_id)
    claims = _license_claims(client.post("/billing/license", json=request, headers=headers).json()["license"], license_key)
    assert (claims["sub"], claims["plan"], claims["did"]) == (user_id, "solo", "device-12345")
    assert claims["exp"] > (datetime.now(UTC) + timedelta(days=36000)).timestamp()


async def test_pro_license_lapses_without_check_ins(client: TestClient, subscribe: Subscribe, license_key) -> None:
    user_id, headers = _register(client)
    await subscribe(user_id, SubscriptionPlan.STUDIO)
    license_ = client.post("/billing/license", json={"device_id": "device-12345"}, headers=headers).json()["license"]
    claims = _license_claims(license_, license_key)
    assert claims["plan"] == "studio"
    assert claims["exp"] <= (datetime.now(UTC) + timedelta(days=14, seconds=5)).timestamp()
