use ore_common::{MetricsSnapshot, OreError, Result, TreasuryConfig, MAX_STAKE_MULTIPLIER};
use solana_client::rpc_client::RpcClient;
use solana_sdk::{
    pubkey::Pubkey,
    signature::{Keypair, Signer},
};
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio::time::{interval, Duration};
use tracing::{info, warn};

/// Treasury manager for automated staking and profit management
///
/// Responsibilities:
/// 1. Auto-stake ORE rewards to increase multiplier
/// 2. Track profitability metrics
/// 3. Manage SOL reserves for operations
/// 4. Execute profit-taking when conditions are met
pub struct TreasuryManager {
    config: TreasuryConfig,
    rpc_client: RpcClient,
    wallet: Pubkey,
    metrics: Arc<RwLock<MetricsSnapshot>>,
}

impl TreasuryManager {
    pub fn new(config: TreasuryConfig, rpc_client: RpcClient, wallet: Pubkey) -> Self {
        let metrics = Arc::new(RwLock::new(MetricsSnapshot {
            timestamp: ore_common::utils::current_timestamp(),
            total_rounds_played: 0,
            rounds_won: 0,
            total_ore_earned: 0,
            total_sol_spent: 0,
            current_roi: 0.0,
            average_ev_accuracy: 0.0,
            current_stake_multiplier: 1.0,
        }));

        Self {
            config,
            rpc_client,
            wallet,
            metrics,
        }
    }

    /// Start the treasury manager
    pub async fn start(self: Arc<Self>) {
        info!("Starting treasury manager");

        // Spawn auto-staking task
        if self.config.auto_stake_enabled {
            let manager = Arc::clone(&self);
            tokio::spawn(async move {
                manager.auto_stake_loop().await;
            });
        }

        // Spawn metrics tracking task
        let manager = Arc::clone(&self);
        tokio::spawn(async move {
            manager.metrics_loop().await;
        });
    }

    /// Auto-staking loop
    async fn auto_stake_loop(&self) {
        let mut stake_interval = interval(Duration::from_secs(3600)); // Every hour

        loop {
            stake_interval.tick().await;

            if let Err(e) = self.auto_stake_rewards().await {
                warn!("Auto-stake failed: {:?}", e);
            }
        }
    }

    /// Auto-stake ORE rewards
    async fn auto_stake_rewards(&self) -> Result<()> {
        let metrics = self.metrics.read().await;

        // Check if we've reached the target multiplier
        if metrics.current_stake_multiplier >= self.config.target_multiplier {
            info!(
                "Target multiplier reached: {:.2}x (target: {:.2}x)",
                metrics.current_stake_multiplier, self.config.target_multiplier
            );
            return Ok(());
        }

        drop(metrics);

        // Get ORE balance
        let ore_balance = self.get_ore_balance().await?;

        if ore_balance == 0 {
            info!("No ORE to stake");
            return Ok(());
        }

        info!(
            "Auto-staking {} ORE (current multiplier: {:.2}x)",
            ore_balance,
            self.metrics.read().await.current_stake_multiplier
        );

        // Execute stake transaction
        // In production, this would call the actual ORE V2 stake instruction
        self.stake_ore(ore_balance).await?;

        // Update metrics
        let mut metrics = self.metrics.write().await;
        metrics.current_stake_multiplier = (metrics.current_stake_multiplier + 0.1)
            .min(MAX_STAKE_MULTIPLIER);

        info!("Staked successfully. New multiplier: {:.2}x", metrics.current_stake_multiplier);

        Ok(())
    }

    /// Metrics tracking loop
    async fn metrics_loop(&self) {
        let mut metrics_interval = interval(Duration::from_secs(300)); // Every 5 minutes

        loop {
            metrics_interval.tick().await;

            if let Err(e) = self.update_metrics().await {
                warn!("Metrics update failed: {:?}", e);
            }
        }
    }

    /// Update performance metrics
    async fn update_metrics(&self) -> Result<()> {
        let mut metrics = self.metrics.write().await;

        // Calculate ROI
        if metrics.total_sol_spent > 0 {
            let ore_value_in_sol = self.estimate_ore_value(metrics.total_ore_earned).await?;
            metrics.current_roi = (ore_value_in_sol - metrics.total_sol_spent as f64)
                / metrics.total_sol_spent as f64;
        }

        // Calculate win rate
        if metrics.total_rounds_played > 0 {
            let win_rate = metrics.rounds_won as f64 / metrics.total_rounds_played as f64;
            info!(
                "Performance: {} rounds played, {} won ({:.1}% win rate), ROI: {:.2}%",
                metrics.total_rounds_played,
                metrics.rounds_won,
                win_rate * 100.0,
                metrics.current_roi * 100.0
            );
        }

        metrics.timestamp = ore_common::utils::current_timestamp();

        Ok(())
    }

    /// Get ORE token balance
    async fn get_ore_balance(&self) -> Result<u64> {
        // In production, fetch actual ORE token account balance
        // For now, return placeholder
        Ok(0)
    }

    /// Stake ORE tokens
    async fn stake_ore(&self, amount: u64) -> Result<()> {
        // In production, construct and send stake transaction
        // This would interact with the ORE V2 staking program
        info!("Staking {} ORE (placeholder)", amount);
        Ok(())
    }

    /// Estimate ORE value in SOL
    async fn estimate_ore_value(&self, ore_amount: u64) -> Result<f64> {
        // In production, fetch from DEX price oracle
        // For now, use placeholder conversion
        Ok(ore_amount as f64 * 0.001) // Placeholder: 1 ORE = 0.001 SOL
    }

    /// Get current metrics
    pub async fn get_metrics(&self) -> MetricsSnapshot {
        self.metrics.read().await.clone()
    }

    /// Record a round result
    pub async fn record_round(&self, won: bool, ore_earned: u64, sol_spent: u64) {
        let mut metrics = self.metrics.write().await;

        metrics.total_rounds_played += 1;
        if won {
            metrics.rounds_won += 1;
        }
        metrics.total_ore_earned += ore_earned;
        metrics.total_sol_spent += sol_spent;
    }

    /// Check if we should take profits
    pub async fn should_take_profits(&self) -> bool {
        let metrics = self.metrics.read().await;

        // Take profits if ROI exceeds threshold
        if metrics.current_roi > self.config.profit_take_threshold {
            info!(
                "Profit-taking triggered: ROI {:.2}% > threshold {:.2}%",
                metrics.current_roi * 100.0,
                self.config.profit_take_threshold * 100.0
            );
            return true;
        }

        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_metrics_recording() {
        let config = TreasuryConfig {
            auto_stake_enabled: true,
            target_multiplier: 2.0,
            profit_take_threshold: 0.5,
            reserve_sol_amount: 100_000_000,
        };

        let rpc_client = RpcClient::new("https://api.mainnet-beta.solana.com".to_string());
        let wallet = Keypair::new().pubkey();

        let manager = TreasuryManager::new(config, rpc_client, wallet);

        // Record some rounds
        manager.record_round(true, 1_000_000, 100_000_000).await;
        manager.record_round(false, 0, 100_000_000).await;
        manager.record_round(true, 1_000_000, 100_000_000).await;

        let metrics = manager.get_metrics().await;

        assert_eq!(metrics.total_rounds_played, 3);
        assert_eq!(metrics.rounds_won, 2);
        assert_eq!(metrics.total_ore_earned, 2_000_000);
    }
}
