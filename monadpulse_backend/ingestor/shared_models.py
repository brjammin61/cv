"""
Shared database models for the MonadPulse ingestor.
This is a subset of models.py from the API, containing only DB models.
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://trader:your_secret_password@localhost/monadpulse')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base = declarative_base()

# =============================================================================
# SQLAlchemy Database Models (shared with API)
# =============================================================================

class ValidatorDB(Base):
    """Validator performance data stored in database."""
    __tablename__ = "validators"

    id = Column(Integer, primary_key=True, index=True)
    rank = Column(Integer, unique=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    address = Column(String, unique=True, nullable=True)
    uptime_pct = Column(Float, default=99.0, nullable=False)
    apy_pct = Column(Float, default=8.0, nullable=False)
    mev_efficiency = Column(Float, default=0.0, nullable=False)
    is_omega_partner = Column(Boolean, default=False, nullable=False)
    blocks_produced = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChartDataDB(Base):
    """Historical MEV data for charting."""
    __tablename__ = "chart_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    name = Column(String, nullable=False)  # e.g., "11/10"
    mev_captured_usd = Column(Float, nullable=False)


class NetworkStatsDB(Base):
    """Network-wide statistics."""
    __tablename__ = "network_stats"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_mev = Column(Float, default=0.0)
    network_tps = Column(Integer, default=0)
    avg_mev_efficiency = Column(Float, default=0.0)
    mev_change_pct = Column(Float, default=0.0)


def create_db_and_tables():
    """Create all database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
