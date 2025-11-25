#!/usr/bin/env python3
"""
Clear fake chart data from the database.
Run this once to remove simulated MEV chart data.
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path so we can import shared_models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingestor.shared_models import ChartDataDB

# Database connection
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://monadpulse:monadpulse123@db:5432/monadpulse"
)

def clear_fake_data():
    """Clear all chart data from database."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Count existing records
        count = session.query(ChartDataDB).count()
        print(f"Found {count} chart data records")

        if count > 0:
            # Delete all chart data
            session.query(ChartDataDB).delete()
            session.commit()
            print(f"✅ Cleared {count} fake chart data records")
            print("⏳ Chart will show 'AWAITING API' until real Monad MEV data is available")
        else:
            print("✅ No chart data to clear")

    except Exception as e:
        print(f"❌ Error clearing chart data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    clear_fake_data()
