from __future__ import annotations

import hashlib
import hmac
import json
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings

SECRET = "sk_test_unit"


@pytest.fixture(autouse=True)
def _paystack_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(get_settings(), "paystack_secret_key", SECRET)


def _auth_headers(client: TestClient, email: str = "artist@example.com") -> dict[str, str]:
    response = client.post("/auth/register", json={"email": email, "password": "correct-horse-1"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _checkout(client: TestClient, headers: dict[str, str], plan: str = "solo") -> tuple[str, mock.AsyncMock]:
    init = mock.AsyncMock(return_value={"authorization_url": "https://checkout.paystack.com/abc"})
    with mock.patch("app.services.paystack.initialize_transaction", init):
        response = client.post("/billing/checkout", json={"plan": plan}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["reference"], init


def _charge(reference: str, amount_kobo: int = 750_000) -> dict:
    return {"id": 4242, "reference": reference, "amount": amount_kobo, "status": "success", "currency": "NGN"}


def _signed_webhook(client: TestClient, payload: dict, secret: str = SECRET):
    body = json.dumps(payload).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    return client.post("/billing/paystack/webhook", content=body,
                       headers={"x-paystack-signature": sig, "content-type": "application/json"})


def test_checkout_reference_and_metadata_identify_mirror(client: TestClient) -> None:
    headers = _auth_headers(client)
    reference, init = _checkout(client, headers)

    assert reference.startswith("MIRROR-UNLOCK-")
    kwargs = init.call_args.kwargs
    assert kwargs["amount_kobo"] == 750_000
    assert kwargs["callback_url"].endswith("/billing/return")
    assert kwargs["metadata"]["app"] == "MIRROR"
    assert kwargs["metadata"]["custom_fields"][0]["value"] == "Mirror"


def test_webhook_unlocks_the_account_for_good(client: TestClient) -> None:
    headers = _auth_headers(client)
    reference, _ = _checkout(client, headers)
    assert client.get("/billing/subscription", headers=headers).json()["unlocked"] is False

    payload = {"event": "charge.success", "data": _charge(reference)}
    assert _signed_webhook(client, payload).status_code == 200
    assert _signed_webhook(client, payload).status_code == 200  # re-delivery

    assert client.get("/billing/subscription", headers=headers).json() == {
        "plan": None, "active": False, "renews_at": None, "unlocked": True,
    }


def test_unlocked_account_is_not_charged_again(client: TestClient) -> None:
    headers = _auth_headers(client)
    reference, _ = _checkout(client, headers)
    _signed_webhook(client, {"event": "charge.success", "data": _charge(reference)})
    assert client.post("/billing/checkout", json={"plan": "solo"}, headers=headers).status_code == 409


def test_studio_reference_is_pro(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "studio_plan_available", True)
    reference, _ = _checkout(client, _auth_headers(client), plan="studio")
    assert reference.startswith("MIRROR-PRO-")


def test_webhook_rejects_bad_signature(client: TestClient) -> None:
    response = _signed_webhook(client, {"event": "charge.success", "data": _charge("MIRROR-PRO-X")}, secret="nope")
    assert response.status_code == 400


def test_webhook_ignores_other_apps(client: TestClient) -> None:
    response = _signed_webhook(client, {"event": "charge.success", "data": _charge("CHOROPIA-ORDER-20261023-AB")})
    assert response.status_code == 200


def test_short_payment_does_not_activate(client: TestClient) -> None:
    headers = _auth_headers(client)
    reference, _ = _checkout(client, headers)
    _signed_webhook(client, {"event": "charge.success", "data": _charge(reference, amount_kobo=100)})
    assert client.get("/billing/subscription", headers=headers).json()["unlocked"] is False


def test_verify_without_webhook(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "studio_plan_available", True)
    headers = _auth_headers(client)
    reference, _ = _checkout(client, headers, plan="studio")
    verify = mock.AsyncMock(return_value=_charge(reference, amount_kobo=1_200_000))
    with mock.patch("app.services.paystack.verify_transaction", verify):
        response = client.post(f"/billing/verify/{reference}", headers=headers)
    assert response.json()["status"] == "success"
    assert client.get("/billing/subscription", headers=headers).json()["plan"] == "studio"


def test_studio_checkout_refused_while_unavailable(client: TestClient) -> None:
    # studio_plan_available defaults to False - pricing under review, not purchasable yet.
    response = client.post("/billing/checkout", json={"plan": "studio"}, headers=_auth_headers(client))
    assert response.status_code == 409


def test_verify_is_owner_only(client: TestClient) -> None:
    reference, _ = _checkout(client, _auth_headers(client, "a@example.com"))
    response = client.post(f"/billing/verify/{reference}", headers=_auth_headers(client, "b@example.com"))
    assert response.status_code == 404


def test_return_page_confirms_payment(client: TestClient) -> None:
    reference, _ = _checkout(client, _auth_headers(client))
    with mock.patch("app.services.paystack.verify_transaction", mock.AsyncMock(return_value=_charge(reference))):
        response = client.get(f"/billing/return?reference={reference}")
    assert response.status_code == 200
    assert "Payment received" in response.text


def test_plans_are_public(client: TestClient) -> None:
    plans = client.get("/billing/plans").json()
    assert {p["plan"]: p["price_ngn"] for p in plans} == {"solo": 7500, "studio": 12000}
    assert {p["plan"]: p["available"] for p in plans} == {"solo": True, "studio": False}
    assert {p["plan"]: p["one_time"] for p in plans} == {"solo": True, "studio": False}
    assert {p["plan"]: p["period_days"] for p in plans} == {"solo": None, "studio": 30}
