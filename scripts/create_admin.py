"""One-off CLI to bootstrap the first admin console account.

There's no self-service admin signup by design (admin_users are Mirror staff, not
customers) — this script is how the very first "owner" account gets created on a
fresh database. Usage:

    python scripts/create_admin.py owner@mirror.app --role owner
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.admin_user import AdminUser
from app.models.enums import AdminRole


async def create_admin(email: str, password: str, role: AdminRole) -> None:
    email_normalized = email.strip().lower()
    async with async_session_factory() as session:
        existing = (
            await session.execute(select(AdminUser).where(AdminUser.email == email_normalized))
        ).scalar_one_or_none()
        if existing:
            print(f"An admin with email {email_normalized} already exists.")
            return

        admin = AdminUser(email=email_normalized, password_hash=hash_password(password), role=role)
        session.add(admin)
        await session.commit()
        print(f"Created {role.value} admin account: {email_normalized}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    parser.add_argument("--role", choices=[r.value for r in AdminRole], default=AdminRole.OWNER.value)
    args = parser.parse_args()

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords did not match.", file=sys.stderr)
        raise SystemExit(1)
    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        raise SystemExit(1)

    asyncio.run(create_admin(args.email, password, AdminRole(args.role)))


if __name__ == "__main__":
    main()
