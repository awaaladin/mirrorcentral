from __future__ import annotations

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "user@example.com", password: str = "correct-horse-1") -> dict:
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()


def test_register_returns_tokens(client: TestClient) -> None:
    body = _register(client)
    assert body["user"]["email"] == "user@example.com"
    assert body["user"]["account_type"] == "consumer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_register_duplicate_email_conflicts(client: TestClient) -> None:
    _register(client)
    response = client.post("/auth/register", json={"email": "user@example.com", "password": "another-pass-1"})
    assert response.status_code == 409


def test_register_short_password_rejected(client: TestClient) -> None:
    response = client.post("/auth/register", json={"email": "short@example.com", "password": "short"})
    assert response.status_code == 422


def test_login_success(client: TestClient) -> None:
    _register(client)
    response = client.post("/auth/login", json={"email": "user@example.com", "password": "correct-horse-1"})
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "user@example.com"


def test_login_wrong_password(client: TestClient) -> None:
    _register(client)
    response = client.post("/auth/login", json={"email": "user@example.com", "password": "wrong-password"})
    assert response.status_code == 401


def test_login_unknown_email(client: TestClient) -> None:
    response = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever-1"})
    assert response.status_code == 401


def test_refresh_issues_new_tokens(client: TestClient) -> None:
    tokens = _register(client)
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["access_token"] != tokens["access_token"]


def test_refresh_rejects_access_token(client: TestClient) -> None:
    tokens = _register(client)
    response = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401


def test_refresh_rejects_garbage_token(client: TestClient) -> None:
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-jwt"})
    assert response.status_code == 401


def test_protected_endpoint_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/clients")
    assert response.status_code == 403  # HTTPBearer's auto_error response for a missing header


def test_protected_endpoint_accepts_valid_token(client: TestClient) -> None:
    tokens = _register(client)
    response = client.get("/clients", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200


def test_login_elsewhere_signs_out_the_old_device(client: TestClient) -> None:
    first = _register(client)
    second = client.post("/auth/login", json={"email": "user@example.com", "password": "correct-horse-1"}).json()

    # The device that registered is now signed out, even though its access token hasn't expired.
    stale = client.get("/clients", headers={"Authorization": f"Bearer {first['access_token']}"})
    assert stale.status_code == 401

    # ...and its refresh token is dead too.
    stale_refresh = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert stale_refresh.status_code == 401

    # The device that just logged in works fine.
    fresh = client.get("/clients", headers={"Authorization": f"Bearer {second['access_token']}"})
    assert fresh.status_code == 200


def test_refresh_from_the_active_device_keeps_working(client: TestClient) -> None:
    tokens = _register(client)
    refreshed = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).json()
    still_works = client.get("/clients", headers={"Authorization": f"Bearer {refreshed['access_token']}"})
    assert still_works.status_code == 200
