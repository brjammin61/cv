"""
MonadPulse FastAPI Backend
Production-ready API server for MonadPulse validator analytics dashboard.
"""
import os
import logging
from typing import List
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text

import models
from models import (
    SessionLocal,
    ValidatorDB,
    ChartDataDB,
    NetworkStatsDB,
    KPIStats,
    ChartData,
    Validator,
    HealthCheck,
    create_db_and_tables,
    get_db
)

# =============================================================================
# Logging Configuration
# =============================================================================

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | API | %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# FastAPI Application Setup
# =============================================================================

app = FastAPI(
    title="MonadPulse API",
    description="Production-grade API for Monad mainnet validator analytics and MEV tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# =============================================================================
# CORS Middleware Configuration
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development
        "http://localhost:5173",  # Vite development
        "https://monadpulse.io",  # Production domain (update this)
        "*"  # Allow all for development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Database Initialization
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    logger.info("Starting MonadPulse API...")
    try:
        create_db_and_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information."""
    return {
        "name": "MonadPulse API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "kpi": "/stats/kpi",
            "chart": "/stats/chart",
            "leaderboard": "/validators/leaderboard"
        }
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring and load balancers.
    Verifies database connectivity.
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return HealthCheck(
            status="healthy",
            timestamp=datetime.utcnow(),
            database="connected"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "disconnected",
                "error": str(e)
            }
        )


@app.get("/stats/kpi", response_model=KPIStats, tags=["Statistics"])
async def get_kpi_stats(db: Session = Depends(get_db)):
    """
    Get Key Performance Indicators for the dashboard.

    Returns REAL data where available, zeros for unavailable metrics.
    Dashboard will show "Coming Soon" for unavailable data.
    """
    try:
        # Get all validators
        validators = db.query(ValidatorDB).all()

        # Get latest network stats (contains REAL TPS from Monad blockchain)
        latest_stats = db.query(NetworkStatsDB).order_by(desc(NetworkStatsDB.timestamp)).first()

        # REAL DATA: Network TPS from Monad blockchain
        network_tps = latest_stats.network_tps if latest_stats else 0

        # If no validators yet, return zeros (dashboard will show "Coming Soon")
        if not validators:
            logger.info("⏳ Validator data not available yet - returning zeros")
            return KPIStats(
                total_mev=0.0,
                mev_change_pct=0.0,
                network_tps=network_tps,  # This is REAL
                top_validator="",
                top_validator_is_partner=False,
                avg_mev_efficiency=0.0
            )

        # When validators are available, calculate real metrics
        total_mev = sum(v.mev_efficiency for v in validators) * 1000
        top_validator = max(validators, key=lambda v: v.mev_efficiency)
        avg_mev_efficiency = sum(v.mev_efficiency for v in validators) / len(validators)
        mev_change_pct = latest_stats.mev_change_pct if latest_stats else 0.0

        return KPIStats(
            total_mev=total_mev,
            mev_change_pct=mev_change_pct,
            network_tps=network_tps,
            top_validator=top_validator.name,
            top_validator_is_partner=top_validator.is_omega_partner,
            avg_mev_efficiency=avg_mev_efficiency
        )

    except Exception as e:
        logger.error(f"Error calculating KPI stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate KPI statistics: {str(e)}"
        )


@app.get("/stats/chart", response_model=List[ChartData], tags=["Statistics"])
async def get_chart_data(db: Session = Depends(get_db)):
    """
    Get historical MEV data for charting (last 14 days).

    Returns:
        List of data points with date labels and MEV captured in USD
    """
    try:
        # Query chart data, ordered by timestamp
        chart_data = db.query(ChartDataDB).order_by(ChartDataDB.timestamp).all()

        if not chart_data:
            logger.warning("No chart data available")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No chart data available. The ingestor may still be initializing."
            )

        # Convert to response format
        result = []
        for point in chart_data:
            result.append(
                ChartData(
                    name=point.name,
                    mev_captured_usd=point.mev_captured_usd
                )
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chart data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chart data: {str(e)}"
        )


@app.get("/validators/leaderboard", response_model=List[Validator], tags=["Validators"])
async def get_leaderboard(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get validator leaderboard ranked by MEV efficiency.

    Args:
        limit: Maximum number of validators to return (default: 100)

    Returns:
        List of validators ordered by rank
    """
    try:
        # Query validators ordered by rank
        validators = (
            db.query(ValidatorDB)
            .order_by(ValidatorDB.rank)
            .limit(limit)
            .all()
        )

        if not validators:
            logger.warning("No validator data available for leaderboard")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No validator data available. The ingestor may still be initializing."
            )

        return validators

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch validator leaderboard: {str(e)}"
        )


@app.get("/validators/{validator_name}", response_model=Validator, tags=["Validators"])
async def get_validator_details(
    validator_name: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific validator.

    Args:
        validator_name: Name of the validator

    Returns:
        Validator details
    """
    try:
        validator = db.query(ValidatorDB).filter(
            ValidatorDB.name == validator_name
        ).first()

        if not validator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validator '{validator_name}' not found"
            )

        return validator

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching validator details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch validator details: {str(e)}"
        )


# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )
