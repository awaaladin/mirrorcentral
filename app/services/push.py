from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.app_release import AppRelease
from app.models.device_token import DeviceToken

logger = logging.getLogger(__name__)

_firebase_app: Any = None
_firebase_app_initialized = False


def _get_firebase_app() -> Any | None:
    """Lazily initializes the Firebase Admin SDK from the service account file configured via
    FIREBASE_SERVICE_ACCOUNT_PATH/_JSON. Returns None (rather than raising) when unconfigured OR
    when the firebase-admin package itself fails to import/initialize - a serverless deployment's
    dependency bundle is a different environment than local dev, and push notifications being
    unavailable should never take the rest of the API down with it. The import is deliberately
    inside this function (not at module level): this module gets imported at app startup via the
    admin releases router, so a module-level import failure here would crash every request, not
    just release-publishing ones.
    """
    global _firebase_app, _firebase_app_initialized
    if _firebase_app_initialized:
        return _firebase_app
    _firebase_app_initialized = True

    try:
        import firebase_admin
        from firebase_admin import credentials
    except Exception:
        logger.exception("firebase-admin unavailable - push notifications disabled")
        return None

    settings = get_settings()
    try:
        if settings.firebase_service_account_json:
            cred = credentials.Certificate(json.loads(settings.firebase_service_account_json))
        elif settings.firebase_service_account_path:
            cred = credentials.Certificate(settings.firebase_service_account_path)
        else:
            return None
        _firebase_app = firebase_admin.initialize_app(cred)
    except Exception:
        logger.exception("Failed to initialize Firebase Admin SDK - push notifications disabled")
        return None

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

    try:
        from firebase_admin import messaging

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
    except Exception:
        logger.exception("Failed to send push notification for release %s", release.version_name)
        return 0

    logger.info("Push notification sent: %d succeeded, %d failed", response.success_count, response.failure_count)
    return response.success_count
