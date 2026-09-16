"""One-off CLI to seed the public shade catalog with Mirror's starter shade library.

This is the authoritative source for the *starter* catalog (admins can add more via
/admin/shades) - re-running it deletes and reinserts every row below, so it always converges
to exactly this list rather than accumulating stale duplicates from earlier versions. Usage:

    python scripts/seed_shades.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete

from app.db.session import async_session_factory
from app.models.enums import ShadeCategory, ShadeFinish
from app.models.shade_item import ShadeItem

# Shade families and naming are grounded in real makeup shade vocabulary for deep/Nigerian skin
# tones (brick red, oxblood, terracotta, warm cocoa, etc.), with the foundation range extended
# up to fair tones so it also works for non-Nigerian users - mirrors
# app/ui/editor/EditorShadeData.kt on the Android side; keep the two in sync.
STARTER_SHADES: list[tuple[str, str, ShadeCategory, ShadeFinish]] = [
    # Lips
    ("Warm Mahogany", "#7B3B2E", ShadeCategory.LIPSTICK, ShadeFinish.MATTE),
    ("Toffee Nude", "#A4623B", ShadeCategory.LIPSTICK, ShadeFinish.SATIN),
    ("Rosewood", "#65323A", ShadeCategory.LIPSTICK, ShadeFinish.MATTE),
    ("Clay Taupe", "#8B5E52", ShadeCategory.LIPSTICK, ShadeFinish.SATIN),
    ("Brick Red", "#B33921", ShadeCategory.LIPSTICK, ShadeFinish.MATTE),
    ("Oxblood", "#4A1420", ShadeCategory.LIPSTICK, ShadeFinish.MATTE),
    ("Cherry Red", "#9E1B32", ShadeCategory.LIPSTICK, ShadeFinish.GLOSSY),
    ("Wine", "#722F37", ShadeCategory.LIPSTICK, ShadeFinish.MATTE),
    ("Deep Plum Berry", "#6E2142", ShadeCategory.LIPSTICK, ShadeFinish.SATIN),
    ("Burgundy", "#5C0923", ShadeCategory.LIPSTICK, ShadeFinish.MATTE),
    ("Coral Gloss", "#E2725B", ShadeCategory.LIPSTICK, ShadeFinish.GLOSSY),
    ("Nude Gloss", "#C98374", ShadeCategory.LIPSTICK, ShadeFinish.GLOSSY),
    # Foundation - fair through deepest, weighted toward deep/Nigerian-representative tones
    ("Porcelain Fair", "#F1D5C0", ShadeCategory.FOUNDATION, ShadeFinish.SATIN),
    ("Warm Beige", "#E0AC81", ShadeCategory.FOUNDATION, ShadeFinish.SATIN),
    ("Honey Tan", "#C68863", ShadeCategory.FOUNDATION, ShadeFinish.SATIN),
    ("Caramel", "#A96A43", ShadeCategory.FOUNDATION, ShadeFinish.SATIN),
    ("Golden Toffee", "#8B5A34", ShadeCategory.FOUNDATION, ShadeFinish.MATTE),
    ("Deep Cinnamon", "#6F4228", ShadeCategory.FOUNDATION, ShadeFinish.MATTE),
    ("Rich Cocoa", "#5A3A24", ShadeCategory.FOUNDATION, ShadeFinish.SATIN),
    ("Dark Chocolate", "#3E2415", ShadeCategory.FOUNDATION, ShadeFinish.MATTE),
    ("Deep Mystery Ebony", "#2C160C", ShadeCategory.FOUNDATION, ShadeFinish.SATIN),
    # Eyeshadow
    ("Golden Bronze", "#B8752E", ShadeCategory.EYESHADOW, ShadeFinish.SHIMMER),
    ("Copper Shimmer", "#B36A34", ShadeCategory.EYESHADOW, ShadeFinish.SHIMMER),
    ("Tangerine Pop", "#D9702E", ShadeCategory.EYESHADOW, ShadeFinish.SATIN),
    ("Deep Plum Brown", "#5A3A44", ShadeCategory.EYESHADOW, ShadeFinish.MATTE),
    ("Charcoal Smoke", "#3A3532", ShadeCategory.EYESHADOW, ShadeFinish.MATTE),
    ("Jet Black Matte", "#1B1714", ShadeCategory.EYESHADOW, ShadeFinish.MATTE),
    ("Champagne Gold", "#D4AF6A", ShadeCategory.EYESHADOW, ShadeFinish.SHIMMER),
    ("Espresso Brown", "#4A3123", ShadeCategory.EYESHADOW, ShadeFinish.MATTE),
    # Eyeliner
    ("Jet Black", "#14100D", ShadeCategory.EYELINER, ShadeFinish.MATTE),
    ("Espresso Brown", "#3B2418", ShadeCategory.EYELINER, ShadeFinish.MATTE),
    ("Deep Navy", "#1B2A4A", ShadeCategory.EYELINER, ShadeFinish.SATIN),
    ("Bronze Shimmer", "#8C5A2A", ShadeCategory.EYELINER, ShadeFinish.SHIMMER),
    # Blush
    ("Rich Terracotta", "#C1552E", ShadeCategory.BLUSH, ShadeFinish.SATIN),
    ("Warm Brick", "#B33921", ShadeCategory.BLUSH, ShadeFinish.MATTE),
    ("Deep Berry", "#8E2A4E", ShadeCategory.BLUSH, ShadeFinish.SATIN),
    ("Burnt Sienna", "#A85327", ShadeCategory.BLUSH, ShadeFinish.MATTE),
    ("Vibrant Fuchsia", "#C2226E", ShadeCategory.BLUSH, ShadeFinish.SHIMMER),
    ("Deep Coral", "#E2603E", ShadeCategory.BLUSH, ShadeFinish.SATIN),
    # Eyebrow
    ("Jet Black", "#1C1611", ShadeCategory.EYEBROW, ShadeFinish.MATTE),
    ("Espresso Brown", "#3B2418", ShadeCategory.EYEBROW, ShadeFinish.MATTE),
    ("Warm Chocolate", "#4E2F1D", ShadeCategory.EYEBROW, ShadeFinish.MATTE),
    ("Soft Auburn", "#6B3A22", ShadeCategory.EYEBROW, ShadeFinish.SATIN),
    ("Ash Taupe", "#5C4A3E", ShadeCategory.EYEBROW, ShadeFinish.MATTE),
    # Gele (real Nigerian textile references)
    ("Royal Gold Aso-Oke", "#C9971F", ShadeCategory.GELE, ShadeFinish.SHIMMER),
    ("Coral Red Damask", "#B8322A", ShadeCategory.GELE, ShadeFinish.SATIN),
    ("Royal Blue Adire", "#1F3E7A", ShadeCategory.GELE, ShadeFinish.SATIN),
    ("Emerald Ankara", "#1E5C45", ShadeCategory.GELE, ShadeFinish.SATIN),
    ("Deep Plum Velvet", "#5A2A4A", ShadeCategory.GELE, ShadeFinish.MATTE),
    ("Ivory Celebrant Lace", "#EDE3D3", ShadeCategory.GELE, ShadeFinish.SATIN),
]


async def seed_shades() -> None:
    async with async_session_factory() as session:
        await session.execute(delete(ShadeItem))
        for name, hex_color, category, finish in STARTER_SHADES:
            session.add(ShadeItem(name=name, hex_color=hex_color, category=category, finish=finish))
        await session.commit()
        print(f"Reset shade catalog to {len(STARTER_SHADES)} starter shade(s).")


if __name__ == "__main__":
    asyncio.run(seed_shades())
