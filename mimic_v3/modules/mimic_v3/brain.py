"""
Brain.py - Online Learning Pipeline with River
MIMIC V3.1 - Production Ready

Implements:
- River online learning for real-time model updates
- Feature engineering from whale signals
- Shadow ID encoding with target encoding
- Probability calibration
- Model persistence
"""

import os
import json
import pickle
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import math

# River imports
from river import (
    compose,
    preprocessing,
    linear_model,
    optim,
    feature_extraction,
    metrics,
    stats
)


@dataclass
class FeatureStats:
    """Rolling statistics for feature normalization"""
    mean: stats.Mean = field(default_factory=stats.Mean)
    var: stats.Var = field(default_factory=stats.Var)

    def update(self, value: float):
        self.mean.update(value)
        self.var.update(value)

    def normalize(self, value: float) -> float:
        m = self.mean.get() or 0
        v = self.var.get() or 1
        std = math.sqrt(v) if v > 0 else 1
        return (value - m) / std if std > 0 else 0


class MimicBrain:
    """
    Online learning prediction engine.

    Features:
    - Whale win rate (historical)
    - Whale PnL (log-scaled)
    - Sentiment score (from Oracle)
    - Implied probability (market price)
    - Order flow imbalance
    - Resolution proximity
    - Strategy type encoding

    Model:
    - Logistic Regression with SGD
    - Online learning (learn_one / predict_one)
    - Target encoding for shadow IDs
    """

    def __init__(
        self,
        learning_rate: float = 0.05,
        model_path: str = None,
        logger: logging.Logger = None
    ):
        self.learning_rate = learning_rate
        self.model_path = model_path or "models/brain_model.pkl"
        self.logger = logger or logging.getLogger(__name__)

        # Whale statistics (maintained internally)
        self.whale_stats: Dict[str, Dict] = defaultdict(lambda: {
            "wins": 0,
            "losses": 0,
            "total_pnl": 0.0,
            "trades": []
        })

        # Feature statistics for normalization
        self.feature_stats: Dict[str, FeatureStats] = defaultdict(FeatureStats)

        # Build the model pipeline
        self.model = self._build_pipeline()

        # Performance tracking
        self.metrics = {
            "accuracy": metrics.Accuracy(),
            "log_loss": metrics.LogLoss(),
            "precision": metrics.Precision(),
            "recall": metrics.Recall(),
            "f1": metrics.F1()
        }

        # Prediction history for calibration
        self.predictions: List[Tuple[float, int]] = []

        # Load existing model if available
        self._load_model()

    def _build_pipeline(self):
        """
        Build River online learning pipeline.

        Pipeline:
        1. Numerical features -> StandardScaler
        2. Categorical features -> TargetEncoder
        3. Combined -> Logistic Regression
        """
        # Numerical features
        num_features = [
            'whale_win_rate',
            'whale_log_pnl',
            'sentiment_score',
            'implied_prob',
            'order_flow_imbalance',
            'resolution_hours',
            'volume_normalized',
            'confidence'
        ]

        # Select and scale numerical features
        num_pipe = (
            compose.Select(*num_features) |
            preprocessing.StandardScaler()
        )

        # Categorical features with target encoding
        cat_pipe = (
            compose.Select('shadow_id', 'strategy_type') |
            feature_extraction.TargetEncoder(smoothing=10)
        )

        # Combined model
        model = (
            (num_pipe + cat_pipe) |
            linear_model.LogisticRegression(
                optimizer=optim.SGD(lr=self.learning_rate),
                l2=0.01  # Regularization
            )
        )

        return model

    def extract_features(
        self,
        signal: Any,  # WhaleSignal from scanner
        sentiment_score: float = 0.0,
        additional_features: Dict = None
    ) -> Dict:
        """
        Extract feature vector from whale signal.

        Args:
            signal: WhaleSignal object from scanner
            sentiment_score: From News Oracle (-1 to 1)
            additional_features: Any extra features to include

        Returns:
            Feature dictionary for model
        """
        shadow_id = signal.shadow_id if hasattr(signal, 'shadow_id') else signal.get('shadow_id', 'UNKNOWN')
        stats = self.whale_stats[shadow_id]

        # Calculate whale metrics
        total_trades = stats["wins"] + stats["losses"]
        win_rate = stats["wins"] / total_trades if total_trades > 0 else 0.5

        # Log-scale PnL to handle large values
        pnl = stats["total_pnl"]
        log_pnl = math.copysign(math.log1p(abs(pnl)), pnl) if pnl != 0 else 0

        # Normalize volume
        volume = signal.volume if hasattr(signal, 'volume') else signal.get('volume', 0)
        self.feature_stats['volume'].update(volume)
        volume_normalized = self.feature_stats['volume'].normalize(volume)

        # Resolution proximity (cap at 72 hours, normalize)
        resolution_hours = signal.resolution_proximity if hasattr(signal, 'resolution_proximity') else signal.get('resolution_proximity')
        if resolution_hours is None:
            resolution_hours = 72.0
        resolution_hours = min(resolution_hours, 72.0) / 72.0  # Normalize to 0-1

        # Extract other signal attributes
        price = signal.price if hasattr(signal, 'price') else signal.get('price', 0.5)
        imbalance = signal.order_flow_imbalance if hasattr(signal, 'order_flow_imbalance') else signal.get('order_flow_imbalance', 0)
        confidence = signal.confidence if hasattr(signal, 'confidence') else signal.get('confidence', 0.5)
        strategy = signal.strategy_type.value if hasattr(signal, 'strategy_type') and hasattr(signal.strategy_type, 'value') else signal.get('strategy_type', 'UNKNOWN')

        features = {
            'shadow_id': shadow_id,
            'strategy_type': strategy,
            'whale_win_rate': win_rate,
            'whale_log_pnl': log_pnl,
            'sentiment_score': sentiment_score,
            'implied_prob': price,
            'order_flow_imbalance': imbalance,
            'resolution_hours': resolution_hours,
            'volume_normalized': volume_normalized,
            'confidence': confidence
        }

        # Add any additional features
        if additional_features:
            features.update(additional_features)

        return features

    def predict(self, features: Dict) -> float:
        """
        Predict probability of trade success.

        Args:
            features: Feature dictionary from extract_features()

        Returns:
            Probability of win (0-1)
        """
        try:
            # Get probability distribution
            proba = self.model.predict_proba_one(features)

            # Return probability of class 1 (win)
            win_prob = proba.get(1, 0.5) if proba else 0.5

            # Calibration adjustment (if we have enough data)
            if len(self.predictions) > 100:
                win_prob = self._calibrate(win_prob)

            return win_prob

        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return 0.5  # Default to uncertain

    def _calibrate(self, raw_prob: float) -> float:
        """
        Apply Platt scaling calibration based on historical predictions.
        Simple linear calibration for now.
        """
        # Group predictions into bins
        bins = defaultdict(list)
        for pred, actual in self.predictions[-1000:]:  # Last 1000
            bin_idx = int(pred * 10)  # 10 bins
            bins[bin_idx].append(actual)

        # Find actual rate for this probability bin
        bin_idx = int(raw_prob * 10)
        if bin_idx in bins and len(bins[bin_idx]) > 10:
            actual_rate = sum(bins[bin_idx]) / len(bins[bin_idx])
            # Blend raw and calibrated
            return 0.7 * raw_prob + 0.3 * actual_rate

        return raw_prob

    def learn(self, features: Dict, is_win: bool, pnl: float = 0.0):
        """
        Update model with trade outcome.

        Args:
            features: Feature dictionary used for prediction
            is_win: Whether the trade was profitable
            pnl: Actual P&L of the trade
        """
        label = 1 if is_win else 0

        # Update River model
        try:
            self.model.learn_one(features, label)
        except Exception as e:
            self.logger.error(f"Learning error: {e}")

        # Update metrics
        pred_prob = self.predict(features)
        for metric in self.metrics.values():
            try:
                metric.update(label, pred_prob)
            except Exception:
                pass

        # Store for calibration
        self.predictions.append((pred_prob, label))
        if len(self.predictions) > 10000:
            self.predictions = self.predictions[-5000:]

        # Update whale stats
        shadow_id = features.get('shadow_id', 'UNKNOWN')
        if is_win:
            self.whale_stats[shadow_id]["wins"] += 1
        else:
            self.whale_stats[shadow_id]["losses"] += 1
        self.whale_stats[shadow_id]["total_pnl"] += pnl
        self.whale_stats[shadow_id]["trades"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "is_win": is_win,
            "pnl": pnl
        })

        # Keep only last 100 trades per whale
        if len(self.whale_stats[shadow_id]["trades"]) > 100:
            self.whale_stats[shadow_id]["trades"] = self.whale_stats[shadow_id]["trades"][-100:]

        # Periodic save
        if len(self.predictions) % 100 == 0:
            self._save_model()

    def get_metrics(self) -> Dict:
        """Get current model performance metrics"""
        return {
            name: float(metric.get()) if hasattr(metric, 'get') else 0
            for name, metric in self.metrics.items()
        }

    def get_whale_info(self, shadow_id: str) -> Dict:
        """Get detailed info for a specific whale"""
        stats = self.whale_stats.get(shadow_id, {})
        total = stats.get("wins", 0) + stats.get("losses", 0)
        return {
            "shadow_id": shadow_id,
            "total_trades": total,
            "wins": stats.get("wins", 0),
            "losses": stats.get("losses", 0),
            "win_rate": stats.get("wins", 0) / total if total > 0 else 0.5,
            "total_pnl": stats.get("total_pnl", 0),
            "recent_trades": stats.get("trades", [])[-10:]
        }

    def _save_model(self):
        """Persist model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

            state = {
                "model": self.model,
                "whale_stats": dict(self.whale_stats),
                "predictions": self.predictions[-5000:],
                "feature_stats": {k: {"mean": v.mean.get(), "var": v.var.get()}
                                   for k, v in self.feature_stats.items()},
                "saved_at": datetime.utcnow().isoformat()
            }

            with open(self.model_path, 'wb') as f:
                pickle.dump(state, f)

            self.logger.debug(f"Model saved to {self.model_path}")

        except Exception as e:
            self.logger.error(f"Failed to save model: {e}")

    def _load_model(self):
        """Load model from disk if available"""
        if not os.path.exists(self.model_path):
            self.logger.info("No existing model found, starting fresh")
            return

        try:
            with open(self.model_path, 'rb') as f:
                state = pickle.load(f)

            self.model = state.get("model", self._build_pipeline())
            self.whale_stats = defaultdict(
                lambda: {"wins": 0, "losses": 0, "total_pnl": 0.0, "trades": []},
                state.get("whale_stats", {})
            )
            self.predictions = state.get("predictions", [])

            # Restore feature stats
            for k, v in state.get("feature_stats", {}).items():
                self.feature_stats[k] = FeatureStats()
                # Approximate restoration
                if v.get("mean"):
                    for _ in range(10):
                        self.feature_stats[k].update(v["mean"])

            self.logger.info(f"Model loaded from {self.model_path} (saved {state.get('saved_at', 'unknown')})")

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            self.model = self._build_pipeline()

    def reset(self):
        """Reset model to initial state"""
        self.model = self._build_pipeline()
        self.whale_stats.clear()
        self.predictions.clear()
        self.feature_stats.clear()
        for metric in self.metrics.values():
            if hasattr(metric, 'revert'):
                metric.revert(0, 0)
        self.logger.info("Brain reset to initial state")
