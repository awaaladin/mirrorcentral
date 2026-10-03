from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.device_token import DeviceToken
from app.schemas.app_releases import DeviceTokenRegister

# No auth dependency on purpose: a device should start receiving update alerts the moment the
# app installs the FCM token, before any sign-in - same reasoning as the public shade catalog.
router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/register", status_code=status.HTTP_204_NO_CONTENT)
async def register_device_token(
    payload: DeviceTokenRegister,
    session: AsyncSession = Depends(get_session),
) -> None:
    # Upsert on the token's unique constraint - a token re-registering (e.g. app reinstalled,
    # token unchanged) shouldn't 409, it should just be a no-op.
    stmt = (
        pg_insert(DeviceToken)
        .values(token=payload.token, platform=payload.platform)
        .on_conflict_do_nothing(index_elements=[DeviceToken.token])
    )
    await session.execute(stmt)
    await session.commit()
