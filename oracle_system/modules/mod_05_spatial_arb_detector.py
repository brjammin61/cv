"""
Module 5: SpatialArbitrageDetector (Cross-Venue Arbitrage)

Implements the "Spatial Arbitrage" (Cross-Venue) bot logic.

This module finds risk-free profit by identifying price discrepancies
for the *same market* between two different venues (Kalshi and Polymarket).
"""

import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class SpatialArbitrageDetector:
    """
    Detects spatial arbitrage opportunities across prediction market venues.

    Exploits the fragmented liquidity landscape between Kalshi (regulated, fiat)
    and Polymarket (crypto, global) to find risk-free cross-venue arbitrage.
    """

    def __init__(self, total_fee_cost: float = 0.02):
        """
        Initializes the detector.

        Args:
            total_fee_cost (float): The total, all-in cost (in dollars)
                to execute a full "buy-then-sell" arbitrage.
                This value *must* include:
                - Kalshi trading fees
                - Polymarket trading fees
                - Polymarket gas fees (amortized)
                - Any potential slippage

                Example: 0.02 represents an all-in cost of 2 cents.

        Raises:
            ValueError: If total_fee_cost is negative
        """
        if total_fee_cost < 0:
            raise ValueError("Total fee cost cannot be negative")

        self.total_fee_cost = total_fee_cost
        logger.info(
            f"Spatial Arbitrage Detector initialized. "
            f"All-in fee cost: {total_fee_cost*100:.1f} cents"
        )

    def find_arbitrage(
        self,
        kalshi_bid: float,
        kalshi_ask: float,
        poly_bid: float,
        poly_ask: float,
        market_name: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Analyzes the order books of both platforms to find a signal.

        Args:
            kalshi_bid (float): The best price to SELL "Yes" on Kalshi.
            kalshi_ask (float): The best price to BUY "Yes" on Kalshi.
            poly_bid (float): The best price to SELL "Yes" on Polymarket.
            poly_ask (float): The best price to BUY "Yes" on Polymarket.
            market_name (str, optional): Market name for logging

        Returns:
            tuple: (SIGNAL_TYPE, RATIONALE)
                   e.g., ("BUY_KALSHI_SELL_POLY", "Net profit of 2.5 cents.")

        Raises:
            ValueError: If any price is not between 0.0 and 1.0
        """
        # Validate inputs
        prices = {
            'kalshi_bid': kalshi_bid,
            'kalshi_ask': kalshi_ask,
            'poly_bid': poly_bid,
            'poly_ask': poly_ask
        }

        for name, price in prices.items():
            if not (0.0 <= price <= 1.0):
                raise ValueError(f"{name} must be between 0.0 and 1.0, got {price}")

        # Validate bid-ask spreads
        if kalshi_bid > kalshi_ask:
            raise ValueError(
                f"Invalid Kalshi spread: bid ({kalshi_bid}) > ask ({kalshi_ask})"
            )
        if poly_bid > poly_ask:
            raise ValueError(
                f"Invalid Polymarket spread: bid ({poly_bid}) > ask ({poly_ask})"
            )

        # --- Check Arb 1: Buy on Kalshi (pay ask), Sell on Polymarket (get bid) ---

        buy_price_1 = kalshi_ask
        sell_price_1 = poly_bid
        gross_spread_1 = sell_price_1 - buy_price_1
        net_profit_1 = gross_spread_1 - self.total_fee_cost

        if net_profit_1 > 0:
            rationale = (
                f"BUY Kalshi @ {buy_price_1:.3f}, SELL Polymarket @ {sell_price_1:.3f}. "
                f"Gross Spread: {gross_spread_1*100:.2f}c. "
                f"Net Profit: {net_profit_1*100:.2f}c."
            )

            log_msg = (
                f"Spatial Arb [{market_name or 'Unknown'}]: "
                f"BUY_KALSHI_SELL_POLY -> {rationale}"
            )
            logger.info(log_msg)

            return ("BUY_KALSHI_SELL_POLY", rationale)

        # --- Check Arb 2: Buy on Polymarket (pay ask), Sell on Kalshi (get bid) ---

        buy_price_2 = poly_ask
        sell_price_2 = kalshi_bid
        gross_spread_2 = sell_price_2 - buy_price_2
        net_profit_2 = gross_spread_2 - self.total_fee_cost

        if net_profit_2 > 0:
            rationale = (
                f"BUY Polymarket @ {buy_price_2:.3f}, SELL Kalshi @ {sell_price_2:.3f}. "
                f"Gross Spread: {gross_spread_2*100:.2f}c. "
                f"Net Profit: {net_profit_2*100:.2f}c."
            )

            log_msg = (
                f"Spatial Arb [{market_name or 'Unknown'}]: "
                f"BUY_POLY_SELL_KALSHI -> {rationale}"
            )
            logger.info(log_msg)

            return ("BUY_POLY_SELL_KALSHI", rationale)

        # --- No arbitrage found ---
        efficiency_msg = "No spatial arbitrage detected. Markets are efficient."

        log_msg = f"Spatial Arb [{market_name or 'Unknown'}]: HOLD -> {efficiency_msg}"
        logger.debug(log_msg)

        return ("HOLD", efficiency_msg)

    def get_full_analysis(
        self,
        kalshi_bid: float,
        kalshi_ask: float,
        poly_bid: float,
        poly_ask: float,
        market_name: Optional[str] = None
    ) -> Dict:
        """
        Get complete spatial arbitrage analysis with all metrics.

        Args:
            kalshi_bid (float): Kalshi best bid
            kalshi_ask (float): Kalshi best ask
            poly_bid (float): Polymarket best bid
            poly_ask (float): Polymarket best ask
            market_name (str, optional): Market name for reference

        Returns:
            dict: Complete analysis including both arb scenarios, spreads, etc.
        """
        # Calculate mid prices
        kalshi_mid = (kalshi_bid + kalshi_ask) / 2
        poly_mid = (poly_bid + poly_ask) / 2
        mid_price_delta = poly_mid - kalshi_mid

        # Calculate spreads
        kalshi_spread = kalshi_ask - kalshi_bid
        poly_spread = poly_ask - poly_bid

        # Calculate both arbitrage scenarios
        # Scenario 1: Buy Kalshi, Sell Poly
        buy_price_1 = kalshi_ask
        sell_price_1 = poly_bid
        gross_spread_1 = sell_price_1 - buy_price_1
        net_profit_1 = gross_spread_1 - self.total_fee_cost

        # Scenario 2: Buy Poly, Sell Kalshi
        buy_price_2 = poly_ask
        sell_price_2 = kalshi_bid
        gross_spread_2 = sell_price_2 - buy_price_2
        net_profit_2 = gross_spread_2 - self.total_fee_cost

        signal, rationale = self.find_arbitrage(
            kalshi_bid,
            kalshi_ask,
            poly_bid,
            poly_ask,
            market_name
        )

        # Determine which scenario is profitable
        arb_1_profitable = net_profit_1 > 0
        arb_2_profitable = net_profit_2 > 0
        any_arb_available = arb_1_profitable or arb_2_profitable

        return {
            'market_name': market_name,
            'kalshi': {
                'bid': kalshi_bid,
                'ask': kalshi_ask,
                'mid': kalshi_mid,
                'spread': kalshi_spread,
                'spread_cents': kalshi_spread * 100,
                'spread_bps': kalshi_spread * 10000
            },
            'polymarket': {
                'bid': poly_bid,
                'ask': poly_ask,
                'mid': poly_mid,
                'spread': poly_spread,
                'spread_cents': poly_spread * 100,
                'spread_bps': poly_spread * 10000
            },
            'price_comparison': {
                'mid_price_delta': mid_price_delta,
                'mid_price_delta_cents': mid_price_delta * 100,
                'poly_premium': mid_price_delta > 0,
                'kalshi_premium': mid_price_delta < 0
            },
            'scenario_1_buy_kalshi_sell_poly': {
                'buy_price': buy_price_1,
                'sell_price': sell_price_1,
                'gross_spread': gross_spread_1,
                'gross_spread_cents': gross_spread_1 * 100,
                'net_profit': net_profit_1,
                'net_profit_cents': net_profit_1 * 100,
                'profitable': arb_1_profitable
            },
            'scenario_2_buy_poly_sell_kalshi': {
                'buy_price': buy_price_2,
                'sell_price': sell_price_2,
                'gross_spread': gross_spread_2,
                'gross_spread_cents': gross_spread_2 * 100,
                'net_profit': net_profit_2,
                'net_profit_cents': net_profit_2 * 100,
                'profitable': arb_2_profitable
            },
            'arbitrage_available': any_arb_available,
            'total_fee_cost': self.total_fee_cost,
            'total_fee_cost_cents': self.total_fee_cost * 100,
            'signal': signal,
            'rationale': rationale
        }

    def calculate_position_size(
        self,
        signal: str,
        capital: float,
        kalshi_ask: float,
        poly_ask: float
    ) -> Optional[float]:
        """
        Calculate the optimal position size for a spatial arbitrage trade.

        Args:
            signal (str): The signal type from find_arbitrage
            capital (float): Available capital
            kalshi_ask (float): Kalshi ask price
            poly_ask (float): Polymarket ask price

        Returns:
            Optional[float]: Number of shares to trade, or None if no arb
        """
        if signal == "HOLD":
            return None

        # For spatial arb, we buy on one venue and sell on another
        # Position size is limited by the capital we can deploy
        if signal == "BUY_KALSHI_SELL_POLY":
            # We need to buy on Kalshi
            max_shares = capital / kalshi_ask if kalshi_ask > 0 else 0
        elif signal == "BUY_POLY_SELL_KALSHI":
            # We need to buy on Polymarket
            max_shares = capital / poly_ask if poly_ask > 0 else 0
        else:
            return None

        return max_shares


# Example usage and testing
if __name__ == "__main__":
    # Set up logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("SpatialArbitrageDetector Module - Example Usage")
    print("=" * 80)

    # Assume we've calculated our all-in costs (fees + gas) to be 1.5 cents.
    detector = SpatialArbitrageDetector(total_fee_cost=0.015)

    # SCENARIO 1: "Buy Kalshi" Signal
    print("\n--- SCENARIO 1: BUY Kalshi, SELL Polymarket ---")

    # "Will Trump win?"
    k_bid, k_ask = 0.50, 0.51  # Kalshi: 50-51c
    p_bid, p_ask = 0.53, 0.54  # Poly: 53-54c

    signal, rationale = detector.find_arbitrage(
        k_bid, k_ask, p_bid, p_ask,
        "Trump 2028 Election"
    )
    print(f"SIGNAL: {signal}")
    print(f"Rationale: {rationale}")

    # Calculate position size
    position_size = detector.calculate_position_size(signal, 1000.0, k_ask, p_ask)
    if position_size:
        print(f"Position Size (with $1000): {position_size:.2f} shares")

    # SCENARIO 2: "Buy Polymarket" Signal
    print("\n--- SCENARIO 2: BUY Polymarket, SELL Kalshi ---")

    # "Will Fed cut rates?"
    k_bid, k_ask = 0.70, 0.71  # Kalshi: 70-71c
    p_bid, p_ask = 0.65, 0.66  # Poly: 65-66c

    signal, rationale = detector.find_arbitrage(
        k_bid, k_ask, p_bid, p_ask,
        "Fed Rate Cut Dec 2026"
    )
    print(f"SIGNAL: {signal}")
    print(f"Rationale: {rationale}")

    # SCENARIO 3: No Arb (Spread smaller than fees)
    print("\n--- SCENARIO 3: No Arb (Spread < Fees) ---")

    # "CPI > 3%?"
    k_bid, k_ask = 0.40, 0.41  # Kalshi: 40-41c
    p_bid, p_ask = 0.41, 0.42  # Poly: 41-42c

    signal, rationale = detector.find_arbitrage(
        k_bid, k_ask, p_bid, p_ask,
        "CPI Above 3%"
    )
    print(f"SIGNAL: {signal}")
    print(f"Rationale: {rationale}")

    # SCENARIO 4: Full analysis
    print("\n--- SCENARIO 4: Full Analysis ---")
    analysis = detector.get_full_analysis(
        0.50, 0.51, 0.53, 0.54,
        "Example Market"
    )
    print("\nDetailed Analysis:")
    for key, value in analysis.items():
        if isinstance(value, dict):
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
