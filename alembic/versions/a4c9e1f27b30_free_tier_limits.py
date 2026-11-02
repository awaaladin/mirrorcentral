"""free tier limits: usage_events, email confirmation, users.unlocked_at; retire account_type

Revision ID: a4c9e1f27b30
Revises: fcdde9a26217
Create Date: 2026-11-02 12:00:00.000000

* usage_events counts monthly photos and Showroom analyses (app/services/entitlements.py).
* Everyone who already paid for Solo was sold it as a one-time payment, so users.unlocked_at keeps
  them unlimited photos and no watermark for good.
* Anyone who has paid has a working address, so they count as email-confirmed.
* account_type is reset because anyone could register as "business" for free and a payment set it
  permanently, so the stored value means nothing.

Hand-written: the database is shared with other projects, so autogenerate would touch their tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'a4c9e1f27b30'
down_revision: Union[str, None] = 'fcdde9a26217'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('email_code_hash', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True))
    op.add_column('users', sa.Column('email_code_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('email_code_attempts', sa.Integer(), nullable=False, server_default='0'))

    op.create_table(
        'usage_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('kind', sqlmodel.sql.sqltypes.AutoString(length=16), nullable=False),
        sa.Column('period', sqlmodel.sql.sqltypes.AutoString(length=7), nullable=False),
        sa.Column('key', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column('paid', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'kind', 'period', 'key', name='uq_usage_event'),
    )
    op.create_index('ix_usage_events_user_id', 'usage_events', ['user_id'])
    op.create_index('ix_usage_events_period', 'usage_events', ['period'])
    op.create_index('ix_usage_events_created_at', 'usage_events', ['created_at'])

    op.execute("""
        UPDATE users SET unlocked_at = paid.first_paid_at
        FROM (
            SELECT user_id, MIN(COALESCE(paid_at, created_at)) AS first_paid_at
            FROM payments WHERE plan = 'solo' AND status = 'success' GROUP BY user_id
        ) AS paid
        WHERE users.id = paid.user_id
    """)
    op.execute("""
        UPDATE users SET email_verified_at = now()
        WHERE id IN (SELECT user_id FROM payments WHERE status = 'success')
    """)
    op.execute("UPDATE users SET account_type = 'consumer' WHERE account_type = 'business'")


def downgrade() -> None:
    op.drop_index('ix_usage_events_created_at', table_name='usage_events')
    op.drop_index('ix_usage_events_period', table_name='usage_events')
    op.drop_index('ix_usage_events_user_id', table_name='usage_events')
    op.drop_table('usage_events')
    op.drop_column('users', 'email_code_attempts')
    op.drop_column('users', 'email_code_expires_at')
    op.drop_column('users', 'email_code_hash')
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'unlocked_at')
