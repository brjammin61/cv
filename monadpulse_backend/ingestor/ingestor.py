"""
MonadPulse Data Ingestor Service

This service continuously fetches validator data and populates the database.

PRODUCTION NOTE:
- This currently uses MOCK DATA for rapid launch
- Before mainnet, replace mock data with real Monad SDK calls
- The Monad SDK will be available at: https://github.com/monad-developers/monad-sdk
"""
import os
import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session

from db_utils import get_db_session
from shared_models import ValidatorDB, ChartDataDB, NetworkStatsDB, create_db_and_tables

# =============================================================================
# Configuration
# =============================================================================

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
UPDATE_INTERVAL_SECONDS = int(os.environ.get('UPDATE_INTERVAL_SECONDS', 60))

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | INGESTOR | %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# Mock Data Configuration
# =============================================================================
# This mock data represents what we expect to receive from the Monad SDK
# Replace with real SDK calls before mainnet launch

MOCK_VALIDATORS = [
    {
        "name": "Omega Validator",
        "address": "monad1omega...",
        "apy": 9.5,
        "mev": 250.8,
        "partner": True,
        "uptime_base": 99.95
    },
    {
        "name": "Figment",
        "address": "monad1figment...",
        "apy": 9.1,
        "mev": 120.5,
        "partner": False,
        "uptime_base": 99.8
    },
    {
        "name": "Everstake",
        "address": "monad1everstake...",
        "apy": 8.5,
        "mev": 110.2,
        "partner": False,
        "uptime_base": 99.7
    },
    {
        "name": "Coinbase Cloud",
        "address": "monad1coinbase...",
        "apy": 8.0,
        "mev": 90.0,
        "partner": False,
        "uptime_base": 99.9
    },
    {
        "name": "P2P.org",
        "address": "monad1p2p...",
        "apy": 8.8,
        "mev": 105.1,
        "partner": False,
        "uptime_base": 99.6
    },
    {
        "name": "Stakin",
        "address": "monad1stakin...",
        "apy": 8.2,
        "mev": 75.3,
        "partner": False,
        "uptime_base": 99.5
    },
    {
        "name": "Lido",
        "address": "monad1lido...",
        "apy": 8.7,
        "mev": 65.0,
        "partner": False,
        "uptime_base": 99.8
    },
    {
        "name": "Chorus One",
        "address": "monad1chorus...",
        "apy": 8.3,
        "mev": 55.2,
        "partner": False,
        "uptime_base": 99.4
    },
    {
        "name": "Staked",
        "address": "monad1staked...",
        "apy": 8.1,
        "mev": 48.7,
        "partner": False,
        "uptime_base": 99.3
    },
    {
        "name": "Anchorage Digital",
        "address": "monad1anchorage...",
        "apy": 7.9,
        "mev": 42.1,
        "partner": False,
        "uptime_base": 99.2
    },
]

# =============================================================================
# Data Fetching Functions
# =============================================================================

def generate_chart_data(days: int = 14) -> List[Dict]:
    """
    Generate historical MEV chart data.

    In production, this will query the Monad blockchain for historical MEV data.
    For now, we generate realistic-looking mock data.

    Args:
        days: Number of days of historical data to generate

    Returns:
        List of chart data points
    """
    chart_data = []
    base_mev = 50000
    volatility = 0.15

    today = datetime.utcnow()

    for i in range(days):
        date = today - timedelta(days=(days - i - 1))
        date_str = date.strftime("%m/%d")

        # Simulate growing MEV with some volatility
        growth_factor = 1 + (i / days) * 0.8  # 80% growth over period
        daily_change = random.uniform(-volatility, volatility)
        mev_value = base_mev * growth_factor * (1 + daily_change)

        chart_data.append({
            "timestamp": date,
            "name": date_str,
            "mev": round(mev_value, 2)
        })

    return chart_data


def fetch_validator_data() -> List[Dict]:
    """
    Fetch current validator data.

    PRODUCTION: This will call the Monad SDK:
        from monad_sdk import MonadClient
        client = MonadClient(rpc_url="...")
        validators = client.staking.get_validators()

    For now, returns mock data with slight randomization to simulate live updates.

    Returns:
        List of validator data dictionaries
    """
    validators = []

    for mock_val in MOCK_VALIDATORS:
        # Add slight random variation to simulate live data
        mev_variation = random.uniform(-0.05, 0.05)  # ±5% variation
        uptime_variation = random.uniform(-0.1, 0.1)  # ±0.1% variation

        validators.append({
            "name": mock_val["name"],
            "address": mock_val["address"],
            "uptime_pct": min(100.0, mock_val["uptime_base"] + uptime_variation),
            "apy_pct": mock_val["apy"],
            "mev_efficiency": max(0, mock_val["mev"] * (1 + mev_variation)),
            "is_omega_partner": mock_val["partner"],
            "blocks_produced": random.randint(1000, 5000)
        })

    return validators


def calculate_network_stats(validators: List[Dict]) -> Dict:
    """
    Calculate network-wide statistics.

    Args:
        validators: List of validator data

    Returns:
        Dictionary of network statistics
    """
    if not validators:
        return {
            "total_mev": 0.0,
            "network_tps": 0,
            "avg_mev_efficiency": 0.0,
            "mev_change_pct": 0.0
        }

    total_mev = sum(v["mev_efficiency"] for v in validators) * 1000
    avg_mev_efficiency = sum(v["mev_efficiency"] for v in validators) / len(validators)

    # Simulate network TPS with some randomness
    base_tps = 1540
    tps_variation = random.randint(-50, 100)
    network_tps = base_tps + tps_variation

    # Simulate MEV growth
    mev_change_pct = random.uniform(10.0, 20.0)

    return {
        "total_mev": total_mev,
        "network_tps": network_tps,
        "avg_mev_efficiency": avg_mev_efficiency,
        "mev_change_pct": mev_change_pct
    }


# =============================================================================
# Database Population Functions
# =============================================================================

def populate_validators(db: Session, validators_data: List[Dict]):
    """
    Update validator data in the database.

    Args:
        db: Database session
        validators_data: List of validator dictionaries
    """
    # Sort by MEV efficiency to assign ranks
    sorted_validators = sorted(
        validators_data,
        key=lambda v: v["mev_efficiency"],
        reverse=True
    )

    # Clear existing validator data
    db.query(ValidatorDB).delete()
    db.commit()

    # Insert updated validator data
    for rank, val_data in enumerate(sorted_validators, start=1):
        validator = ValidatorDB(
            rank=rank,
            name=val_data["name"],
            address=val_data["address"],
            uptime_pct=val_data["uptime_pct"],
            apy_pct=val_data["apy_pct"],
            mev_efficiency=val_data["mev_efficiency"],
            is_omega_partner=val_data["is_omega_partner"],
            blocks_produced=val_data["blocks_produced"],
            last_updated=datetime.utcnow()
        )
        db.add(validator)

    db.commit()
    logger.info(f"Updated {len(sorted_validators)} validators in database")


def populate_chart_data(db: Session, chart_data: List[Dict]):
    """
    Update chart data in the database.

    Args:
        db: Database session
        chart_data: List of chart data dictionaries
    """
    # Clear existing chart data
    db.query(ChartDataDB).delete()
    db.commit()

    # Insert new chart data
    for point in chart_data:
        chart_point = ChartDataDB(
            timestamp=point["timestamp"],
            name=point["name"],
            mev_captured_usd=point["mev"]
        )
        db.add(chart_point)

    db.commit()
    logger.info(f"Updated {len(chart_data)} chart data points in database")


def populate_network_stats(db: Session, stats: Dict):
    """
    Add new network statistics entry.

    Args:
        db: Database session
        stats: Dictionary of network statistics
    """
    network_stat = NetworkStatsDB(
        timestamp=datetime.utcnow(),
        total_mev=stats["total_mev"],
        network_tps=stats["network_tps"],
        avg_mev_efficiency=stats["avg_mev_efficiency"],
        mev_change_pct=stats["mev_change_pct"]
    )
    db.add(network_stat)
    db.commit()
    logger.info("Updated network statistics")


# =============================================================================
# Main Ingestor Loop
# =============================================================================

def run_ingestor_cycle(db: Session):
    """
    Execute one complete data ingestion cycle.

    Args:
        db: Database session
    """
    try:
        logger.info("=== Starting data ingestion cycle ===")

        # Fetch validator data
        logger.info("Fetching validator data...")
        validators_data = fetch_validator_data()

        # Calculate network statistics
        logger.info("Calculating network statistics...")
        network_stats = calculate_network_stats(validators_data)

        # Generate chart data (only on first run or periodically)
        # Check if chart data exists
        existing_chart_data = db.query(ChartDataDB).count()
        if existing_chart_data == 0:
            logger.info("Generating historical chart data...")
            chart_data = generate_chart_data(days=14)
            populate_chart_data(db, chart_data)

        # Update database
        logger.info("Updating database...")
        populate_validators(db, validators_data)
        populate_network_stats(db, network_stats)

        logger.info("=== Data ingestion cycle completed successfully ===")

    except Exception as e:
        logger.error(f"Error during ingestion cycle: {e}", exc_info=True)
        db.rollback()


def main():
    """Main entry point for the ingestor service."""
    logger.info("=" * 70)
    logger.info("MonadPulse Data Ingestor Service - Starting")
    logger.info("=" * 70)
    logger.info(f"Update interval: {UPDATE_INTERVAL_SECONDS} seconds")
    logger.info(f"Log level: {LOG_LEVEL}")

    # Wait for database and get session
    logger.info("Connecting to database...")
    db = get_db_session()

    # Ensure tables exist
    logger.info("Ensuring database tables exist...")
    try:
        create_db_and_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise

    # Main ingestion loop
    logger.info("Entering main ingestion loop...")
    cycle_count = 0

    while True:
        try:
            cycle_count += 1
            logger.info(f"--- Cycle #{cycle_count} ---")

            run_ingestor_cycle(db)

            logger.info(f"Sleeping for {UPDATE_INTERVAL_SECONDS} seconds...")
            time.sleep(UPDATE_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal. Exiting gracefully...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            logger.info("Retrying in 30 seconds...")
            time.sleep(30)

    # Cleanup
    db.close()
    logger.info("Ingestor service stopped")


if __name__ == "__main__":
    main()
