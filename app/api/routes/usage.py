from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.services.entitlements import PHOTO, SHOWROOM, access_for, claim, used_this_month

# The app asks here before starting a new photo in the studio. Makeup is painted on the phone, so
# this is where the free photo allowance is counted (see app/services/entitlements.py).
router = APIRouter(prefix="/usage", tags=["usage"])


class Allowance(BaseModel):
    used: int
    # None = unlimited.
    limit: int | None


class UsagePublic(BaseModel):
    photos: Allowance
    showroom: Allowance
    email_verified: bool
    paid: bool


class PhotoClaim(BaseModel):
    # The app's id for the photo (a hash of it), so reopening the same photo isn't counted again.
    photo_id: str = Field(min_length=16, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


class PhotoClaimResult(BaseModel):
    allowed: bool
    reason: Literal["verify_email", "limit"] | None = None
    photos: Allowance


@router.get("", response_model=UsagePublic)
async def my_usage(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> UsagePublic:
    access = await access_for(session, user)
    return UsagePublic(
        photos=Allowance(used=await used_this_month(session, user.id, PHOTO), limit=access.photo_limit),
        showroom=Allowance(used=await used_this_month(session, user.id, SHOWROOM), limit=access.showroom_limit),
        email_verified=user.email_verified,
        paid=access.is_paid,
    )


@router.post("/photo", response_model=PhotoClaimResult)
async def claim_photo(
    request: PhotoClaim,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PhotoClaimResult:
    access = await access_for(session, user)
    if access.is_paid:
        return PhotoClaimResult(allowed=True, photos=Allowance(used=await used_this_month(session, user.id, PHOTO), limit=None))
    if not user.email_verified:
        allowance = Allowance(used=await used_this_month(session, user.id, PHOTO), limit=access.photo_limit)
        return PhotoClaimResult(allowed=False, reason="verify_email", photos=allowance)
    allowed = await claim(session, user.id, PHOTO, request.photo_id, access.photo_limit, paid=False)
    allowance = Allowance(used=await used_this_month(session, user.id, PHOTO), limit=access.photo_limit)
    return PhotoClaimResult(allowed=allowed, reason=None if allowed else "limit", photos=allowance)
