use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BotConfig {
    /// RPC endpoint URL (private/premium RPC recommended)
    pub rpc_url: String,

    /// Path to wallet keypair JSON file
    pub wallet_path: String,

    /// ORE token mint address
    pub ore_mint: String,

    /// SOL token mint address (wrapped SOL)
    pub sol_mint: String,

    /// Path to miner executable
    pub miner_path: String,

    /// Arguments to pass to miner
    pub miner_args: Vec<String>,

    /// Estimated compute units for mining transaction
    pub estimated_compute_units: u64,

    /// Profit threshold percentage (e.g., 5.0 = 5%)
    pub profit_threshold_percent: f64,

    /// Poll interval in seconds
    pub poll_interval_seconds: u64,

    /// Slippage tolerance in basis points (e.g., 50 = 0.5%)
    pub slippage_bps: u64,

    /// Amount of SOL to swap per buy operation
    pub swap_amount_sol: f64,

    /// Auto-execute swaps (if false, will only log what it would do)
    pub auto_execute_swaps: bool,
}

impl BotConfig {
    /// Load configuration from environment variables
    pub fn load() -> Result<Self> {
        let rpc_url = env::var("RPC_URL")
            .context("RPC_URL not set in environment")?;

        let wallet_path = env::var("WALLET_PATH")
            .unwrap_or_else(|_| "wallet.json".to_string());

        let ore_mint = env::var("ORE_MINT")
            .unwrap_or_else(|_| "oreoU2P8bN6jkk3jbaiVxYnG1dCXcYxwhwyK9jSybcp".to_string());

        let sol_mint = env::var("SOL_MINT")
            .unwrap_or_else(|_| "So11111111111111111111111111111111111111112".to_string());

        let miner_path = env::var("MINER_PATH")
            .unwrap_or_else(|_| "ore".to_string());

        let miner_args_str = env::var("MINER_ARGS")
            .unwrap_or_else(|_| "mine".to_string());
        let miner_args: Vec<String> = miner_args_str
            .split_whitespace()
            .map(|s| s.to_string())
            .collect();

        let estimated_compute_units = env::var("ESTIMATED_COMPUTE_UNITS")
            .unwrap_or_else(|_| "200000".to_string())
            .parse::<u64>()
            .context("Invalid ESTIMATED_COMPUTE_UNITS")?;

        let profit_threshold_percent = env::var("PROFIT_THRESHOLD_PERCENT")
            .unwrap_or_else(|_| "5.0".to_string())
            .parse::<f64>()
            .context("Invalid PROFIT_THRESHOLD_PERCENT")?;

        let poll_interval_seconds = env::var("POLL_INTERVAL_SECONDS")
            .unwrap_or_else(|_| "30".to_string())
            .parse::<u64>()
            .context("Invalid POLL_INTERVAL_SECONDS")?;

        let slippage_bps = env::var("SLIPPAGE_BPS")
            .unwrap_or_else(|_| "50".to_string())
            .parse::<u64>()
            .context("Invalid SLIPPAGE_BPS")?;

        let swap_amount_sol = env::var("SWAP_AMOUNT_SOL")
            .unwrap_or_else(|_| "0.1".to_string())
            .parse::<f64>()
            .context("Invalid SWAP_AMOUNT_SOL")?;

        let auto_execute_swaps = env::var("AUTO_EXECUTE_SWAPS")
            .unwrap_or_else(|_| "false".to_string())
            .parse::<bool>()
            .unwrap_or(false);

        Ok(Self {
            rpc_url,
            wallet_path,
            ore_mint,
            sol_mint,
            miner_path,
            miner_args,
            estimated_compute_units,
            profit_threshold_percent,
            poll_interval_seconds,
            slippage_bps,
            swap_amount_sol,
            auto_execute_swaps,
        })
    }

    /// Validate configuration
    pub fn validate(&self) -> Result<()> {
        if self.profit_threshold_percent < 0.0 || self.profit_threshold_percent > 100.0 {
            anyhow::bail!("profit_threshold_percent must be between 0 and 100");
        }

        if self.poll_interval_seconds < 1 {
            anyhow::bail!("poll_interval_seconds must be at least 1");
        }

        if self.slippage_bps > 10000 {
            anyhow::bail!("slippage_bps cannot exceed 10000 (100%)");
        }

        if self.swap_amount_sol <= 0.0 {
            anyhow::bail!("swap_amount_sol must be positive");
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_validation() {
        let mut config = BotConfig {
            rpc_url: "https://api.mainnet-beta.solana.com".to_string(),
            wallet_path: "wallet.json".to_string(),
            ore_mint: "ore".to_string(),
            sol_mint: "sol".to_string(),
            miner_path: "ore".to_string(),
            miner_args: vec!["mine".to_string()],
            estimated_compute_units: 200000,
            profit_threshold_percent: 5.0,
            poll_interval_seconds: 30,
            slippage_bps: 50,
            swap_amount_sol: 0.1,
            auto_execute_swaps: false,
        };

        assert!(config.validate().is_ok());

        // Test invalid threshold
        config.profit_threshold_percent = 150.0;
        assert!(config.validate().is_err());

        config.profit_threshold_percent = 5.0;
        assert!(config.validate().is_ok());
    }
}
