from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.deps import current_admin
from app.admin.templating import render
from app.db.session import get_session
from app.models.admin_user import AdminUser
from app.models.client_profile import ClientProfile
from app.models.makeup_look import MakeupLook
from app.models.user import User

router = APIRouter(tags=["admin-clients"])


@router.get("/admin/clients")
async def list_clients(
    request: Request,
    admin: AdminUser = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
):
    q = request.query_params.get("q", "").strip()
    stmt = select(ClientProfile, User).join(User, User.id == ClientProfile.owner_user_id)
    if q:
        stmt = stmt.where(ClientProfile.name.ilike(f"%{q}%"))
    rows = (await session.execute(stmt.order_by(ClientProfile.name).limit(100))).all()

    return render(request, "clients_list.html", {"rows": rows, "q": q}, admin=admin, active="clients")


@router.get("/admin/clients/{client_id}")
async def client_detail(
    client_id: uuid.UUID,
    request: Request,
    admin: AdminUser = Depends(current_admin),
    session: AsyncSession = Depends(get_session),
):
    client = await session.get(ClientProfile, client_id)
    if client is None:
        return render(request, "not_found.html", {"kind": "Client"}, admin=admin, active="clients", status_code=404)

    owner = await session.get(User, client.owner_user_id)
    looks = (
        await session.execute(
            select(MakeupLook)
            .where(MakeupLook.client_profile_id == client_id)
            .order_by(MakeupLook.created_at.desc())
        )
    ).scalars().all()

    return render(
        request, "client_detail.html", {"client": client, "owner": owner, "looks": looks}, admin=admin, active="clients"
    )
