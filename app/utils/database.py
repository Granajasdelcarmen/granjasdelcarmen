"""
Database utilities and connection management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, DisconnectionError
from contextlib import contextmanager
from typing import Generator, Dict, Any, Optional
import time
import logging
from app.config.settings import Config

# Get logger (don't configure globally)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_POOL_SIZE = 2
DEFAULT_MAX_OVERFLOW = 3
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 1

# Determine database type from URL
def is_postgresql(url: str) -> bool:
    """Check if database URL is PostgreSQL"""
    if not url:
        return False
    url_lower = url.lower()
    return url_lower.startswith('postgresql://') or url_lower.startswith('postgres://') or 'postgresql' in url_lower

# Get database URL from config
database_url = Config.DATABASE_URL

# Build connection args based on database type
# Log database URL type for debugging (without exposing credentials)
logger.info(f"Database URL type detected: {'PostgreSQL' if is_postgresql(database_url) else 'SQLite'}")

if is_postgresql(database_url):
    # PostgreSQL-specific connection arguments
    # Note: sslmode should be in the connection URL, not in connect_args
    # For psycopg2, SSL is handled via the connection string or connect_args with 'sslmode' key
    # But psycopg2 uses different parameter names - use 'sslmode' in URL or handle via connect_args properly
    connect_args = {
        "connect_timeout": 5,
        "application_name": "granjas-del-carmen-be",
        "options": "-c statement_timeout=30000",
    }
    
    # If sslmode is needed, it should be in the DATABASE_URL itself
    # Format: postgresql://user:pass@host:port/db?sslmode=require
    
    # Create PostgreSQL engine with optimized connection pooling
    engine = create_engine(
        database_url,
        pool_size=DEFAULT_POOL_SIZE,
        max_overflow=DEFAULT_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,  # 1 hour
        pool_timeout=20,
        pool_reset_on_return='commit',
        echo=False,
        connect_args=connect_args
    )
    logger.info("PostgreSQL engine created successfully")
else:
    # SQLite configuration (for local development only)
    # SQLite-specific connection args
    sqlite_connect_args = {"check_same_thread": False}
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        echo=False,
        connect_args=sqlite_connect_args
    )
    logger.info("SQLite engine created successfully")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with retry logic
    Provides automatic session cleanup and connection error handling
    """
    db: Optional[Session] = None
    
    for attempt in range(DEFAULT_RETRY_ATTEMPTS):
        try:
            db = SessionLocal()
            # Test the connection
            db.execute(text("SELECT 1"))
            yield db
            return  # Success, exit the function
        except (OperationalError, DisconnectionError) as e:
            logger.warning(f"Database connection failed (attempt {attempt + 1}/{DEFAULT_RETRY_ATTEMPTS}): {e}")
            if db:
                db.close()
                db = None
            
            if attempt < DEFAULT_RETRY_ATTEMPTS - 1:
                time.sleep(DEFAULT_RETRY_DELAY * (2 ** attempt))  # Exponential backoff
            else:
                logger.error("Max retries reached. Database connection failed.")
                raise
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            if db:
                db.rollback()
            raise
        finally:
            # Only close if we haven't yielded successfully
            if db and attempt < DEFAULT_RETRY_ATTEMPTS - 1:
                try:
                    db.close()
                except Exception as e:
                    logger.warning(f"Error closing database session: {e}")
    
    # This should never be reached, but just in case
    if db:
        try:
            db.close()
        except Exception as e:
            logger.warning(f"Error closing database session: {e}")

def get_db() -> Generator[Session, None, None]:
    """
    Generator for database sessions (for dependency injection)
    Uses the same retry logic as get_db_session
    """
    with get_db_session() as db:
        yield db

def check_database_connection() -> bool:
    """
    Check if database connection is healthy
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

def get_connection_pool_status() -> Dict[str, int]:
    """
    Get current connection pool status
    
    Returns:
        dict: Pool status information
    """
    try:
        pool = engine.pool
        # SQLite pool doesn't have all these methods
        if is_postgresql(Config.DATABASE_URL):
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        else:
            # SQLite pool status
            return {
                "pool_size": getattr(pool, 'size', lambda: 0)(),
                "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                "overflow": 0,
                "invalid": 0
            }
    except Exception as e:
        logger.warning(f"Could not get pool status: {e}")
        return {
            "pool_size": 0,
            "checked_in": 0,
            "checked_out": 0,
            "overflow": 0,
            "invalid": 0
        }

def cleanup_connections() -> bool:
    """
    Clean up and close all connections in the pool
    Useful for graceful shutdown or when resetting connections
    """
    try:
        engine.dispose()
        logger.info("Database connections cleaned up successfully")
        return True
    except Exception as e:
        logger.error(f"Error cleaning up connections: {e}")
        return False

def get_connection_stats() -> Dict[str, Any]:
    """
    Get detailed connection statistics
    
    Returns:
        dict: Detailed connection statistics
    """
    try:
        pool = engine.pool
        if is_postgresql(Config.DATABASE_URL):
            total_connections = pool.size() + pool.overflow()
            utilization = (pool.checkedout() / total_connections * 100) if total_connections > 0 else 0
            
            return {
                "total_connections": total_connections,
                "permanent_connections": pool.size(),
                "temporary_connections": pool.overflow(),
                "available_connections": pool.checkedin(),
                "busy_connections": pool.checkedout(),
                "invalid_connections": pool.invalid(),
                "pool_utilization": f"{utilization:.1f}%"
            }
        else:
            # SQLite simplified stats
            return {
                "total_connections": 1,
                "permanent_connections": 1,
                "temporary_connections": 0,
                "available_connections": 1,
                "busy_connections": 0,
                "invalid_connections": 0,
                "pool_utilization": "0.0%"
            }
    except Exception as e:
        logger.warning(f"Could not get connection stats: {e}")
        return {
            "total_connections": 0,
            "permanent_connections": 0,
            "temporary_connections": 0,
            "available_connections": 0,
            "busy_connections": 0,
            "invalid_connections": 0,
            "pool_utilization": "0.0%"
        }
