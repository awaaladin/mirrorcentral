"""Paystack REST calls (plain httpx), plus webhook signature checking.

The Paystack account is shared with other apps. A webhook router in front of it forwards only
MIRROR- references here, byte for byte, so the HMAC signature still verifies.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

import httpx

from app.config import get_settings


class PaystackError(Exception):
    pass


class PaystackNotConfigured(PaystackError):
    pass


async def _request(method: str, path: str, *, client: httpx.AsyncClient | None = None, **kwargs: Any) -> dict:
    settings = get_settings()
    if not settings.paystack_secret_key:
        raise PaystackNotConfigured("PAYSTACK_SECRET_KEY is not set.")
    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=10.0))
    try:
        response = await client.request(
            method,
            f"{settings.paystack_base_url.rstrip('/')}{path}",
            headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
            **kwargs,
        )
        body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise PaystackError(f"Paystack unreachable: {exc}") from exc
    finally:
        if owns_client:
            await client.aclose()
    if response.is_error or not body.get("status"):
        raise PaystackError(body.get("message") or f"Paystack error {response.status_code}")
    return body["data"]


async def initialize_transaction(
    *, email: str, amount_kobo: int, reference: str, callback_url: str, metadata: dict,
    client: httpx.AsyncClient | None = None,
) -> dict:
    return await _request(
        "POST",
        "/transaction/initialize",
        client=client,
        json={
            "email": email,
            "amount": amount_kobo,
            "currency": "NGN",
            "reference": reference,
            "callback_url": callback_url,
            "metadata": metadata,
        },
    )


async def verify_transaction(reference: str, *, client: httpx.AsyncClient | None = None) -> dict:
    return await _request("GET", f"/transaction/verify/{reference}", client=client)


def verify_webhook_signature(raw_body: bytes, signature: str | None) -> bool:
    secret = get_settings().paystack_secret_key
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)
