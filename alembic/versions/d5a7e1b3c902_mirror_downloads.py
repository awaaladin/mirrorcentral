"""mirror_downloads: a counted row for each download of the Android app

Revision ID: d5a7e1b3c902
Revises: c81f0d2e5a17
Create Date: 2026-11-18 14:30:00.000000

Hand-written: the database is shared with other projects, so autogenerate would touch their tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd5a7e1b3c902'
down_revision: Union[str, None] = 'c81f0d2e5a17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'mirror_downloads',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('version_code', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=8), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mirror_downloads_version_code', 'mirror_downloads', ['version_code'])
    op.create_index('ix_mirror_downloads_created_at', 'mirror_downloads', ['created_at'])


def downgrade() -> None:
    op.drop_table('mirror_downloads')
