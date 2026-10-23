"""add payments table (Paystack prepaid Pro)

Revision ID: e7b1c4d2a9f0
Revises: d3a2a0e40fc1
Create Date: 2026-10-23 12:00:00.000000

Hand-written for the same reason as d3a2a0e40fc1: the database is shared with another project,
so autogenerate would try to drop that project's tables. This only adds Mirror's payments table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e7b1c4d2a9f0'
down_revision: Union[str, None] = 'd3a2a0e40fc1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # subscription_plan already exists (initial schema), so it uses the dialect ENUM with
    # create_type=False; payment_status is new and is created by create_table().
    op.create_table(
        'payments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('reference', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('plan', postgresql.ENUM('solo', 'studio', name='subscription_plan', create_type=False), nullable=False),
        sa.Column('amount_kobo', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'success', 'failed', name='payment_status'), nullable=False),
        sa.Column('authorization_url', sqlmodel.sql.sqltypes.AutoString(length=2048), nullable=False),
        sa.Column('paystack_transaction_id', sqlmodel.sql.sqltypes.AutoString(length=40), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_payments_reference'), 'payments', ['reference'], unique=True)
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_reference'), table_name='payments')
    op.drop_table('payments')
    sa.Enum(name='payment_status').drop(op.get_bind(), checkfirst=True)
