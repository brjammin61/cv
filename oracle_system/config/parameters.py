"""
Oracle Model Parameters Configuration

This module defines all tunable parameters for the Oracle analytical models.
Adjust these values to fine-tune the model's behavior based on your
risk tolerance and market observations.
"""

from dataclasses import dataclass, field
from typing import Dict, Any
import json


@dataclass
class BiasCorrectorParams:
    """Parameters for the BiasCorrector (Théo Strategy) module."""

    # Weight given to the shy voter index (0.0 to 1.0)
    # Higher = trust neighbor polls more, lower = trust self polls more
    shy_voter_weight: float = 0.75

    # Minimum sample size for polls to be considered reliable
    min_poll_sample_size: int = 500

    # Maximum age of poll data in days
    max_poll_age_days: int = 14


@dataclass
class FavoriteLongshotParams:
    """Parameters for the FavoriteLongshotAdjuster module."""

    # Probability above which an outcome is considered a "Favorite"
    favorite_threshold: float = 0.80

    # Probability below which an outcome is considered a "Longshot"
    longshot_threshold: float = 0.20

    # Minimum edge required to generate a signal (in cents)
    min_edge_cents: float = 1.0


@dataclass
class RiskFreeRateParams:
    """Parameters for the RiskFreeRateAdjuster (Domer Strategy) module."""

    # Annual risk-free rate (e.g., 0.05 for 5%)
    # Update this based on current T-bill rates or USDC lending rates
    risk_free_rate: float = 0.05

    # Minimum probability for time-value analysis to be relevant
    # Below this, probability risk dominates time risk
    min_probability_threshold: float = 0.80

    # Minimum yield advantage (in basis points) to generate a signal
    min_yield_advantage_bps: float = 50.0


@dataclass
class DutchBookParams:
    """Parameters for the DutchBookDetector module."""

    # Transaction fee per share (e.g., 0.005 for 0.5 cents)
    transaction_fee_per_share: float = 0.005

    # Minimum net profit (in cents) to generate a signal
    # This accounts for slippage and execution risk
    min_net_profit_cents: float = 0.5


@dataclass
class SpatialArbitrageParams:
    """Parameters for the SpatialArbitrageDetector module."""

    # Total all-in cost for cross-venue arbitrage (in dollars)
    # This should include:
    # - Kalshi trading fees (~0.7%)
    # - Polymarket trading fees (~2%)
    # - Gas fees on Polygon (amortized, ~$0.01)
    # - Slippage estimate
    total_fee_cost: float = 0.020

    # Minimum net profit (in cents) to generate a signal
    min_net_profit_cents: float = 1.0

    # Maximum price staleness in seconds before data is considered stale
    max_price_staleness_seconds: int = 30


@dataclass
class RiskManagementParams:
    """Risk management parameters for position sizing and safety."""

    # Kelly Criterion fraction (0.0 to 1.0)
    # Full Kelly = 1.0, Half Kelly = 0.5 (recommended for safety)
    kelly_fraction: float = 0.25

    # Maximum position size as % of total capital
    max_position_size_percent: float = 10.0

    # Maximum total exposure across all positions
    max_total_exposure_percent: float = 50.0

    # Minimum edge (in %) required to take a position
    min_edge_percent: float = 2.0

    # Maximum number of simultaneous positions
    max_concurrent_positions: int = 10


@dataclass
class DataRefreshParams:
    """Parameters for data refresh rates and timeouts."""

    # How often to refresh Kalshi order book data (seconds)
    kalshi_refresh_interval: int = 5

    # How often to refresh Polymarket order book data (seconds)
    polymarket_refresh_interval: int = 5

    # How often to refresh polling data (seconds)
    polling_refresh_interval: int = 900  # 15 minutes

    # How often to refresh the dashboard UI (seconds)
    dashboard_refresh_interval: int = 2

    # API request timeout (seconds)
    api_timeout: int = 10


@dataclass
class SignalFilterParams:
    """Parameters for filtering and prioritizing signals."""

    # Minimum conviction level to display ("NONE", "LOW", "MEDIUM", "HIGH")
    min_conviction_level: str = "MEDIUM"

    # Only show signals with positive expected value
    only_positive_ev: bool = True

    # Maximum number of signals to display simultaneously
    max_signals_displayed: int = 20

    # Prioritize signals by (options: "edge", "conviction", "volume", "recency")
    prioritize_by: str = "edge"


class OracleParameters:
    """
    Master configuration class for all Oracle parameters.

    This class provides a centralized way to manage and access all
    model parameters with type safety and validation.
    """

    def __init__(self):
        """Initialize with default parameters."""
        self.bias_corrector = BiasCorrectorParams()
        self.flb_adjuster = FavoriteLongshotParams()
        self.rfr_adjuster = RiskFreeRateParams()
        self.dutchbook = DutchBookParams()
        self.spatial_arb = SpatialArbitrageParams()
        self.risk_management = RiskManagementParams()
        self.data_refresh = DataRefreshParams()
        self.signal_filter = SignalFilterParams()

    def to_dict(self) -> Dict[str, Any]:
        """Convert all parameters to a dictionary."""
        return {
            'bias_corrector': self.bias_corrector.__dict__,
            'flb_adjuster': self.flb_adjuster.__dict__,
            'rfr_adjuster': self.rfr_adjuster.__dict__,
            'dutchbook': self.dutchbook.__dict__,
            'spatial_arb': self.spatial_arb.__dict__,
            'risk_management': self.risk_management.__dict__,
            'data_refresh': self.data_refresh.__dict__,
            'signal_filter': self.signal_filter.__dict__
        }

    def save_to_file(self, filepath: str) -> None:
        """Save parameters to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'OracleParameters':
        """Load parameters from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        params = cls()

        # Update each parameter group
        for key, value in data.get('bias_corrector', {}).items():
            setattr(params.bias_corrector, key, value)
        for key, value in data.get('flb_adjuster', {}).items():
            setattr(params.flb_adjuster, key, value)
        for key, value in data.get('rfr_adjuster', {}).items():
            setattr(params.rfr_adjuster, key, value)
        for key, value in data.get('dutchbook', {}).items():
            setattr(params.dutchbook, key, value)
        for key, value in data.get('spatial_arb', {}).items():
            setattr(params.spatial_arb, key, value)
        for key, value in data.get('risk_management', {}).items():
            setattr(params.risk_management, key, value)
        for key, value in data.get('data_refresh', {}).items():
            setattr(params.data_refresh, key, value)
        for key, value in data.get('signal_filter', {}).items():
            setattr(params.signal_filter, key, value)

        return params

    def print_summary(self) -> None:
        """Print a formatted summary of all parameters."""
        print("=" * 80)
        print("ORACLE PARAMETERS SUMMARY")
        print("=" * 80)

        sections = [
            ("Bias Corrector (Théo Strategy)", self.bias_corrector),
            ("Favorite-Longshot Adjuster", self.flb_adjuster),
            ("Risk-Free Rate Adjuster (Domer)", self.rfr_adjuster),
            ("Dutch Book Detector", self.dutchbook),
            ("Spatial Arbitrage Detector", self.spatial_arb),
            ("Risk Management", self.risk_management),
            ("Data Refresh Intervals", self.data_refresh),
            ("Signal Filters", self.signal_filter),
        ]

        for section_name, section_params in sections:
            print(f"\n{section_name}:")
            print("-" * 80)
            for key, value in section_params.__dict__.items():
                print(f"  {key}: {value}")


# Create a global default instance
default_parameters = OracleParameters()


# Example usage and testing
if __name__ == "__main__":
    print("Oracle Parameters Module - Example Usage\n")

    # Create parameters instance
    params = OracleParameters()

    # Print summary
    params.print_summary()

    # Modify a parameter
    print("\n" + "=" * 80)
    print("Modifying risk-free rate to 4.5%...")
    params.rfr_adjuster.risk_free_rate = 0.045
    print(f"New RFR: {params.rfr_adjuster.risk_free_rate:.2%}")

    # Save to file
    print("\nSaving parameters to file...")
    params.save_to_file('/tmp/oracle_params.json')
    print("✅ Saved to /tmp/oracle_params.json")

    # Load from file
    print("\nLoading parameters from file...")
    loaded_params = OracleParameters.load_from_file('/tmp/oracle_params.json')
    print(f"Loaded RFR: {loaded_params.rfr_adjuster.risk_free_rate:.2%}")
