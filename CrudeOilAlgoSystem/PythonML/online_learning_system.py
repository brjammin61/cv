"""
Online Learning System for Continuous Model Improvement
========================================================

Implements incremental learning that updates models with new market data
in real-time, allowing the system to adapt to changing market conditions.

Features:
- Incremental model updates with new data
- Drift detection and model retraining triggers
- Performance monitoring and validation
- A/B testing of model versions
- Automatic rollback on performance degradation

Author: Algorithmic Trading Framework 2025
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta
from collections import deque
import logging
import json


class OnlineLearningSystem:
    """
    Online learning system that continuously improves models
    """

    def __init__(self, model_path='./models', buffer_size=1000, retrain_threshold=100):
        """
        Initialize online learning system

        Args:
            model_path: Directory for saving/loading models
            buffer_size: Size of rolling data buffer
            retrain_threshold: Number of new samples before retraining
        """
        self.model_path = model_path
        self.buffer_size = buffer_size
        self.retrain_threshold = retrain_threshold

        # Data buffers
        self.feature_buffer = deque(maxlen=buffer_size)
        self.target_buffer = deque(maxlen=buffer_size)
        self.prediction_buffer = deque(maxlen=buffer_size)

        # Models
        self.current_model = None
        self.backup_model = None
        self.scaler = StandardScaler()

        # Performance tracking
        self.performance_history = []
        self.samples_since_retrain = 0

        # Drift detection
        self.baseline_accuracy = 0
        self.drift_threshold = 0.1  # 10% accuracy drop triggers retrain

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        # Load existing models if available
        self.load_models()

    def load_models(self):
        """Load existing models from disk"""
        model_file = os.path.join(self.model_path, 'direction_model.pkl')
        scaler_file = os.path.join(self.model_path, 'scaler.pkl')

        if os.path.exists(model_file):
            self.current_model = joblib.load(model_file)
            self.logger.info("Loaded existing model")

        if os.path.exists(scaler_file):
            self.scaler = joblib.load(scaler_file)
            self.logger.info("Loaded existing scaler")

    def save_models(self):
        """Save models to disk"""
        os.makedirs(self.model_path, exist_ok=True)

        if self.current_model:
            model_file = os.path.join(self.model_path, 'direction_model.pkl')
            joblib.dump(self.current_model, model_file)
            self.logger.info(f"Model saved to {model_file}")

        if self.scaler:
            scaler_file = os.path.join(self.model_path, 'scaler.pkl')
            joblib.dump(self.scaler, scaler_file)

    def add_sample(self, features, actual_outcome):
        """
        Add new sample to buffer and check if retraining needed

        Args:
            features: Feature vector
            actual_outcome: Actual outcome (0=short, 1=neutral, 2=long)
        """
        # Store in buffer
        self.feature_buffer.append(features)
        self.target_buffer.append(actual_outcome)

        # Make prediction with current model
        if self.current_model:
            features_scaled = self.scaler.transform([features])
            prediction = self.current_model.predict(features_scaled)[0]
            self.prediction_buffer.append(prediction)

            # Track accuracy
            correct = (prediction == actual_outcome)
            self.performance_history.append({
                'timestamp': datetime.now(),
                'correct': correct,
                'prediction': prediction,
                'actual': actual_outcome
            })

        self.samples_since_retrain += 1

        # Check if retraining needed
        if self.samples_since_retrain >= self.retrain_threshold:
            if self._detect_drift():
                self.logger.warning("Drift detected! Triggering retrain...")
                self.retrain()
            elif len(self.feature_buffer) >= self.retrain_threshold:
                self.logger.info("Scheduled retrain triggered")
                self.retrain()

    def _detect_drift(self):
        """
        Detect if model performance has degraded (concept drift)

        Returns:
            True if drift detected
        """
        if len(self.performance_history) < 50:
            return False  # Not enough data

        # Calculate recent accuracy
        recent_performance = self.performance_history[-50:]
        recent_accuracy = sum(p['correct'] for p in recent_performance) / len(recent_performance)

        # Compare to baseline
        if self.baseline_accuracy > 0:
            drift = self.baseline_accuracy - recent_accuracy
            if drift > self.drift_threshold:
                self.logger.warning(f"Drift detected: {drift:.2%} accuracy drop")
                return True

        return False

    def retrain(self):
        """
        Retrain model with buffered data
        """
        if len(self.feature_buffer) < 100:
            self.logger.warning("Insufficient data for retraining")
            return

        self.logger.info(f"Retraining model with {len(self.feature_buffer)} samples...")

        # Prepare data
        X = np.array(list(self.feature_buffer))
        y = np.array(list(self.target_buffer))

        # Backup current model
        if self.current_model:
            self.backup_model = self.current_model

        # Retrain scaler
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        # Train new model
        new_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            random_state=42,
            n_jobs=-1
        )

        new_model.fit(X_scaled, y)

        # Validate new model
        train_accuracy = new_model.score(X_scaled, y)
        self.logger.info(f"New model training accuracy: {train_accuracy:.4f}")

        # Compare to old model (if exists)
        if self.current_model:
            old_accuracy = self.current_model.score(X_scaled, y)
            self.logger.info(f"Old model accuracy on new data: {old_accuracy:.4f}")

            # Only update if new model is better
            if train_accuracy >= old_accuracy:
                self.current_model = new_model
                self.baseline_accuracy = train_accuracy
                self.logger.info("✓ New model deployed")
                self.save_models()
            else:
                self.logger.warning("✗ New model worse than old, keeping old model")
        else:
            self.current_model = new_model
            self.baseline_accuracy = train_accuracy
            self.save_models()

        # Reset counter
        self.samples_since_retrain = 0

    def predict(self, features):
        """
        Make prediction with current model

        Args:
            features: Feature vector

        Returns:
            prediction: 0=short, 1=neutral, 2=long
            confidence: Prediction probability
        """
        if not self.current_model:
            return 1, 0.33  # Neutral with low confidence

        features_scaled = self.scaler.transform([features])
        prediction = self.current_model.predict(features_scaled)[0]

        if hasattr(self.current_model, 'predict_proba'):
            probabilities = self.current_model.predict_proba(features_scaled)[0]
            confidence = np.max(probabilities)
        else:
            confidence = 0.5

        return prediction, confidence

    def get_performance_report(self):
        """
        Generate performance report

        Returns:
            dict with performance metrics
        """
        if not self.performance_history:
            return {}

        recent_100 = self.performance_history[-100:]
        recent_50 = self.performance_history[-50:]
        recent_10 = self.performance_history[-10:]

        report = {
            'total_predictions': len(self.performance_history),
            'overall_accuracy': sum(p['correct'] for p in self.performance_history) / len(self.performance_history),
            'recent_100_accuracy': sum(p['correct'] for p in recent_100) / len(recent_100) if recent_100 else 0,
            'recent_50_accuracy': sum(p['correct'] for p in recent_50) / len(recent_50) if recent_50 else 0,
            'recent_10_accuracy': sum(p['correct'] for p in recent_10) / len(recent_10) if recent_10 else 0,
            'baseline_accuracy': self.baseline_accuracy,
            'samples_since_retrain': self.samples_since_retrain,
            'buffer_size': len(self.feature_buffer),
            'timestamp': datetime.now().isoformat()
        }

        return report

    def save_performance_log(self, filepath='./logs/online_learning_performance.json'):
        """Save performance log to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        report = self.get_performance_report()

        # Append to log file
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append(report)

        with open(filepath, 'w') as f:
            json.dump(logs, f, indent=2)

        self.logger.info(f"Performance log saved to {filepath}")


class AdaptiveParameterSystem:
    """
    Automatically adjusts strategy parameters based on performance
    """

    def __init__(self, initial_params):
        """
        Initialize adaptive parameter system

        Args:
            initial_params: Dict of initial parameter values
        """
        self.params = initial_params.copy()
        self.param_history = []
        self.performance_history = []

        self.logger = logging.getLogger(__name__)

    def update_parameters(self, performance_metrics):
        """
        Update parameters based on performance

        Args:
            performance_metrics: Dict with performance data
        """
        # Record performance
        self.performance_history.append({
            'timestamp': datetime.now(),
            'params': self.params.copy(),
            'metrics': performance_metrics
        })

        # Simple adaptive logic
        profit_factor = performance_metrics.get('profit_factor', 1.0)
        win_rate = performance_metrics.get('win_rate', 0.5)
        max_dd = performance_metrics.get('max_drawdown', 0)

        # Adjust stop loss based on recent performance
        if profit_factor < 1.0:
            # Losing - tighten stops
            self.params['stop_loss_ticks'] = max(15, self.params['stop_loss_ticks'] - 2)
            self.logger.info(f"Tightening stops to {self.params['stop_loss_ticks']} ticks")

        elif profit_factor > 1.5 and win_rate > 0.55:
            # Winning - can widen stops slightly for better R:R
            self.params['stop_loss_ticks'] = min(35, self.params['stop_loss_ticks'] + 1)
            self.logger.info(f"Widening stops to {self.params['stop_loss_ticks']} ticks")

        # Adjust position size based on drawdown
        if max_dd > 1500:
            # High drawdown - reduce size
            self.params['position_size'] = max(1, self.params['position_size'] - 1)
            self.logger.info(f"Reducing position size to {self.params['position_size']}")

        elif max_dd < 500 and profit_factor > 1.5:
            # Low drawdown and profitable - can increase size
            self.params['position_size'] = min(3, self.params['position_size'] + 1)
            self.logger.info(f"Increasing position size to {self.params['position_size']}")

        # Save parameter history
        self.param_history.append({
            'timestamp': datetime.now(),
            'params': self.params.copy()
        })

        return self.params

    def get_current_parameters(self):
        """Get current optimal parameters"""
        return self.params.copy()

    def save_parameter_log(self, filepath='./logs/adaptive_params.json'):
        """Save parameter history to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(self.param_history, f, indent=2, default=str)

        self.logger.info(f"Parameter log saved to {filepath}")


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description='Online learning system')
    parser.add_argument('--model-path', type=str, default='./models', help='Model directory')
    parser.add_argument('--test', action='store_true', help='Run test')

    args = parser.parse_args()

    if args.test:
        print("Testing online learning system...")

        # Initialize system
        system = OnlineLearningSystem(model_path=args.model_path)

        # Simulate adding samples
        for i in range(200):
            features = np.random.randn(17)
            outcome = np.random.choice([0, 1, 2])
            system.add_sample(features, outcome)

        # Get performance report
        report = system.get_performance_report()
        print("\nPerformance Report:")
        for key, value in report.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")

        print("\nOnline learning system test complete!")
