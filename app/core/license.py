"""Signed Pro licenses for the Android app.

A license is `<base64url JSON>.<base64url DER ECDSA signature>`, signed with an EC P-256 key the
server alone holds. The app embeds the public key (see LicenseVerifier.kt), so it can check a
license with no network - and, unlike a JWT signed with the shared jwt_secret, a copy of the app
can't mint one.
"""

from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from app.config import get_settings


class LicenseNotConfigured(Exception):
    pass


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def sign_license(user_id: uuid.UUID, plan: str, device_id: str, expires_at: datetime) -> str:
    private_key = get_settings().license_private_key
    if not private_key:
        raise LicenseNotConfigured
    key = serialization.load_der_private_key(base64.b64decode(private_key), password=None)
    assert isinstance(key, ec.EllipticCurvePrivateKey)
    claims = {"sub": str(user_id), "plan": plan, "did": device_id, "exp": int(expires_at.timestamp())}
    payload = _b64url(json.dumps(claims, separators=(",", ":")).encode())
    return f"{payload}.{_b64url(key.sign(payload.encode(), ec.ECDSA(hashes.SHA256())))}"
