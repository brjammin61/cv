"""
THE CORTEX PROTOCOL - INTELLIGENCE LAYER
========================================

Architecture: Event-Driven Online Learning
Memory: O(1) - Learns immediately, no batch storage
Components:
  - Gatekeeper: Filters high-risk market regimes
  - Brain: Adaptive Random Forest (incremental learning)
  - Amplifier: Dynamic position sizing based on confidence
  - Reflex: Immediate learning on trade close

Tech Stack: River (Online ML), ZeroMQ, ADWIN (Drift Detection)

Author: Cortex Protocol v1.0
"""

import zmq
import json
import numpy as np
from datetime import datetime
from collections import deque

try:
    from river import forest, compose, preprocessing, metrics, drift
    RIVER_AVAILABLE = True
except ImportError:
    print("⚠️ River not installed. Run: pip install river")
    RIVER_AVAILABLE = False

# =============================================================================
# CONFIGURATION
# =============================================================================

ZMQ_PORT = 5555
ATR_THRESHOLD_HIGH = 2.5    # Above this = HIGH_VOLATILITY (dangerous)
ATR_THRESHOLD_LOW = 0.5     # Below this = LOW_VOLATILITY (choppy)
MOMENTUM_THRESHOLD = 0.02   # Above this = TRENDING (avoid mean reversion)
MIN_CONFIDENCE = 0.50       # Below this = don't trade


class CortexBrain:
    """
    The Intelligence Core of the Cortex Protocol

    Layers:
    1. GATEKEEPER: Filters out high-risk market regimes
    2. BRAIN: Adaptive Random Forest for signal generation
    3. AMPLIFIER: Scales position size based on confidence
    4. REFLEX: Learns immediately after each trade
    """

    def __init__(self):
        print("=" * 60)
        print("🧠 INITIALIZING CORTEX CORE...")
        print("=" * 60)

        if not RIVER_AVAILABLE:
            raise ImportError("River library required. Install with: pip install river")

        # =====================================================================
        # 1. THE BRAIN: Adaptive Random Forest (Incremental Learning)
        # =====================================================================
        # ARF automatically handles concept drift and is designed for streaming
        self.model = compose.Pipeline(
            preprocessing.StandardScaler(),
            forest.ARFClassifier(
                n_models=10,      # Ensemble of 10 trees
                seed=42,
                grace_period=50,  # Wait 50 samples before making splits
                max_depth=10
            )
        )

        # =====================================================================
        # 2. DRIFT DETECTION: ADWIN (Adaptive Windowing)
        # =====================================================================
        # Detects when the underlying data distribution changes
        self.adwin = drift.ADWIN(delta=0.002)

        # =====================================================================
        # 3. PERFORMANCE TRACKING
        # =====================================================================
        self.accuracy = metrics.Accuracy()
        self.f1 = metrics.F1()
        self.confusion = metrics.ConfusionMatrix()

        # =====================================================================
        # STATE MEMORY (Minimal - O(1))
        # =====================================================================
        self.last_features = None
        self.last_prediction = None
        self.trade_count = 0
        self.win_count = 0
        self.total_pnl = 0.0
        self.drift_events = 0

        # Recent performance window (for display only)
        self.recent_trades = deque(maxlen=20)

        print("✓ Brain: Adaptive Random Forest (10 trees)")
        print("✓ Drift Detection: ADWIN (delta=0.002)")
        print("✓ Memory: O(1) - No batch storage")
        print("=" * 60)
        print("👁️ CORTEX ONLINE: READY FOR MARKET STREAM")
        print("=" * 60)

    def _gatekeeper(self, features: dict) -> tuple:
        """
        GATEKEEPER LAYER: Filters out high-risk market regimes

        Returns:
            tuple: (regime_name, should_trade, reason)
        """
        atr = features.get('atr', 1.0)
        momentum = features.get('momentum', 0.0)
        hour = features.get('hour', 10)

        # High volatility = dangerous for mean reversion
        if atr > ATR_THRESHOLD_HIGH:
            return ("HIGH_VOL", False, "ATR too high - whipsaw risk")

        # Low volatility = no movement, waste of time
        if atr < ATR_THRESHOLD_LOW:
            return ("LOW_VOL", False, "ATR too low - no movement")

        # Strong trend = mean reversion will get run over
        if abs(momentum) > MOMENTUM_THRESHOLD:
            direction = "UP" if momentum > 0 else "DOWN"
            return ("TRENDING_" + direction, False, f"Strong {direction} trend - avoid mean reversion")

        # Outside trading hours (optional)
        if hour < 9 or hour > 15:
            return ("OFF_HOURS", False, "Outside prime trading hours")

        # All clear
        return ("OPTIMAL", True, "Ideal conditions")

    def _amplifier(self, confidence: float) -> int:
        """
        AMPLIFIER LAYER: Scales position size based on model confidence

        Args:
            confidence: Model's confidence in the prediction (0.0 - 1.0)

        Returns:
            int: Number of contracts (0-3)
        """
        if confidence > 0.80:
            return 3  # MAX AGGRESSION - Very confident
        elif confidence > 0.65:
            return 2  # MODERATE - Reasonably confident
        elif confidence > MIN_CONFIDENCE:
            return 1  # BASELINE - Minimum threshold met
        else:
            return 0  # BLOCK - Not confident enough

    def _extract_feature_dict(self, features: dict) -> dict:
        """
        Ensures features are in correct format for River model
        """
        return {
            'close': float(features.get('close', 0)),
            'atr': float(features.get('atr', 1.0)),
            'rsi': float(features.get('rsi', 50)),
            'volume': float(features.get('volume', 0)),
            'hour': float(features.get('hour', 10)),
            'vwap_dist': float(features.get('vwap_dist', 0)),
            'momentum': float(features.get('momentum', 0))
        }

    def process_request(self, request: dict) -> dict:
        """
        Main request handler - routes to appropriate layer

        Message Types:
        - PREDICT: Get trading signal for current bar
        - TRAIN: Learn from completed trade result
        - STATUS: Get system status
        """
        msg_type = request.get('type', 'PREDICT').upper()

        # =================================================================
        # THE REFLEX (LEARNING LOOP)
        # Triggered immediately after a trade closes in NinjaTrader
        # =================================================================
        if msg_type == 'TRAIN':
            return self._handle_training(request)

        # =================================================================
        # STATUS REQUEST
        # =================================================================
        if msg_type == 'STATUS':
            return self._get_status()

        # =================================================================
        # THE INFERENCE (PREDICTION LOOP)
        # Triggered on every bar close
        # =================================================================
        return self._handle_prediction(request)

    def _handle_training(self, request: dict) -> dict:
        """
        REFLEX LAYER: Immediate learning from trade result

        This is the core of online learning - we update the model
        immediately when we get feedback, not in batches.
        """
        if self.last_features is None:
            return {"status": "IGNORED", "reason": "No previous features to learn from"}

        pnl = request.get('pnl', 0)

        # Convert PnL to binary classification target
        # 1 = winning trade (should have taken it)
        # 0 = losing trade (should have avoided it)
        y_actual = 1 if pnl > 0 else 0

        # IMMEDIATE LEARNING (O(1) update)
        feature_dict = self._extract_feature_dict(self.last_features)
        self.model.learn_one(feature_dict, y_actual)

        # Update metrics
        if self.last_prediction is not None:
            self.accuracy.update(y_actual, self.last_prediction)
            self.f1.update(y_actual, self.last_prediction)
            self.confusion.update(y_actual, self.last_prediction)

        # Update stats
        self.trade_count += 1
        self.total_pnl += pnl
        if pnl > 0:
            self.win_count += 1

        # Track recent trades
        self.recent_trades.append({
            'pnl': pnl,
            'prediction': self.last_prediction,
            'actual': y_actual,
            'correct': self.last_prediction == y_actual if self.last_prediction is not None else None
        })

        # CHECK FOR REGIME DRIFT
        is_correct = (self.last_prediction == y_actual) if self.last_prediction is not None else True
        self.adwin.update(int(is_correct))

        drift_status = "STABLE"
        if self.adwin.drift_detected:
            drift_status = "DRIFT_DETECTED"
            self.drift_events += 1
            print("=" * 60)
            print("⚠️  CORTEX ALERT: MARKET REGIME SHIFT DETECTED")
            print(f"    Drift Event #{self.drift_events}")
            print(f"    Model may need time to adapt to new conditions")
            print("=" * 60)

        # Calculate recent win rate
        recent_correct = sum(1 for t in self.recent_trades if t.get('correct', False))
        recent_win_rate = recent_correct / len(self.recent_trades) if self.recent_trades else 0

        print(f"🎓 LEARNED: PnL=${pnl:.2f} | " +
              f"Total={self.trade_count} | " +
              f"Win%={self.win_count/self.trade_count*100:.1f}% | " +
              f"Acc={self.accuracy.get()*100:.1f}% | " +
              f"Status={drift_status}")

        # Clear state
        self.last_features = None
        self.last_prediction = None

        return {
            "status": "LEARNED",
            "drift": drift_status,
            "trade_count": self.trade_count,
            "accuracy": round(self.accuracy.get(), 4),
            "recent_win_rate": round(recent_win_rate, 4)
        }

    def _handle_prediction(self, request: dict) -> dict:
        """
        INFERENCE LOOP: Generate trading signal

        Pipeline:
        1. Gatekeeper filters market conditions
        2. Brain generates prediction
        3. Amplifier scales position size
        """
        features = request.get('features', {})

        # =================================================================
        # 1. GATEKEEPER CHECK
        # =================================================================
        regime, should_trade, reason = self._gatekeeper(features)

        if not should_trade:
            return {
                "signal": "WAIT",
                "contracts": 0,
                "reason": reason,
                "regime": regime,
                "confidence": 0.0
            }

        # =================================================================
        # 2. BRAIN PREDICTION
        # =================================================================
        feature_dict = self._extract_feature_dict(features)

        # Get prediction and probability
        prediction = self.model.predict_one(feature_dict)
        probs = self.model.predict_proba_one(feature_dict)

        # Handle cold start (no training data yet)
        if prediction is None:
            prediction = 1  # Default to "trade" during warm-up
            confidence = 0.51  # Just above threshold
        else:
            confidence = probs.get(1, 0.5) if probs else 0.5

        # Store state for next learning cycle (THE REFLEX)
        self.last_features = features
        self.last_prediction = prediction

        # =================================================================
        # 3. AMPLIFIER SIZING
        # =================================================================
        if prediction == 1:
            contracts = self._amplifier(confidence)
            signal = "GO" if contracts > 0 else "WAIT"
            if contracts == 0:
                reason = f"Confidence too low ({confidence:.1%})"
        else:
            signal = "WAIT"
            contracts = 0
            reason = "Model predicts unfavorable setup"

        return {
            "signal": signal,
            "contracts": contracts,
            "confidence": round(confidence, 4),
            "regime": regime,
            "reason": reason if signal == "WAIT" else "Conditions favorable"
        }

    def _get_status(self) -> dict:
        """Returns current system status"""
        return {
            "status": "ONLINE",
            "trade_count": self.trade_count,
            "win_count": self.win_count,
            "win_rate": round(self.win_count / self.trade_count, 4) if self.trade_count > 0 else 0,
            "total_pnl": round(self.total_pnl, 2),
            "accuracy": round(self.accuracy.get(), 4),
            "f1_score": round(self.f1.get(), 4),
            "drift_events": self.drift_events
        }


def start_server():
    """
    Main server loop - listens for ZeroMQ messages
    """
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{ZMQ_PORT}")

    print(f"\n👁️  CORTEX LISTENING ON PORT {ZMQ_PORT}")
    print("    Waiting for NinjaTrader connection...\n")

    brain = CortexBrain()

    while True:
        try:
            # Receive request
            message = socket.recv()
            request = json.loads(message.decode('utf-8'))

            # Process and respond
            response = brain.process_request(request)
            socket.send_string(json.dumps(response))

        except json.JSONDecodeError as e:
            print(f"❌ JSON Error: {e}")
            socket.send_string(json.dumps({"error": "Invalid JSON"}))
        except Exception as e:
            print(f"❌ Error: {e}")
            socket.send_string(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   THE CORTEX PROTOCOL - INTELLIGENCE LAYER")
    print("   Event-Driven Online Learning Trading Engine")
    print("=" * 60 + "\n")

    start_server()
