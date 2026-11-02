"""Shared FastAPI dependencies for the mobile-facing API (distinct from app/admin/deps.py,
which handles the admin console's separate session-cookie auth)."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import ACCESS_TOKEN_TYPE, decode_token
from app.db.session import get_session
from app.models.enums import SubscriptionPlan
from app.models.user import User
from app.services.entitlements import active_plan, can_use_client_mode, can_use_showroom


class _ForbiddenOnMissingBearer(HTTPBearer):
    """FastAPI's HTTPBearer raises 401 for a missing/malformed Authorization header in the
    installed version here; call sites in this API expect 403 for "no credentials supplied
    at all" (reserving 401 for "credentials supplied but invalid/expired" - see
    get_current_user below), so that specific case is normalized to 403 here."""

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        try:
            return await super().__call__(request)
        except HTTPException as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.detail) from exc


_bearer_scheme = _ForbiddenOnMissingBearer(auto_error=True)

_INVALID_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired session. Please sign in again.",
    headers={"WWW-Authenticate": "Bearer"},
)

_SIGNED_IN_ELSEWHERE = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="This account was signed in on another device. Please sign in again.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    claims = decode_token(credentials.credentials)
    if claims is None or claims.get("type") != ACCESS_TOKEN_TYPE:
        raise _INVALID_TOKEN

    try:
        user_id = uuid.UUID(claims.get("sub", ""))
    except ValueError:
        raise _INVALID_TOKEN

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise _INVALID_TOKEN

    # One active sign-in per account (see User.current_session_id). A newer login elsewhere
    # already overwrote it, so this token - however fresh - is from a session that's been
    # signed out. No extra query: `user` is already loaded above.
    if claims.get("sid") != user.current_session_id:
        raise _SIGNED_IN_ELSEWHERE

    return user


async def require_showroom(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> tuple[User, SubscriptionPlan]:
    plan = await active_plan(session, user.id)
    if plan is None or not can_use_showroom(plan):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Showroom is part of Mirror Pro.")
    return user, plan


async def require_client_mode(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    plan = await active_plan(session, user.id)
    if plan is None or not can_use_client_mode(plan):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Client Mode is part of Mirror Pro.")
    return user
