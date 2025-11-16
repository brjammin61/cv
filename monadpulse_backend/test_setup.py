"""
Test runner for MonadPulse without Docker
Runs the system using SQLite for immediate testing
"""
import sys
import os

# Set environment to use SQLite instead of PostgreSQL for testing
os.environ['DATABASE_URL'] = 'sqlite:///./monadpulse_test.db'
os.environ['LOG_LEVEL'] = 'INFO'

print("=" * 70)
print("MonadPulse Test Environment Starting")
print("=" * 70)
print(f"Database: SQLite (test mode)")
print(f"Log Level: INFO")
print()

# First, run the ingestor once to populate the database
print("Step 1: Populating database with initial data...")
sys.path.insert(0, '/home/user/cv/monadpulse_backend/ingestor')

# Modify shared_models to use SQLite
import shared_models as models_ingestor
models_ingestor.DATABASE_URL = 'sqlite:///./monadpulse_test.db'
models_ingestor.engine = models_ingestor.create_engine('sqlite:///./monadpulse_test.db')
models_ingestor.Base.metadata.create_all(bind=models_ingestor.engine)

# Import and run ingestor
from ingestor import fetch_validator_data, generate_chart_data, calculate_network_stats
from ingestor import populate_validators, populate_chart_data, populate_network_stats
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=models_ingestor.engine)
db = Session()

try:
    # Generate and populate data
    validators_data = fetch_validator_data()
    chart_data = generate_chart_data(days=14)
    network_stats = calculate_network_stats(validators_data)

    populate_validators(db, validators_data)
    populate_chart_data(db, chart_data)
    populate_network_stats(db, network_stats)

    print(f"✓ Populated {len(validators_data)} validators")
    print(f"✓ Populated {len(chart_data)} chart data points")
    print(f"✓ Populated network statistics")
    print()
except Exception as e:
    print(f"✗ Error populating database: {e}")
    sys.exit(1)
finally:
    db.close()

print("=" * 70)
print("Database populated successfully!")
print("=" * 70)
print()
print("Now you can start the API server with:")
print("  cd /home/user/cv/monadpulse_backend/api")
print("  DATABASE_URL='sqlite:///./monadpulse_test.db' uvicorn main:app --host 0.0.0.0 --port 8000")
print()
print("Test endpoints:")
print("  curl http://localhost:8000/health")
print("  curl http://localhost:8000/stats/kpi")
print("  curl http://localhost:8000/validators/leaderboard")
print()
