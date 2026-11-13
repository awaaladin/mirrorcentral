"""mirror_crash_reports: why the Android app closed, sent by the app on its next launch

Revision ID: c81f0d2e5a17
Revises: a4c9e1f27b30
Create Date: 2026-11-13 10:00:00.000000

Hand-written: the database is shared with other projects, so autogenerate would touch their tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c81f0d2e5a17'
down_revision: Union[str, None] = 'a4c9e1f27b30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'mirror_crash_reports',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('summary', sa.String(length=500), nullable=False),
        sa.Column('trace', sa.Text(), nullable=False, server_default=''),
        sa.Column('app_version', sa.String(length=20), nullable=False),
        sa.Column('version_code', sa.Integer(), nullable=False),
        sa.Column('device', sa.String(length=120), nullable=False),
        sa.Column('android_sdk', sa.Integer(), nullable=False),
        sa.Column('abis', sa.String(length=120), nullable=False),
        sa.Column('ram_mb', sa.Integer(), nullable=False),
        sa.Column('pss_kb', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mirror_crash_reports_kind', 'mirror_crash_reports', ['kind'])
    op.create_index('ix_mirror_crash_reports_created_at', 'mirror_crash_reports', ['created_at'])


def downgrade() -> None:
    op.drop_table('mirror_crash_reports')
