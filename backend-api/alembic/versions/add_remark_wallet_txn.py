"""Add remark column to wallet_transactions

Revision ID: add_remark_wallet_txn
Revises: 834dacd3d611
Create Date: 2025-02-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_remark_wallet_txn'
down_revision: Union[str, Sequence[str], None] = '834dacd3d611'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add remark column to wallet_transactions table
    op.add_column('wallet_transactions', sa.Column('remark', sa.String(500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove remark column from wallet_transactions table
    op.drop_column('wallet_transactions', 'remark')
