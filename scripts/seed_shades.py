"""One-off CLI to seed the public shade catalog with Mirror's starter shade library.

Idempotent - safe to run more than once, since it skips any (name, category) pair that
already exists rather than inserting duplicates. Usage:

    python scripts/seed_shades.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.enums import ShadeCategory, ShadeFinish
from app.models.shade_item import ShadeItem

STARTER_SHADES: list[tuple[str, str, ShadeCategory, ShadeFinish]] = [
    ("Agbani 04 · Terracotta Earth", "#994422", ShadeCategory.LIPSTICK, ShadeFinish.MATTE),
    ("Zaria 02 · Deep Cocoa Plum", "#FFDBCF", ShadeCategory.LIPSTICK, ShadeFinish.SATIN),
    ("Enugu 07 · Spiced Ochre", "#7B5804", ShadeCategory.LIPSTICK, ShadeFinish.MATTE),
    ("Ibadan 01 · Warm Raw Umber", "#55433C", ShadeCategory.LIPSTICK, ShadeFinish.MATTE),
    ("Calabar 09 · Burnished Coral", "#B85C38", ShadeCategory.LIPSTICK, ShadeFinish.GLOSSY),
    ("Oyin 08 · Warm Sand", "#D9A876", ShadeCategory.FOUNDATION, ShadeFinish.SATIN),
    ("Oyin 12 · Rich Golden", "#B87F4E", ShadeCategory.FOUNDATION, ShadeFinish.SATIN),
    ("Oyin 14 · Deep Olive Gold", "#8C5E36", ShadeCategory.FOUNDATION, ShadeFinish.MATTE),
    ("Lekki 18 · Espresso Neutral", "#5A3826", ShadeCategory.FOUNDATION, ShadeFinish.MATTE),
    ("Lekki 20 · Deep Ebony", "#3B2219", ShadeCategory.FOUNDATION, ShadeFinish.SATIN),
    ("Sahara Dusk", "#A47C2B", ShadeCategory.EYESHADOW, ShadeFinish.SHIMMER),
    ("Nile Bronze", "#8C4F2E", ShadeCategory.EYESHADOW, ShadeFinish.SHIMMER),
    ("Charcoal Smoke", "#34302B", ShadeCategory.EYESHADOW, ShadeFinish.MATTE),
    ("Copper Glow", "#B85C38", ShadeCategory.EYESHADOW, ShadeFinish.SHIMMER),
    ("Coral Clay", "#B85C38", ShadeCategory.BLUSH, ShadeFinish.SATIN),
    ("Terra Rose", "#994422", ShadeCategory.BLUSH, ShadeFinish.MATTE),
    ("Golden Lustre 18K", "#EFBF67", ShadeCategory.BLUSH, ShadeFinish.SHIMMER),
    ("Jet Black", "#1C1611", ShadeCategory.EYEBROW, ShadeFinish.MATTE),
    ("Espresso Brown", "#3B2418", ShadeCategory.EYEBROW, ShadeFinish.MATTE),
    ("Warm Chocolate", "#4E2F1D", ShadeCategory.EYEBROW, ShadeFinish.MATTE),
    ("Soft Auburn", "#6B3A22", ShadeCategory.EYEBROW, ShadeFinish.SATIN),
    ("Ash Taupe", "#5C4A3E", ShadeCategory.EYEBROW, ShadeFinish.MATTE),
    ("Royal Gold Aso-Oke", "#C9971F", ShadeCategory.GELE, ShadeFinish.SHIMMER),
    ("Coral Red Damask", "#B8322A", ShadeCategory.GELE, ShadeFinish.SATIN),
    ("Royal Blue Adire", "#1F3E7A", ShadeCategory.GELE, ShadeFinish.SATIN),
    ("Emerald Ankara", "#1E5C45", ShadeCategory.GELE, ShadeFinish.SATIN),
    ("Deep Plum Velvet", "#5A2A4A", ShadeCategory.GELE, ShadeFinish.MATTE),
    ("Ivory Celebrant Lace", "#EDE3D3", ShadeCategory.GELE, ShadeFinish.SATIN),
]


async def seed_shades() -> None:
    async with async_session_factory() as session:
        existing = (
            await session.execute(select(ShadeItem.name, ShadeItem.category))
        ).all()
        existing_keys = {(name, category) for name, category in existing}

        created = 0
        for name, hex_color, category, finish in STARTER_SHADES:
            if (name, category) in existing_keys:
                continue
            session.add(ShadeItem(name=name, hex_color=hex_color, category=category, finish=finish))
            created += 1

        if created:
            await session.commit()
        print(f"Seeded {created} shade(s); {len(STARTER_SHADES) - created} already existed.")


if __name__ == "__main__":
    asyncio.run(seed_shades())
