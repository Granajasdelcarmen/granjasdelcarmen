"""add_inventory_models

Revision ID: f7f020ed9cf9
Revises: 49b77d5f0769
Create Date: 2025-11-06 23:06:00.597835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7f020ed9cf9'
down_revision: Union[str, Sequence[str], None] = '49b77d5f0769'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add inventory models (inventory_products and inventory_transactions tables)."""
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if tables already exist
    existing_tables = inspector.get_table_names()
    
    # Create inventory_products table
    if 'inventory_products' not in existing_tables:
        op.create_table(
            'inventory_products',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('product_type', sa.Enum('MEAT_RABBIT', 'MEAT_CHICKEN', 'MEAT_COW', 'MEAT_SHEEP', 'EGGS', 'MILK', 'CHEESE', 'BUTTER', 'WOOL', 'HONEY', 'WAX', 'OTHER', name='inventoryproducttype'), nullable=False),
            sa.Column('product_name', sa.String(), nullable=False),
            sa.Column('quantity', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('unit', sa.Enum('KG', 'GRAMS', 'LITERS', 'UNITS', 'DOZENS', name='inventoryunit'), nullable=False),
            sa.Column('production_date', sa.DateTime(), nullable=False),
            sa.Column('expiration_date', sa.DateTime(), nullable=True),
            sa.Column('location', sa.String(), nullable=True),
            sa.Column('unit_price', sa.Float(), nullable=True),
            sa.Column('status', sa.Enum('AVAILABLE', 'RESERVED', 'SOLD', 'EXPIRED', 'DISCARDED', name='inventorystatus'), nullable=False, server_default='AVAILABLE'),
            sa.Column('animal_id', sa.String(), nullable=True),
            sa.Column('created_by', sa.String(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['animal_id'], ['animals.id'], ),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create inventory_transactions table
    if 'inventory_transactions' not in existing_tables:
        op.create_table(
            'inventory_transactions',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('product_id', sa.String(), nullable=False),
            sa.Column('transaction_type', sa.Enum('ENTRY', 'EXIT', 'ADJUSTMENT', name='inventorytransactiontype'), nullable=False),
            sa.Column('quantity', sa.Float(), nullable=False),
            sa.Column('reason', sa.String(), nullable=True),
            sa.Column('sale_id', sa.String(), nullable=True),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['product_id'], ['inventory_products.id'], ),
            sa.ForeignKeyConstraint(['sale_id'], ['product_sales.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for better performance
        op.create_index('ix_inventory_products_status', 'inventory_products', ['status'])
        op.create_index('ix_inventory_products_product_type', 'inventory_products', ['product_type'])
        op.create_index('ix_inventory_products_animal_id', 'inventory_products', ['animal_id'])
        op.create_index('ix_inventory_transactions_product_id', 'inventory_transactions', ['product_id'])
        op.create_index('ix_inventory_transactions_created_at', 'inventory_transactions', ['created_at'])


def downgrade() -> None:
    """Remove inventory models."""
    # Drop indexes first
    op.drop_index('ix_inventory_transactions_created_at', table_name='inventory_transactions', if_exists=True)
    op.drop_index('ix_inventory_transactions_product_id', table_name='inventory_transactions', if_exists=True)
    op.drop_index('ix_inventory_products_animal_id', table_name='inventory_products', if_exists=True)
    op.drop_index('ix_inventory_products_product_type', table_name='inventory_products', if_exists=True)
    op.drop_index('ix_inventory_products_status', table_name='inventory_products', if_exists=True)
    
    # Drop tables
    op.drop_table('inventory_transactions', if_exists=True)
    op.drop_table('inventory_products', if_exists=True)
    
    # Drop enums (PostgreSQL specific)
    op.execute('DROP TYPE IF EXISTS inventorytransactiontype')
    op.execute('DROP TYPE IF EXISTS inventorystatus')
    op.execute('DROP TYPE IF EXISTS inventoryunit')
    op.execute('DROP TYPE IF EXISTS inventoryproducttype')
