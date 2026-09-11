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
from app.models.user import User


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

    return user
