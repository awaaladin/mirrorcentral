from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.services import mailer
from app.services.email_verification import check_code, issue_code

router = APIRouter(prefix="/auth/email", tags=["auth"])


class VerifyRequest(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class VerifiedPublic(BaseModel):
    email_verified: bool


# Same in-process throttle as the password-reset emails: enough to stop a script hammering one inbox.
_RECENT: dict[str, list[float]] = {}
_MAX_PER_USER_PER_HOUR = 3


def _allowed_to_send(user: User) -> bool:
    now = time.monotonic()
    key = str(user.id)
    recent = [t for t in _RECENT.get(key, []) if now - t < 3600]
    if len(recent) >= _MAX_PER_USER_PER_HOUR:
        _RECENT[key] = recent
        return False
    _RECENT[key] = [*recent, now]
    if len(_RECENT) > 5000:  # never grow without bound
        _RECENT.clear()
    return True


@router.post("/send", response_model=VerifiedPublic)
async def send_code(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> VerifiedPublic:
    if user.email_verified_at is not None:
        return VerifiedPublic(email_verified=True)
    if not _allowed_to_send(user):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "We've sent a few codes already. Check your inbox and spam, or try again in an hour.")
    mailer.send_verification_code(user.email, await issue_code(session, user))
    return VerifiedPublic(email_verified=False)


@router.post("/verify", response_model=VerifiedPublic)
async def verify(
    request: VerifyRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VerifiedPublic:
    if not await check_code(session, user, request.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That code is wrong or has expired. Ask for a new one.")
    return VerifiedPublic(email_verified=True)
