"""
Module 4: DutchBookDetector (Arbitrage)

Implements a "Dutch Book" arbitrage detector.

This module scans markets with multiple mutually exclusive
outcomes (e.g., candidates for a primary) to check if the
sum of their prices deviates from 1.00, creating risk-free
arbitrage opportunities.
"""

import logging
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)


class DutchBookDetector:
    """
    Detects Dutch Book arbitrage opportunities in combinatorial markets.

    When the sum of all mutually exclusive outcome prices deviates from $1.00,
    there is a risk-free profit opportunity.
    """

    def __init__(self, transaction_fee_per_share: float = 0.005):
        """
        Initializes the detector.

        Args:
            transaction_fee_per_share (float): The cost (fees, gas, slippage)
                per share. A 0.5 cent fee would be 0.005. We must ensure
                our profit is greater than our costs.

        Raises:
            ValueError: If fee is negative
        """
        if transaction_fee_per_share < 0:
            raise ValueError("Transaction fee cannot be negative")

        self.transaction_fee_per_share = transaction_fee_per_share
        logger.info(
            f"DutchBook Detector initialized. "
            f"Fee per share: {transaction_fee_per_share*100:.2f} cents"
        )

    def find_arbitrage(
        self,
        market_prices: Dict[str, float],
        market_name: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Analyzes a dictionary of market prices to find a Dutch Book.

        Args:
            market_prices (Dict[str, float]): A dictionary where the
                key is the outcome (e.g., "Trump", "DeSantis") and
                the value is the *current "Yes" price* (e.g., 0.45).
            market_name (str, optional): Market name for logging

        Returns:
            tuple: (SIGNAL_TYPE, RATIONALE)
                   e.g., ("BUY_ALL", "Under-round profit of 2.5 cents detected.")

        Raises:
            ValueError: If market_prices is empty or has invalid values
        """
        if not market_prices or len(market_prices) < 2:
            return ("NONE", "Not a combinatorial market (need at least 2 outcomes).")

        # Validate all prices
        for outcome, price in market_prices.items():
            if not (0.0 <= price <= 1.0):
                raise ValueError(
                    f"Invalid price for '{outcome}': {price}. Must be between 0.0 and 1.0"
                )

        # 1. Sum the prices of all outcomes
        price_sum = sum(market_prices.values())

        # 2. Calculate the total transaction cost for the entire book
        # We pay a fee for *each* contract we buy or sell.
        num_contracts = len(market_prices)
        total_fees = num_contracts * self.transaction_fee_per_share

        # 3. Check for an "Under-round" (Risk-Free BUY)
        # This is when the sum of prices is *less* than $1.00.
        # We can buy the whole set for less than $1.
        profit_margin_under = 1.00 - price_sum
        net_profit_under = profit_margin_under - total_fees

        if net_profit_under > 0:
            rationale = (
                f"UNDER-ROUND DETECTED. Sum={price_sum:.4f}. "
                f"Gross Profit={profit_margin_under*100:.2f}c. "
                f"Net Profit (after {total_fees*100:.2f}c fees) = {net_profit_under*100:.2f}c. "
                f"ACTION: Buy 'Yes' on all {num_contracts} outcomes."
            )

            log_msg = f"DutchBook [{market_name or 'Unknown'}]: UNDER-ROUND -> {rationale}"
            logger.info(log_msg)

            return ("BUY_ALL", rationale)

        # 4. Check for an "Over-round" (Risk-Free SELL)
        # This is when the sum of prices is *more* than $1.00.
        # We can sell the whole set for more than $1.
        profit_margin_over = price_sum - 1.00
        net_profit_over = profit_margin_over - total_fees

        if net_profit_over > 0:
            rationale = (
                f"OVER-ROUND DETECTED. Sum={price_sum:.4f}. "
                f"Gross Profit={profit_margin_over*100:.2f}c. "
                f"Net Profit (after {total_fees*100:.2f}c fees) = {net_profit_over*100:.2f}c. "
                f"ACTION: Sell 'Yes' on all {num_contracts} outcomes."
            )

            log_msg = f"DutchBook [{market_name or 'Unknown'}]: OVER-ROUND -> {rationale}"
            logger.info(log_msg)

            return ("SELL_ALL", rationale)

        # 5. No arbitrage found
        efficiency_msg = f"Market is efficient. Price sum={price_sum:.4f}. No profit after fees."

        log_msg = f"DutchBook [{market_name or 'Unknown'}]: HOLD -> {efficiency_msg}"
        logger.debug(log_msg)

        return ("HOLD", efficiency_msg)

    def get_full_analysis(
        self,
        market_prices: Dict[str, float],
        market_name: Optional[str] = None
    ) -> Dict:
        """
        Get complete Dutch Book analysis with all metrics.

        Args:
            market_prices (Dict[str, float]): Outcome prices
            market_name (str, optional): Market name for reference

        Returns:
            dict: Complete analysis including signal, profits, outcomes breakdown
        """
        if not market_prices or len(market_prices) < 2:
            return {
                'market_name': market_name,
                'is_valid': False,
                'error': 'Not a combinatorial market (need at least 2 outcomes)',
                'num_outcomes': len(market_prices)
            }

        price_sum = sum(market_prices.values())
        num_contracts = len(market_prices)
        total_fees = num_contracts * self.transaction_fee_per_share

        # Calculate both scenarios
        profit_margin_under = 1.00 - price_sum
        net_profit_under = profit_margin_under - total_fees

        profit_margin_over = price_sum - 1.00
        net_profit_over = profit_margin_over - total_fees

        signal, rationale = self.find_arbitrage(market_prices, market_name)

        # Determine market efficiency
        deviation_from_fair = abs(price_sum - 1.00)
        is_efficient = (net_profit_under <= 0 and net_profit_over <= 0)

        # Create outcome breakdown
        outcomes_sorted = sorted(
            market_prices.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            'market_name': market_name,
            'is_valid': True,
            'num_outcomes': num_contracts,
            'price_sum': price_sum,
            'deviation_from_fair': deviation_from_fair,
            'deviation_cents': deviation_from_fair * 100,
            'is_efficient': is_efficient,
            'total_fees': total_fees,
            'total_fees_cents': total_fees * 100,
            'under_round': {
                'gross_profit': profit_margin_under,
                'net_profit': net_profit_under,
                'gross_profit_cents': profit_margin_under * 100,
                'net_profit_cents': net_profit_under * 100,
                'profitable': net_profit_under > 0
            },
            'over_round': {
                'gross_profit': profit_margin_over,
                'net_profit': net_profit_over,
                'gross_profit_cents': profit_margin_over * 100,
                'net_profit_cents': net_profit_over * 100,
                'profitable': net_profit_over > 0
            },
            'signal': signal,
            'rationale': rationale,
            'outcomes': outcomes_sorted,
            'fee_per_share': self.transaction_fee_per_share
        }

    def get_position_sizes(
        self,
        market_prices: Dict[str, float],
        total_capital: float,
        market_name: Optional[str] = None
    ) -> Optional[Dict[str, float]]:
        """
        Calculate exact position sizes for executing a Dutch Book arbitrage.

        Args:
            market_prices (Dict[str, float]): Outcome prices
            total_capital (float): Total capital to deploy
            market_name (str, optional): Market name for logging

        Returns:
            Dict[str, float] or None: Position sizes for each outcome, or None if no arb
        """
        signal, _ = self.find_arbitrage(market_prices, market_name)

        if signal not in ["BUY_ALL", "SELL_ALL"]:
            return None

        # For Dutch Book, we want equal exposure on all outcomes
        # Total shares = capital / average_price (for BUY_ALL)
        # For SELL_ALL, we're collecting premium

        num_outcomes = len(market_prices)
        capital_per_outcome = total_capital / num_outcomes

        positions = {}
        for outcome, price in market_prices.items():
            if signal == "BUY_ALL":
                # Calculate shares to buy
                shares = capital_per_outcome / price if price > 0 else 0
                positions[outcome] = shares
            elif signal == "SELL_ALL":
                # Calculate shares to sell (collect premium)
                shares = capital_per_outcome / (1.0 - price) if price < 1.0 else 0
                positions[outcome] = shares

        return positions


# Example usage and testing
if __name__ == "__main__":
    # Set up logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("DutchBookDetector Module - Example Usage")
    print("=" * 80)

    # Fees are 0.5 cents ($0.005) per trade.
    detector = DutchBookDetector(transaction_fee_per_share=0.005)

    # SCENARIO 1: "Under-round" (BUY Signal)
    print("\n--- SCENARIO 1: 'Under-round' BUY Signal ---")
    under_round_market = {
        "Candidate A": 0.40,
        "Candidate B": 0.30,
        "Candidate C": 0.25,  # Total Sum = 0.95
    }

    signal, rationale = detector.find_arbitrage(
        under_round_market,
        "2028 Republican Primary"
    )
    print(f"SIGNAL: {signal}")
    print(f"Rationale: {rationale}")

    # Calculate position sizes
    positions = detector.get_position_sizes(under_round_market, 1000.0)
    if positions:
        print("\nPosition Sizes (for $1000 deployment):")
        for outcome, shares in positions.items():
            print(f"  {outcome}: {shares:.2f} shares")

    # SCENARIO 2: "Over-round" (SELL Signal)
    print("\n--- SCENARIO 2: 'Over-round' SELL Signal ---")
    over_round_market = {
        "Candidate A": 0.55,
        "Candidate B": 0.30,
        "Candidate C": 0.20,  # Total Sum = 1.05
    }

    signal, rationale = detector.find_arbitrage(
        over_round_market,
        "2028 Democratic Primary"
    )
    print(f"SIGNAL: {signal}")
    print(f"Rationale: {rationale}")

    # SCENARIO 3: Efficient Market (HOLD Signal)
    print("\n--- SCENARIO 3: Efficient Market (No Profit) ---")
    efficient_market = {
        "Candidate A": 0.50,
        "Candidate B": 0.30,
        "Candidate C": 0.19,  # Total Sum = 0.99 (but fees make it unprofitable)
    }

    signal, rationale = detector.find_arbitrage(
        efficient_market,
        "Efficient Market Example"
    )
    print(f"SIGNAL: {signal}")
    print(f"Rationale: {rationale}")

    # SCENARIO 4: Full analysis
    print("\n--- SCENARIO 4: Full Analysis ---")
    analysis = detector.get_full_analysis(under_round_market, "Example Market")
    print("\nDetailed Analysis:")
    for key, value in analysis.items():
        if key == 'outcomes':
            print(f"  {key}:")
            for outcome, price in value:
                print(f"    {outcome}: {price:.4f}")
        elif isinstance(value, dict):
            print(f"  {key}:")
            for subkey, subval in value.items():
                if isinstance(subval, float):
                    print(f"    {subkey}: {subval:.4f}")
                else:
                    print(f"    {subkey}: {subval}")
        elif isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
