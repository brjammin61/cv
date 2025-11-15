"""
Module 1: BiasCorrector (Théo Strategy)

Implements the "Neighbor Method" to correct raw polling data for
social desirability bias (e.g., "Shy Voter" effect).

The core thesis is that respondents project their own "shy"
preferences onto their neighbors. The delta between "neighbor"
and "self" preference is the "Shy Voter Index," which we use
to adjust the base probability.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BiasCorrector:
    """
    Corrects polling data for social desirability bias using the Neighbor Method.

    This class implements the strategy used by the "Trump Whale" (Théo) who made
    $50M+ by recognizing that traditional polls undercount support for socially
    controversial candidates.
    """

    def __init__(self, shy_voter_weight: float = 0.75):
        """
        Initializes the corrector model.

        Args:
            shy_voter_weight (float): How much to trust the "shy_index" delta.
                A value of 1.0 would mean you trust the neighbor poll
                *completely*. A value of 0.75 (default) is a more
                conservative blend, trusting 75% of the observed gap.

        Raises:
            ValueError: If shy_voter_weight is not between 0.0 and 1.0
        """
        if not 0.0 <= shy_voter_weight <= 1.0:
            raise ValueError("shy_voter_weight must be between 0.0 and 1.0")

        self.shy_voter_weight = shy_voter_weight
        logger.info(f"BiasCorrector initialized with shy_voter_weight={self.shy_voter_weight:.2%}")

    def calculate_fair_value(
        self,
        self_pref: float,
        neighbor_pref: float,
        market_name: Optional[str] = None
    ) -> float:
        """
        Calculates the bias-corrected fair value probability.

        Args:
            self_pref (float): The raw, uncorrected poll (e.g., 0.48 for 48%).
                               Represents the "Who will *you* vote for?" result.
            neighbor_pref (float): The "neighbor" poll (e.g., 0.52 for 52%).
                                   Represents the "Who do you think your
                                   *neighbors* will vote for?" result.
            market_name (str, optional): Market name for logging purposes.

        Returns:
            float: The adjusted "Fair Value" probability, bounded between 0.0 and 1.0.

        Raises:
            ValueError: If self_pref or neighbor_pref are not between 0.0 and 1.0
        """
        # Validate inputs
        if not (0.0 <= self_pref <= 1.0):
            raise ValueError(f"self_pref must be between 0.0 and 1.0, got {self_pref}")
        if not (0.0 <= neighbor_pref <= 1.0):
            raise ValueError(f"neighbor_pref must be between 0.0 and 1.0, got {neighbor_pref}")

        # 1. Calculate the Shy Voter Index
        # This is the "hidden" support we've found.
        shy_index = neighbor_pref - self_pref

        # 2. Determine the base probability
        # We use the 'self_pref' as the starting point.
        base_probability = self_pref

        # 3. Calculate the adjustment
        # We apply our weight to the shy_index to get the
        # actual adjustment we'll make.
        adjustment = shy_index * self.shy_voter_weight

        # 4. Calculate the new Fair Value
        fair_value = base_probability + adjustment

        # 5. Bound the result (clamp between 0.0 and 1.0)
        # A probability can't be > 100% or < 0%.
        fair_value_clamped = max(0.0, min(1.0, fair_value))

        if fair_value != fair_value_clamped:
            logger.warning(
                f"Fair value {fair_value:.4f} was outside bounds. "
                f"Clamped to {fair_value_clamped:.4f}."
            )

        log_msg = (
            f"BiasCorrector [{market_name or 'Unknown'}]: "
            f"Self={self_pref:.3f}, Neighbor={neighbor_pref:.3f} -> "
            f"ShyIndex={shy_index:.3f}, Adj={adjustment:.3f} -> "
            f"FAIR VALUE={fair_value_clamped:.3f}"
        )
        logger.info(log_msg)

        return fair_value_clamped

    def get_analysis(
        self,
        self_pref: float,
        neighbor_pref: float,
        market_name: Optional[str] = None
    ) -> dict:
        """
        Get a complete analysis including fair value and component breakdown.

        Args:
            self_pref (float): Self-preference polling data
            neighbor_pref (float): Neighbor-preference polling data
            market_name (str, optional): Market name for reference

        Returns:
            dict: Complete analysis with fair_value, shy_index, adjustment, etc.
        """
        shy_index = neighbor_pref - self_pref
        adjustment = shy_index * self.shy_voter_weight
        fair_value = self.calculate_fair_value(self_pref, neighbor_pref, market_name)

        return {
            'market_name': market_name,
            'self_preference': self_pref,
            'neighbor_preference': neighbor_pref,
            'shy_voter_index': shy_index,
            'adjustment': adjustment,
            'fair_value': fair_value,
            'shy_voter_weight': self.shy_voter_weight
        }


# Example usage and testing
if __name__ == "__main__":
    # Set up logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("BiasCorrector Module - Example Usage")
    print("=" * 80)

    corrector = BiasCorrector(shy_voter_weight=0.75)

    # SCENARIO 1: The "Shy Trump Voter" Example
    print("\n--- SCENARIO 1: 'Shy' Candidate ---")
    self_poll = 0.48  # 48% in "self" polls
    neighbor_poll = 0.52  # 52% in "neighbor" polls

    fair_value = corrector.calculate_fair_value(
        self_poll,
        neighbor_poll,
        market_name="Will Trump win?"
    )

    print(f"\nRaw 'Self' Poll: {self_poll * 100:.1f}%")
    print(f"Model Fair Value: {fair_value * 100:.1f}%")

    market_price = 0.48
    edge = fair_value - market_price

    print(f"Market Price: {market_price * 100:.1f} cents")
    print(f"Calculated Edge: {edge * 100:+.1f} cents")
    if edge > 0:
        print("✅ SIGNAL: BUY. Market is underpricing this asset.")

    # SCENARIO 2: No "Shy" Effect
    print("\n--- SCENARIO 2: No 'Shy' Effect ---")
    self_poll_2 = 0.55
    neighbor_poll_2 = 0.55

    fair_value_2 = corrector.calculate_fair_value(
        self_poll_2,
        neighbor_poll_2,
        market_name="Standard candidate"
    )

    print(f"Raw 'Self' Poll: {self_poll_2 * 100:.1f}%")
    print(f"Model Fair Value: {fair_value_2 * 100:.1f}%")

    market_price_2 = 0.55
    edge_2 = fair_value_2 - market_price_2
    print(f"Market Price: {market_price_2 * 100:.1f} cents")
    print(f"Calculated Edge: {edge_2 * 100:+.1f} cents")
    print("⏸️  SIGNAL: HOLD. Market price is efficient.")

    # SCENARIO 3: Full analysis
    print("\n--- SCENARIO 3: Full Analysis ---")
    analysis = corrector.get_analysis(0.48, 0.53, "Example Market")
    print("\nDetailed Analysis:")
    for key, value in analysis.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
