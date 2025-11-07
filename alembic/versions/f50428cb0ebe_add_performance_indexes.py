"""add_performance_indexes

Revision ID: f50428cb0ebe
Revises: 6ff0c0154f85
Create Date: 2025-11-06 18:43:31.910552

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f50428cb0ebe'
down_revision: Union[str, Sequence[str], None] = '6ff0c0154f85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for frequently queried columns."""
    # Check if indexes already exist (idempotent migration)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('animals')]
    
    # Single column indexes for frequently filtered columns
    if 'ix_animals_species' not in existing_indexes:
        op.create_index('ix_animals_species', 'animals', ['species'])
    
    if 'ix_animals_gender' not in existing_indexes:
        op.create_index('ix_animals_gender', 'animals', ['gender'])
    
    if 'ix_animals_discarded' not in existing_indexes:
        op.create_index('ix_animals_discarded', 'animals', ['discarded'])
    
    if 'ix_animals_birth_date' not in existing_indexes:
        op.create_index('ix_animals_birth_date', 'animals', ['birth_date'])
    
    if 'ix_animals_mother_id' not in existing_indexes:
        op.create_index('ix_animals_mother_id', 'animals', ['mother_id'])
    
    if 'ix_animals_father_id' not in existing_indexes:
        op.create_index('ix_animals_father_id', 'animals', ['father_id'])
    
    # Check if is_breeder column exists before creating index
    columns = [col['name'] for col in inspector.get_columns('animals')]
    if 'is_breeder' in columns and 'ix_animals_is_breeder' not in existing_indexes:
        op.create_index('ix_animals_is_breeder', 'animals', ['is_breeder'])
    
    # Composite indexes for common query patterns
    # (species, discarded) - most common filter combination
    if 'ix_animals_species_discarded' not in existing_indexes:
        op.create_index('ix_animals_species_discarded', 'animals', ['species', 'discarded'])
    
    # (species, gender, discarded) - common filter for gender-specific queries
    if 'ix_animals_species_gender_discarded' not in existing_indexes:
        op.create_index('ix_animals_species_gender_discarded', 'animals', ['species', 'gender', 'discarded'])
    
    # (species, birth_date) - for sorted queries
    if 'ix_animals_species_birth_date' not in existing_indexes:
        op.create_index('ix_animals_species_birth_date', 'animals', ['species', 'birth_date'])


def downgrade() -> None:
    """Remove performance indexes."""
    # Remove indexes in reverse order
    op.drop_index('ix_animals_species_birth_date', table_name='animals', if_exists=True)
    op.drop_index('ix_animals_species_gender_discarded', table_name='animals', if_exists=True)
    op.drop_index('ix_animals_species_discarded', table_name='animals', if_exists=True)
    op.drop_index('ix_animals_is_breeder', table_name='animals', if_exists=True)
    op.drop_index('ix_animals_father_id', table_name='animals', if_exists=True)
    op.drop_index('ix_animals_mother_id', table_name='animals', if_exists=True)
    op.drop_index('ix_animals_birth_date', table_name='animals', if_exists=True)
    op.drop_index('ix_animals_discarded', table_name='animals', if_exists=True)
    op.drop_index('ix_animals_gender', table_name='animals', if_exists=True)
    op.drop_index('ix_animals_species', table_name='animals', if_exists=True)
