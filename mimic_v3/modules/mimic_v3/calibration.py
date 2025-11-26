"""
Calibration Layer - Statistical Probability Calibration
MIMIC V3.1 CORTEX

Implements:
- C.1: Isotonic Regression for post-hoc probability correction
- C.2: Time-to-Expiry (TtE) Bias Correction

The raw output P_LLM_Raw is systemically biased and unusable for trading.
This module transforms it into P_LLM_Calibrated which is statistically
reliable for Kelly sizing.

Isotonic Regression is the preferred non-parametric method for achieving
correct probability alignment (calibration), making P_sim statistically
sound for optimal position sizing.
"""

import math
import pickle
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import bisect


# =============================================================================
# C.1: ISOTONIC REGRESSION CALIBRATOR
# =============================================================================

@dataclass
class CalibrationPoint:
    """Single calibration observation"""
    predicted: float    # Raw predicted probability
    actual: int         # Actual outcome (0 or 1)
    tte_days: int       # Time to expiry when prediction made
    timestamp: datetime = field(default_factory=datetime.utcnow)


class IsotonicRegressor:
    """
    Isotonic Regression implementation for probability calibration.

    Isotonic regression fits a free-form line to data subject to
    the constraint that it must be monotonically increasing.

    This is ideal for probability calibration because:
    1. Non-parametric: No assumptions about distribution shape
    2. Monotonic: Higher raw predictions = higher calibrated predictions
    3. Optimal: Minimizes squared error under monotonicity constraint
    """

    def __init__(self, min_samples: int = 30, logger: logging.Logger = None):
        self.min_samples = min_samples
        self.logger = logger or logging.getLogger(__name__)

        # Fitted values: list of (x, y) pairs where x is raw, y is calibrated
        self._fitted_points: List[Tuple[float, float]] = []

        # Raw data for refitting
        self._observations: List[CalibrationPoint] = []

        # Binned statistics for quick updates
        self._bins: Dict[int, Dict] = defaultdict(lambda: {"sum_actual": 0, "count": 0})
        self._n_bins = 20

        self._is_fitted = False

    def add_observation(self, predicted: float, actual: int, tte_days: int = 30):
        """
        Add a single observation for incremental learning.

        Args:
            predicted: Raw predicted probability (0-1)
            actual: Actual outcome (0 or 1)
            tte_days: Days to expiry when prediction was made
        """
        self._observations.append(CalibrationPoint(
            predicted=predicted,
            actual=actual,
            tte_days=tte_days
        ))

        # Update bin statistics
        bin_idx = min(int(predicted * self._n_bins), self._n_bins - 1)
        self._bins[bin_idx]["sum_actual"] += actual
        self._bins[bin_idx]["count"] += 1

        # Refit if we have enough data
        if len(self._observations) >= self.min_samples:
            self._fit()

    def _fit(self):
        """
        Fit isotonic regression using Pool Adjacent Violators Algorithm (PAVA).

        PAVA is the standard algorithm for isotonic regression:
        1. Start with initial estimates
        2. Find adjacent pairs that violate monotonicity
        3. Pool them and replace with weighted average
        4. Repeat until no violations
        """
        if len(self._observations) < self.min_samples:
            return

        # Create bins
        bin_stats = []
        for i in range(self._n_bins):
            stats = self._bins[i]
            if stats["count"] > 0:
                bin_center = (i + 0.5) / self._n_bins
                bin_mean = stats["sum_actual"] / stats["count"]
                bin_stats.append({
                    "x": bin_center,
                    "y": bin_mean,
                    "count": stats["count"]
                })

        if len(bin_stats) < 2:
            return

        # Sort by x
        bin_stats.sort(key=lambda b: b["x"])

        # PAVA algorithm
        n = len(bin_stats)
        y_values = [b["y"] for b in bin_stats]
        weights = [b["count"] for b in bin_stats]

        # Pool Adjacent Violators
        while True:
            # Find first violation
            violation_idx = -1
            for i in range(n - 1):
                if y_values[i] > y_values[i + 1]:
                    violation_idx = i
                    break

            if violation_idx == -1:
                break  # No violations, we're done

            # Pool adjacent violators
            i = violation_idx
            j = i + 1

            # Extend pool to include all adjacent violators
            while j < n and y_values[i] > y_values[j]:
                j += 1

            # Calculate weighted average for the pool
            pool_weight = sum(weights[i:j])
            pool_avg = sum(y_values[k] * weights[k] for k in range(i, j)) / pool_weight if pool_weight > 0 else 0

            # Replace all pooled values with average
            for k in range(i, j):
                y_values[k] = pool_avg

        # Store fitted points
        self._fitted_points = [
            (bin_stats[i]["x"], y_values[i])
            for i in range(n)
        ]

        self._is_fitted = True
        self.logger.debug(f"Isotonic regression fitted with {len(self._fitted_points)} points")

    def calibrate(self, raw_prob: float) -> float:
        """
        Calibrate a raw probability using the fitted model.

        Args:
            raw_prob: Raw predicted probability (0-1)

        Returns:
            Calibrated probability (0-1)
        """
        if not self._is_fitted or not self._fitted_points:
            return raw_prob

        # Clamp input
        raw_prob = max(0.0, min(1.0, raw_prob))

        # Binary search for interpolation
        x_values = [p[0] for p in self._fitted_points]
        y_values = [p[1] for p in self._fitted_points]

        # Find position
        idx = bisect.bisect_left(x_values, raw_prob)

        if idx == 0:
            return y_values[0]
        if idx >= len(x_values):
            return y_values[-1]

        # Linear interpolation
        x0, x1 = x_values[idx - 1], x_values[idx]
        y0, y1 = y_values[idx - 1], y_values[idx]

        if x1 == x0:
            return y0

        t = (raw_prob - x0) / (x1 - x0)
        calibrated = y0 + t * (y1 - y0)

        return max(0.0, min(1.0, calibrated))

    def get_calibration_curve(self) -> List[Tuple[float, float]]:
        """Get the fitted calibration curve"""
        return self._fitted_points.copy()

    def get_metrics(self) -> Dict:
        """Get calibration metrics"""
        if not self._observations:
            return {"n_observations": 0, "is_fitted": False}

        # Calculate Brier score
        brier = sum(
            (obs.actual - obs.predicted) ** 2
            for obs in self._observations
        ) / len(self._observations)

        # Calculate calibrated Brier score
        if self._is_fitted:
            brier_calibrated = sum(
                (obs.actual - self.calibrate(obs.predicted)) ** 2
                for obs in self._observations
            ) / len(self._observations)
        else:
            brier_calibrated = brier

        return {
            "n_observations": len(self._observations),
            "is_fitted": self._is_fitted,
            "brier_score_raw": brier,
            "brier_score_calibrated": brier_calibrated,
            "improvement": (brier - brier_calibrated) / brier if brier > 0 else 0
        }


# =============================================================================
# C.2: TIME-TO-EXPIRY BIAS CORRECTION
# =============================================================================

class TTEBiasCorrector:
    """
    Time-to-Expiry (TtE) Bias Correction

    LLM predictions systematically bias toward 50% for long-term events.
    This corrector adjusts based on historical TTE-specific accuracy.

    Key insight: A 60% prediction 30 days out should be treated differently
    than a 60% prediction 1 day out. Long-term predictions regress to 50%
    unrealistically.
    """

    def __init__(
        self,
        tte_buckets: List[int] = None,
        logger: logging.Logger = None
    ):
        self.logger = logger or logging.getLogger(__name__)

        # TTE buckets (in days)
        self.tte_buckets = tte_buckets or [1, 3, 7, 14, 30, 60, 90]

        # Per-bucket calibrators
        self.bucket_calibrators: Dict[int, IsotonicRegressor] = {
            bucket: IsotonicRegressor(min_samples=20, logger=self.logger)
            for bucket in self.tte_buckets
        }

        # General calibrator for unknown TTE
        self.general_calibrator = IsotonicRegressor(min_samples=30, logger=self.logger)

        # TTE-specific bias factors
        self._tte_bias: Dict[int, float] = defaultdict(lambda: 1.0)

        self._observations: List[CalibrationPoint] = []

    def _get_bucket(self, tte_days: int) -> int:
        """Get the appropriate bucket for a TTE value"""
        for bucket in self.tte_buckets:
            if tte_days <= bucket:
                return bucket
        return self.tte_buckets[-1]

    def add_observation(self, predicted: float, actual: int, tte_days: int):
        """Add observation for TTE-specific calibration"""
        self._observations.append(CalibrationPoint(
            predicted=predicted,
            actual=actual,
            tte_days=tte_days
        ))

        # Update bucket-specific calibrator
        bucket = self._get_bucket(tte_days)
        self.bucket_calibrators[bucket].add_observation(predicted, actual, tte_days)

        # Update general calibrator
        self.general_calibrator.add_observation(predicted, actual, tte_days)

        # Update TTE bias factor
        self._update_tte_bias(bucket)

    def _update_tte_bias(self, bucket: int):
        """Calculate TTE-specific bias adjustment"""
        bucket_obs = [
            obs for obs in self._observations
            if self._get_bucket(obs.tte_days) == bucket
        ]

        if len(bucket_obs) < 10:
            return

        # Calculate bias: how much predictions deviate from actual
        # Positive bias = predictions too high, negative = too low
        deviations = [obs.predicted - obs.actual for obs in bucket_obs]
        avg_deviation = sum(deviations) / len(deviations)

        # Bias factor: reduce predictions that are systematically too extreme
        # If predictions are too high for wins and too low for losses,
        # the model is overconfident -> bias factor < 1
        self._tte_bias[bucket] = 1.0 - avg_deviation * 2

    def correct(self, raw_prob: float, tte_days: int) -> float:
        """
        Apply TTE-specific bias correction.

        Args:
            raw_prob: Raw probability
            tte_days: Days to expiry

        Returns:
            TTE-adjusted probability
        """
        bucket = self._get_bucket(tte_days)
        calibrator = self.bucket_calibrators.get(bucket, self.general_calibrator)

        # First, apply isotonic calibration if available
        if calibrator._is_fitted:
            calibrated = calibrator.calibrate(raw_prob)
        else:
            calibrated = raw_prob

        # Then, apply TTE-specific bias correction
        bias_factor = self._tte_bias.get(bucket, 1.0)

        # Apply bias: shift away from 0.5 for short TTE, toward 0.5 for long TTE
        if tte_days > 30:
            # Long TTE: regression toward 50%
            regression = (tte_days - 30) / 100  # More regression for longer TTE
            regression = min(regression, 0.3)  # Cap at 30% regression
            corrected = calibrated * (1 - regression) + 0.5 * regression
        else:
            # Short TTE: less regression
            corrected = calibrated * bias_factor + (1 - bias_factor) * 0.5

        return max(0.01, min(0.99, corrected))

    def get_bucket_metrics(self) -> Dict[int, Dict]:
        """Get metrics for each TTE bucket"""
        return {
            bucket: calibrator.get_metrics()
            for bucket, calibrator in self.bucket_calibrators.items()
        }


# =============================================================================
# UNIFIED CALIBRATION LAYER
# =============================================================================

class CalibrationLayer:
    """
    Unified Calibration Layer combining:
    - C.1: Isotonic Regression
    - C.2: Time-to-Expiry Bias Correction

    This is the mandatory calibration for turning P_LLM_Raw
    into the statistically reliable P_LLM_Calibrated.
    """

    def __init__(
        self,
        model_path: str = "models/calibration.pkl",
        logger: logging.Logger = None
    ):
        self.model_path = model_path
        self.logger = logger or logging.getLogger(__name__)

        # Initialize components
        self.isotonic = IsotonicRegressor(min_samples=30, logger=self.logger)
        self.tte_corrector = TTEBiasCorrector(logger=self.logger)

        # Overall statistics
        self.stats = {
            "total_calibrations": 0,
            "total_observations": 0,
            "avg_adjustment": 0.0
        }

        # Load existing model
        self._load_model()

        self.logger.info("Calibration Layer initialized")

    def calibrate(
        self,
        raw_prob: float,
        tte_days: int = 30,
        source: str = "unknown"
    ) -> float:
        """
        Main calibration entry point.

        Applies both Isotonic Regression and TTE Bias Correction.

        Args:
            raw_prob: Raw predicted probability
            tte_days: Days to expiry
            source: Source of prediction (for logging)

        Returns:
            Calibrated probability
        """
        self.stats["total_calibrations"] += 1

        # 1. Apply Isotonic Regression
        isotonic_calibrated = self.isotonic.calibrate(raw_prob)

        # 2. Apply TTE Bias Correction
        final_calibrated = self.tte_corrector.correct(isotonic_calibrated, tte_days)

        # Track adjustment
        adjustment = abs(final_calibrated - raw_prob)
        n = self.stats["total_calibrations"]
        self.stats["avg_adjustment"] = (
            self.stats["avg_adjustment"] * (n - 1) + adjustment
        ) / n

        self.logger.debug(
            f"Calibration [{source}]: {raw_prob:.2%} -> {final_calibrated:.2%} "
            f"(TTE={tte_days}d, adj={adjustment:.2%})"
        )

        return final_calibrated

    def learn(self, predicted: float, actual: int, tte_days: int = 30):
        """
        Add observation for online learning.

        Args:
            predicted: Original raw prediction
            actual: Actual outcome (0 or 1)
            tte_days: Days to expiry when prediction was made
        """
        self.stats["total_observations"] += 1

        # Update both calibrators
        self.isotonic.add_observation(predicted, actual, tte_days)
        self.tte_corrector.add_observation(predicted, actual, tte_days)

        # Periodic save
        if self.stats["total_observations"] % 100 == 0:
            self._save_model()

    def get_calibration_curve(self) -> List[Tuple[float, float]]:
        """Get the main isotonic calibration curve"""
        return self.isotonic.get_calibration_curve()

    def get_metrics(self) -> Dict:
        """Get comprehensive calibration metrics"""
        return {
            "stats": self.stats,
            "isotonic": self.isotonic.get_metrics(),
            "tte_buckets": self.tte_corrector.get_bucket_metrics()
        }

    def _save_model(self):
        """Persist calibration state"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

            state = {
                "isotonic_observations": self.isotonic._observations,
                "isotonic_bins": dict(self.isotonic._bins),
                "tte_observations": self.tte_corrector._observations,
                "tte_bias": dict(self.tte_corrector._tte_bias),
                "stats": self.stats,
                "saved_at": datetime.utcnow().isoformat()
            }

            with open(self.model_path, 'wb') as f:
                pickle.dump(state, f)

            self.logger.debug(f"Calibration model saved to {self.model_path}")

        except Exception as e:
            self.logger.error(f"Failed to save calibration model: {e}")

    def _load_model(self):
        """Load calibration state from disk"""
        if not os.path.exists(self.model_path):
            self.logger.info("No existing calibration model found, starting fresh")
            return

        try:
            with open(self.model_path, 'rb') as f:
                state = pickle.load(f)

            # Restore isotonic
            for obs in state.get("isotonic_observations", []):
                self.isotonic._observations.append(obs)
            self.isotonic._bins = defaultdict(
                lambda: {"sum_actual": 0, "count": 0},
                state.get("isotonic_bins", {})
            )
            self.isotonic._fit()

            # Restore TTE
            for obs in state.get("tte_observations", []):
                self.tte_corrector._observations.append(obs)
            self.tte_corrector._tte_bias = defaultdict(
                lambda: 1.0,
                state.get("tte_bias", {})
            )

            self.stats = state.get("stats", self.stats)

            self.logger.info(
                f"Calibration model loaded from {self.model_path} "
                f"(saved {state.get('saved_at', 'unknown')}, "
                f"{self.stats['total_observations']} observations)"
            )

        except Exception as e:
            self.logger.error(f"Failed to load calibration model: {e}")


# =============================================================================
# CALIBRATION DIAGNOSTICS
# =============================================================================

class CalibrationDiagnostics:
    """
    Diagnostic tools for evaluating calibration quality.

    Produces reliability diagrams, expected calibration error (ECE),
    and other metrics for model evaluation.
    """

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins

    def reliability_diagram_data(
        self,
        predictions: List[float],
        actuals: List[int]
    ) -> Dict:
        """
        Generate data for a reliability diagram.

        Returns:
            Dict with bin_centers, mean_predicted, mean_actual, counts
        """
        if len(predictions) != len(actuals):
            raise ValueError("Predictions and actuals must have same length")

        bins = defaultdict(lambda: {"sum_pred": 0, "sum_actual": 0, "count": 0})

        for pred, actual in zip(predictions, actuals):
            bin_idx = min(int(pred * self.n_bins), self.n_bins - 1)
            bins[bin_idx]["sum_pred"] += pred
            bins[bin_idx]["sum_actual"] += actual
            bins[bin_idx]["count"] += 1

        result = {
            "bin_centers": [],
            "mean_predicted": [],
            "mean_actual": [],
            "counts": []
        }

        for i in range(self.n_bins):
            if bins[i]["count"] > 0:
                result["bin_centers"].append((i + 0.5) / self.n_bins)
                result["mean_predicted"].append(bins[i]["sum_pred"] / bins[i]["count"])
                result["mean_actual"].append(bins[i]["sum_actual"] / bins[i]["count"])
                result["counts"].append(bins[i]["count"])

        return result

    def expected_calibration_error(
        self,
        predictions: List[float],
        actuals: List[int]
    ) -> float:
        """
        Calculate Expected Calibration Error (ECE).

        ECE = sum_i (n_i / N) * |mean_predicted_i - mean_actual_i|

        Lower is better. Well-calibrated models have ECE < 0.05.
        """
        diagram = self.reliability_diagram_data(predictions, actuals)

        if not diagram["counts"]:
            return 1.0

        total = sum(diagram["counts"])
        ece = sum(
            (count / total) * abs(pred - actual)
            for pred, actual, count in zip(
                diagram["mean_predicted"],
                diagram["mean_actual"],
                diagram["counts"]
            )
        )

        return ece

    def maximum_calibration_error(
        self,
        predictions: List[float],
        actuals: List[int]
    ) -> float:
        """
        Calculate Maximum Calibration Error (MCE).

        MCE = max_i |mean_predicted_i - mean_actual_i|

        Useful for detecting worst-case miscalibration.
        """
        diagram = self.reliability_diagram_data(predictions, actuals)

        if not diagram["counts"]:
            return 1.0

        mce = max(
            abs(pred - actual)
            for pred, actual in zip(
                diagram["mean_predicted"],
                diagram["mean_actual"]
            )
        )

        return mce

    def brier_score(
        self,
        predictions: List[float],
        actuals: List[int]
    ) -> float:
        """
        Calculate Brier Score.

        BS = (1/N) * sum_i (p_i - o_i)^2

        Lower is better. BS < 0.25 is generally good for binary predictions.
        """
        if len(predictions) != len(actuals):
            raise ValueError("Predictions and actuals must have same length")

        n = len(predictions)
        if n == 0:
            return 1.0

        bs = sum((p - a) ** 2 for p, a in zip(predictions, actuals)) / n
        return bs


# =============================================================================
# CONVENIENCE EXPORTS
# =============================================================================

def create_calibration_layer(
    model_path: str = "models/calibration.pkl",
    logger: logging.Logger = None
) -> CalibrationLayer:
    """Factory function to create a CalibrationLayer"""
    return CalibrationLayer(model_path=model_path, logger=logger)
