"""
Database models and API schemas for MonadPulse.
"""
import os
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, Field

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://trader:your_secret_password@localhost/monadpulse')

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# =============================================================================
# SQLAlchemy Database Models
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


# =============================================================================
# Pydantic API Response Models
# =============================================================================

class KPIStats(BaseModel):
    """KPI statistics for the dashboard."""
    total_mev: float = Field(..., description="Total MEV captured in USD")
    mev_change_pct: float = Field(..., description="MEV change percentage vs previous period")
    network_tps: int = Field(..., description="Network transactions per second (24h avg)")
    top_validator: str = Field(..., description="Top validator by MEV efficiency")
    top_validator_is_partner: bool = Field(..., description="Is top validator an Omega partner")
    avg_mev_efficiency: float = Field(..., description="Average MEV efficiency across all validators")

    class Config:
        json_schema_extra = {
            "example": {
                "total_mev": 2500000.50,
                "mev_change_pct": 15.2,
                "network_tps": 1540,
                "top_validator": "Omega Validator",
                "top_validator_is_partner": True,
                "avg_mev_efficiency": 125.5
            }
        }


class ChartData(BaseModel):
    """Chart data point for MEV over time."""
    name: str = Field(..., description="Date label for x-axis")
    mev_captured_usd: float = Field(..., alias="MEV Captured (USD)", description="MEV captured in USD")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "11/14",
                "MEV Captured (USD)": 95000.00
            }
        }


class Validator(BaseModel):
    """Validator leaderboard entry."""
    rank: int = Field(..., description="Validator rank by MEV efficiency")
    name: str = Field(..., description="Validator name")
    uptime_pct: float = Field(..., description="Uptime percentage")
    apy_pct: float = Field(..., description="Annual percentage yield")
    mev_efficiency: float = Field(..., description="MEV efficiency score (24h)")
    is_omega_partner: bool = Field(..., description="Is this an Omega Engine partner validator")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "rank": 1,
                "name": "Omega Validator",
                "uptime_pct": 99.95,
                "apy_pct": 9.5,
                "mev_efficiency": 250.80,
                "is_omega_partner": True
            }
        }


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database: str = "connected"


# =============================================================================
# Utility Functions
# =============================================================================

def create_db_and_tables():
    """Create all database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
