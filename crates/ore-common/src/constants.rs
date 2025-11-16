/// ORE V2 Protocol Constants

/// Grid dimensions (5x5)
pub const GRID_SIZE: usize = 25;
pub const GRID_WIDTH: usize = 5;
pub const GRID_HEIGHT: usize = 5;

/// Round timing (60 seconds per round)
pub const ROUND_DURATION_SECS: u64 = 60;

/// Sniper window (last N seconds of a round)
pub const SNIPER_WINDOW_SECS: u64 = 5;

/// Maximum stake multiplier
pub const MAX_STAKE_MULTIPLIER: f64 = 2.0;

/// Refining fee (10%)
pub const REFINING_FEE_PCT: f64 = 0.10;

/// Default Jito tip (in lamports)
pub const DEFAULT_JITO_TIP: u64 = 10_000; // 0.00001 SOL

/// Aggressive mode Jito tip (for motherlode)
pub const AGGRESSIVE_JITO_TIP: u64 = 100_000; // 0.0001 SOL

/// Minimum hash difficulty target
pub const MIN_DIFFICULTY: u32 = 8;

/// Redis channel names
pub const REDIS_CHANNEL_SOLUTIONS: &str = "ore:solutions";
pub const REDIS_CHANNEL_GRID_STATE: &str = "ore:grid_state";
pub const REDIS_CHANNEL_STRATEGY: &str = "ore:strategy";
pub const REDIS_CHANNEL_COMMANDS: &str = "ore:commands";

/// Redis keys
pub const REDIS_KEY_BEST_SOLUTION: &str = "ore:best_solution";
pub const REDIS_KEY_CURRENT_ROUND: &str = "ore:current_round";
pub const REDIS_KEY_METRICS: &str = "ore:metrics";

/// State monitoring
pub const WS_RECONNECT_DELAY_MS: u64 = 5000;
pub const STATE_UPDATE_INTERVAL_MS: u64 = 1000;

/// Mempool monitoring
pub const MEMPOOL_POLL_INTERVAL_MS: u64 = 500;
pub const SHADOW_BOARD_CONFIDENCE_THRESHOLD: f64 = 0.7;

/// EV calculation parameters
pub const EV_MIN_SAMPLE_SIZE: usize = 10;
pub const EV_HISTORICAL_WEIGHT: f64 = 0.3;
pub const EV_CURRENT_WEIGHT: f64 = 0.7;

/// Motherlode thresholds
pub const MOTHERLODE_AGGRESSIVE_THRESHOLD: u64 = 1_000_000_000; // 1 SOL in lamports
pub const MOTHERLODE_EV_MULTIPLIER: f64 = 1.5;

/// Treasury management
pub const AUTO_STAKE_INTERVAL_SECS: u64 = 3600; // 1 hour
pub const MIN_SOL_RESERVE: u64 = 100_000_000; // 0.1 SOL

/// Worker heartbeat
pub const WORKER_HEARTBEAT_INTERVAL_SECS: u64 = 30;
pub const WORKER_TIMEOUT_SECS: u64 = 120;

/// Retry configuration
pub const MAX_RETRIES: u32 = 3;
pub const RETRY_DELAY_MS: u64 = 1000;

/// Logging
pub const LOG_LEVEL_DEFAULT: &str = "info";
pub const METRICS_PORT: u16 = 9090;
