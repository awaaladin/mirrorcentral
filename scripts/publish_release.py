"""One-off CLI to publish a new AppRelease row, exactly as POST /admin/releases/new does
(including the push notification to existing devices) - for when there's no admin session
cookie handy to use the real form. Usage:

    python scripts/publish_release.py android 6 0.3.0 https://host/mirror-0.3.0.apk \
        --notes "Release notes" [--mandatory]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import async_session_factory
from app.models.app_release import AppRelease
from app.models.enums import AppPlatform
from app.services.push import notify_new_release


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("platform", choices=[p.value for p in AppPlatform])
    parser.add_argument("version_code", type=int)
    parser.add_argument("version_name")
    parser.add_argument("download_url")
    parser.add_argument("--notes", default="")
    parser.add_argument("--mandatory", action="store_true")
    args = parser.parse_args()

    async with async_session_factory() as session:
        release = AppRelease(
            platform=AppPlatform(args.platform),
            version_code=args.version_code,
            version_name=args.version_name,
            download_url=args.download_url,
            release_notes=args.notes,
            is_mandatory=args.mandatory,
        )
        session.add(release)
        await session.commit()
        await session.refresh(release)
        notified = await notify_new_release(session, release)
        print(f"Published {release.platform.value} {release.version_name} (code {release.version_code}); notified {notified} device(s).")


if __name__ == "__main__":
    asyncio.run(main())
