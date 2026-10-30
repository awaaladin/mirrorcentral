"""Forgotten-password flow: an emailed link that opens a small web page (the app cannot open links itself).

* Always answers 200 to "send me a link", so nobody can use it to learn which emails have accounts.
* The link carries a signed token that expires in one hour and stops working the moment the password
  changes (it embeds a fingerprint of the current password hash), so it can be used only once.
* Changing the password also signs the account out everywhere (single-active-session rule).
"""
from __future__ import annotations

import hashlib
import secrets
import time
import uuid
from datetime import UTC, datetime, timedelta
from html import escape
from urllib.parse import parse_qs, quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import hash_password
from app.db.session import get_session
from app.models.user import User
from app.services import mailer

router = APIRouter(prefix="/auth/password-reset", tags=["auth"])

RESET_TOKEN_TYPE = "password_reset"
RESET_TOKEN_MINUTES = 60
_BAD_LINK = "This reset link is wrong, already used, or too old. Ask for a new one from the app."


class ResetRequest(BaseModel):
    email: EmailStr


class ResetConfirm(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


# An open "send an email" endpoint must not be usable to flood someone's inbox (or use up the shared sender's daily
# limit). In-process, so each server instance keeps its own count; enough to stop a script hammering one address.
_RECENT: dict[str, list[float]] = {}
_MAX_PER_ADDRESS_PER_HOUR = 3


def _allowed_to_send(email: str) -> bool:
    now = time.monotonic()
    recent = [t for t in _RECENT.get(email, []) if now - t < 3600]
    if len(recent) >= _MAX_PER_ADDRESS_PER_HOUR:
        _RECENT[email] = recent
        return False
    _RECENT[email] = [*recent, now]
    if len(_RECENT) > 5000:  # never grow without bound
        _RECENT.clear()
    return True


def _fingerprint(user: User) -> str:
    return hashlib.sha256((user.password_hash or "").encode()).hexdigest()[:16]


def make_reset_token(user: User) -> str:
    settings = get_settings()
    claims = {
        "sub": str(user.id),
        "type": RESET_TOKEN_TYPE,
        "pf": _fingerprint(user),
        "exp": datetime.now(UTC) + timedelta(minutes=RESET_TOKEN_MINUTES),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def user_for_token(session: AsyncSession, token: str) -> User | None:
    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = uuid.UUID(claims.get("sub", ""))
    except (JWTError, ValueError):
        return None
    if claims.get("type") != RESET_TOKEN_TYPE:
        return None
    user = await session.get(User, user_id)
    if user is None or not secrets.compare_digest(claims.get("pf", ""), _fingerprint(user)):
        return None
    return user


async def _set_password(session: AsyncSession, user: User, password: str) -> None:
    user.password_hash = hash_password(password)
    user.current_session_id = secrets.token_hex(16)  # every signed-in device is signed out
    session.add(user)
    await session.commit()


@router.post("")
async def request_reset(body: ResetRequest, session: AsyncSession = Depends(get_session)) -> dict:
    email = body.email.strip().lower()
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is not None and _allowed_to_send(email):
        link = f"{mailer.public_base_url()}/auth/password-reset/page?token={quote(make_reset_token(user))}"
        mailer.send_password_reset(user.email, link)
    return {"detail": "If that email has an account, we sent a link to reset the password."}


@router.post("/confirm")
async def confirm_reset(body: ResetConfirm, session: AsyncSession = Depends(get_session)) -> dict:
    user = await user_for_token(session, body.token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_BAD_LINK)
    await _set_password(session, user, body.password)
    return {"detail": "Password changed. You can sign in now."}


def _page(inner: str, status_code: int = 200) -> HTMLResponse:
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Choose a new password | Mirror</title>
<style>body{{font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f5f7fa;color:#0b192c}}
main{{max-width:420px;margin:0 auto;padding:32px 16px}}.card{{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:24px}}
label{{display:block;margin:14px 0 4px;font-size:14px}}input{{width:100%;box-sizing:border-box;padding:12px;border:1px solid #cbd5e1;border-radius:10px;font-size:16px}}
button{{margin-top:18px;width:100%;padding:13px;border:0;border-radius:10px;background:#0b192c;color:#fff;font-size:16px}}.err{{color:#b91c1c;font-size:14px}}.ok{{color:#166534}}</style>
</head><body><main><h1>Mirror</h1><div class="card">{inner}</div></main></body></html>"""
    return HTMLResponse(html, status_code=status_code, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


def _form(token: str, error: str = "") -> str:
    err = f'<p class="err">{escape(error)}</p>' if error else ""
    return (
        f'<form method="post" action="/auth/password-reset/page"><input type="hidden" name="token" value="{escape(token, quote=True)}">'
        '<label for="password">New password</label><input id="password" name="password" type="password" autocomplete="new-password" required minlength="8">'
        '<label for="confirm">Repeat the new password</label><input id="confirm" name="confirm" type="password" autocomplete="new-password" required minlength="8">'
        f'{err}<button type="submit">Save new password</button></form>'
    )


@router.get("/page", response_class=HTMLResponse)
async def reset_page(token: str = "", session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    if await user_for_token(session, token) is None:
        return _page(f"<p>{escape(_BAD_LINK)}</p>", status.HTTP_400_BAD_REQUEST)
    return _page(_form(token))


@router.post("/page", response_class=HTMLResponse)
async def reset_page_submit(request: Request, session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    fields = {k: v[0] for k, v in parse_qs((await request.body()).decode("utf-8", "ignore")).items()}
    token, password, confirm = fields.get("token", ""), fields.get("password", ""), fields.get("confirm", "")
    user = await user_for_token(session, token)
    if user is None:
        return _page(f"<p>{escape(_BAD_LINK)}</p>", status.HTTP_400_BAD_REQUEST)
    if password != confirm:
        return _page(_form(token, "The two passwords do not match."), status.HTTP_400_BAD_REQUEST)
    if not 8 <= len(password) <= 128:
        return _page(_form(token, "Use a password of 8 to 128 characters."), status.HTTP_400_BAD_REQUEST)
    await _set_password(session, user, password)
    return _page('<p class="ok">Your password was changed. Open the Mirror app and sign in with the new one.</p>')


def _request_form(message: str = "") -> str:
    if message:
        return f'<p class="ok">{escape(message)}</p>'
    return (
        '<p>Enter the email you signed up with and we will send you a link.</p>'
        '<form method="post" action="/auth/password-reset/request-page"><label for="email">Email</label>'
        '<input id="email" name="email" type="email" autocomplete="email" required><button type="submit">Send reset link</button></form>'
    )


@router.get("/request-page", response_class=HTMLResponse)
async def request_page() -> HTMLResponse:
    """What the app's "Forgot password?" link opens."""
    return _page(_request_form())


@router.post("/request-page", response_class=HTMLResponse)
async def request_page_submit(request: Request, session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    fields = {k: v[0] for k, v in parse_qs((await request.body()).decode("utf-8", "ignore")).items()}
    email = fields.get("email", "").strip().lower()
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none() if email else None
    if user is not None and _allowed_to_send(email):
        link = f"{mailer.public_base_url()}/auth/password-reset/page?token={quote(make_reset_token(user))}"
        mailer.send_password_reset(user.email, link)
    return _page(_request_form("If that email has an account, we just sent a link to choose a new password. It may land in spam."))
