"""Session-based auth, CSRF protection, and audit logging for the admin console.

Deliberately separate from the mobile app's JWT auth (see app/core/security.py for
the password hashing they share): the admin console is a server-rendered surface for
Mirror staff, authenticated via a signed session cookie, not a bearer token.
"""

from __future__ import annotations

import secrets
import uuid
from typing import Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.admin_audit_log import AdminAuditLog
from app.models.admin_user import AdminUser
from app.models.enums import AdminRole

SESSION_KEY = "admin_user_id"
CSRF_SESSION_KEY = "csrf_token"
FLASH_SESSION_KEY = "flashes"


def flash(request: Request, text: str, kind: str = "info") -> None:
    """Queue a one-time banner message, shown on the next page render then discarded."""
    request.session.setdefault(FLASH_SESSION_KEY, [])
    request.session[FLASH_SESSION_KEY].append([kind, text])


def pop_flashes(request: Request) -> list[tuple[str, str]]:
    return request.session.pop(FLASH_SESSION_KEY, [])


class AdminAuthRequired(Exception):
    """Raised by `current_admin` when no valid session is present.

    Caught by an exception handler (registered in app.main) that redirects to the
    login page — this keeps every admin route free of repetitive auth-check
    boilerplate while still producing a normal browser redirect, not a JSON 401.
    """

    def __init__(self, next_path: str = "/admin/") -> None:
        self.next_path = next_path


class AdminForbidden(Exception):
    """Raised when a logged-in admin's role doesn't permit the action."""


async def current_admin(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AdminUser:
    raw_id = request.session.get(SESSION_KEY)
    if not raw_id:
        raise AdminAuthRequired(next_path=request.url.path)

    admin = await session.get(AdminUser, uuid.UUID(raw_id))
    if admin is None or not admin.is_active:
        request.session.clear()
        raise AdminAuthRequired(next_path=request.url.path)
    return admin


def require_role(*allowed: AdminRole) -> Any:
    """Dependency factory: 403s (via AdminForbidden) if the admin's role isn't in `allowed`."""

    async def _dependency(admin: AdminUser = Depends(current_admin)) -> AdminUser:
        if admin.role not in allowed:
            raise AdminForbidden()
        return admin

    return _dependency


def get_or_create_csrf_token(request: Request) -> str:
    token = request.session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[CSRF_SESSION_KEY] = token
    return token


def validate_csrf(request: Request, submitted_token: str) -> bool:
    expected = request.session.get(CSRF_SESSION_KEY)
    return bool(expected) and secrets.compare_digest(expected, submitted_token)


async def record_audit(
    db_session: AsyncSession,
    *,
    admin: AdminUser,
    action: str,
    target_type: str,
    target_id: str,
    detail: dict[str, Any] | None = None,
) -> None:
    db_session.add(
        AdminAuditLog(
            admin_user_id=admin.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail or {},
        )
    )
