"""
One-off hotfix script to align DB schema with current models without relying on Alembic.
Adds missing columns/enums usage for events/alerts/animals tables in Postgres.
Safe to re-run; uses IF NOT EXISTS.
"""
from sqlalchemy import text
from app.utils.database import engine


DDL_STATEMENTS = [
    # Create or update animaltype enum - must be done before using it
    """
    DO $$ BEGIN
        CREATE TYPE animaltype AS ENUM ('RABBIT', 'COW', 'CHICKEN', 'SHEEP', 'OTHER');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """,
    # Create or update role enum - must be done before using it
    """
    DO $$ BEGIN
        CREATE TYPE role AS ENUM ('admin', 'user', 'viewer', 'trabajador');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """,
    # Add missing values to role enum if they don't exist
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'trabajador' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'role')
        ) THEN
            ALTER TYPE role ADD VALUE 'trabajador';
        END IF;
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """,
    # Add missing values to animaltype enum if they don't exist
    # PostgreSQL doesn't support IF NOT EXISTS for ADD VALUE, so we catch errors
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'RABBIT' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'animaltype')
        ) THEN
            ALTER TYPE animaltype ADD VALUE 'RABBIT';
        END IF;
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """,
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'COW' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'animaltype')
        ) THEN
            ALTER TYPE animaltype ADD VALUE 'COW';
        END IF;
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """,
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'CHICKEN' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'animaltype')
        ) THEN
            ALTER TYPE animaltype ADD VALUE 'CHICKEN';
        END IF;
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """,
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'SHEEP' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'animaltype')
        ) THEN
            ALTER TYPE animaltype ADD VALUE 'SHEEP';
        END IF;
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """,
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum 
            WHERE enumlabel = 'OTHER' 
            AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'animaltype')
        ) THEN
            ALTER TYPE animaltype ADD VALUE 'OTHER';
        END IF;
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """,
    # animals table columns - unified animal model
    """
    ALTER TABLE IF EXISTS animals
    ADD COLUMN IF NOT EXISTS image varchar;
    """,
    """
    ALTER TABLE IF EXISTS animals
    ADD COLUMN IF NOT EXISTS species animaltype NOT NULL DEFAULT 'OTHER';
    """,
    """
    ALTER TABLE IF EXISTS animals
    ADD COLUMN IF NOT EXISTS birth_date timestamp NULL;
    """,
    """
    ALTER TABLE IF EXISTS animals
    ADD COLUMN IF NOT EXISTS gender gender;
    """,
    """
    ALTER TABLE IF EXISTS animals
    ADD COLUMN IF NOT EXISTS discarded boolean NOT NULL DEFAULT false;
    """,
    """
    ALTER TABLE IF EXISTS animals
    ADD COLUMN IF NOT EXISTS discarded_reason text;
    """,
    """
    ALTER TABLE IF EXISTS animals
    ADD COLUMN IF NOT EXISTS user_id varchar;
    """,
    """
    ALTER TABLE IF EXISTS animals
    ADD COLUMN IF NOT EXISTS corral_id varchar;
    """,
    """
    ALTER TABLE IF EXISTS animals
    ADD COLUMN IF NOT EXISTS created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP;
    """,
    """
    ALTER TABLE IF EXISTS animals
    ADD COLUMN IF NOT EXISTS updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP;
    """,
    # events table columns
    """
    ALTER TABLE IF EXISTS events
    ADD COLUMN IF NOT EXISTS scope scope NOT NULL DEFAULT 'INDIVIDUAL';
    """,
    """
    ALTER TABLE IF EXISTS events
    ADD COLUMN IF NOT EXISTS rabbit_event rabbiteventtype;
    """,
    """
    ALTER TABLE IF EXISTS events
    ADD COLUMN IF NOT EXISTS chicken_event chickeneventtype;
    """,
    """
    ALTER TABLE IF EXISTS events
    ADD COLUMN IF NOT EXISTS cow_event coweventtype;
    """,
    """
    ALTER TABLE IF EXISTS events
    ADD COLUMN IF NOT EXISTS sheep_event sheepeventtype;
    """,
    """
    ALTER TABLE IF EXISTS events
    ADD COLUMN IF NOT EXISTS animal_id varchar;
    """,
    """
    ALTER TABLE IF EXISTS events
    ADD COLUMN IF NOT EXISTS corral_id varchar;
    """,
    # alerts table columns
    """
    ALTER TABLE IF EXISTS alerts
    ADD COLUMN IF NOT EXISTS status alertstatus NOT NULL DEFAULT 'PENDING';
    """,
    """
    ALTER TABLE IF EXISTS alerts
    ADD COLUMN IF NOT EXISTS priority alertpriority NOT NULL DEFAULT 'MEDIUM';
    """,
    """
    ALTER TABLE IF EXISTS alerts
    ADD COLUMN IF NOT EXISTS acknowledged_at timestamp NULL;
    """,
    """
    ALTER TABLE IF EXISTS alerts
    ADD COLUMN IF NOT EXISTS resolved_at timestamp NULL;
    """,
    """
    ALTER TABLE IF EXISTS alerts
    ADD COLUMN IF NOT EXISTS corral_id varchar;
    """,
    # Create animal_sales table if it doesn't exist
    """
    CREATE TABLE IF NOT EXISTS animal_sales (
        id varchar PRIMARY KEY,
        animal_id varchar NOT NULL REFERENCES animals(id),
        animal_type animaltype NOT NULL,
        price float NOT NULL,
        weight float,
        height float,
        notes text,
        sold_by varchar NOT NULL,
        created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # Restore foreign key constraint for sold_by (users.id = Auth0 sub)
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'animal_sales_sold_by_fkey' 
            AND table_name = 'animal_sales'
        ) THEN
            ALTER TABLE animal_sales 
            ADD CONSTRAINT animal_sales_sold_by_fkey 
            FOREIGN KEY (sold_by) REFERENCES users(id);
        END IF;
    END $$;
    """,
    # Create producttype enum for financial module
    """
    DO $$ BEGIN
        CREATE TYPE producttype AS ENUM ('miel', 'huevos', 'leche', 'otros');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """,
    # Create expensecategory enum for financial module
    """
    DO $$ BEGIN
        CREATE TYPE expensecategory AS ENUM ('alimentacion', 'medicamentos', 'mantenimiento', 'personal', 'servicios', 'equipos', 'otros');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """,
    # Create product_sales table
    """
    CREATE TABLE IF NOT EXISTS product_sales (
        id VARCHAR PRIMARY KEY,
        product_type producttype NOT NULL,
        quantity FLOAT NOT NULL,
        unit_price FLOAT NOT NULL,
        total_price FLOAT NOT NULL,
        sale_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        customer_name VARCHAR,
        notes TEXT,
        sold_by VARCHAR NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # Add foreign key constraint for product_sales.sold_by
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'product_sales_sold_by_fkey' 
            AND table_name = 'product_sales'
        ) THEN
            ALTER TABLE product_sales 
            ADD CONSTRAINT product_sales_sold_by_fkey 
            FOREIGN KEY (sold_by) REFERENCES users(id);
        END IF;
    END $$;
    """,
    # Create expenses table
    """
    CREATE TABLE IF NOT EXISTS expenses (
        id VARCHAR PRIMARY KEY,
        category expensecategory NOT NULL,
        description TEXT NOT NULL,
        amount FLOAT NOT NULL,
        expense_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        vendor VARCHAR,
        notes TEXT,
        created_by VARCHAR NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # Add foreign key constraint for expenses.created_by
    """
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'expenses_created_by_fkey' 
            AND table_name = 'expenses'
        ) THEN
            ALTER TABLE expenses 
            ADD CONSTRAINT expenses_created_by_fkey 
            FOREIGN KEY (created_by) REFERENCES users(id);
        END IF;
    END $$;
    """,
]


def main() -> None:
    with engine.begin() as conn:
        for stmt in DDL_STATEMENTS:
            conn.execute(text(stmt))
    print("DB hotfix applied successfully")


if __name__ == "__main__":
    main()


