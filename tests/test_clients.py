from __future__ import annotations

from fastapi.testclient import TestClient


def _auth_headers(client: TestClient, email: str = "artist@example.com") -> dict[str, str]:
    response = client.post("/auth/register", json={"email": email, "password": "correct-horse-1"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_clients(client: TestClient) -> None:
    headers = _auth_headers(client)

    create_response = client.post("/clients", json={"name": "Amina T.", "tag": "client"}, headers=headers)
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["name"] == "Amina T."
    assert body["tag"] == "client"

    list_response = client.get("/clients", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_clients_are_scoped_to_owner(client: TestClient) -> None:
    headers_a = _auth_headers(client, "artist-a@example.com")
    headers_b = _auth_headers(client, "artist-b@example.com")

    created = client.post("/clients", json={"name": "Private Client"}, headers=headers_a).json()

    assert client.get("/clients", headers=headers_b).json() == []
    assert client.get(f"/clients/{created['id']}", headers=headers_b).status_code == 404


def test_update_and_delete_client(client: TestClient) -> None:
    headers = _auth_headers(client)
    created = client.post("/clients", json={"name": "Original Name"}, headers=headers).json()

    patched = client.patch(f"/clients/{created['id']}", json={"notes": "VIP"}, headers=headers)
    assert patched.status_code == 200
    assert patched.json()["notes"] == "VIP"
    assert patched.json()["name"] == "Original Name"

    deleted = client.delete(f"/clients/{created['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/clients/{created['id']}", headers=headers).status_code == 404


def test_create_and_list_looks(client: TestClient) -> None:
    headers = _auth_headers(client)
    client_profile = client.post("/clients", json={"name": "Amina T."}, headers=headers).json()

    look_payload = {
        "source_photo_url": "https://cdn.example.com/photo.jpg",
        "layers": {"lip_color": "#B85C38", "eyebrow_style": "soft_arch"},
    }
    create_response = client.post(f"/clients/{client_profile['id']}/looks", json=look_payload, headers=headers)
    assert create_response.status_code == 201
    look = create_response.json()
    assert look["layers"]["lip_color"] == "#B85C38"
    assert look["layers"]["eyebrow_style"] == "soft_arch"

    list_response = client.get(f"/clients/{client_profile['id']}/looks", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_look_rejects_invalid_style_enum(client: TestClient) -> None:
    headers = _auth_headers(client)
    client_profile = client.post("/clients", json={"name": "Amina T."}, headers=headers).json()

    response = client.post(
        f"/clients/{client_profile['id']}/looks",
        json={"source_photo_url": "https://cdn.example.com/photo.jpg", "layers": {"eyebrow_style": "not-a-style"}},
        headers=headers,
    )
    assert response.status_code == 422


def test_looks_scoped_through_client_ownership(client: TestClient) -> None:
    headers_a = _auth_headers(client, "artist-a@example.com")
    headers_b = _auth_headers(client, "artist-b@example.com")

    client_profile = client.post("/clients", json={"name": "Amina T."}, headers=headers_a).json()
    look = client.post(
        f"/clients/{client_profile['id']}/looks",
        json={"source_photo_url": "https://cdn.example.com/photo.jpg"},
        headers=headers_a,
    ).json()

    response = client.get(f"/clients/{client_profile['id']}/looks/{look['id']}", headers=headers_b)
    assert response.status_code == 404


def test_update_and_delete_look(client: TestClient) -> None:
    headers = _auth_headers(client)
    client_profile = client.post("/clients", json={"name": "Amina T."}, headers=headers).json()
    look = client.post(
        f"/clients/{client_profile['id']}/looks",
        json={"source_photo_url": "https://cdn.example.com/a.jpg", "layers": {"lip_color": "red"}},
        headers=headers,
    ).json()

    patched = client.patch(
        f"/clients/{client_profile['id']}/looks/{look['id']}",
        json={"layers": {"lip_color": "blue"}},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["layers"] == {"lip_color": "blue"}

    deleted = client.delete(f"/clients/{client_profile['id']}/looks/{look['id']}", headers=headers)
    assert deleted.status_code == 204
