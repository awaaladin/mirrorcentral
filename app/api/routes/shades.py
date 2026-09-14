from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.enums import ShadeCategory
from app.models.shade_item import ShadeItem
from app.schemas.shades import ShadePublic

# No auth dependency here on purpose: browsing the shade catalog (including search) is part of
# the free/offline tier's experience too, and the Android app needs to be able to refresh its
# bundled shade list without requiring a signed-in session.
router = APIRouter(prefix="/shades", tags=["shades"])


@router.get("", response_model=list[ShadePublic])
async def list_shades(
    category: ShadeCategory | None = None,
    q: str | None = Query(default=None, min_length=1, max_length=100, description="Search by shade name."),
    session: AsyncSession = Depends(get_session),
) -> list[ShadeItem]:
    stmt = select(ShadeItem)
    if category is not None:
        stmt = stmt.where(ShadeItem.category == category)
    if q:
        stmt = stmt.where(ShadeItem.name.ilike(f"%{q}%"))
    stmt = stmt.order_by(ShadeItem.category, ShadeItem.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())
