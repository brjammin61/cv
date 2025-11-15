"""
Module 3: RiskFreeRateAdjuster (Domer Strategy)

Implements the "Domer" strategy by treating long-duration prediction
market contracts as zero-coupon bonds.

It calculates the "Time-Adjusted Fair Value" of a contract to
determine if its yield (implied return) is better or worse
than the risk-free rate (e.g., Treasury yields or DeFi lending).
"""

import logging
from datetime import datetime, date
from typing import Tuple, Optional, Dict

logger = logging.getLogger(__name__)


class RiskFreeRateAdjuster:
    """
    Treats prediction market contracts as bonds and compares their yields.

    This class implements the "Domer" strategy of analyzing long-duration
    contracts through the lens of time value of money.
    """

    def __init__(self, risk_free_rate: float):
        """
        Initializes the adjuster.

        Args:
            risk_free_rate (float): The *annual* risk-free rate to
                                    benchmark against (e.g., 0.05 for 5%).

        Raises:
            ValueError: If risk_free_rate is negative
        """
        if risk_free_rate < 0:
            raise ValueError("Risk-free rate cannot be negative.")

        self.risk_free_rate = risk_free_rate
        logger.info(
            f"RFR Adjuster initialized with annual rate={self.risk_free_rate * 100:.2f}%"
        )

    def get_time_adjusted_fair_value(
        self,
        market_price: float,
        resolution_date: date,
        market_name: Optional[str] = None
    ) -> Tuple[float, float]:
        """
        Calculates the "Time-Adjusted Fair Value" (TA-FV) of a contract.
        This is the "breakeven" price to pay *today* for a $1.00 payout
        in the future, discounted by the risk-free rate.

        Args:
            market_price (float): The current price of the "Yes" share.
            resolution_date (date): The date the contract resolves.
            market_name (str, optional): Market name for logging

        Returns:
            tuple: (time_adjusted_fair_value, implied_yield)
                   - time_adjusted_fair_value (float): The discounted present value.
                   - implied_yield (float): The annualized yield the market price implies.

        Raises:
            ValueError: If market_price is not between 0.0 and 1.0
        """
        # Validate inputs
        if not (0.0 < market_price <= 1.0):
            raise ValueError(f"market_price must be between 0.0 and 1.0, got {market_price}")

        # 1. Calculate days until resolution
        days_to_resolution = (resolution_date - date.today()).days

        if days_to_resolution <= 0:
            # Contract resolves today or in the past. Time value is irrelevant.
            logger.warning(
                f"RFR Adjuster [{market_name or 'Unknown'}]: "
                f"Resolution date is in the past or today. Returning market price."
            )
            return (market_price, float('inf'))

        # 2. Calculate the fraction of a year
        years_to_resolution = days_to_resolution / 365.25

        # 3. Calculate Time-Adjusted Fair Value (Present Value)
        # This is the "no-arbitrage" price.
        # Formula: PV = FV / (1 + r)^t
        time_adjusted_fair_value = 1.0 / (1 + self.risk_free_rate) ** years_to_resolution

        # 4. Calculate the Implied Yield of the *current market price*
        # This tells us what return the market is offering.
        # Formula: Yield = (FV / PV)^(1/t) - 1
        if market_price <= 0:
            implied_yield = float('inf')  # Avoid division by zero
        else:
            implied_yield = (1.0 / market_price) ** (1 / years_to_resolution) - 1

        log_msg = (
            f"RFR Adjuster [{market_name or 'Unknown'}]: "
            f"MP={market_price:.3f}, Days={days_to_resolution}, "
            f"TA-FV={time_adjusted_fair_value:.4f}, "
            f"ImpliedYield={implied_yield:.2%}, RFR={self.risk_free_rate:.2%}"
        )
        logger.info(log_msg)

        return (time_adjusted_fair_value, implied_yield)

    def get_time_value_signal(
        self,
        market_price: float,
        resolution_date: date,
        market_name: Optional[str] = None,
        min_probability: float = 0.80
    ) -> Tuple[str, str]:
        """
        Generates an actionable signal based on time value.

        Args:
            market_price (float): The current price of the "Yes" share.
            resolution_date (date): The date the contract resolves.
            market_name (str, optional): Market name for logging
            min_probability (float): Minimum probability for time-value analysis

        Returns:
            tuple: (SIGNAL_TYPE, RATIONALE)
        """
        # We only care about this model for "near-certainty" bets.
        # If a bet is 50/50, probability risk swamps time risk.
        if market_price < min_probability:
            return (
                "HOLD",
                f"Probability risk is too high (MP={market_price:.1%} < {min_probability:.1%}). "
                f"Time-value is not the primary factor."
            )

        ta_fv, implied_yield = self.get_time_adjusted_fair_value(
            market_price,
            resolution_date,
            market_name
        )

        # Handle edge case of past/current resolution
        if implied_yield == float('inf'):
            return ("HOLD", "Contract resolves today or has passed. No time value.")

        yield_delta = implied_yield - self.risk_free_rate
        yield_delta_bps = yield_delta * 10000  # Convert to basis points

        if implied_yield < self.risk_free_rate:
            # The market is paying you *less* than a savings account.
            # The price is too high. This is a "SELL" signal.
            return (
                "SELL",
                f"Implied Yield ({implied_yield:.2%}) is {abs(yield_delta_bps):.0f}bps "
                f"BELOW risk-free rate ({self.risk_free_rate:.2%}). "
                f"Market price ({market_price:.3f}) is OVERVALUED. "
                f"Time-Adjusted Fair Value is {ta_fv:.3f}."
            )
        elif implied_yield > self.risk_free_rate:
            # The market is paying you *more* than a savings account
            # for a perceived "sure thing." This is a "BUY" signal.
            return (
                "BUY",
                f"Implied Yield ({implied_yield:.2%}) is {yield_delta_bps:.0f}bps "
                f"ABOVE risk-free rate ({self.risk_free_rate:.2%}). "
                f"Market price ({market_price:.3f}) is UNDERVALUED. "
                f"Time-Adjusted Fair Value is {ta_fv:.3f}."
            )
        else:
            return (
                "HOLD",
                f"Implied Yield ({implied_yield:.2%}) matches risk-free rate. Fair value."
            )

    def get_full_analysis(
        self,
        market_price: float,
        resolution_date: date,
        market_name: Optional[str] = None,
        min_probability: float = 0.80
    ) -> Dict:
        """
        Get complete time-value analysis with all metrics.

        Args:
            market_price (float): Current market price
            resolution_date (date): Resolution date
            market_name (str, optional): Market name for reference
            min_probability (float): Minimum probability threshold

        Returns:
            dict: Complete analysis including yields, signals, etc.
        """
        days_to_resolution = (resolution_date - date.today()).days
        years_to_resolution = days_to_resolution / 365.25 if days_to_resolution > 0 else 0

        ta_fv, implied_yield = self.get_time_adjusted_fair_value(
            market_price,
            resolution_date,
            market_name
        )

        signal, rationale = self.get_time_value_signal(
            market_price,
            resolution_date,
            market_name,
            min_probability
        )

        # Calculate profit metrics
        profit_if_win = 1.0 - market_price
        profit_percent = (profit_if_win / market_price * 100) if market_price > 0 else 0
        annualized_return = implied_yield * 100 if implied_yield != float('inf') else float('inf')

        return {
            'market_name': market_name,
            'market_price': market_price,
            'resolution_date': resolution_date,
            'days_to_resolution': days_to_resolution,
            'years_to_resolution': years_to_resolution,
            'time_adjusted_fair_value': ta_fv,
            'implied_yield': implied_yield,
            'implied_yield_percent': annualized_return,
            'risk_free_rate': self.risk_free_rate,
            'risk_free_rate_percent': self.risk_free_rate * 100,
            'yield_advantage_bps': (implied_yield - self.risk_free_rate) * 10000,
            'profit_if_win': profit_if_win,
            'profit_percent': profit_percent,
            'signal': signal,
            'rationale': rationale,
            'applicable': market_price >= min_probability
        }


# Example usage and testing
if __name__ == "__main__":
    # Set up logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("RiskFreeRateAdjuster Module - Example Usage")
    print("=" * 80)

    # Assume RFR is 5% (current T-bill rates)
    rfr_adjuster = RiskFreeRateAdjuster(risk_free_rate=0.05)

    # SCENARIO 1: The "Bad Bond" (Domer SELL Signal)
    print("\n--- SCENARIO 1: 'Bad Bond' SELL Signal ---")
    market_price_1 = 0.98
    resolve_date_1 = date(2026, 11, 15)  # One year from now

    signal, rationale = rfr_adjuster.get_time_value_signal(
        market_price_1,
        resolve_date_1,
        "Sure Thing - 1 Year"
    )

    print(f"Market Price: {market_price_1:.1%}")
    print(f"Resolution Date: {resolve_date_1}")
    print(f"SIGNAL: {signal}")
    print(f"Rationale: {rationale}")

    # SCENARIO 2: The "Good Bond" (Domer BUY Signal)
    print("\n--- SCENARIO 2: 'Good Bond' BUY Signal ---")
    market_price_2 = 0.95
    resolve_date_2 = date(2026, 5, 15)  # Six months from now

    signal, rationale = rfr_adjuster.get_time_value_signal(
        market_price_2,
        resolve_date_2,
        "High Probability - 6 Months"
    )

    print(f"Market Price: {market_price_2:.1%}")
    print(f"Resolution Date: {resolve_date_2}")
    print(f"SIGNAL: {signal}")
    print(f"Rationale: {rationale}")

    # SCENARIO 3: Probability Bet (Model ignores)
    print("\n--- SCENARIO 3: Probability Bet (RFR Not Applicable) ---")
    signal, rationale = rfr_adjuster.get_time_value_signal(
        0.50,
        resolve_date_1,
        "50/50 Election"
    )
    print(f"SIGNAL: {signal}")
    print(f"Rationale: {rationale}")

    # SCENARIO 4: Full analysis
    print("\n--- SCENARIO 4: Full Analysis ---")
    analysis = rfr_adjuster.get_full_analysis(
        0.92,
        date(2027, 1, 1),
        "Long-Duration High Probability"
    )
    print("\nDetailed Analysis:")
    for key, value in analysis.items():
        if isinstance(value, float) and value != float('inf'):
            print(f"  {key}: {value:.4f}")
        elif isinstance(value, date):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")
