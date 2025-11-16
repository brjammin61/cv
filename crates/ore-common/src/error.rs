use thiserror::Error;

#[derive(Error, Debug)]
pub enum OreError {
    #[error("Solver error: {0}")]
    Solver(String),

    #[error("Redis error: {0}")]
    Redis(#[from] redis::RedisError),

    #[error("Solana client error: {0}")]
    SolanaClient(#[from] solana_sdk::client_error::ClientError),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("Invalid configuration: {0}")]
    InvalidConfig(String),

    #[error("State monitoring error: {0}")]
    StateMonitoring(String),

    #[error("Jito submission error: {0}")]
    JitoSubmission(String),

    #[error("Strategy calculation error: {0}")]
    Strategy(String),

    #[error("Treasury operation error: {0}")]
    Treasury(String),

    #[error("Network error: {0}")]
    Network(#[from] reqwest::Error),

    #[error("Timeout error: {0}")]
    Timeout(String),

    #[error("Invalid state: {0}")]
    InvalidState(String),

    #[error("Worker not found: {0}")]
    WorkerNotFound(String),

    #[error("Insufficient funds: required {required}, available {available}")]
    InsufficientFunds { required: u64, available: u64 },

    #[error("Round expired: {0}")]
    RoundExpired(u64),

    #[error("Unknown error: {0}")]
    Unknown(String),
}

pub type Result<T> = std::result::Result<T, OreError>;
