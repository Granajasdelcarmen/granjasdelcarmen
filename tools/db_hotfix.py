"""
One-off hotfix script to align DB schema with current models without relying on Alembic.
Adds missing columns/enums usage for events/alerts tables in Postgres.
Safe to re-run; uses IF NOT EXISTS.
"""
from sqlalchemy import text
from app.utils.database import engine


DDL_STATEMENTS = [
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
]


def main() -> None:
    with engine.begin() as conn:
        for stmt in DDL_STATEMENTS:
            conn.execute(text(stmt))
    print("DB hotfix applied successfully")


if __name__ == "__main__":
    main()


