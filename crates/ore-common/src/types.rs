use serde::{Deserialize, Serialize};
use solana_sdk::pubkey::Pubkey;

/// Represents a valid hash solution from a miner
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MiningSolution {
    /// The nonce that produces the valid hash
    pub nonce: u64,
    /// The resulting hash digest
    pub hash: [u8; 32],
    /// The difficulty (number of leading zeros)
    pub difficulty: u32,
    /// Timestamp when this solution was found
    pub timestamp: i64,
    /// Worker ID that found this solution
    pub worker_id: String,
}

/// Represents the 5x5 Grid state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GridState {
    /// Current round number
    pub round: u64,
    /// 25 blocks (5x5 grid) with their stake amounts
    pub blocks: [BlockState; 25],
    /// Current motherlode jackpot size
    pub motherlode_size: u64,
    /// Total SOL staked this round
    pub total_staked: u64,
    /// Timestamp of round start
    pub round_start: i64,
    /// Last update timestamp
    pub last_update: i64,
}

/// Individual block in the 5x5 grid
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BlockState {
    /// Block index (0-24)
    pub index: u8,
    /// Total SOL staked on this block
    pub staked_amount: u64,
    /// Number of participants on this block
    pub participant_count: u32,
    /// Historical win rate (for ML models)
    pub historical_win_rate: f64,
}

/// Expected Value calculation result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EVCalculation {
    /// Block index
    pub block_index: u8,
    /// Expected value in SOL
    pub expected_value: f64,
    /// Probability of winning
    pub win_probability: f64,
    /// Estimated competition intensity
    pub competition_score: f64,
    /// Whether this includes motherlode consideration
    pub includes_motherlode: bool,
    /// Recommended stake amount
    pub recommended_stake: u64,
}

/// Shadow board state (includes pending mempool txs)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShadowBoardState {
    /// Current confirmed grid state
    pub confirmed_state: GridState,
    /// Predicted state after pending transactions land
    pub predicted_state: GridState,
    /// Pending transactions we've observed
    pub pending_transactions: Vec<PendingTransaction>,
    /// Confidence score in predictions (0.0-1.0)
    pub confidence: f64,
}

/// Pending transaction observed in mempool
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingTransaction {
    pub signature: String,
    pub block_index: u8,
    pub stake_amount: u64,
    pub timestamp: i64,
}

/// Strategy decision from the strategist
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyDecision {
    /// Chosen block to stake on
    pub target_block: u8,
    /// Amount to stake
    pub stake_amount: u64,
    /// Expected value of this decision
    pub expected_value: f64,
    /// Confidence score (0.0-1.0)
    pub confidence: f64,
    /// Execution mode
    pub execution_mode: ExecutionMode,
    /// Recommended Jito tip in lamports
    pub jito_tip: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ExecutionMode {
    /// Normal execution - submit during the round
    Normal,
    /// Sniper mode - wait until last second
    Sniper,
    /// Aggressive mode - higher stakes for motherlode
    Aggressive,
    /// Conservative mode - lower risk
    Conservative,
}

/// Configuration for a miner worker
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MinerConfig {
    pub worker_id: String,
    pub redis_url: String,
    pub gpu_enabled: bool,
    pub gpu_device_id: Option<u32>,
    pub target_difficulty: u32,
}

/// Configuration for the bus/dispatcher
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BusConfig {
    pub redis_url: String,
    pub rpc_url: String,
    pub ws_url: String,
    pub jito_url: String,
    pub jito_tip_account: String,
    pub wallet_path: String,
    pub grid_program_id: String,
    pub max_stake_per_round: u64,
    pub enable_mempool_monitoring: bool,
}

/// Treasury management configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TreasuryConfig {
    pub auto_stake_enabled: bool,
    pub target_multiplier: f64, // Target stake multiplier (max 2.0)
    pub profit_take_threshold: f64, // When to liquidate ORE for SOL
    pub reserve_sol_amount: u64, // Minimum SOL to keep for operations
}

/// Metrics snapshot
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricsSnapshot {
    pub timestamp: i64,
    pub total_rounds_played: u64,
    pub rounds_won: u64,
    pub total_ore_earned: u64,
    pub total_sol_spent: u64,
    pub current_roi: f64,
    pub average_ev_accuracy: f64,
    pub current_stake_multiplier: f64,
}
