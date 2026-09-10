"""Shared SQLAlchemy column-type helpers."""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Enum as SAEnum


def pg_enum[E: StrEnum](enum_cls: type[E], name: str) -> SAEnum:
    """A native Postgres ENUM column storing each member's lowercase `.value`.

    SQLAlchemy's `Enum` type stores the Python member *name* by default (e.g.
    "LIPSTICK"), not its `.value` ("lipstick") — surprising for a `StrEnum` where the
    two differ only in case. `values_callable` makes the DB, the wire format, and
    `.value` agree.
    """
    return SAEnum(enum_cls, name=name, values_callable=lambda cls: [member.value for member in cls])
