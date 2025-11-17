"""
Omega Engine Database Utilities
Separate database for proprietary MEV data
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from contextlib import contextmanager
import time

from .models import OmegaBase

logger = logging.getLogger(__name__)

# Separate database for Omega (encrypted, private)
OMEGA_DATABASE_URL = os.environ.get(
    'OMEGA_DATABASE_URL',
    'postgresql://trader:omega_secret@localhost/omega_monadpulse'
)


def create_omega_engine():
    """Create SQLAlchemy engine for Omega database"""
    return create_engine(
        OMEGA_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )


# Global engine and session factory
omega_engine = create_omega_engine()
OmegaSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=omega_engine)


def init_omega_database():
    """
    Initialize Omega database tables
    Run this once on first deployment
    """
    try:
        logger.info("OMEGA: Creating database tables...")
        OmegaBase.metadata.create_all(bind=omega_engine)
        logger.info("OMEGA: Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"OMEGA: Failed to create database tables: {e}")
        return False


def get_omega_session(max_retries=5, retry_interval=2) -> Session:
    """
    Get Omega database session with retry logic
    
    Args:
        max_retries: Maximum connection attempts
        retry_interval: Seconds between retries
        
    Returns:
        SQLAlchemy session
        
    Raises:
        RuntimeError: If connection fails after retries
    """
    retries = 0
    while retries < max_retries:
        try:
            session = OmegaSessionLocal()
            # Test connection
            session.execute(text("SELECT 1"))
            return session
        except OperationalError as e:
            retries += 1
            if retries < max_retries:
                logger.warning(
                    f"OMEGA DB: Connection failed (attempt {retries}/{max_retries}). "
                    f"Retrying in {retry_interval}s... Error: {e}"
                )
                time.sleep(retry_interval)
            else:
                raise RuntimeError(f"Failed to connect to Omega DB after {max_retries} attempts")
    
    raise RuntimeError("Unexpected error in get_omega_session")


@contextmanager
def omega_db_session():
    """
    Context manager for Omega database sessions
    
    Usage:
        with omega_db_session() as db:
            # do database operations
            db.add(mev_opportunity)
            db.commit()
    """
    session = get_omega_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"OMEGA DB: Transaction failed, rolling back: {e}")
        raise
    finally:
        session.close()


def test_omega_connection() -> bool:
    """Test Omega database connectivity"""
    try:
        with omega_db_session() as db:
            db.execute(text("SELECT 1"))
        logger.info("OMEGA DB: Connection test successful")
        return True
    except Exception as e:
        logger.error(f"OMEGA DB: Connection test failed: {e}")
        return False
