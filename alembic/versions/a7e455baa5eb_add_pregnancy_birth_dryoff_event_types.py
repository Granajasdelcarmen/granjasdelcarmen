"""add_pregnancy_birth_dryoff_event_types

Revision ID: a7e455baa5eb
Revises: 7bc34f4782a4
Create Date: 2025-11-06 19:45:58.577638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7e455baa5eb'
down_revision: Union[str, Sequence[str], None] = '7bc34f4782a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new event types to RabbitEventType and CowEventType enums."""
    # Check database type
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    
    if dialect_name == 'postgresql':
        # PostgreSQL: Add values to enum types
        # Note: PostgreSQL doesn't support IF NOT EXISTS for ADD VALUE
        # We need to check if value exists first, or catch the error
        
        # Helper function to safely add enum value
        def add_enum_value(enum_type: str, value: str):
            try:
                # Check if value already exists
                check_query = sa.text("""
                    SELECT 1 FROM pg_enum 
                    WHERE enumlabel = :value 
                    AND enumtypid = (SELECT oid FROM pg_type WHERE typname = :enum_type)
                """)
                result = conn.execute(
                    check_query,
                    {'value': value, 'enum_type': enum_type}
                ).fetchone()
                
                if not result:
                    # Value doesn't exist, add it
                    op.execute(sa.text(f"ALTER TYPE {enum_type} ADD VALUE '{value}'"))
            except Exception as e:
                # If error occurs (e.g., value already exists or type doesn't exist), continue
                # PostgreSQL will raise an error if value exists, which is fine
                pass
        
        # RabbitEventType: Add PREGNANCY
        add_enum_value('rabbiteventtype', 'PREGNANCY')
        
        # CowEventType: Add PREGNANCY, BIRTH, DRY_OFF
        add_enum_value('coweventtype', 'PREGNANCY')
        add_enum_value('coweventtype', 'BIRTH')
        add_enum_value('coweventtype', 'DRY_OFF')
        
    elif dialect_name == 'sqlite':
        # SQLite doesn't support enums natively, they're stored as strings
        # No migration needed for SQLite
        pass
    else:
        # For other databases, log a warning
        print(f"Warning: Enum migration not implemented for {dialect_name}")


def downgrade() -> None:
    """Remove new event types from enums (not fully reversible in PostgreSQL)."""
    # Note: PostgreSQL doesn't support removing enum values easily
    # This is a one-way migration in practice
    # If needed, you would need to recreate the enum type
    pass
