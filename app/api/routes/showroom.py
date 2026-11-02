from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import get_settings
from app.db.session import get_session
from app.models.user import User
from app.services.entitlements import (
    SHOWROOM,
    access_for,
    claim,
    free_showroom_today,
    release,
    used_this_month,
)
from app.services.showroom import FaceAnalysis, ShowroomUnavailable, analyze_face

# Every call costs a Gemini request, so each one counts against the account's monthly allowance (3 on
# free, which also needs a confirmed email), and free use has a daily ceiling across everyone. Analysis
# only - this route never returns or stores an image, and nothing here touches the app's saved looks.
# X-Mirror-Reason on a refusal tells the app which message to show.
router = APIRouter(prefix="/showroom", tags=["showroom"])

MAX_IMAGE_BYTES = 6 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _refused(code: int, message: str, reason: str) -> HTTPException:
    return HTTPException(code, message, headers={"X-Mirror-Reason": reason})


@router.post("/analyze", response_model=FaceAnalysis)
async def analyze(
    response: Response,
    image: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FaceAnalysis:
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a JPEG, PNG or WebP photo.")
    data = await image.read(MAX_IMAGE_BYTES + 1)
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty image.")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Photo is too large (max 6 MB).")

    access = await access_for(session, user)
    if not access.is_paid:
        if not user.email_verified:
            raise _refused(status.HTTP_403_FORBIDDEN, "Confirm your email to use Showroom.", "verify_email")
        if await free_showroom_today(session) >= get_settings().free_showroom_daily_total:
            raise _refused(status.HTTP_503_SERVICE_UNAVAILABLE, "Showroom is very busy today. Please try again tomorrow.", "busy")

    key = uuid.uuid4().hex
    if not await claim(session, user.id, SHOWROOM, key, access.showroom_limit, access.is_paid):
        raise _refused(status.HTTP_429_TOO_MANY_REQUESTS, "You've used this month's Showroom analyses.", "limit")
    try:
        analysis = await analyze_face(data, image.content_type)
    except ShowroomUnavailable as exc:
        await release(session, user.id, SHOWROOM, key)
        code = status.HTTP_503_SERVICE_UNAVAILABLE if not exc.configured else status.HTTP_502_BAD_GATEWAY
        raise HTTPException(code, str(exc)) from exc
    response.headers["X-Mirror-Used"] = str(await used_this_month(session, user.id, SHOWROOM))
    response.headers["X-Mirror-Limit"] = str(access.showroom_limit)
    return analysis
