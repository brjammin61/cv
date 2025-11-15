"""
Module 10: ML Optimizer

Machine Learning enhancement layer that learns from data and improves over time.

Uses:
- LSTM neural networks for price prediction
- Reinforcement learning for parameter optimization
- Pattern recognition for manipulation detection
- Adaptive learning from outcomes
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3

logger = logging.getLogger(__name__)


class MLOptimizer:
    """
    Machine Learning optimization engine.

    Continuously learns from market data and trading outcomes to improve
    strategy parameters and signal quality.
    """

    def __init__(self, db_path: str = "data/oracle_data.db"):
        """
        Initialize ML Optimizer.

        Args:
            db_path: Path to database with historical data
        """
        self.db_path = db_path

        # Model placeholders (would use actual ML models in production)
        self.price_predictor = None  # LSTM model
        self.parameter_optimizer = None  # RL agent
        self.pattern_detector = None  # Anomaly detection

        # Learning state
        self.training_cycles = 0
        self.last_optimization = None

        # Performance tracking
        self.optimization_history = []

        logger.info("ML Optimizer initialized")

    def prepare_training_data(
        self,
        days: int = 30,
        market_id: Optional[str] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data from historical market snapshots.

        Args:
            days: Number of days of historical data
            market_id: Specific market to train on (None = all markets)

        Returns:
            (X, y) training arrays
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = datetime.now() - timedelta(days=days)

        query = """
            SELECT timestamp, mid_price, spread, volume_24h
            FROM market_snapshots
            WHERE timestamp > ?
        """
        params = [cutoff]

        if market_id:
            query += " AND market_id = ?"
            params.append(market_id)

        query += " ORDER BY timestamp"

        cursor.execute(query, params)
        data = cursor.fetchall()
        conn.close()

        if not data:
            logger.warning("No training data available")
            return np.array([]), np.array([])

        # Convert to numpy arrays
        # X features: [price, spread, volume]
        # y target: next price
        X = []
        y = []

        for i in range(len(data) - 1):
            current = data[i]
            next_point = data[i + 1]

            features = [
                current[1],  # mid_price
                current[2],  # spread
                current[3] or 0  # volume
            ]

            target = next_point[1]  # next mid_price

            X.append(features)
            y.append(target)

        return np.array(X), np.array(y)

    def train_price_predictor(self, X: np.ndarray, y: np.ndarray):
        """
        Train LSTM model for price prediction.

        NOTE: This is a placeholder. In production, would use:
        - TensorFlow/Keras for LSTM
        - Proper train/test split
        - Cross-validation
        - Hyperparameter tuning

        Args:
            X: Feature matrix
            y: Target vector
        """
        logger.info(f"Training price predictor on {len(X)} samples...")

        # Placeholder for actual LSTM training
        # In production:
        # from tensorflow.keras.models import Sequential
        # from tensorflow.keras.layers import LSTM, Dense
        #
        # model = Sequential([
        #     LSTM(50, activation='relu', input_shape=(X.shape[1], 1)),
        #     Dense(1)
        # ])
        # model.compile(optimizer='adam', loss='mse')
        # model.fit(X, y, epochs=50, verbose=0)
        # self.price_predictor = model

        # For now, use simple linear regression as placeholder
        if len(X) > 0 and len(y) > 0:
            # Calculate simple moving average as baseline
            window_size = min(10, len(y))
            self.price_predictor = {
                'type': 'moving_average',
                'window': window_size,
                'last_prices': list(y[-window_size:])
            }

            logger.info(f"✅ Price predictor trained (baseline model)")
        else:
            logger.warning("Insufficient data for training")

    def predict_price_movement(
        self,
        current_price: float,
        spread: float,
        volume: float
    ) -> Tuple[float, float]:
        """
        Predict next price movement.

        Args:
            current_price: Current market price
            spread: Current spread
            volume: Current volume

        Returns:
            (predicted_price, confidence)
        """
        if not self.price_predictor:
            # No model trained, return current price with low confidence
            return current_price, 0.1

        # Placeholder prediction using moving average
        if self.price_predictor['type'] == 'moving_average':
            recent_prices = self.price_predictor['last_prices']
            predicted = np.mean(recent_prices)
            confidence = 0.5  # Moderate confidence in baseline model

            return predicted, confidence

        # With real LSTM, would do:
        # features = np.array([[current_price, spread, volume]])
        # predicted = self.price_predictor.predict(features)[0][0]
        # confidence = calculate_model_confidence(predicted, features)
        # return predicted, confidence

    def optimize_parameters(self, strategy: str = "all") -> Dict:
        """
        Use reinforcement learning to optimize strategy parameters.

        This would use historical outcomes to learn optimal:
        - shy_voter_weight
        - risk_free_rate adjustments
        - favorite/longshot thresholds
        - fee estimates

        Args:
            strategy: Which strategy to optimize ("all" or specific name)

        Returns:
            Dict of optimized parameters
        """
        logger.info(f"Optimizing parameters for {strategy}...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get historical signal outcomes
        cursor.execute("""
            SELECT strategy, edge_cents, conviction, profit_loss
            FROM signals
            WHERE status = 'closed' AND profit_loss IS NOT NULL
        """)

        outcomes = cursor.fetchall()
        conn.close()

        if not outcomes:
            logger.warning("No closed signals to learn from")
            return {}

        # Group by strategy
        strategy_performance = {}

        for strat, edge, conviction, pnl in outcomes:
            if strat not in strategy_performance:
                strategy_performance[strat] = []

            strategy_performance[strat].append({
                'edge': edge,
                'conviction': conviction,
                'pnl': pnl
            })

        # Calculate optimal thresholds based on performance
        optimized = {}

        for strat, results in strategy_performance.items():
            if strategy != "all" and strategy != strat:
                continue

            # Find edge threshold that maximizes win rate
            edges = [r['edge'] for r in results]
            pnls = [r['pnl'] for r in results]

            # Simple optimization: find edge threshold where win rate > 70%
            thresholds = np.linspace(min(edges), max(edges), 20)
            best_threshold = 1.0
            best_win_rate = 0

            for threshold in thresholds:
                filtered_results = [pnl for edge, pnl in zip(edges, pnls) if edge >= threshold]

                if len(filtered_results) > 5:  # Need minimum sample
                    win_rate = sum(1 for pnl in filtered_results if pnl > 0) / len(filtered_results)

                    if win_rate > best_win_rate:
                        best_win_rate = win_rate
                        best_threshold = threshold

            optimized[strat] = {
                'min_edge_threshold': best_threshold,
                'expected_win_rate': best_win_rate,
                'sample_size': len(results)
            }

            logger.info(
                f"  {strat}: min_edge={best_threshold:.2f}¢, "
                f"win_rate={best_win_rate:.1%} (n={len(results)})"
            )

        self.optimization_history.append({
            'timestamp': datetime.now(),
            'results': optimized
        })

        return optimized

    def detect_manipulation(
        self,
        price_history: List[float],
        volume_history: List[float]
    ) -> Tuple[bool, str]:
        """
        Detect potential market manipulation patterns.

        Looks for:
        - Sudden large price movements on low volume
        - Unusual order flow patterns
        - Coordinated buying/selling

        Args:
            price_history: Recent price history
            volume_history: Recent volume history

        Returns:
            (is_suspicious, reason)
        """
        if len(price_history) < 5 or len(volume_history) < 5:
            return False, "Insufficient data"

        # Calculate price volatility
        prices = np.array(price_history)
        price_changes = np.diff(prices) / prices[:-1]
        volatility = np.std(price_changes)

        # Calculate volume consistency
        volumes = np.array(volume_history)
        avg_volume = np.mean(volumes)
        volume_std = np.std(volumes)

        # Check for suspicious patterns

        # Pattern 1: Large price movement on very low volume
        latest_price_change = abs(price_changes[-1])
        latest_volume = volumes[-1]

        if latest_price_change > 2 * volatility and latest_volume < 0.5 * avg_volume:
            return True, "Large price movement on unusually low volume (possible manipulation)"

        # Pattern 2: Sudden volume spike without news
        if latest_volume > avg_volume + 3 * volume_std:
            return True, "Unusual volume spike (possible coordinated action)"

        # Pattern 3: Repeated identical-sized orders (bot pattern)
        unique_volumes = len(set(volumes))
        if unique_volumes < len(volumes) * 0.3:  # Less than 30% unique
            return True, "Repetitive order sizes (possible bot manipulation)"

        return False, "No manipulation detected"

    def calculate_optimal_entry_timing(
        self,
        signal: Dict,
        market_id: str
    ) -> Tuple[str, float]:
        """
        Use ML to determine optimal entry timing for a signal.

        Args:
            signal: Signal dictionary
            market_id: Market identifier

        Returns:
            (timing_recommendation, confidence)
                - "immediate": Execute now
                - "wait_5min": Wait 5 minutes
                - "wait_15min": Wait 15 minutes
                - "skip": Don't execute
        """
        # Placeholder for ML-based timing optimization

        # In production, would:
        # 1. Analyze historical patterns of price movement after similar signals
        # 2. Predict optimal entry time
        # 3. Consider market microstructure (bid-ask bounce, etc.)

        # For now, simple heuristic
        edge = signal.get('edge_cents', 0)
        conviction = signal.get('conviction', 'MEDIUM')

        if conviction == "HIGH" and edge > 5:
            return "immediate", 0.9
        elif conviction == "HIGH":
            return "immediate", 0.7
        elif conviction == "MEDIUM" and edge > 4:
            return "wait_5min", 0.6
        else:
            return "wait_15min", 0.4

    def learn_from_outcome(
        self,
        signal_id: int,
        outcome: str,
        pnl: float
    ):
        """
        Learn from a completed trade outcome.

        Updates models based on what happened.

        Args:
            signal_id: Signal ID
            outcome: "win" or "loss"
            pnl: Profit/loss amount
        """
        logger.info(f"Learning from signal #{signal_id}: {outcome} ({pnl:+.2f}¢)")

        # In production, would:
        # 1. Update LSTM model with actual price movements
        # 2. Adjust parameter optimization based on outcome
        # 3. Update confidence scores

        # For now, just track
        self.training_cycles += 1

        if self.training_cycles % 10 == 0:
            logger.info(f"Completed {self.training_cycles} learning cycles")

    def get_ml_insights(self) -> Dict:
        """Get current ML system insights and recommendations."""
        return {
            'price_predictor_trained': self.price_predictor is not None,
            'training_cycles': self.training_cycles,
            'last_optimization': self.last_optimization,
            'optimization_count': len(self.optimization_history),
            'status': 'learning' if self.training_cycles > 0 else 'untrained'
        }

    def print_status(self):
        """Print ML system status."""
        insights = self.get_ml_insights()

        print("\n" + "=" * 80)
        print("ML OPTIMIZER STATUS")
        print("=" * 80)

        print(f"\n🤖 Training Status:")
        print(f"  Price Predictor: {'✅ Trained' if insights['price_predictor_trained'] else '❌ Not trained'}")
        print(f"  Training Cycles: {insights['training_cycles']}")
        print(f"  Optimizations: {insights['optimization_count']}")

        if insights['last_optimization']:
            print(f"  Last Optimization: {insights['last_optimization']}")

        print(f"\n📊 System Status: {insights['status'].upper()}")

        print("\n" + "=" * 80)


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 80)
    print("ML OPTIMIZER - Module 10")
    print("=" * 80)

    optimizer = MLOptimizer()

    print("\n[1] Preparing training data...")
    X, y = optimizer.prepare_training_data(days=7)
    print(f"✅ Prepared {len(X)} training samples")

    if len(X) > 0:
        print("\n[2] Training price predictor...")
        optimizer.train_price_predictor(X, y)

        print("\n[3] Testing price prediction...")
        predicted, confidence = optimizer.predict_price_movement(0.50, 0.01, 10000)
        print(f"Predicted price: {predicted:.4f} (confidence: {confidence:.1%})")

    print("\n[4] Optimizing parameters...")
    optimized = optimizer.optimize_parameters(strategy="all")
    if optimized:
        print(f"✅ Optimized {len(optimized)} strategies")

    print("\n[5] Testing manipulation detection...")
    # Simulate normal market
    normal_prices = [0.50, 0.51, 0.50, 0.52, 0.51]
    normal_volumes = [1000, 1100, 950, 1050, 1000]
    is_suspicious, reason = optimizer.detect_manipulation(normal_prices, normal_volumes)
    print(f"Normal market: {'⚠️  Suspicious' if is_suspicious else '✅ Clean'} - {reason}")

    # Simulate manipulation
    manip_prices = [0.50, 0.51, 0.50, 0.62, 0.61]  # Big jump
    manip_volumes = [1000, 1100, 950, 200, 180]  # Low volume
    is_suspicious, reason = optimizer.detect_manipulation(manip_prices, manip_volumes)
    print(f"Suspicious market: {'⚠️  Suspicious' if is_suspicious else '✅ Clean'} - {reason}")

    print("\n[6] Current status:")
    optimizer.print_status()
