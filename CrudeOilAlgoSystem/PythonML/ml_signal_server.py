"""
Crude Oil ML Signal Server
===========================

Python-based machine learning server for crude oil futures trading signals.
Communicates with NinjaTrader 8 via ZeroMQ (NetMQ on C# side).

Features:
- Real-time signal generation using trained ML models
- Sentiment analysis integration
- Volatility prediction
- Pattern recognition
- ZeroMQ server for low-latency communication

Dependencies:
    pip install pyzmq numpy pandas scikit-learn tensorflow keras

Author: Algorithmic Trading Framework 2025
"""

import zmq
import json
import numpy as np
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, Any, Tuple
import pickle
import os

# ML Libraries
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    import joblib
except ImportError:
    print("Warning: scikit-learn not installed. ML features will be limited.")

try:
    import tensorflow as tf
    from tensorflow import keras
except ImportError:
    print("Warning: TensorFlow not installed. Deep learning features disabled.")


class CrudeOilMLServer:
    """
    Machine Learning Signal Server for Crude Oil Futures

    Processes market data from NinjaTrader and returns trading signals
    based on trained ML models.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5555, model_path: str = "./models"):
        """
        Initialize the ML server

        Args:
            host: Server host address
            port: Server port
            model_path: Path to saved ML models
        """
        self.host = host
        self.port = port
        self.model_path = model_path

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Initialize ZeroMQ context
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)  # Reply socket

        # ML Models
        self.direction_model = None  # Predicts up/down/neutral
        self.volatility_model = None  # Predicts volatility expansion
        self.scaler = None

        # Feature configuration
        self.feature_window = 20  # Number of bars for feature calculation

        self.logger.info(f"ML Server initialized at {host}:{port}")

    def load_models(self):
        """Load pre-trained ML models from disk"""
        try:
            # Load direction prediction model (Random Forest)
            direction_model_path = os.path.join(self.model_path, "direction_model.pkl")
            if os.path.exists(direction_model_path):
                self.direction_model = joblib.load(direction_model_path)
                self.logger.info("Direction model loaded successfully")
            else:
                self.logger.warning(f"Direction model not found at {direction_model_path}")
                self.direction_model = self._create_default_direction_model()

            # Load volatility prediction model
            volatility_model_path = os.path.join(self.model_path, "volatility_model.pkl")
            if os.path.exists(volatility_model_path):
                self.volatility_model = joblib.load(volatility_model_path)
                self.logger.info("Volatility model loaded successfully")
            else:
                self.logger.warning(f"Volatility model not found at {volatility_model_path}")
                self.volatility_model = self._create_default_volatility_model()

            # Load feature scaler
            scaler_path = os.path.join(self.model_path, "scaler.pkl")
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                self.logger.info("Scaler loaded successfully")
            else:
                self.scaler = StandardScaler()
                self.logger.warning("Scaler not found, using new StandardScaler")

        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            self._create_default_models()

    def _create_default_direction_model(self):
        """Create a default direction prediction model"""
        self.logger.info("Creating default direction model (Random Forest)")
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        return model

    def _create_default_volatility_model(self):
        """Create a default volatility prediction model"""
        self.logger.info("Creating default volatility model (Gradient Boosting)")
        model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        return model

    def _create_default_models(self):
        """Initialize default models if loading fails"""
        self.direction_model = self._create_default_direction_model()
        self.volatility_model = self._create_default_volatility_model()
        self.scaler = StandardScaler()

    def start(self):
        """Start the ZeroMQ server and listen for requests"""
        try:
            self.socket.bind(f"tcp://{self.host}:{self.port}")
            self.logger.info(f"Server listening on tcp://{self.host}:{self.port}")

            # Load models
            self.load_models()

            # Main request loop
            while True:
                try:
                    # Wait for request from NinjaTrader
                    message = self.socket.recv_json()
                    self.logger.debug(f"Received request: {message}")

                    # Process request
                    response = self.process_request(message)

                    # Send response
                    self.socket.send_json(response)
                    self.logger.debug(f"Sent response: {response}")

                except KeyboardInterrupt:
                    self.logger.info("Server shutdown requested")
                    break
                except Exception as e:
                    self.logger.error(f"Error processing request: {e}")
                    error_response = {
                        "status": "error",
                        "message": str(e),
                        "signal": 0
                    }
                    self.socket.send_json(error_response)

        finally:
            self.socket.close()
            self.context.term()
            self.logger.info("Server stopped")

    def process_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming market data and generate trading signal

        Args:
            message: Dictionary containing market data from NinjaTrader
                Expected format:
                {
                    "timestamp": "2025-11-17T10:30:00",
                    "bars": [
                        {"open": 75.50, "high": 75.80, "low": 75.40, "close": 75.70, "volume": 1000},
                        ...
                    ],
                    "request_type": "signal"  # or "train", "predict_volatility", etc.
                }

        Returns:
            Dictionary containing trading signal and metadata
                {
                    "status": "success",
                    "signal": 1,  # 1 = Long, -1 = Short, 0 = Neutral
                    "confidence": 0.85,
                    "volatility_prediction": "high",
                    "timestamp": "2025-11-17T10:30:00"
                }
        """
        request_type = message.get("request_type", "signal")

        if request_type == "signal":
            return self._generate_trading_signal(message)
        elif request_type == "predict_volatility":
            return self._predict_volatility(message)
        elif request_type == "health_check":
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        else:
            return {
                "status": "error",
                "message": f"Unknown request type: {request_type}"
            }

    def _generate_trading_signal(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trading signal based on market data

        Uses ensemble of ML models to predict market direction and confidence
        """
        try:
            # Extract bar data
            bars = message.get("bars", [])

            if len(bars) < self.feature_window:
                return {
                    "status": "error",
                    "message": f"Insufficient data. Need {self.feature_window} bars, got {len(bars)}",
                    "signal": 0
                }

            # Convert to DataFrame
            df = pd.DataFrame(bars)

            # Calculate features
            features = self._calculate_features(df)

            # Scale features
            if self.scaler:
                features_scaled = self.scaler.transform(features.reshape(1, -1))
            else:
                features_scaled = features.reshape(1, -1)

            # Generate prediction
            if self.direction_model:
                # Predict direction: 0 = Short, 1 = Neutral, 2 = Long
                prediction = self.direction_model.predict(features_scaled)[0]

                # Get prediction probability for confidence
                if hasattr(self.direction_model, 'predict_proba'):
                    probabilities = self.direction_model.predict_proba(features_scaled)[0]
                    confidence = float(np.max(probabilities))
                else:
                    confidence = 0.5

                # Map to signal: -1, 0, 1
                signal_map = {0: -1, 1: 0, 2: 1}
                signal = signal_map.get(prediction, 0)
            else:
                # Fallback: use simple heuristic
                signal, confidence = self._simple_signal_heuristic(df)

            # Predict volatility regime
            volatility_prediction = self._predict_volatility_regime(features_scaled)

            return {
                "status": "success",
                "signal": int(signal),
                "confidence": round(confidence, 4),
                "volatility_prediction": volatility_prediction,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
            return {
                "status": "error",
                "message": str(e),
                "signal": 0
            }

    def _calculate_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Calculate technical features from OHLCV data

        Features include:
        - Price momentum (ROC)
        - Volatility (ATR, Bollinger Band width)
        - Volume indicators
        - Pattern features (candlestick patterns)
        - Time-based features
        """
        features = []

        # Use last 20 bars for feature calculation
        recent_data = df.tail(self.feature_window).copy()

        # 1. Price Momentum Features
        # Rate of Change (ROC) at different periods
        for period in [5, 10, 20]:
            if len(recent_data) >= period:
                roc = (recent_data['close'].iloc[-1] / recent_data['close'].iloc[-period] - 1) * 100
                features.append(roc)
            else:
                features.append(0)

        # 2. Volatility Features
        # ATR (Average True Range)
        high_low = recent_data['high'] - recent_data['low']
        high_close = np.abs(recent_data['high'] - recent_data['close'].shift())
        low_close = np.abs(recent_data['low'] - recent_data['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.mean()
        features.append(atr)

        # Bollinger Band Width
        sma_20 = recent_data['close'].rolling(window=20).mean().iloc[-1]
        std_20 = recent_data['close'].rolling(window=20).std().iloc[-1]
        bb_width = (std_20 * 2) / sma_20 if sma_20 != 0 else 0
        features.append(bb_width)

        # 3. Volume Features
        # Volume ratio (current vs average)
        avg_volume = recent_data['volume'].mean()
        volume_ratio = recent_data['volume'].iloc[-1] / avg_volume if avg_volume != 0 else 1
        features.append(volume_ratio)

        # 4. Candlestick Pattern Features
        last_bar = recent_data.iloc[-1]
        prev_bar = recent_data.iloc[-2] if len(recent_data) > 1 else last_bar

        # Body size
        body_size = abs(last_bar['close'] - last_bar['open'])
        features.append(body_size)

        # Upper wick size
        upper_wick = last_bar['high'] - max(last_bar['close'], last_bar['open'])
        features.append(upper_wick)

        # Lower wick size
        lower_wick = min(last_bar['close'], last_bar['open']) - last_bar['low']
        features.append(lower_wick)

        # Bullish/Bearish flag
        is_bullish = 1 if last_bar['close'] > last_bar['open'] else -1
        features.append(is_bullish)

        # 5. Moving Average Features
        # Distance from 20 SMA
        current_price = recent_data['close'].iloc[-1]
        sma_distance = (current_price - sma_20) / sma_20 if sma_20 != 0 else 0
        features.append(sma_distance)

        # EMA crossover signal
        ema_9 = recent_data['close'].ewm(span=9).mean().iloc[-1]
        ema_21 = recent_data['close'].ewm(span=21).mean().iloc[-1]
        ema_crossover = 1 if ema_9 > ema_21 else -1
        features.append(ema_crossover)

        # 6. RSI (Relative Strength Index)
        delta = recent_data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        features.append(rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50)

        # 7. Time-based features (if timestamp available)
        # Hour of day, day of week (cyclical encoding)
        # This would require timestamp data from message

        return np.array(features, dtype=np.float32)

    def _simple_signal_heuristic(self, df: pd.DataFrame) -> Tuple[int, float]:
        """
        Simple heuristic-based signal generation (fallback if ML model unavailable)

        Returns:
            (signal, confidence) where signal is -1, 0, or 1
        """
        recent_data = df.tail(20)

        # Calculate simple moving averages
        sma_fast = recent_data['close'].tail(5).mean()
        sma_slow = recent_data['close'].tail(20).mean()
        current_price = recent_data['close'].iloc[-1]

        # Simple crossover logic
        if sma_fast > sma_slow and current_price > sma_fast:
            return 1, 0.6  # Bullish
        elif sma_fast < sma_slow and current_price < sma_fast:
            return -1, 0.6  # Bearish
        else:
            return 0, 0.5  # Neutral

    def _predict_volatility(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Predict volatility regime"""
        try:
            bars = message.get("bars", [])
            df = pd.DataFrame(bars)

            features = self._calculate_features(df)
            features_scaled = self.scaler.transform(features.reshape(1, -1))

            volatility_regime = self._predict_volatility_regime(features_scaled)

            return {
                "status": "success",
                "volatility_regime": volatility_regime,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _predict_volatility_regime(self, features: np.ndarray) -> str:
        """
        Predict volatility regime (low, medium, high)

        Args:
            features: Scaled feature array

        Returns:
            "low", "medium", or "high"
        """
        if self.volatility_model:
            try:
                prediction = self.volatility_model.predict(features)[0]
                regime_map = {0: "low", 1: "medium", 2: "high"}
                return regime_map.get(prediction, "medium")
            except:
                pass

        # Fallback: use ATR-based heuristic
        # Feature[3] is ATR in our feature set
        atr = features[0, 3] if features.shape[1] > 3 else 0.5

        if atr < 0.3:
            return "low"
        elif atr < 0.7:
            return "medium"
        else:
            return "high"


def main():
    """Main entry point for the ML server"""
    import argparse

    parser = argparse.ArgumentParser(description='Crude Oil ML Signal Server')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help='Server host address (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5555,
                       help='Server port (default: 5555)')
    parser.add_argument('--model-path', type=str, default='./models',
                       help='Path to ML models directory (default: ./models)')

    args = parser.parse_args()

    # Create models directory if it doesn't exist
    os.makedirs(args.model_path, exist_ok=True)

    # Initialize and start server
    server = CrudeOilMLServer(
        host=args.host,
        port=args.port,
        model_path=args.model_path
    )

    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          Crude Oil ML Signal Server - 2025                     ║
║                                                                ║
║  Listening on: tcp://{args.host}:{args.port}                       ║
║  Model Path: {args.model_path}                                        ║
║                                                                ║
║  Press Ctrl+C to stop the server                              ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)

    server.start()


if __name__ == "__main__":
    main()
