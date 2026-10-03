from __future__ import annotations

import json
import logging

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.app_release import AppRelease
from app.models.device_token import DeviceToken

logger = logging.getLogger(__name__)

_firebase_app: firebase_admin.App | None = None


def _get_firebase_app() -> firebase_admin.App | None:
    """Lazily initializes the Firebase Admin SDK from the service account file configured via
    FIREBASE_SERVICE_ACCOUNT_PATH. Returns None (rather than raising) when unconfigured, so local
    dev and any environment without push notifications set up doesn't need a dummy credential."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    settings = get_settings()
    if settings.firebase_service_account_json:
        cred = credentials.Certificate(json.loads(settings.firebase_service_account_json))
    elif settings.firebase_service_account_path:
        cred = credentials.Certificate(settings.firebase_service_account_path)
    else:
        return None

    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


async def notify_new_release(session: AsyncSession, release: AppRelease) -> int:
    """Pushes an "update available" notification to every registered device for [release]'s
    platform. Best-effort: a device with a stale/revoked token just fails silently (FCM's
    multicast response reports per-token success, not an all-or-nothing result), and the whole
    thing is a no-op if Firebase isn't configured - publishing a release should never fail because
    push notifications aren't set up. Returns how many devices were successfully notified.
    """
    app = _get_firebase_app()
    if app is None:
        logger.info("Firebase not configured - skipping push for release %s", release.version_name)
        return 0

    result = await session.execute(select(DeviceToken).where(DeviceToken.platform == release.platform))
    tokens = [row.token for row in result.scalars().all()]
    if not tokens:
        return 0

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title="Mirror update available",
            body=f"Version {release.version_name} is ready - tap to download.",
        ),
        data={
            "type": "app_update",
            "version_code": str(release.version_code),
            "version_name": release.version_name,
            "download_url": release.download_url,
        },
        tokens=tokens,
    )
    response = messaging.send_each_for_multicast(message, app=app)
    logger.info("Push notification sent: %d succeeded, %d failed", response.success_count, response.failure_count)
    return response.success_count
