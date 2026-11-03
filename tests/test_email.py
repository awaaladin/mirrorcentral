"""Email: welcome, payment receipt, forgot-password. SMTP is faked; nothing leaves the machine."""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from email.message import EmailMessage
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.services import mailer

SECRET = "sk_test_unit"


class FakeSMTP:
    sent: list[EmailMessage] = []
    fail = False

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def login(self, user, password):
        if FakeSMTP.fail:
            raise OSError("smtp down")

    def send_message(self, message):
        FakeSMTP.sent.append(message)


@pytest.fixture(autouse=True)
def _smtp(monkeypatch: pytest.MonkeyPatch):
    FakeSMTP.sent, FakeSMTP.fail = [], False
    monkeypatch.setenv("EMAIL_HOST_USER", "sender@example.com")
    monkeypatch.setenv("EMAIL_HOST_PASSWORD", "app-password")
    monkeypatch.setenv("EMAIL_FROM", "Mirror <sender@example.com>")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://mirror.test")
    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setattr(get_settings(), "paystack_secret_key", SECRET)


def _register(client: TestClient, email: str = "user@example.com", password: str = "correct-horse-1") -> dict:
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()


def _html(message: EmailMessage) -> str:
    return message.get_body(preferencelist=("html",)).get_content()


def _reset_token() -> str:
    text = FakeSMTP.sent[-1].get_body(preferencelist=("plain",)).get_content()
    return re.search(r"token=([^\s]+)", text).group(1)


def test_registering_sends_one_welcome_email(client: TestClient) -> None:
    _register(client)
    assert [m["To"] for m in FakeSMTP.sent] == ["user@example.com"]
    assert "Welcome" in FakeSMTP.sent[0]["Subject"]
    assert FakeSMTP.sent[0]["From"] == "Mirror <sender@example.com>"


def test_a_duplicate_registration_sends_nothing_more(client: TestClient) -> None:
    _register(client)
    client.post("/auth/register", json={"email": "user@example.com", "password": "another-pass-1"})
    assert len(FakeSMTP.sent) == 1


def test_a_broken_mail_server_never_breaks_signup(client: TestClient) -> None:
    FakeSMTP.fail = True
    body = _register(client)
    assert body["access_token"]
    assert FakeSMTP.sent == []


def test_nothing_is_sent_without_credentials(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EMAIL_HOST_PASSWORD")
    _register(client)
    assert FakeSMTP.sent == []


def test_user_text_is_escaped_and_subjects_have_no_newlines() -> None:
    html, _ = mailer.render("<script>x</script>", ["<b>hi</b>"], ("Go", 'https://x.test/?a="b"'))
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "<b>hi</b>" not in html
    mailer.send_email("a@example.com", "Hi\nBcc: x@y.z", "h", ["p"])
    assert "\n" not in FakeSMTP.sent[-1]["Subject"]


def _checkout_and_pay(client: TestClient) -> str:
    headers = {"Authorization": f"Bearer {_register(client, 'payer@example.com')['access_token']}"}
    init = mock.AsyncMock(return_value={"authorization_url": "https://checkout.paystack.com/abc"})
    with mock.patch("app.services.paystack.initialize_transaction", init):
        reference = client.post("/billing/checkout", json={"plan": "solo"}, headers=headers).json()["reference"]
    payload = {"event": "charge.success", "data": {"id": 4242, "reference": reference, "amount": 750_000, "status": "success", "currency": "NGN"}}
    body = json.dumps(payload).encode()
    sig = hmac.new(SECRET.encode(), body, hashlib.sha512).hexdigest()
    for _ in range(2):  # Paystack re-delivers
        client.post("/billing/paystack/webhook", content=body, headers={"x-paystack-signature": sig, "content-type": "application/json"})
    return reference


def test_a_confirmed_payment_sends_exactly_one_receipt(client: TestClient) -> None:
    reference = _checkout_and_pay(client)
    receipts = [m for m in FakeSMTP.sent if "receipt" in m["Subject"].lower()]
    assert len(receipts) == 1
    assert receipts[0]["To"] == "payer@example.com"
    assert "7,500.00" in receipts[0]["Subject"]
    assert reference in _html(receipts[0])


def test_reset_for_a_known_email_sends_a_link_and_for_an_unknown_one_sends_nothing(client: TestClient) -> None:
    _register(client)
    FakeSMTP.sent.clear()
    assert client.post("/auth/password-reset", json={"email": "nobody@example.com"}).status_code == 200
    assert FakeSMTP.sent == []
    assert client.post("/auth/password-reset", json={"email": "USER@example.com"}).status_code == 200
    assert len(FakeSMTP.sent) == 1
    assert "https://mirror.test/auth/password-reset/page?token=" in FakeSMTP.sent[0].get_body(preferencelist=("plain",)).get_content()


def test_reset_changes_the_password_once_and_signs_everyone_out(client: TestClient) -> None:
    tokens = _register(client)
    client.post("/auth/password-reset", json={"email": "user@example.com"})
    token = _reset_token()
    assert client.post("/auth/password-reset/confirm", json={"token": token, "password": "short"}).status_code == 422
    assert client.post("/auth/password-reset/confirm", json={"token": token, "password": "a-brand-new-pass-1"}).status_code == 200
    assert client.post("/auth/login", json={"email": "user@example.com", "password": "correct-horse-1"}).status_code == 401
    assert client.post("/auth/login", json={"email": "user@example.com", "password": "a-brand-new-pass-1"}).status_code == 200
    # the same link cannot be used again, and an older sign-in no longer refreshes
    assert client.post("/auth/password-reset/confirm", json={"token": token, "password": "yet-another-pass-1"}).status_code == 400
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_a_garbage_or_wrong_type_token_is_refused(client: TestClient) -> None:
    tokens = _register(client)
    assert client.post("/auth/password-reset/confirm", json={"token": "nope", "password": "a-brand-new-pass-1"}).status_code == 400
    # an ordinary access token must not work as a reset token
    assert client.post("/auth/password-reset/confirm", json={"token": tokens["access_token"], "password": "a-brand-new-pass-1"}).status_code == 400


def test_the_web_page_from_the_email_works_once(client: TestClient) -> None:
    _register(client)
    client.post("/auth/password-reset", json={"email": "user@example.com"})
    token = _reset_token()
    page = client.get(f"/auth/password-reset/page?token={token}")
    assert page.status_code == 200 and "New password" in page.text
    bad = client.post("/auth/password-reset/page", content=f"token={token}&password=a-brand-new-pass-1&confirm=different",
                      headers={"content-type": "application/x-www-form-urlencoded"})
    assert bad.status_code == 400 and "do not match" in bad.text
    ok = client.post("/auth/password-reset/page", content=f"token={token}&password=a-brand-new-pass-1&confirm=a-brand-new-pass-1",
                     headers={"content-type": "application/x-www-form-urlencoded"})
    assert ok.status_code == 200 and "Your password was changed" in ok.text
    assert client.get(f"/auth/password-reset/page?token={token}").status_code == 400


def test_a_script_cannot_flood_one_address_with_reset_emails(client: TestClient) -> None:
    from app.api.routes import password_reset

    password_reset._RECENT.clear()
    _register(client)
    FakeSMTP.sent.clear()
    for _ in range(6):
        assert client.post("/auth/password-reset", json={"email": "user@example.com"}).status_code == 200
    assert len(FakeSMTP.sent) == 3


def test_the_request_page_sends_the_link(client: TestClient) -> None:
    from app.api.routes import password_reset

    password_reset._RECENT.clear()
    _register(client)
    FakeSMTP.sent.clear()
    assert client.get("/auth/password-reset/request-page").status_code == 200
    r = client.post("/auth/password-reset/request-page", content="email=user%40example.com",
                    headers={"content-type": "application/x-www-form-urlencoded"})
    assert r.status_code == 200 and "we just sent a link" in r.text
    assert len(FakeSMTP.sent) == 1
    again = client.post("/auth/password-reset/request-page", content="email=nobody%40example.com",
                        headers={"content-type": "application/x-www-form-urlencoded"})
    assert "we just sent a link" in again.text and len(FakeSMTP.sent) == 1
