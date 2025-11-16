use anyhow::Result;
use tracing::info;

/// Reinforcement learning-based strategy optimizer
///
/// Uses Q-learning to optimize strategy parameters over time
pub struct StrategyOptimizer {
    /// Minimum stake parameter
    min_stake: f64,
    /// Maximum stake parameter
    max_stake: f64,
    /// Risk tolerance parameter
    risk_tolerance: f64,
    /// Learning rate
    learning_rate: f64,
    /// Discount factor
    discount_factor: f64,
    /// Exploration rate (epsilon)
    epsilon: f64,
    /// Total rounds trained
    rounds_trained: u64,
}

#[derive(Debug, Clone)]
pub struct OptimizedParameters {
    pub min_stake: u64,
    pub max_stake: u64,
    pub risk_tolerance: f64,
    pub motherlode_threshold: u64,
    pub sniper_window_secs: u64,
}

impl StrategyOptimizer {
    pub fn new() -> Self {
        Self {
            min_stake: 100_000_000.0, // 0.1 SOL
            max_stake: 1_000_000_000.0, // 1 SOL
            risk_tolerance: 0.7,
            learning_rate: 0.1,
            discount_factor: 0.95,
            epsilon: 0.1, // 10% exploration
            rounds_trained: 0,
        }
    }

    /// Update parameters based on round outcome
    pub fn update_from_outcome(
        &mut self,
        won: bool,
        predicted_ev: f64,
        actual_return: f64,
        stake_used: u64,
    ) -> Result<()> {
        // Calculate reward
        let reward = if won {
            actual_return - stake_used as f64
        } else {
            -(stake_used as f64)
        };

        // Calculate EV prediction error
        let ev_error = (actual_return - predicted_ev).abs();

        // Adjust parameters using gradient-like updates

        // If we're consistently underperforming, adjust risk tolerance
        if reward < 0.0 && ev_error > predicted_ev * 0.5 {
            // We were too optimistic, reduce risk
            self.risk_tolerance *= (1.0 - self.learning_rate);
            self.risk_tolerance = self.risk_tolerance.max(0.3);

            info!("Reducing risk tolerance to {:.2}", self.risk_tolerance);
        } else if reward > predicted_ev * 2.0 {
            // We were too conservative, increase risk
            self.risk_tolerance *= (1.0 + self.learning_rate);
            self.risk_tolerance = self.risk_tolerance.min(1.0);

            info!("Increasing risk tolerance to {:.2}", self.risk_tolerance);
        }

        // Adjust stake limits based on performance
        if won && stake_used as f64 > self.max_stake * 0.8 {
            // High stakes are working, can increase max
            self.max_stake *= (1.0 + self.learning_rate * 0.5);
            self.max_stake = self.max_stake.min(10_000_000_000.0); // Cap at 10 SOL

            info!("Increasing max stake to {:.2} SOL", self.max_stake / 1e9);
        }

        self.rounds_trained += 1;

        // Decay exploration rate over time
        self.epsilon = (0.1 * (1.0 - self.rounds_trained as f64 / 10000.0)).max(0.01);

        Ok(())
    }

    /// Get current optimized parameters
    pub fn get_parameters(&self) -> OptimizedParameters {
        OptimizedParameters {
            min_stake: self.min_stake as u64,
            max_stake: self.max_stake as u64,
            risk_tolerance: self.risk_tolerance,
            motherlode_threshold: self.calculate_motherlode_threshold(),
            sniper_window_secs: self.calculate_sniper_window(),
        }
    }

    fn calculate_motherlode_threshold(&self) -> u64 {
        // Higher risk tolerance = lower threshold (more aggressive on motherlode)
        let base_threshold = 1_000_000_000u64; // 1 SOL
        (base_threshold as f64 * (2.0 - self.risk_tolerance)) as u64
    }

    fn calculate_sniper_window(&self) -> u64 {
        // Higher risk tolerance = shorter window (more aggressive timing)
        let base_window = 5u64;
        ((base_window as f64 * (1.5 - self.risk_tolerance * 0.5)) as u64).max(2)
    }

    /// Should we explore (try new strategies) or exploit (use best known)?
    pub fn should_explore(&self) -> bool {
        rand::random::<f64>() < self.epsilon
    }
}
