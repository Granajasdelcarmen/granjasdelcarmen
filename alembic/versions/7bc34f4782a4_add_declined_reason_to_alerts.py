"""add_declined_reason_to_alerts

Revision ID: 7bc34f4782a4
Revises: f50428cb0ebe
Create Date: 2025-11-06 19:05:31.341259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bc34f4782a4'
down_revision: Union[str, Sequence[str], None] = 'f50428cb0ebe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add declined_reason column to alerts table."""
    # Check if column already exists (idempotent migration)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('alerts')]
    
    if 'declined_reason' not in columns:
        op.add_column('alerts', sa.Column('declined_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove declined_reason column from alerts table."""
    op.drop_column('alerts', 'declined_reason', if_exists=True)
