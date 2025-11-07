"""add_animal_parent_relationships_and_origin

Revision ID: cf7221fee9ce
Revises: 55ff92007355
Create Date: 2025-11-06 10:43:21.628293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf7221fee9ce'
down_revision: Union[str, Sequence[str], None] = '55ff92007355'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add origin column (default to PURCHASED for existing animals)
    # For SQLite, use String instead of Enum
    op.add_column('animals', sa.Column('origin', sa.String(), nullable=False, server_default='PURCHASED'))
    
    # Add parent relationship columns
    op.add_column('animals', sa.Column('mother_id', sa.String(), nullable=True))
    op.add_column('animals', sa.Column('father_id', sa.String(), nullable=True))
    
    # Add purchase information columns
    op.add_column('animals', sa.Column('purchase_date', sa.DateTime(), nullable=True))
    op.add_column('animals', sa.Column('purchase_price', sa.Float(), nullable=True))
    op.add_column('animals', sa.Column('purchase_vendor', sa.String(), nullable=True))
    
    # Add foreign key constraints for parent relationships
    op.create_foreign_key('fk_animals_mother', 'animals', 'animals', ['mother_id'], ['id'])
    op.create_foreign_key('fk_animals_father', 'animals', 'animals', ['father_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove foreign key constraints
    op.drop_constraint('fk_animals_father', 'animals', type_='foreignkey')
    op.drop_constraint('fk_animals_mother', 'animals', type_='foreignkey')
    
    # Remove columns
    op.drop_column('animals', 'purchase_vendor')
    op.drop_column('animals', 'purchase_price')
    op.drop_column('animals', 'purchase_date')
    op.drop_column('animals', 'father_id')
    op.drop_column('animals', 'mother_id')
    op.drop_column('animals', 'origin')
    
    # Drop enum type (SQLite doesn't support this, but PostgreSQL does)
    # For SQLite, we'll just leave it as it doesn't matter
    # op.execute("DROP TYPE IF EXISTS animalorigin")
