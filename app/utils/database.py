"""
Database utilities and connection management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from app.config.settings import Config

# Create database engine
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session():
    """
    Context manager for database sessions
    Provides automatic session cleanup
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db():
    """
    Generator for database sessions (for dependency injection)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
