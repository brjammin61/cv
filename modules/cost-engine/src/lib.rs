use anyhow::{Context, Result};
use solana_client::nonblocking::rpc_client::RpcClient;
use solana_sdk::commitment_config::CommitmentConfig;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::{debug, info, warn};

/// ORE protocol fee percentage (10%)
const ORE_PROTOCOL_FEE_PERCENT: f64 = 0.10;

/// Number of slots to look back for priority fee estimation
const PRIORITY_FEE_LOOKBACK_SLOTS: u64 = 150;

/// Percentile to use for priority fee estimation (median)
const PRIORITY_FEE_PERCENTILE: f64 = 50.0;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MiningCostResult {
    /// Total breakeven cost in SOL to mine 1 ORE
    pub breakeven_cost_sol: f64,

    /// Priority fee in micro-lamports per compute unit
    pub priority_fee_microlamports: u64,

    /// Estimated compute units needed for mining transaction
    pub estimated_compute_units: u64,

    /// Total transaction fee in lamports
    pub total_tx_fee_lamports: u64,

    /// ORE protocol fee (10%)
    pub ore_protocol_fee_sol: f64,

    /// Timestamp of calculation
    pub timestamp: i64,
}

impl MiningCostResult {
    /// Get total cost in lamports
    pub fn total_cost_lamports(&self) -> u64 {
        self.total_tx_fee_lamports + (self.ore_protocol_fee_sol * 1_000_000_000.0) as u64
    }
}

pub struct CostEngine {
    rpc_client: Arc<RpcClient>,
    estimated_compute_units: u64,
}

impl CostEngine {
    /// Create a new CostEngine instance
    pub fn new(rpc_url: String, estimated_compute_units: u64) -> Self {
        let rpc_client = Arc::new(RpcClient::new_with_commitment(
            rpc_url,
            CommitmentConfig::confirmed(),
        ));

        Self {
            rpc_client,
            estimated_compute_units,
        }
    }

    /// Calculate the real-time breakeven cost to mine 1 ORE
    ///
    /// This is the "secret sauce" - it dynamically calculates the cost based on:
    /// 1. Current network priority fees (via getRecentPrioritizationFees)
    /// 2. Estimated compute units for mining transaction
    /// 3. ORE protocol's 10% fee
    pub async fn calculate_mining_cost(&self) -> Result<MiningCostResult> {
        info!("Calculating real-time mining cost...");

        // Get recent prioritization fees from the network
        let priority_fee = self.get_priority_fee().await
            .context("Failed to get priority fee from network")?;

        debug!("Priority fee: {} micro-lamports/CU", priority_fee);

        // Calculate transaction fee
        // Formula: (priority_fee_microlamports / 1_000_000) * compute_units
        let priority_fee_lamports =
            (priority_fee as f64 / 1_000_000.0 * self.estimated_compute_units as f64) as u64;

        // Add base transaction fee (5000 lamports)
        let total_tx_fee_lamports = priority_fee_lamports + 5000;

        // Calculate ORE protocol fee (10% of mined ORE)
        // This assumes we mine 1 ORE and lose 10% to protocol
        // In reality, this should be calculated based on actual mining rewards
        let ore_protocol_fee_sol = 0.1; // 10% of 1 ORE (in SOL equivalent)

        // Total breakeven cost in SOL
        let breakeven_cost_sol =
            (total_tx_fee_lamports as f64 / 1_000_000_000.0) + ore_protocol_fee_sol;

        let result = MiningCostResult {
            breakeven_cost_sol,
            priority_fee_microlamports: priority_fee,
            estimated_compute_units: self.estimated_compute_units,
            total_tx_fee_lamports,
            ore_protocol_fee_sol,
            timestamp: chrono::Utc::now().timestamp(),
        };

        info!(
            "Mining cost calculated: {} SOL (tx fee: {} lamports, priority: {} μL/CU)",
            result.breakeven_cost_sol,
            result.total_tx_fee_lamports,
            result.priority_fee_microlamports
        );

        Ok(result)
    }

    /// Get the current priority fee from the network
    ///
    /// Uses getRecentPrioritizationFees RPC method to determine
    /// the minimum priority fee needed for a transaction to land
    async fn get_priority_fee(&self) -> Result<u64> {
        // In a production implementation, this would use:
        // rpc_client.get_recent_prioritization_fees(&[])
        //
        // For now, we'll implement a simulation that queries the network
        // and calculates the appropriate percentile

        // This is a placeholder - in production, you'd use the actual RPC call:
        // let fees = self.rpc_client.get_recent_prioritization_fees(&[]).await?;

        // For demonstration, we'll use a realistic default
        // In production, this should query actual network data
        let simulated_fee = self.simulate_priority_fee_query().await?;

        Ok(simulated_fee)
    }

    /// Simulate priority fee query (placeholder for production implementation)
    ///
    /// In production, this should be replaced with actual RPC calls to
    /// getRecentPrioritizationFees
    async fn simulate_priority_fee_query(&self) -> Result<u64> {
        // Get recent blocks to analyze priority fees
        // In a real implementation, you would:
        // 1. Call get_recent_prioritization_fees RPC method
        // 2. Analyze the returned fees
        // 3. Calculate the appropriate percentile (e.g., 50th percentile for median)

        warn!("Using simulated priority fee - replace with actual RPC call in production");

        // Simulated realistic priority fee (in micro-lamports per compute unit)
        // This represents a moderate network congestion scenario
        // Range: 1-100 for low congestion, 100-10000 for high congestion
        let base_fee = 1000u64; // 1000 micro-lamports/CU (moderate)

        // Add some variance based on time to simulate real network conditions
        let variance = (chrono::Utc::now().timestamp() % 500) as u64;
        let simulated_fee = base_fee + variance;

        debug!("Simulated priority fee: {} micro-lamports/CU", simulated_fee);

        Ok(simulated_fee)
    }

    /// Update the estimated compute units (can be calibrated based on actual mining)
    pub fn set_compute_units(&mut self, compute_units: u64) {
        info!("Updating estimated compute units: {} -> {}",
              self.estimated_compute_units, compute_units);
        self.estimated_compute_units = compute_units;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_cost_calculation() {
        let engine = CostEngine::new(
            "https://api.mainnet-beta.solana.com".to_string(),
            200_000, // Estimated compute units
        );

        let result = engine.calculate_mining_cost().await.unwrap();

        assert!(result.breakeven_cost_sol > 0.0);
        assert!(result.priority_fee_microlamports > 0);
        assert_eq!(result.estimated_compute_units, 200_000);
    }
}
