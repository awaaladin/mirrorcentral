"""add users.current_session_id (single active sign-in)

Revision ID: fcdde9a26217
Revises: e7b1c4d2a9f0
Create Date: 2026-10-24 21:00:00.000000

Hand-written for the same reason as the other recent migrations: the database is shared
with other projects, so autogenerate would try to touch their tables too. This only adds
one nullable column to Mirror's own users table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'fcdde9a26217'
down_revision: Union[str, None] = 'e7b1c4d2a9f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('current_session_id', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('users', 'current_session_id')
