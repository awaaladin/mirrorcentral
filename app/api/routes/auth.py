from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.security import hash_password, verify_password
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_INVALID_REFRESH_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired refresh token.",
)

_SIGNED_IN_ELSEWHERE_REFRESH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="This account was signed in on another device. Please sign in again.",
)


def _issue_tokens(user: User, session_id: str) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.email, session_id),
        refresh_token=create_refresh_token(user.id, session_id),
        user=user,
    )


async def _start_new_session(session: AsyncSession, user: User) -> TokenResponse:
    """Register/login: a fresh sign-in, so it replaces whatever session (if any) was active
    before - signing that device out, per the single-active-session rule."""
    user.current_session_id = secrets.token_hex(16)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return _issue_tokens(user, user.current_session_id)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    email = request.email.strip().lower()

    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=email,
        password_hash=hash_password(request.password),
        account_type=request.account_type,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return await _start_new_session(session, user)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    email = request.email.strip().lower()

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    return await _start_new_session(session, user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    claims = decode_token(request.refresh_token)
    if claims is None or claims.get("type") != REFRESH_TOKEN_TYPE:
        raise _INVALID_REFRESH_TOKEN

    try:
        user_id = uuid.UUID(claims.get("sub", ""))
    except ValueError:
        raise _INVALID_REFRESH_TOKEN

    user = await session.get(User, user_id)
    if user is None:
        raise _INVALID_REFRESH_TOKEN

    # Same single-active-session rule as get_current_user: a login elsewhere since this
    # refresh token was issued means this device's session has already been signed out.
    if claims.get("sid") != user.current_session_id:
        raise _SIGNED_IN_ELSEWHERE_REFRESH

    return _issue_tokens(user, user.current_session_id)
