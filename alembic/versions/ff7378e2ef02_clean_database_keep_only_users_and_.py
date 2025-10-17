"""Clean database - keep only users and rabbits

Revision ID: ff7378e2ef02
Revises: 001
Create Date: 2025-10-17 17:09:08.589877

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff7378e2ef02'
down_revision: Union[str, Sequence[str], None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop unnecessary tables, keep only users and rabbits
    tables_to_drop = [
        'Account',
        'Client', 
        'Session',
        'Shopping',
        'User',
        'VerificationToken',
        '_prisma_migrations',
        'alembic_version',
        'order_items',
        'orders', 
        'products',
        'test_table'
    ]
    
    for table in tables_to_drop:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    # Note: This downgrade cannot restore the dropped tables
    # as we don't have their original schema definitions
    pass
