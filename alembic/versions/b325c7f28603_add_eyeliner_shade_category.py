"""add eyeliner shade category

Revision ID: b325c7f28603
Revises: 6e31c6e34de1
Create Date: 2026-09-15 20:47:13.427227

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b325c7f28603'
down_revision: Union[str, None] = '6e31c6e34de1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE shade_category ADD VALUE IF NOT EXISTS 'eyeliner'")


def downgrade() -> None:
    # Postgres has no ALTER TYPE ... DROP VALUE - see the eyebrow/gele migration for the same note.
    pass
