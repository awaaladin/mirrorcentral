from __future__ import annotations

import uuid

from sqlalchemy import Column
from sqlmodel import Field, SQLModel

from app.db.types import pg_enum
from app.models.enums import ClientTag


class ClientProfile(SQLModel, table=True):
    __tablename__ = "client_profiles"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    name: str = Field(nullable=False, max_length=255)
    notes: str = Field(default="", nullable=False)
    tag: ClientTag = Field(
        default=ClientTag.SELF,
        sa_column=Column(pg_enum(ClientTag, "client_tag"), nullable=False),
    )
