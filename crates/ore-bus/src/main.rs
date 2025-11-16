mod orchestrator;

use anyhow::Result;
use config::Config;
use ore_common::BusConfig;
use tracing::info;

use crate::orchestrator::Orchestrator;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into()),
        )
        .json()
        .init();

    // Load configuration
    dotenv::dotenv().ok();

    let config_builder = Config::builder()
        .set_default("redis_url", "redis://127.0.0.1:6379")?
        .set_default("rpc_url", "https://api.mainnet-beta.solana.com")?
        .set_default("ws_url", "wss://api.mainnet-beta.solana.com")?
        .set_default("jito_url", "https://mainnet.block-engine.jito.wtf/api/v1/bundles")?
        .set_default("jito_tip_account", "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5")?
        .set_default("grid_program_id", "ore1111111111111111111111111111111111111111")?
        .set_default("max_stake_per_round", 1_000_000_000u64)? // 1 SOL
        .set_default("enable_mempool_monitoring", true)?
        .add_source(config::Environment::with_prefix("ORE_BUS"));

    let config: BusConfig = config_builder.build()?.try_deserialize()?;

    info!("=== ORE V2 Dominance Bot - Bus/Dispatcher ===");
    info!("RPC: {}", config.rpc_url);
    info!("WebSocket: {}", config.ws_url);
    info!("Jito: {}", config.jito_url);
    info!("Max stake per round: {} SOL", config.max_stake_per_round as f64 / 1e9);
    info!("Mempool monitoring: {}", config.enable_mempool_monitoring);

    // Create and start orchestrator
    let mut orchestrator = Orchestrator::new(config).await?;
    orchestrator.run().await?;

    Ok(())
}
