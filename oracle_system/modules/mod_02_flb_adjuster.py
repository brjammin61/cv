"""
Module 2: FavoriteLongshotAdjuster (Conviction Layer)

Implements the Favorite-Longshot Bias as a "Conviction Layer."

This module does *not* change the Fair Value. Instead, it advises
on the *quality* of the trading signal by comparing the model's
Fair Value against the known market tendency to:
1. UNDER-price heavy favorites (e.g., 90% chance trades at 88 cents)
2. OVER-price longshots (e.g., 10% chance trades at 12 cents)
"""

import logging
from typing import Tuple, Optional, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class ConvictionLevel(Enum):
    """Enum for signal conviction levels."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SignalDirection(Enum):
    """Enum for signal direction."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class FavoriteLongshotAdjuster:
    """
    Implements the Favorite-Longshot Bias as a conviction layer.

    This class helps identify HIGH-CONVICTION trades by recognizing when
    your signal aligns with (or fights against) the market's known biases.
    """

    def __init__(
        self,
        favorite_threshold: float = 0.80,
        longshot_threshold: float = 0.20
    ):
        """
        Initializes the adjuster.

        Args:
            favorite_threshold (float): Price above which we consider
                                        an asset a "Favorite."
            longshot_threshold (float): Price below which we consider
                                        an asset a "Longshot."

        Raises:
            ValueError: If thresholds are invalid
        """
        if not (0.0 < longshot_threshold < favorite_threshold < 1.0):
            raise ValueError(
                f"Invalid thresholds: longshot ({longshot_threshold}) must be < "
                f"favorite ({favorite_threshold}), both between 0 and 1"
            )

        self.fav_thresh = favorite_threshold
        self.long_thresh = longshot_threshold
        logger.info(
            f"FLB Adjuster initialized (Favorite: {self.fav_thresh*100:.0f}%, "
            f"Longshot: {self.long_thresh*100:.0f}%)"
        )

    def analyze_conviction(
        self,
        fair_value: float,
        market_price: float,
        market_name: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Analyzes the conviction of a trade based on Fair Value and Market Price.

        Args:
            fair_value (float): The "true" probability from the BiasCorrector.
            market_price (float): The current live price on the exchange.
            market_name (str, optional): Market name for logging

        Returns:
            tuple: (CONVICTION_LEVEL, RATIONALE)
                   e.g., ("HIGH", "Signal enhanced: Market is underpricing a 'Favorite'.")

        Raises:
            ValueError: If inputs are not between 0.0 and 1.0
        """
        # Validate inputs
        if not (0.0 <= fair_value <= 1.0):
            raise ValueError(f"fair_value must be between 0.0 and 1.0, got {fair_value}")
        if not (0.0 <= market_price <= 1.0):
            raise ValueError(f"market_price must be between 0.0 and 1.0, got {market_price}")

        # Calculate the edge. Positive edge means BUY, negative edge means SELL.
        edge = fair_value - market_price

        conviction = ConvictionLevel.NONE
        rationale = ""
        direction = SignalDirection.HOLD

        if edge > 0:
            # --- SIGNAL IS TO "BUY" (Market price is < Fair Value) ---
            direction = SignalDirection.BUY

            if fair_value >= self.fav_thresh:
                # We are buying a Favorite.
                # The market bias is to UNDER-price favorites.
                # This signal is AMPLIFIED by the bias.
                conviction = ConvictionLevel.HIGH
                rationale = "Signal Enhanced: Buying an underpriced 'Favorite'."

            elif fair_value <= self.long_thresh:
                # We are buying a Longshot.
                # The market bias is to OVER-price longshots.
                # Our model is fighting the known market bias.
                conviction = ConvictionLevel.LOW
                rationale = "Signal Warning: Buying a 'Longshot'. Market bias is to overprice these."

            else:
                conviction = ConvictionLevel.MEDIUM
                rationale = "Signal is to BUY. No strong FLB influence."

        elif edge < 0:
            # --- SIGNAL IS TO "SELL" (Market price is > Fair Value) ---
            direction = SignalDirection.SELL

            if fair_value <= self.long_thresh:
                # We are selling a Longshot.
                # The market bias is to OVER-price longshots.
                # This signal is AMPLIFIED by the bias.
                conviction = ConvictionLevel.HIGH
                rationale = "Signal Enhanced: Selling an overpriced 'Longshot'."

            elif fair_value >= self.fav_thresh:
                # We are selling a Favorite.
                # The market bias is to UNDER-price favorites.
                # Our model is fighting the known market bias.
                conviction = ConvictionLevel.LOW
                rationale = "Signal Warning: Selling a 'Favorite'. Market bias is to underprice these."

            else:
                conviction = ConvictionLevel.MEDIUM
                rationale = "Signal is to SELL. No strong FLB influence."

        else:
            # Edge is zero.
            conviction = ConvictionLevel.NONE
            direction = SignalDirection.HOLD
            rationale = "No edge detected. Market is efficient."

        log_msg = (
            f"FLB Adjuster [{market_name or 'Unknown'}]: "
            f"FV={fair_value:.3f}, MP={market_price:.3f}, Edge={edge:.3f} -> "
            f"{direction.value} {conviction.value}"
        )
        logger.info(log_msg)

        return (conviction.value, rationale)

    def get_full_analysis(
        self,
        fair_value: float,
        market_price: float,
        market_name: Optional[str] = None
    ) -> Dict:
        """
        Get complete analysis with all metrics.

        Args:
            fair_value (float): Model's calculated fair value
            market_price (float): Current market price
            market_name (str, optional): Market name for reference

        Returns:
            dict: Complete analysis including conviction, direction, edge, etc.
        """
        edge = fair_value - market_price
        conviction, rationale = self.analyze_conviction(fair_value, market_price, market_name)

        # Determine asset type
        asset_type = "Mid-Range"
        if fair_value >= self.fav_thresh:
            asset_type = "Favorite"
        elif fair_value <= self.long_thresh:
            asset_type = "Longshot"

        # Determine direction
        if edge > 0:
            direction = "BUY"
        elif edge < 0:
            direction = "SELL"
        else:
            direction = "HOLD"

        return {
            'market_name': market_name,
            'fair_value': fair_value,
            'market_price': market_price,
            'edge': edge,
            'edge_cents': edge * 100,
            'direction': direction,
            'conviction': conviction,
            'rationale': rationale,
            'asset_type': asset_type,
            'favorite_threshold': self.fav_thresh,
            'longshot_threshold': self.long_thresh
        }


# Example usage and testing
if __name__ == "__main__":
    # Set up logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("FavoriteLongshotAdjuster Module - Example Usage")
    print("=" * 80)

    adjuster = FavoriteLongshotAdjuster(
        favorite_threshold=0.80,
        longshot_threshold=0.20
    )

    # SCENARIO 1: HIGH-CONVICTION BUY (Underpriced Favorite)
    print("\n--- SCENARIO 1: HIGH-CONVICTION BUY (Underpriced Favorite) ---")
    fair_value_1 = 0.92  # Our model says 92%
    market_price_1 = 0.88  # Market only pricing at 88%

    conviction, rationale = adjuster.analyze_conviction(
        fair_value_1,
        market_price_1,
        "Trump 2028 Election"
    )

    print(f"Fair Value: {fair_value_1:.1%}")
    print(f"Market Price: {market_price_1:.1%}")
    print(f"Edge: {(fair_value_1 - market_price_1)*100:+.2f} cents")
    print(f"Conviction: {conviction}")
    print(f"Rationale: {rationale}")

    # SCENARIO 2: HIGH-CONVICTION SELL (Overpriced Longshot)
    print("\n--- SCENARIO 2: HIGH-CONVICTION SELL (Overpriced Longshot) ---")
    fair_value_2 = 0.10  # Our model says 10%
    market_price_2 = 0.15  # Market pricing at 15% (lottery ticket bias)

    conviction, rationale = adjuster.analyze_conviction(
        fair_value_2,
        market_price_2,
        "Unlikely Event"
    )

    print(f"Fair Value: {fair_value_2:.1%}")
    print(f"Market Price: {market_price_2:.1%}")
    print(f"Edge: {(fair_value_2 - market_price_2)*100:+.2f} cents")
    print(f"Conviction: {conviction}")
    print(f"Rationale: {rationale}")

    # SCENARIO 3: LOW-CONVICTION (Fighting the bias)
    print("\n--- SCENARIO 3: LOW-CONVICTION (Selling a Favorite - Dangerous!) ---")
    fair_value_3 = 0.90  # Model says 90%
    market_price_3 = 0.93  # Market at 93%

    conviction, rationale = adjuster.analyze_conviction(
        fair_value_3,
        market_price_3,
        "Heavy Favorite"
    )

    print(f"Fair Value: {fair_value_3:.1%}")
    print(f"Market Price: {market_price_3:.1%}")
    print(f"Edge: {(fair_value_3 - market_price_3)*100:+.2f} cents")
    print(f"Conviction: {conviction}")
    print(f"Rationale: {rationale}")
    print("⚠️  WARNING: This trade fights the FLB bias!")

    # SCENARIO 4: Full analysis
    print("\n--- SCENARIO 4: Full Analysis ---")
    analysis = adjuster.get_full_analysis(0.85, 0.80, "Example Favorite")
    print("\nDetailed Analysis:")
    for key, value in analysis.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
