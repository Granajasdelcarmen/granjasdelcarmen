"""add_rabbit_breeder_and_dead_offspring

Revision ID: 6ff0c0154f85
Revises: cf7221fee9ce
Create Date: 2025-11-06 11:45:39.039189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ff0c0154f85'
down_revision: Union[str, Sequence[str], None] = 'cf7221fee9ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_breeder column to animals table (if it doesn't exist)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('animals')]
    
    if 'is_breeder' not in columns:
        op.add_column('animals', sa.Column('is_breeder', sa.Boolean(), nullable=False, server_default='0'))
    
    # Create dead_offspring table (if it doesn't exist)
    tables = inspector.get_table_names()
    if 'dead_offspring' not in tables:
        op.create_table(
            'dead_offspring',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('mother_id', sa.String(), nullable=False),
            sa.Column('father_id', sa.String(), nullable=True),
            sa.Column('birth_date', sa.DateTime(), nullable=False),
            sa.Column('death_date', sa.DateTime(), nullable=False),
            sa.Column('species', sa.String(), nullable=False, server_default='RABBIT'),
            sa.Column('count', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('suspected_cause', sa.String(), nullable=True),
            sa.Column('recorded_by', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['mother_id'], ['animals.id']),
            sa.ForeignKeyConstraint(['father_id'], ['animals.id']),
            sa.ForeignKeyConstraint(['recorded_by'], ['users.id'])
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop dead_offspring table
    op.drop_table('dead_offspring')
    
    # Remove is_breeder column
    op.drop_column('animals', 'is_breeder')
