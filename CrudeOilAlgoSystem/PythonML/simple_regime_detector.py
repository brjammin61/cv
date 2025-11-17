"""
Simple Regime Detector (No External Dependencies)
==================================================

Detects market regimes using simple statistics instead of HMM.
This is faster, more transparent, and doesn't require hmmlearn.

Three Regimes:
1. LOW_VOL: ATR below threshold, ideal for mean reversion
2. HIGH_VOL: ATR above threshold, dangerous for mean reversion
3. TRENDING: Strong directional momentum

Author: Algorithmic Trading Framework 2025
"""

import numpy as np
import pandas as pd


class SimpleRegimeDetector:
    """
    Rule-based regime detection using ATR and momentum
    """

    REGIME_LOW_VOL = 0
    REGIME_HIGH_VOL = 1
    REGIME_TRENDING = 2

    REGIME_NAMES = {
        0: "LOW_VOL_IDEAL",
        1: "HIGH_VOL_DANGER",
        2: "TRENDING"
    }

    def __init__(self,
                 atr_low_threshold=1.0,
                 atr_high_threshold=2.0,
                 trend_threshold=0.02):
        """
        Initialize simple regime detector

        Args:
            atr_low_threshold: ATR below this = low vol regime
            atr_high_threshold: ATR above this = high vol regime
            trend_threshold: Momentum above this = trending regime
        """
        self.atr_low_threshold = atr_low_threshold
        self.atr_high_threshold = atr_high_threshold
        self.trend_threshold = trend_threshold

        self.is_trained = True  # Always "trained" for compatibility

    def _calculate_atr(self, data, period=14):
        """Calculate ATR"""
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values

        if len(data) < period + 1:
            return 1.5

        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1])
            )
        )

        atr = pd.Series(tr).ewm(span=period, adjust=False).mean().iloc[-1]
        return atr

    def _calculate_momentum(self, data, period=20):
        """Calculate price momentum (ROC)"""
        if len(data) < period + 1:
            return 0.0

        close = data['close'].values
        momentum = (close[-1] - close[-period-1]) / close[-period-1]
        return momentum

    def train(self, data: pd.DataFrame, lookback=20):
        """
        "Train" detector (just calculates thresholds from data)

        Args:
            data: Historical OHLCV data
            lookback: Period for calculations
        """
        print("Calibrating regime thresholds from data...")

        # Calculate ATR distribution
        atrs = []
        for i in range(100, len(data)):
            window = data.iloc[i-14:i]
            atr = self._calculate_atr(window, period=14)
            atrs.append(atr)

        atrs = np.array(atrs)

        # Set thresholds at percentiles
        self.atr_low_threshold = np.percentile(atrs, 33)   # 33rd percentile
        self.atr_high_threshold = np.percentile(atrs, 75)  # 75th percentile

        print(f"  Low vol threshold (ATR): {self.atr_low_threshold:.3f}")
        print(f"  High vol threshold (ATR): {self.atr_high_threshold:.3f}")
        print("✓ Regime detector calibrated")

    def predict_regime(self, data: pd.DataFrame, lookback=20):
        """
        Predict current regime

        Args:
            data: Recent OHLCV data
            lookback: Period for calculations

        Returns:
            Tuple of (regime, probabilities)
        """
        # Calculate features
        recent_data = data.iloc[-lookback:] if len(data) > lookback else data

        atr = self._calculate_atr(recent_data, period=14)
        momentum = self._calculate_momentum(recent_data, period=20)

        # Detect regime
        if abs(momentum) > self.trend_threshold:
            # Strong trend
            regime = self.REGIME_TRENDING
            probs = np.array([0.1, 0.1, 0.8])  # 80% confident trending

        elif atr > self.atr_high_threshold:
            # High volatility
            regime = self.REGIME_HIGH_VOL
            probs = np.array([0.1, 0.8, 0.1])  # 80% confident high vol

        elif atr < self.atr_low_threshold:
            # Low volatility (ideal)
            regime = self.REGIME_LOW_VOL
            probs = np.array([0.8, 0.1, 0.1])  # 80% confident low vol

        else:
            # Normal/mixed regime (default to low vol)
            regime = self.REGIME_LOW_VOL
            probs = np.array([0.6, 0.3, 0.1])  # Less confident

        return regime, probs

    def get_position_multiplier(self, regime: int, regime_probs: np.ndarray) -> float:
        """
        Get position size multiplier based on regime

        Args:
            regime: Current regime (0-2)
            regime_probs: Probability distribution

        Returns:
            Position multiplier (0.0 to 1.5)
        """
        confidence = regime_probs[regime]

        # Regime-specific multipliers
        if regime == self.REGIME_LOW_VOL:
            base_multiplier = 1.5  # Trade aggressively
        elif regime == self.REGIME_TRENDING:
            base_multiplier = 0.5  # Mean reversion struggles
        elif regime == self.REGIME_HIGH_VOL:
            base_multiplier = 0.25  # Avoid whipsaws
        else:
            base_multiplier = 1.0

        # Scale by confidence
        confidence_scaling = 0.5 + (0.5 * confidence)

        return base_multiplier * confidence_scaling

    def should_trade(self, regime: int, regime_probs: np.ndarray,
                     min_confidence=0.6):
        """
        Determine if trading allowed in current regime

        Args:
            regime: Current regime
            regime_probs: Probability distribution
            min_confidence: Minimum confidence to trade

        Returns:
            Tuple of (should_trade, reason)
        """
        confidence = regime_probs[regime]

        if confidence < min_confidence:
            return False, f"Low confidence ({confidence:.1%})"

        if regime == self.REGIME_HIGH_VOL:
            return False, "High volatility regime (unsafe)"

        if regime == self.REGIME_TRENDING and confidence < 0.75:
            return False, f"Trending regime ({confidence:.1%})"

        return True, f"{self.REGIME_NAMES[regime]} ({confidence:.1%})"

    def save(self, filepath: str):
        """Save model (compatibility method)"""
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump({
                'atr_low': self.atr_low_threshold,
                'atr_high': self.atr_high_threshold,
                'trend_threshold': self.trend_threshold
            }, f)

    def load(self, filepath: str):
        """Load model (compatibility method)"""
        import pickle
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.atr_low_threshold = data['atr_low']
            self.atr_high_threshold = data['atr_high']
            self.trend_threshold = data['trend_threshold']


# Alias for backward compatibility
RegimeDetector = SimpleRegimeDetector
