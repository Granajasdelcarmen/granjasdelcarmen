"""add_slaughter_fields_to_animals_and_alert_rabbit_ids

Revision ID: 49b77d5f0769
Revises: a7e455baa5eb
Create Date: 2025-11-06 20:50:06.626701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49b77d5f0769'
down_revision: Union[str, Sequence[str], None] = 'a7e455baa5eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add slaughter fields to animals and rabbit_ids to alerts."""
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check and add fields to animals table
    animal_columns = [col['name'] for col in inspector.get_columns('animals')]
    
    if 'slaughtered' not in animal_columns:
        op.add_column('animals', sa.Column('slaughtered', sa.Boolean(), nullable=True, server_default='0'))
    
    if 'slaughtered_date' not in animal_columns:
        op.add_column('animals', sa.Column('slaughtered_date', sa.DateTime(), nullable=True))
    
    if 'in_freezer' not in animal_columns:
        op.add_column('animals', sa.Column('in_freezer', sa.Boolean(), nullable=True, server_default='0'))
    
    # Check and add rabbit_ids field to alerts table (for grouped alerts)
    alert_columns = [col['name'] for col in inspector.get_columns('alerts')]
    
    if 'rabbit_ids' not in alert_columns:
        # Store JSON array of rabbit IDs for grouped slaughter alerts
        op.add_column('alerts', sa.Column('rabbit_ids', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove slaughter fields from animals and rabbit_ids from alerts."""
    op.drop_column('alerts', 'rabbit_ids', if_exists=True)
    op.drop_column('animals', 'in_freezer', if_exists=True)
    op.drop_column('animals', 'slaughtered_date', if_exists=True)
    op.drop_column('animals', 'slaughtered', if_exists=True)
