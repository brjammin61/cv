use anyhow::{Context, Result};
use dotenv::dotenv;
use mev_bot::*;
use solana_sdk::signature::{Keypair, Signer};
use std::env;
use std::str::FromStr;
use tracing::{error, info};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<()> {
    // Load .env file
    dotenv().ok();

    // Initialize logging
    init_logging();

    info!("🚀 MEV Bot Starting...");

    // Load configuration
    let config = load_config()?;

    // Load wallet
    let wallet = load_wallet()?;
    info!("Wallet loaded: {}", wallet.pubkey());

    // Get RPC URL
    let rpc_url = env::var("RPC_URL").context("RPC_URL not set in environment")?;
    let ws_url = env::var("WS_URL").unwrap_or_else(|_| {
        rpc_url.replace("https://", "wss://").replace("http://", "ws://")
    });

    info!("RPC URL: {}", rpc_url);
    info!("WebSocket URL: {}", ws_url);

    // Check if dry run mode
    if config.dry_run {
        info!("⚠️  DRY RUN MODE ENABLED - No real transactions will be sent!");
    } else {
        info!("💰 LIVE MODE - Real transactions will be executed!");
    }

    // Create orchestrator
    let orchestrator = MevOrchestrator::new(rpc_url.clone(), wallet, config.clone())
        .context("Failed to create MEV orchestrator")?;

    // Start dashboard printer (every 5 minutes)
    // TODO: Integrate metrics properly with orchestrator

    // Handle Ctrl+C gracefully
    let (shutdown_tx, mut shutdown_rx) = tokio::sync::mpsc::channel::<()>(1);

    tokio::spawn(async move {
        tokio::signal::ctrl_c().await.ok();
        info!("🛑 Received shutdown signal...");
        let _ = shutdown_tx.send(()).await;
    });

    // Start the bot
    info!("✅ Starting MEV bot with all strategies...");
    info!("Configuration:");
    info!("  - Min Profit: {} SOL ({}%)", config.min_profit_sol, config.min_profit_percent);
    info!("  - Max Trade Size: {} SOL", config.max_trade_size_sol);
    info!("  - Max Daily Loss: {} SOL", config.max_daily_loss_sol);
    info!("  - Scan Interval: {} ms", config.scan_interval_ms);
    info!("  - Priority Fee: {} microlamports", config.priority_fee_microlamports);

    // Run bot until shutdown signal
    tokio::select! {
        result = orchestrator.start() => {
            match result {
                Ok(_) => {
                    info!("Bot stopped normally");
                }
                Err(e) => {
                    error!("Bot error: {}", e);
                    return Err(e);
                }
            }
        }
        _ = shutdown_rx.recv() => {
            info!("Shutting down gracefully...");

            // Print final statistics
            let stats = orchestrator.get_stats().await;
            let risk_metrics = orchestrator.get_risk_metrics().await;

            info!("═══════════════════════════════════════");
            info!("           FINAL STATISTICS            ");
            info!("═══════════════════════════════════════");
            info!("Opportunities Found: {}", stats.total_opportunities_found);
            info!("Trades Executed: {}", stats.total_trades_executed);
            info!("  ✅ Successful: {}", stats.successful_trades);
            info!("  ❌ Failed: {}", stats.failed_trades);
            info!("Daily P/L: {} SOL", risk_metrics.daily_pnl);
            info!("Net P/L: {} SOL", stats.total_profit_sol);
            info!("═══════════════════════════════════════");

            info!("👋 Goodbye!");
        }
    }

    Ok(())
}

/// Initialize logging with pretty formatting
fn init_logging() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,mev_bot=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer().with_target(false))
        .init();
}

/// Load bot configuration from environment variables
fn load_config() -> Result<BotConfig> {
    Ok(BotConfig {
        // Strategy toggles
        enable_cross_dex_arb: parse_env_bool("ENABLE_CROSS_DEX_ARB", true)?,
        enable_multi_hop_arb: parse_env_bool("ENABLE_MULTI_HOP_ARB", true)?,
        enable_mev_searcher: parse_env_bool("ENABLE_MEV_SEARCHER", false)?, // Default off for safety

        // Trading parameters
        min_profit_sol: parse_env_decimal("MIN_PROFIT_SOL", "0.01")?,
        min_profit_percent: parse_env_decimal("MIN_PROFIT_PERCENT", "0.5")?,
        max_trade_size_sol: parse_env_decimal("MAX_TRADE_SIZE_SOL", "10.0")?,
        max_total_exposure_sol: parse_env_decimal("MAX_TOTAL_EXPOSURE_SOL", "50.0")?,
        max_daily_loss_sol: parse_env_decimal("MAX_DAILY_LOSS_SOL", "5.0")?,

        // Execution parameters
        max_slippage_bps: parse_env_u64("MAX_SLIPPAGE_BPS", 50)?,
        priority_fee_microlamports: parse_env_u64("PRIORITY_FEE_MICROLAMPORTS", 100_000)?,
        tx_timeout_seconds: parse_env_u64("TX_TIMEOUT_SECONDS", 30)?,

        // DEX fees (basis points)
        jupiter_fee_bps: parse_env_u64("JUPITER_FEE_BPS", 0)?, // Jupiter aggregator has no fee
        raydium_fee_bps: parse_env_u64("RAYDIUM_FEE_BPS", 25)?, // 0.25%
        orca_fee_bps: parse_env_u64("ORCA_FEE_BPS", 30)?,      // 0.30%

        // Base transaction fee (Solana network fee)
        base_tx_fee: parse_env_decimal("BASE_TX_FEE", "0.000005")?,

        // Operational
        scan_interval_ms: parse_env_u64("SCAN_INTERVAL_MS", 1000)?,
        max_concurrent_ops: parse_env_u64("MAX_CONCURRENT_OPS", 10)? as usize,

        // Jito
        use_jito_bundles: parse_env_bool("USE_JITO_BUNDLES", false)?,
        jito_tip_lamports: parse_env_u64("JITO_TIP_LAMPORTS", 10_000)?,

        // Safety
        dry_run: parse_env_bool("DRY_RUN", true)?,
    })
}

/// Load wallet from environment
fn load_wallet() -> Result<Keypair> {
    let wallet_key = env::var("WALLET_PRIVATE_KEY")
        .context("WALLET_PRIVATE_KEY not set in environment")?;

    // Try parsing as JSON array [1,2,3,...] first
    if wallet_key.trim().starts_with('[') {
        let bytes: Vec<u8> = serde_json::from_str(&wallet_key)
            .context("Failed to parse wallet key as JSON array")?;
        let keypair = Keypair::from_bytes(&bytes)
            .map_err(|e| anyhow::anyhow!("Invalid keypair bytes: {}", e))?;
        return Ok(keypair);
    }

    // Try parsing as base58
    match bs58::decode(&wallet_key).into_vec() {
        Ok(bytes) => {
            let keypair = Keypair::from_bytes(&bytes)
                .map_err(|e| anyhow::anyhow!("Invalid keypair from base58: {}", e))?;
            Ok(keypair)
        }
        Err(_) => {
            anyhow::bail!("Wallet key must be base58 string or JSON array of bytes")
        }
    }
}

/// Parse environment variable as Decimal with default
fn parse_env_decimal(key: &str, default: &str) -> Result<rust_decimal::Decimal> {
    let value = env::var(key).unwrap_or_else(|_| default.to_string());
    rust_decimal::Decimal::from_str(&value)
        .with_context(|| format!("Failed to parse {} as decimal", key))
}

/// Parse environment variable as u64 with default
fn parse_env_u64(key: &str, default: u64) -> Result<u64> {
    let value = env::var(key)
        .unwrap_or_else(|_| default.to_string())
        .parse::<u64>()
        .with_context(|| format!("Failed to parse {} as u64", key))?;
    Ok(value)
}

/// Parse environment variable as bool with default
fn parse_env_bool(key: &str, default: bool) -> Result<bool> {
    let value = env::var(key).unwrap_or_else(|_| default.to_string());
    match value.to_lowercase().as_str() {
        "true" | "1" | "yes" => Ok(true),
        "false" | "0" | "no" => Ok(false),
        _ => anyhow::bail!("{} must be true/false, got: {}", key, value),
    }
}
