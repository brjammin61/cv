"""
Model Training Script for Crude Oil ML
=======================================

Trains machine learning models on historical crude oil futures data.
Saves trained models for use by the ML signal server.

Usage:
    python train_models.py --data historical_cl_data.csv --output ./models

Author: Algorithmic Trading Framework 2025
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import os
import argparse
from datetime import datetime
import logging


class CrudeOilModelTrainer:
    """
    Trains ML models for crude oil trading signals
    """

    def __init__(self, data_path: str, output_path: str = "./models"):
        """
        Initialize the model trainer

        Args:
            data_path: Path to historical OHLCV CSV data
            output_path: Path to save trained models
        """
        self.data_path = data_path
        self.output_path = output_path
        self.df = None
        self.scaler = StandardScaler()

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Create output directory
        os.makedirs(output_path, exist_ok=True)

    def load_data(self):
        """Load historical data from CSV"""
        self.logger.info(f"Loading data from {self.data_path}")

        try:
            # Expected CSV format: timestamp,open,high,low,close,volume
            self.df = pd.read_csv(self.data_path)

            # Ensure required columns exist
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in self.df.columns:
                    raise ValueError(f"Missing required column: {col}")

            self.logger.info(f"Loaded {len(self.df)} bars of data")
            self.logger.info(f"Date range: {self.df.iloc[0]['timestamp']} to {self.df.iloc[-1]['timestamp']}")

        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise

    def calculate_features(self):
        """Calculate technical features for ML"""
        self.logger.info("Calculating features...")

        df = self.df.copy()

        # 1. Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

        # Momentum features
        for period in [5, 10, 20]:
            df[f'roc_{period}'] = df['close'].pct_change(period) * 100

        # 2. Moving averages
        df['sma_9'] = df['close'].rolling(window=9).mean()
        df['sma_21'] = df['close'].rolling(window=21).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_9'] = df['close'].ewm(span=9).mean()
        df['ema_21'] = df['close'].ewm(span=21).mean()

        # MA crossover signals
        df['sma_cross'] = (df['sma_9'] > df['sma_21']).astype(int)
        df['ema_cross'] = (df['ema_9'] > df['ema_21']).astype(int)

        # Distance from moving averages
        df['dist_sma_20'] = (df['close'] - df['sma_21']) / df['sma_21']

        # 3. Volatility features
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr_14'] = true_range.rolling(window=14).mean()

        # Bollinger Bands
        df['bb_upper'] = df['sma_21'] + (df['close'].rolling(window=21).std() * 2)
        df['bb_lower'] = df['sma_21'] - (df['close'].rolling(window=21).std() * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['sma_21']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # 4. Volume features
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']

        # 5. RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))

        # 6. MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # 7. Candlestick pattern features
        df['body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
        df['is_bullish'] = (df['close'] > df['open']).astype(int)

        # 8. Create target variable (future returns)
        # Predict if price will be higher/lower/same in N bars
        PREDICTION_HORIZON = 10  # Predict 10 bars ahead

        df['future_close'] = df['close'].shift(-PREDICTION_HORIZON)
        df['future_return'] = (df['future_close'] - df['close']) / df['close']

        # Classify into 3 categories: Short (-1), Neutral (0), Long (1)
        THRESHOLD = 0.002  # 0.2% threshold for neutral zone

        def classify_direction(ret):
            if pd.isna(ret):
                return np.nan
            elif ret > THRESHOLD:
                return 2  # Long (mapped to signal +1)
            elif ret < -THRESHOLD:
                return 0  # Short (mapped to signal -1)
            else:
                return 1  # Neutral (mapped to signal 0)

        df['target_direction'] = df['future_return'].apply(classify_direction)

        # Volatility target (for volatility prediction model)
        df['future_volatility'] = df['atr_14'].shift(-PREDICTION_HORIZON)
        df['volatility_change'] = (df['future_volatility'] - df['atr_14']) / df['atr_14']

        def classify_volatility(change):
            if pd.isna(change):
                return np.nan
            elif change > 0.2:
                return 2  # High volatility
            elif change < -0.2:
                return 0  # Low volatility
            else:
                return 1  # Medium volatility

        df['target_volatility'] = df['volatility_change'].apply(classify_volatility)

        self.df = df
        self.logger.info("Feature calculation complete")

    def prepare_training_data(self):
        """Prepare features and targets for model training"""
        # Select feature columns (exclude target and auxiliary columns)
        feature_cols = [
            'roc_5', 'roc_10', 'roc_20',
            'sma_cross', 'ema_cross', 'dist_sma_20',
            'atr_14', 'bb_width', 'bb_position',
            'volume_ratio',
            'rsi_14',
            'macd', 'macd_signal', 'macd_hist',
            'body', 'upper_wick', 'lower_wick', 'is_bullish'
        ]

        # Drop rows with NaN (from indicator calculation and shifting)
        df_clean = self.df.dropna(subset=feature_cols + ['target_direction', 'target_volatility'])

        X = df_clean[feature_cols].values
        y_direction = df_clean['target_direction'].values
        y_volatility = df_clean['target_volatility'].values

        self.logger.info(f"Training samples: {len(X)}")
        self.logger.info(f"Features: {len(feature_cols)}")

        # Split data: 80% train, 20% test
        X_train, X_test, y_dir_train, y_dir_test, y_vol_train, y_vol_test = train_test_split(
            X, y_direction, y_volatility, test_size=0.2, shuffle=False  # Don't shuffle time series
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        return X_train_scaled, X_test_scaled, y_dir_train, y_dir_test, y_vol_train, y_vol_test

    def train_direction_model(self, X_train, y_train):
        """Train the direction prediction model"""
        self.logger.info("Training direction prediction model (Random Forest)...")

        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)

        return model

    def train_volatility_model(self, X_train, y_train):
        """Train the volatility prediction model"""
        self.logger.info("Training volatility prediction model (Gradient Boosting)...")

        model = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=8,
            min_samples_split=10,
            random_state=42
        )

        model.fit(X_train, y_train)

        return model

    def evaluate_model(self, model, X_test, y_test, model_name):
        """Evaluate model performance"""
        self.logger.info(f"Evaluating {model_name}...")

        y_pred = model.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        self.logger.info(f"Accuracy: {accuracy:.4f}")

        self.logger.info("Classification Report:")
        print(classification_report(y_test, y_pred))

        self.logger.info("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))

    def save_models(self, direction_model, volatility_model):
        """Save trained models to disk"""
        self.logger.info(f"Saving models to {self.output_path}...")

        # Save direction model
        direction_path = os.path.join(self.output_path, "direction_model.pkl")
        joblib.dump(direction_model, direction_path)
        self.logger.info(f"Direction model saved: {direction_path}")

        # Save volatility model
        volatility_path = os.path.join(self.output_path, "volatility_model.pkl")
        joblib.dump(volatility_model, volatility_path)
        self.logger.info(f"Volatility model saved: {volatility_path}")

        # Save scaler
        scaler_path = os.path.join(self.output_path, "scaler.pkl")
        joblib.dump(self.scaler, scaler_path)
        self.logger.info(f"Scaler saved: {scaler_path}")

    def run(self):
        """Execute the full training pipeline"""
        self.logger.info("="*60)
        self.logger.info("Crude Oil ML Model Training Pipeline")
        self.logger.info("="*60)

        # Load data
        self.load_data()

        # Calculate features
        self.calculate_features()

        # Prepare training data
        X_train, X_test, y_dir_train, y_dir_test, y_vol_train, y_vol_test = self.prepare_training_data()

        # Train direction model
        direction_model = self.train_direction_model(X_train, y_dir_train)
        self.evaluate_model(direction_model, X_test, y_dir_test, "Direction Model")

        # Train volatility model
        volatility_model = self.train_volatility_model(X_train, y_vol_train)
        self.evaluate_model(volatility_model, X_test, y_vol_test, "Volatility Model")

        # Save models
        self.save_models(direction_model, volatility_model)

        self.logger.info("="*60)
        self.logger.info("Training complete!")
        self.logger.info("="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Train Crude Oil ML models')
    parser.add_argument('--data', type=str, required=True,
                       help='Path to historical OHLCV CSV file')
    parser.add_argument('--output', type=str, default='./models',
                       help='Output directory for trained models (default: ./models)')

    args = parser.parse_args()

    trainer = CrudeOilModelTrainer(data_path=args.data, output_path=args.output)
    trainer.run()


if __name__ == "__main__":
    main()
