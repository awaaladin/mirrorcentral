from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.client_profile import ClientProfile
from app.models.makeup_look import MakeupLook
from app.models.user import User
from app.schemas.clients import ClientProfileCreate, ClientProfilePublic, ClientProfileUpdate
from app.schemas.looks import MakeupLookCreate, MakeupLookPublic, MakeupLookUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


async def _get_owned_client(session: AsyncSession, client_id: uuid.UUID, user: User) -> ClientProfile:
    """404s (not 403) when the client exists but belongs to someone else, so a caller
    can't distinguish "not found" from "not yours" by probing other users' ids."""
    client = await session.get(ClientProfile, client_id)
    if client is None or client.owner_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client profile not found.")
    return client


async def _get_owned_look(session: AsyncSession, client: ClientProfile, look_id: uuid.UUID) -> MakeupLook:
    look = await session.get(MakeupLook, look_id)
    if look is None or look.client_profile_id != client.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Look not found.")
    return look


@router.post("", response_model=ClientProfilePublic, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientProfileCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ClientProfile:
    client = ClientProfile(owner_user_id=current_user.id, **payload.model_dump())
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client


@router.get("", response_model=list[ClientProfilePublic])
async def list_clients(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ClientProfile]:
    result = await session.execute(
        select(ClientProfile).where(ClientProfile.owner_user_id == current_user.id).order_by(ClientProfile.name)
    )
    return list(result.scalars().all())


@router.get("/{client_id}", response_model=ClientProfilePublic)
async def get_client(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ClientProfile:
    return await _get_owned_client(session, client_id, current_user)


@router.patch("/{client_id}", response_model=ClientProfilePublic)
async def update_client(
    client_id: uuid.UUID,
    payload: ClientProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ClientProfile:
    client = await _get_owned_client(session, client_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    client = await _get_owned_client(session, client_id, current_user)
    await session.delete(client)
    await session.commit()


@router.post("/{client_id}/looks", response_model=MakeupLookPublic, status_code=status.HTTP_201_CREATED)
async def create_look(
    client_id: uuid.UUID,
    payload: MakeupLookCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MakeupLook:
    client = await _get_owned_client(session, client_id, current_user)
    look = MakeupLook(
        client_profile_id=client.id,
        source_photo_url=payload.source_photo_url,
        layers=payload.layers.model_dump(exclude_none=True),
    )
    session.add(look)
    await session.commit()
    await session.refresh(look)
    return look


@router.get("/{client_id}/looks", response_model=list[MakeupLookPublic])
async def list_looks(
    client_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[MakeupLook]:
    client = await _get_owned_client(session, client_id, current_user)
    result = await session.execute(
        select(MakeupLook).where(MakeupLook.client_profile_id == client.id).order_by(MakeupLook.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{client_id}/looks/{look_id}", response_model=MakeupLookPublic)
async def get_look(
    client_id: uuid.UUID,
    look_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MakeupLook:
    client = await _get_owned_client(session, client_id, current_user)
    return await _get_owned_look(session, client, look_id)


@router.patch("/{client_id}/looks/{look_id}", response_model=MakeupLookPublic)
async def update_look(
    client_id: uuid.UUID,
    look_id: uuid.UUID,
    payload: MakeupLookUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MakeupLook:
    client = await _get_owned_client(session, client_id, current_user)
    look = await _get_owned_look(session, client, look_id)

    updates = payload.model_dump(exclude_unset=True)
    if "source_photo_url" in updates:
        look.source_photo_url = updates["source_photo_url"]
    if "layers" in updates and updates["layers"] is not None:
        look.layers = payload.layers.model_dump(exclude_none=True)

    session.add(look)
    await session.commit()
    await session.refresh(look)
    return look


@router.delete("/{client_id}/looks/{look_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_look(
    client_id: uuid.UUID,
    look_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    client = await _get_owned_client(session, client_id, current_user)
    look = await _get_owned_look(session, client, look_id)
    await session.delete(look)
    await session.commit()
