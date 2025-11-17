"""
Hidden Markov Model (HMM) Regime Detection for Crude Oil Trading
==================================================================

Detects market regimes to avoid trading in unfavorable conditions and
dynamically adjust position sizing.

Three Regimes:
1. LOW_VOL_TREND: Ideal for VWAP mean reversion (calm, predictable)
2. HIGH_VOL_RANGE: Dangerous for mean reversion (whipsaws, fake signals)
3. TRENDING: Strong directional move (mean reversion gets run over)

Author: Algorithmic Trading Framework 2025
"""

import numpy as np
import pandas as pd
from hmmlearn import hmm
import pickle
import os
from datetime import datetime
from typing import Tuple, Dict


class RegimeDetector:
    """
    HMM-based market regime detector
    """

    # Regime definitions
    REGIME_LOW_VOL = 0      # Low volatility, ideal for mean reversion
    REGIME_HIGH_VOL = 1     # High volatility, avoid trading
    REGIME_TRENDING = 2     # Strong trend, mean reversion will lose

    REGIME_NAMES = {
        0: "LOW_VOL_IDEAL",
        1: "HIGH_VOL_DANGER",
        2: "TRENDING"
    }

    def __init__(self, n_states=3, n_features=3):
        """
        Initialize HMM regime detector

        Args:
            n_states: Number of market regimes (default 3)
            n_features: Number of input features (default 3)
        """
        self.n_states = n_states
        self.n_features = n_features

        # Initialize HMM with Gaussian emissions
        self.model = hmm.GaussianHMM(
            n_components=n_states,
            covariance_type="full",
            n_iter=100,
            random_state=42
        )

        self.is_trained = False
        self.feature_scaler_mean = None
        self.feature_scaler_std = None

    def extract_features(self, data: pd.DataFrame, lookback=20) -> np.ndarray:
        """
        Extract regime-relevant features from OHLCV data

        Features:
        1. Returns volatility (rolling std of returns)
        2. Price momentum (rate of change)
        3. Volume ratio (current vs average)

        Args:
            data: DataFrame with OHLCV columns
            lookback: Period for rolling calculations

        Returns:
            2D array of features (n_samples, n_features)
        """
        df = data.copy()

        # Calculate returns
        df['returns'] = df['close'].pct_change()

        # Feature 1: Volatility (rolling std of returns)
        df['volatility'] = df['returns'].rolling(window=lookback).std()

        # Feature 2: Momentum (rate of change)
        df['momentum'] = df['close'].pct_change(periods=lookback)

        # Feature 3: Volume ratio (current vs MA)
        df['volume_ma'] = df['volume'].rolling(window=lookback).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # Drop NaN rows
        df = df.dropna()

        # Combine features
        features = df[['volatility', 'momentum', 'volume_ratio']].values

        return features

    def normalize_features(self, features: np.ndarray, fit=False) -> np.ndarray:
        """
        Normalize features to zero mean, unit variance

        Args:
            features: Raw features
            fit: If True, calculate mean/std from data. If False, use stored values.

        Returns:
            Normalized features
        """
        if fit:
            self.feature_scaler_mean = features.mean(axis=0)
            self.feature_scaler_std = features.std(axis=0)

        if self.feature_scaler_mean is None or self.feature_scaler_std is None:
            raise ValueError("Scaler not fitted. Call with fit=True first.")

        normalized = (features - self.feature_scaler_mean) / (self.feature_scaler_std + 1e-8)

        return normalized

    def train(self, data: pd.DataFrame, lookback=20):
        """
        Train HMM on historical data

        Args:
            data: Historical OHLCV data
            lookback: Period for feature calculations
        """
        print("Extracting features for HMM training...")
        features = self.extract_features(data, lookback)

        print(f"Training HMM on {len(features)} samples...")
        features_normalized = self.normalize_features(features, fit=True)

        # Fit HMM
        self.model.fit(features_normalized)

        self.is_trained = True
        print("✓ HMM training complete")

        # Analyze learned regimes
        self._analyze_regimes(features_normalized)

    def _analyze_regimes(self, features: np.ndarray):
        """
        Analyze what each regime represents based on learned means
        """
        print("\n" + "="*60)
        print("LEARNED REGIME CHARACTERISTICS")
        print("="*60)

        means = self.model.means_

        for i in range(self.n_states):
            vol_mean = means[i, 0]  # Volatility
            mom_mean = means[i, 1]  # Momentum
            vol_ratio_mean = means[i, 2]  # Volume ratio

            print(f"\nRegime {i}:")
            print(f"  Volatility: {vol_mean:.4f}")
            print(f"  Momentum: {mom_mean:.4f}")
            print(f"  Volume Ratio: {vol_ratio_mean:.4f}")

            # Interpret regime
            if abs(mom_mean) > 0.5:
                print(f"  → TRENDING regime")
            elif vol_mean > 0.5:
                print(f"  → HIGH VOLATILITY regime")
            else:
                print(f"  → LOW VOLATILITY regime")

    def predict_regime(self, data: pd.DataFrame, lookback=20) -> Tuple[int, np.ndarray]:
        """
        Predict current market regime

        Args:
            data: Recent OHLCV data (should include enough for lookback)
            lookback: Period for feature calculations

        Returns:
            Tuple of (current_regime, regime_probabilities)
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")

        # Extract features
        features = self.extract_features(data, lookback)

        if len(features) == 0:
            raise ValueError("Not enough data for feature extraction")

        # Normalize
        features_normalized = self.normalize_features(features, fit=False)

        # Predict regime sequence
        regime_sequence = self.model.predict(features_normalized)

        # Get probabilities for current regime
        regime_probs = self.model.predict_proba(features_normalized)

        # Return most recent regime
        current_regime = regime_sequence[-1]
        current_probs = regime_probs[-1]

        return current_regime, current_probs

    def get_position_multiplier(self, regime: int, regime_probs: np.ndarray) -> float:
        """
        Get position size multiplier based on regime

        Args:
            regime: Current regime (0-2)
            regime_probs: Probability distribution over regimes

        Returns:
            Position multiplier (0.0 to 1.5)
        """
        # Confidence in current regime
        confidence = regime_probs[regime]

        # Regime-specific multipliers
        if regime == self.REGIME_LOW_VOL:
            # Ideal conditions - trade aggressively
            base_multiplier = 1.5
        elif regime == self.REGIME_TRENDING:
            # Mean reversion struggles in trends - reduce
            base_multiplier = 0.5
        elif regime == self.REGIME_HIGH_VOL:
            # High volatility = whipsaws - avoid
            base_multiplier = 0.25
        else:
            base_multiplier = 1.0

        # Scale by confidence
        # If confidence is low (regime unclear), reduce sizing
        confidence_scaling = 0.5 + (0.5 * confidence)  # Range: 0.5 to 1.0

        final_multiplier = base_multiplier * confidence_scaling

        return final_multiplier

    def should_trade(self, regime: int, regime_probs: np.ndarray,
                     min_confidence=0.6) -> Tuple[bool, str]:
        """
        Determine if trading should occur in current regime

        Args:
            regime: Current regime
            regime_probs: Probability distribution
            min_confidence: Minimum confidence to trade

        Returns:
            Tuple of (should_trade, reason)
        """
        confidence = regime_probs[regime]

        # Check confidence threshold
        if confidence < min_confidence:
            return False, f"Low confidence ({confidence:.1%})"

        # Check regime type
        if regime == self.REGIME_HIGH_VOL:
            return False, f"High volatility regime (unsafe)"

        if regime == self.REGIME_TRENDING:
            # Only trade if very confident it's trending
            if confidence < 0.75:
                return False, f"Trending regime, not confident enough ({confidence:.1%})"

        # Safe to trade
        return True, f"{self.REGIME_NAMES[regime]} ({confidence:.1%})"

    def save(self, filepath: str):
        """Save trained model to disk"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        model_data = {
            'model': self.model,
            'n_states': self.n_states,
            'n_features': self.n_features,
            'feature_scaler_mean': self.feature_scaler_mean,
            'feature_scaler_std': self.feature_scaler_std,
            'is_trained': self.is_trained
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"✓ Model saved to {filepath}")

    def load(self, filepath: str):
        """Load trained model from disk"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model']
        self.n_states = model_data['n_states']
        self.n_features = model_data['n_features']
        self.feature_scaler_mean = model_data['feature_scaler_mean']
        self.feature_scaler_std = model_data['feature_scaler_std']
        self.is_trained = model_data['is_trained']

        print(f"✓ Model loaded from {filepath}")


def train_and_test_regime_detector(data_path: str, output_dir='./models'):
    """
    Train HMM regime detector and test on historical data

    Args:
        data_path: Path to historical OHLCV CSV
        output_dir: Directory to save model
    """
    print("="*70)
    print("HMM REGIME DETECTOR - TRAINING & TESTING")
    print("="*70)

    # Load data
    print(f"\nLoading data from {data_path}...")
    data = pd.read_csv(data_path)
    print(f"Loaded {len(data)} bars")

    # Split into train/test
    train_size = int(len(data) * 0.7)
    train_data = data.iloc[:train_size]
    test_data = data.iloc[train_size:]

    print(f"Train: {len(train_data)} bars")
    print(f"Test: {len(test_data)} bars")

    # Initialize and train
    detector = RegimeDetector(n_states=3, n_features=3)
    detector.train(train_data, lookback=20)

    # Test on holdout data
    print("\n" + "="*70)
    print("TESTING ON HOLDOUT DATA")
    print("="*70)

    # Get regime predictions for entire test set
    features_test = detector.extract_features(test_data, lookback=20)
    features_normalized = detector.normalize_features(features_test, fit=False)
    regime_sequence = detector.model.predict(features_normalized)
    regime_probs = detector.model.predict_proba(features_normalized)

    # Analyze regime distribution
    unique, counts = np.unique(regime_sequence, return_counts=True)
    regime_dist = dict(zip(unique, counts))

    print("\nRegime Distribution in Test Set:")
    for regime, count in regime_dist.items():
        pct = (count / len(regime_sequence)) * 100
        print(f"  Regime {regime} ({detector.REGIME_NAMES[regime]}): {count} bars ({pct:.1f}%)")

    # Calculate position sizing impact
    position_multipliers = [
        detector.get_position_multiplier(regime_sequence[i], regime_probs[i])
        for i in range(len(regime_sequence))
    ]

    print(f"\nPosition Size Multipliers:")
    print(f"  Mean: {np.mean(position_multipliers):.2f}x")
    print(f"  Min: {np.min(position_multipliers):.2f}x")
    print(f"  Max: {np.max(position_multipliers):.2f}x")

    # Calculate trading filter impact
    trade_signals = [
        detector.should_trade(regime_sequence[i], regime_probs[i])
        for i in range(len(regime_sequence))
    ]
    trade_allowed = sum(1 for allowed, _ in trade_signals if allowed)

    print(f"\nTrading Filter:")
    print(f"  Bars allowing trade: {trade_allowed}/{len(regime_sequence)} ({trade_allowed/len(regime_sequence)*100:.1f}%)")
    print(f"  Bars blocking trade: {len(regime_sequence) - trade_allowed} ({(1 - trade_allowed/len(regime_sequence))*100:.1f}%)")

    # Save model
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, 'regime_detector.pkl')
    detector.save(model_path)

    print(f"\n✓ Training complete. Model saved to {model_path}")

    return detector


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train HMM regime detector')
    parser.add_argument('--data', type=str, required=True, help='Historical data CSV')
    parser.add_argument('--output', type=str, default='./models', help='Output directory')

    args = parser.parse_args()

    detector = train_and_test_regime_detector(args.data, args.output)
