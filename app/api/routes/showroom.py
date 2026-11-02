from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_showroom
from app.config import get_settings
from app.db.session import get_session
from app.models.enums import SubscriptionPlan
from app.models.user import User
from app.services.entitlements import refund_showroom_credit, take_showroom_credit
from app.services.showroom import FaceAnalysis, ShowroomUnavailable, analyze_face

# Pro-gated with a monthly cap: every call costs a Gemini request. Analysis only - this route never returns or
# stores an image, and nothing here touches the app's saved looks.
router = APIRouter(prefix="/showroom", tags=["showroom"])

MAX_IMAGE_BYTES = 6 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/analyze", response_model=FaceAnalysis)
async def analyze(
    image: UploadFile = File(...),
    access: tuple[User, SubscriptionPlan] = Depends(require_showroom),
    session: AsyncSession = Depends(get_session),
) -> FaceAnalysis:
    user, plan = access
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a JPEG, PNG or WebP photo.")
    data = await image.read(MAX_IMAGE_BYTES + 1)
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty image.")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Photo is too large (max 6 MB).")
    if not await take_showroom_credit(session, user.id, get_settings().plan_monthly_cap(plan.value)):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "You've used this month's Showroom analyses.")
    try:
        return await analyze_face(data, image.content_type)
    except ShowroomUnavailable as exc:
        await refund_showroom_credit(session, user.id)
        code = status.HTTP_503_SERVICE_UNAVAILABLE if not exc.configured else status.HTTP_502_BAD_GATEWAY
        raise HTTPException(code, str(exc)) from exc
