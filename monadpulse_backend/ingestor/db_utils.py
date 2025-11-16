"""
Database connection utilities for the MonadPulse ingestor service.
"""
import os
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://trader:your_secret_password@localhost/monadpulse')


def get_db_session(max_retries=10, retry_interval=3):
    """
    Waits for database to be ready and returns a session.

    Args:
        max_retries: Maximum number of connection attempts
        retry_interval: Seconds to wait between retries

    Returns:
        SQLAlchemy session object

    Raises:
        RuntimeError: If unable to connect after max_retries
    """
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    retries = 0
    while retries < max_retries:
        try:
            db = SessionLocal()
            # Test the connection
            db.execute("SELECT 1")
            logger.info("INGESTOR: Database connection successful.")
            return db
        except OperationalError as e:
            retries += 1
            logger.warning(
                f"INGESTOR: Database not ready (attempt {retries}/{max_retries}). "
                f"Retrying in {retry_interval}s... Error: {e}"
            )
            time.sleep(retry_interval)

    raise RuntimeError(f"Failed to connect to database after {max_retries} attempts")


def test_connection():
    """Test database connection and return status."""
    try:
        db = get_db_session(max_retries=1)
        db.close()
        return True
    except Exception:
        return False
