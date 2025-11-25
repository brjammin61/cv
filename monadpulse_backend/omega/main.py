"""
Omega Engine - Main Entry Point
Runs the scanner and API services
"""

import asyncio
import logging
import os
from multiprocessing import Process

from scanner import OmegaScanner
from classifier import MEVClassifier
from db_utils import init_omega_database, test_omega_connection
from api import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)


def run_scanner():
    """Run the Omega scanner service"""
    logger.info("OMEGA: Starting scanner service...")
    
    # Get RPC URL from environment
    rpc_url = os.environ.get('MONAD_RPC_URL', 'http://localhost:8545')
    
    # Create scanner
    scanner = OmegaScanner(rpc_url=rpc_url)
    
    # Run continuous scan
    asyncio.run(scanner.start_continuous_scan())


def run_api():
    """Run the Omega API service"""
    import uvicorn
    
    logger.info("OMEGA: Starting API service...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get('OMEGA_API_PORT', 8001)),
        log_level="info"
    )


def run_daily_scorer():
    """Run daily MEV score calculation (cron job)"""
    logger.info("OMEGA: Running daily score calculation...")
    
    classifier = MEVClassifier()
    classifier.update_daily_scores()
    
    logger.info("OMEGA: Daily scores updated successfully")


def main():
    """
    Main entry point for Omega Engine
    
    Runs both scanner and API in separate processes
    """
    logger.info("=" * 70)
    logger.info("OMEGA ENGINE - Proprietary MEV Analysis System")
    logger.info("=" * 70)
    
    # Initialize database
    logger.info("OMEGA: Initializing database...")
    if not init_omega_database():
        logger.error("OMEGA: Failed to initialize database")
        return
    
    # Test connection
    if not test_omega_connection():
        logger.error("OMEGA: Database connection failed")
        return
    
    logger.info("OMEGA: Database ready")
    
    # Start scanner in background process
    scanner_process = Process(target=run_scanner, daemon=True)
    scanner_process.start()
    logger.info("OMEGA: Scanner process started")
    
    # Run API in main process
    try:
        run_api()
    except KeyboardInterrupt:
        logger.info("OMEGA: Shutting down...")
        scanner_process.terminate()
        scanner_process.join()
        logger.info("OMEGA: Shutdown complete")


if __name__ == "__main__":
    main()
