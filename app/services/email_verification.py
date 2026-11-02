"""Six-digit email codes. Free allowances cost real money (Showroom is a Gemini call), so they need
a confirmed address; otherwise a new throwaway account would mean a fresh set of free uses.

Only a hash of the code is stored. A code lasts CODE_MINUTES and allows MAX_ATTEMPTS guesses, after
which a new one has to be sent.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.billing import aware_utc

CODE_MINUTES = 30
MAX_ATTEMPTS = 5


def _hash(user: User, code: str) -> str:
    return hashlib.sha256(f"{user.id}:{code}".encode()).hexdigest()


async def issue_code(session: AsyncSession, user: User) -> str:
    """A fresh code for `user`, replacing any earlier one. Commits."""
    code = f"{secrets.randbelow(10**6):06d}"
    user.email_code_hash = _hash(user, code)
    user.email_code_expires_at = datetime.now(UTC) + timedelta(minutes=CODE_MINUTES)
    user.email_code_attempts = 0
    session.add(user)
    await session.commit()
    return code


async def check_code(session: AsyncSession, user: User, code: str) -> bool:
    """True once the address is confirmed. Commits."""
    if user.email_verified_at is not None:
        return True
    expires_at = aware_utc(user.email_code_expires_at)
    if user.email_code_hash is None or expires_at is None or expires_at <= datetime.now(UTC):
        return False
    if user.email_code_attempts >= MAX_ATTEMPTS:
        return False
    user.email_code_attempts += 1
    matched = secrets.compare_digest(user.email_code_hash, _hash(user, code))
    if matched:
        user.email_verified_at = datetime.now(UTC)
        user.email_code_hash = None
        user.email_code_expires_at = None
    session.add(user)
    await session.commit()
    return matched
