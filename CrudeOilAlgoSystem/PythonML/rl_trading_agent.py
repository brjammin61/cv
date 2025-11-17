"""
Reinforcement Learning Trading Agent for Crude Oil Futures
===========================================================

Deep Q-Network (DQN) agent that learns optimal trading decisions through
interaction with the market environment. The agent continuously improves
by learning from profitable and unprofitable trades.

Features:
- Deep Q-Network (DQN) with experience replay
- Adaptive exploration (epsilon-greedy with decay)
- Reward shaping for prop firm compliance
- Multi-objective optimization (profit + risk management)
- Continuous learning from live trading

Author: Algorithmic Trading Framework 2025
"""

import numpy as np
import pandas as pd
from collections import deque
import random
import pickle
import os
from datetime import datetime
import logging

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, optimizers
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    print("Warning: TensorFlow not installed. RL agent will use fallback logic.")


class TradingEnvironment:
    """
    Simulated trading environment for RL agent training

    State: [price_position, momentum, volatility, volume, position, pnl, drawdown]
    Actions: [0=Hold, 1=Buy, 2=Sell, 3=Close]
    Rewards: Shaped for profit + risk management
    """

    def __init__(self, data: pd.DataFrame, initial_balance: float = 50000):
        """
        Initialize trading environment

        Args:
            data: DataFrame with OHLCV data
            initial_balance: Starting account balance
        """
        self.data = data.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.current_step = 0
        self.max_steps = len(data) - 1

        # Account state
        self.balance = initial_balance
        self.position = 0  # -1=Short, 0=Flat, 1=Long
        self.entry_price = 0
        self.position_size = 1

        # Performance tracking
        self.total_pnl = 0
        self.trades = []
        self.max_balance = initial_balance
        self.drawdown = 0

        # Risk limits (prop firm style)
        self.daily_loss_limit = 1000
        self.max_drawdown_limit = 2000
        self.daily_pnl = 0

        self.logger = logging.getLogger(__name__)

    def reset(self):
        """Reset environment to initial state"""
        self.current_step = 20  # Start after warm-up period for indicators
        self.balance = self.initial_balance
        self.position = 0
        self.entry_price = 0
        self.total_pnl = 0
        self.trades = []
        self.max_balance = self.initial_balance
        self.drawdown = 0
        self.daily_pnl = 0

        return self._get_state()

    def _get_state(self):
        """
        Get current state representation

        Returns:
            numpy array of state features (normalized)
        """
        if self.current_step >= self.max_steps:
            return np.zeros(20)  # Terminal state

        # Get current and historical data
        current_data = self.data.iloc[self.current_step]
        historical_data = self.data.iloc[max(0, self.current_step-20):self.current_step+1]

        close = current_data['close']

        # Calculate features
        # 1. Price-based features
        sma_20 = historical_data['close'].tail(20).mean()
        price_to_sma = (close - sma_20) / sma_20 if sma_20 != 0 else 0

        # 2. Momentum features
        returns_5 = (close - historical_data['close'].iloc[-5]) / historical_data['close'].iloc[-5] if len(historical_data) >= 5 else 0
        returns_10 = (close - historical_data['close'].iloc[-10]) / historical_data['close'].iloc[-10] if len(historical_data) >= 10 else 0

        # 3. Volatility features
        volatility = historical_data['close'].pct_change().std()
        atr = self._calculate_atr(historical_data)

        # 4. Volume features
        avg_volume = historical_data['volume'].mean()
        volume_ratio = current_data['volume'] / avg_volume if avg_volume > 0 else 1

        # 5. Technical indicators
        rsi = self._calculate_rsi(historical_data)

        # 6. Position and account state
        position_state = self.position  # -1, 0, or 1
        unrealized_pnl = 0
        if self.position != 0:
            unrealized_pnl = (close - self.entry_price) * self.position * self.position_size * 10  # CL tick value

        pnl_percent = unrealized_pnl / self.balance if self.balance > 0 else 0
        drawdown_percent = self.drawdown / self.initial_balance

        # 7. Risk metrics
        daily_pnl_percent = self.daily_pnl / self.initial_balance
        buffer_to_dd_limit = (self.balance - (self.max_balance - self.max_drawdown_limit)) / self.initial_balance

        # Combine into state vector (20 features)
        state = np.array([
            price_to_sma,           # 0: Price position relative to SMA
            returns_5,              # 1: 5-bar momentum
            returns_10,             # 2: 10-bar momentum
            volatility,             # 3: Historical volatility
            atr / close,            # 4: Normalized ATR
            volume_ratio,           # 5: Volume relative to average
            rsi / 100,              # 6: Normalized RSI
            position_state,         # 7: Current position
            pnl_percent,            # 8: Unrealized PnL %
            drawdown_percent,       # 9: Current drawdown %
            daily_pnl_percent,      # 10: Daily PnL %
            buffer_to_dd_limit,     # 11: Distance to DD limit
            close / 100,            # 12: Normalized price
            current_data['high'] / 100,   # 13: Normalized high
            current_data['low'] / 100,    # 14: Normalized low
            current_data['open'] / 100,   # 15: Normalized open
            (current_data['close'] - current_data['open']) / current_data['open'],  # 16: Bar direction
            self.current_step / self.max_steps,  # 17: Time progress
            self.balance / self.initial_balance, # 18: Account size ratio
            len(self.trades) / 100  # 19: Trade count (normalized)
        ], dtype=np.float32)

        # Handle NaN/Inf
        state = np.nan_to_num(state, nan=0.0, posinf=1.0, neginf=-1.0)

        return state

    def step(self, action):
        """
        Execute action and return next state, reward, done

        Args:
            action: 0=Hold, 1=Buy, 2=Sell, 3=Close

        Returns:
            (next_state, reward, done, info)
        """
        if self.current_step >= self.max_steps:
            return self._get_state(), 0, True, {}

        current_data = self.data.iloc[self.current_step]
        close = current_data['close']

        # Initialize reward
        reward = 0
        info = {}

        # Execute action
        if action == 1:  # Buy
            if self.position == 0:
                # Enter long
                self.position = 1
                self.entry_price = close
                reward -= 0.01  # Small penalty for entering (transaction cost)
                info['action'] = 'enter_long'
            elif self.position == -1:
                # Close short and enter long (reversal)
                pnl = (self.entry_price - close) * self.position_size * 10
                reward += self._calculate_reward(pnl)
                self._record_trade(pnl)

                self.position = 1
                self.entry_price = close
                info['action'] = 'reverse_to_long'

        elif action == 2:  # Sell
            if self.position == 0:
                # Enter short
                self.position = -1
                self.entry_price = close
                reward -= 0.01
                info['action'] = 'enter_short'
            elif self.position == 1:
                # Close long and enter short (reversal)
                pnl = (close - self.entry_price) * self.position_size * 10
                reward += self._calculate_reward(pnl)
                self._record_trade(pnl)

                self.position = -1
                self.entry_price = close
                info['action'] = 'reverse_to_short'

        elif action == 3:  # Close position
            if self.position != 0:
                pnl = (close - self.entry_price) * self.position * self.position_size * 10
                reward += self._calculate_reward(pnl)
                self._record_trade(pnl)

                self.position = 0
                self.entry_price = 0
                info['action'] = 'close_position'

        else:  # Hold (action == 0)
            # Small penalty for holding (encourages action)
            reward -= 0.001

            # Reward/penalty for unrealized PnL if in position
            if self.position != 0:
                unrealized_pnl = (close - self.entry_price) * self.position * self.position_size * 10
                reward += unrealized_pnl / 10000  # Small reward for positive unrealized PnL

            info['action'] = 'hold'

        # Update drawdown
        if self.balance > self.max_balance:
            self.max_balance = self.balance
        self.drawdown = self.max_balance - self.balance

        # Check for violations (prop firm rules)
        done = False
        if self.daily_pnl <= -self.daily_loss_limit:
            reward -= 10  # Huge penalty for DLL violation
            done = True
            info['termination'] = 'daily_loss_limit'

        if self.drawdown >= self.max_drawdown_limit:
            reward -= 10  # Huge penalty for drawdown violation
            done = True
            info['termination'] = 'max_drawdown'

        # Move to next step
        self.current_step += 1

        if self.current_step >= self.max_steps:
            # End of episode - close any open position
            if self.position != 0:
                pnl = (close - self.entry_price) * self.position * self.position_size * 10
                reward += self._calculate_reward(pnl)
                self._record_trade(pnl)
                self.position = 0
            done = True
            info['termination'] = 'end_of_data'

        next_state = self._get_state()

        return next_state, reward, done, info

    def _calculate_reward(self, pnl):
        """
        Calculate shaped reward based on PnL and risk metrics

        Reward shaping:
        - High reward for profitable trades
        - Penalty for losses
        - Bonus for maintaining low drawdown
        - Penalty for violating risk limits
        """
        # Base reward from PnL (normalized)
        reward = pnl / 100  # $100 profit = 1.0 reward

        # Bonus for profitable trades
        if pnl > 0:
            reward *= 1.5  # Amplify profitable trades
        else:
            reward *= 2.0  # Amplify penalty for losses (encourages risk management)

        # Drawdown penalty
        if self.drawdown > 500:
            reward -= 0.5
        if self.drawdown > 1000:
            reward -= 1.0

        # Update balance and daily PnL
        self.balance += pnl
        self.daily_pnl += pnl
        self.total_pnl += pnl

        return reward

    def _record_trade(self, pnl):
        """Record trade for analysis"""
        self.trades.append({
            'step': self.current_step,
            'pnl': pnl,
            'balance': self.balance,
            'drawdown': self.drawdown
        })

    def _calculate_atr(self, data, period=14):
        """Calculate Average True Range"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.tail(period).mean()
        return atr if not np.isnan(atr) else 0

    def _calculate_rsi(self, data, period=14):
        """Calculate Relative Strength Index"""
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).tail(period).mean()
        loss = -delta.where(delta < 0, 0).tail(period).mean()
        if loss == 0:
            return 100
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi if not np.isnan(rsi) else 50


class DQNAgent:
    """
    Deep Q-Network agent for trading decisions

    Uses neural network to approximate Q-values for state-action pairs.
    Learns optimal policy through experience replay and target network.
    """

    def __init__(self, state_size=20, action_size=4, learning_rate=0.001):
        """
        Initialize DQN agent

        Args:
            state_size: Dimension of state vector
            action_size: Number of possible actions
            learning_rate: Learning rate for optimizer
        """
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate

        # Hyperparameters
        self.gamma = 0.95  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.batch_size = 64
        self.memory = deque(maxlen=10000)  # Experience replay buffer

        # Build networks
        if HAS_TENSORFLOW:
            self.model = self._build_model()
            self.target_model = self._build_model()
            self.update_target_model()
        else:
            self.model = None
            self.target_model = None
            print("Warning: TensorFlow not available. Using random policy.")

        self.logger = logging.getLogger(__name__)

    def _build_model(self):
        """Build neural network for Q-value approximation"""
        model = keras.Sequential([
            layers.Input(shape=(self.state_size,)),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu'),
            layers.Dense(self.action_size, activation='linear')
        ])

        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse'
        )

        return model

    def update_target_model(self):
        """Copy weights from model to target model"""
        if self.model and self.target_model:
            self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state, training=True):
        """
        Choose action using epsilon-greedy policy

        Args:
            state: Current state
            training: If True, use exploration; if False, use pure exploitation

        Returns:
            action: Chosen action (0-3)
        """
        if not HAS_TENSORFLOW or self.model is None:
            # Fallback: random policy
            return random.randrange(self.action_size)

        # Epsilon-greedy
        if training and np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)

        # Exploitation: choose best action
        q_values = self.model.predict(state.reshape(1, -1), verbose=0)
        return np.argmax(q_values[0])

    def replay(self):
        """
        Train on batch of experiences from memory (experience replay)
        """
        if not HAS_TENSORFLOW or len(self.memory) < self.batch_size:
            return

        # Sample random batch
        batch = random.sample(self.memory, self.batch_size)

        states = np.array([exp[0] for exp in batch])
        actions = np.array([exp[1] for exp in batch])
        rewards = np.array([exp[2] for exp in batch])
        next_states = np.array([exp[3] for exp in batch])
        dones = np.array([exp[4] for exp in batch])

        # Predict Q-values
        current_q = self.model.predict(states, verbose=0)
        next_q = self.target_model.predict(next_states, verbose=0)

        # Update Q-values using Bellman equation
        for i in range(self.batch_size):
            if dones[i]:
                current_q[i][actions[i]] = rewards[i]
            else:
                current_q[i][actions[i]] = rewards[i] + self.gamma * np.max(next_q[i])

        # Train model
        self.model.fit(states, current_q, epochs=1, verbose=0)

        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save(self, filepath):
        """Save model weights"""
        if self.model:
            self.model.save_weights(filepath)
            self.logger.info(f"Model saved to {filepath}")

    def load(self, filepath):
        """Load model weights"""
        if self.model and os.path.exists(filepath):
            self.model.load_weights(filepath)
            self.update_target_model()
            self.logger.info(f"Model loaded from {filepath}")


def train_rl_agent(data: pd.DataFrame, episodes=100, save_path='./models'):
    """
    Train RL agent on historical data

    Args:
        data: Historical OHLCV data
        episodes: Number of training episodes
        save_path: Directory to save trained models

    Returns:
        Trained agent and training history
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    env = TradingEnvironment(data)
    agent = DQNAgent()

    history = {
        'episode': [],
        'total_reward': [],
        'total_pnl': [],
        'num_trades': [],
        'epsilon': [],
        'final_balance': []
    }

    logger.info(f"Starting RL training for {episodes} episodes...")

    for episode in range(episodes):
        state = env.reset()
        total_reward = 0
        done = False

        while not done:
            # Agent chooses action
            action = agent.act(state, training=True)

            # Execute action
            next_state, reward, done, info = env.step(action)

            # Store experience
            agent.remember(state, action, reward, next_state, done)

            # Learn from experience
            agent.replay()

            state = next_state
            total_reward += reward

        # Update target network periodically
        if episode % 10 == 0:
            agent.update_target_model()

        # Record history
        history['episode'].append(episode)
        history['total_reward'].append(total_reward)
        history['total_pnl'].append(env.total_pnl)
        history['num_trades'].append(len(env.trades))
        history['epsilon'].append(agent.epsilon)
        history['final_balance'].append(env.balance)

        # Log progress
        if episode % 10 == 0:
            logger.info(f"Episode {episode}/{episodes} - "
                       f"Reward: {total_reward:.2f}, "
                       f"PnL: ${env.total_pnl:.2f}, "
                       f"Trades: {len(env.trades)}, "
                       f"Epsilon: {agent.epsilon:.3f}, "
                       f"Balance: ${env.balance:.2f}")

        # Save best model
        if env.total_pnl > 0 and episode % 50 == 0:
            os.makedirs(save_path, exist_ok=True)
            agent.save(os.path.join(save_path, f'rl_agent_episode_{episode}.h5'))

    # Save final model
    os.makedirs(save_path, exist_ok=True)
    agent.save(os.path.join(save_path, 'rl_agent_final.h5'))

    # Save history
    history_df = pd.DataFrame(history)
    history_df.to_csv(os.path.join(save_path, 'rl_training_history.csv'), index=False)

    logger.info("Training complete!")

    return agent, history_df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train RL agent for crude oil trading')
    parser.add_argument('--data', type=str, required=True, help='Path to historical OHLCV CSV')
    parser.add_argument('--episodes', type=int, default=100, help='Number of training episodes')
    parser.add_argument('--output', type=str, default='./models', help='Output directory')

    args = parser.parse_args()

    # Load data
    print(f"Loading data from {args.data}...")
    data = pd.read_csv(args.data)

    # Train agent
    agent, history = train_rl_agent(data, episodes=args.episodes, save_path=args.output)

    print("\nTraining Summary:")
    print(f"Final Episode Reward: {history['total_reward'].iloc[-1]:.2f}")
    print(f"Final PnL: ${history['total_pnl'].iloc[-1]:.2f}")
    print(f"Total Trades: {history['num_trades'].iloc[-1]}")
    print(f"Final Balance: ${history['final_balance'].iloc[-1]:.2f}")
