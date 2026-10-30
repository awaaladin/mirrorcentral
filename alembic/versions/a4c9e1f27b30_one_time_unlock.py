"""add users.unlocked_at (one-time payment), and retire account_type

Revision ID: a4c9e1f27b30
Revises: fcdde9a26217
Create Date: 2026-10-30 12:00:00.000000

Everyone who already paid for Solo was sold it as a one-time payment, so they keep it forever.

account_type is reset because anyone could register as "business" for free and a payment set it
permanently, so the stored value means nothing; what an account can use now comes from
users.unlocked_at and subscriptions (app/services/entitlements.py).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a4c9e1f27b30'
down_revision: Union[str, None] = 'fcdde9a26217'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=True))
    op.execute("""
        UPDATE users SET unlocked_at = paid.first_paid_at
        FROM (
            SELECT user_id, MIN(COALESCE(paid_at, created_at)) AS first_paid_at
            FROM payments WHERE plan = 'solo' AND status = 'success' GROUP BY user_id
        ) AS paid
        WHERE users.id = paid.user_id
    """)
    op.execute("UPDATE users SET account_type = 'consumer' WHERE account_type = 'business'")


def downgrade() -> None:
    op.drop_column('users', 'unlocked_at')
