"""add eyebrow and gele shade categories

Revision ID: 6e31c6e34de1
Revises: 1cec6a22bce2
Create Date: 2026-09-14 20:40:37.894547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '6e31c6e34de1'
down_revision: Union[str, None] = '1cec6a22bce2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres allows adding enum values inside a transaction (PG 12+), as long as the new
    # value isn't used by a statement in the same transaction - it isn't here, so no
    # autocommit block is needed.
    op.execute("ALTER TYPE shade_category ADD VALUE IF NOT EXISTS 'eyebrow'")
    op.execute("ALTER TYPE shade_category ADD VALUE IF NOT EXISTS 'gele'")


def downgrade() -> None:
    # Postgres has no ALTER TYPE ... DROP VALUE - removing an enum value cleanly would mean
    # rebuilding the type and every column/row using it. Not worth supporting for a downgrade
    # path; any 'eyebrow'/'gele' shade rows would need to be deleted manually first.
    pass
