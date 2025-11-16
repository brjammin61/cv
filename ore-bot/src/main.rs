use anyhow::{Context, Result};
use cost_engine::{CostEngine, MiningCostResult};
use miner_control::{MinerControl, MinerState};
use price_oracle::PriceOracle;
use swap_executor::SwapExecutor;
use solana_sdk::signature::{Keypair, Signer};
use std::sync::Arc;
use tokio::time::{sleep, Duration};
use tracing::{error, info, warn};

mod config;
use config::BotConfig;

/// Decision threshold (profit margin required to switch strategies)
const PROFIT_THRESHOLD_PERCENT: f64 = 5.0;

/// Poll interval for checking prices and costs
const POLL_INTERVAL_SECONDS: u64 = 30;

/// Bot decision
#[derive(Debug, Clone, PartialEq, Eq)]
enum Decision {
    Mine,
    Buy,
    Hold, // When difference is within threshold
}

struct OreArbitrageBot {
    config: BotConfig,
    cost_engine: CostEngine,
    price_oracle: PriceOracle,
    swap_executor: SwapExecutor,
    miner_control: MinerControl,
    current_decision: Decision,
}

impl OreArbitrageBot {
    /// Create a new bot instance
    async fn new(config: BotConfig) -> Result<Self> {
        info!("Initializing ORE Arbitrage Bot...");

        // Load wallet keypair
        let wallet = Self::load_wallet(&config.wallet_path)?;

        // Initialize modules
        let cost_engine = CostEngine::new(
            config.rpc_url.clone(),
            config.estimated_compute_units,
        );

        let price_oracle = PriceOracle::with_mints(
            config.ore_mint.clone(),
            config.sol_mint.clone(),
        )?;

        let swap_executor = SwapExecutor::new(
            config.rpc_url.clone(),
            wallet,
        )?;

        let miner_control = MinerControl::new(
            config.miner_path.clone(),
            config.miner_args.clone(),
        );

        info!("Bot initialized successfully");

        Ok(Self {
            config,
            cost_engine,
            price_oracle,
            swap_executor,
            miner_control,
            current_decision: Decision::Hold,
        })
    }

    /// Load wallet keypair from file
    fn load_wallet(path: &str) -> Result<Keypair> {
        let wallet_bytes = std::fs::read(path)
            .context(format!("Failed to read wallet file: {}", path))?;

        let wallet_json: Vec<u8> = serde_json::from_slice(&wallet_bytes)
            .context("Failed to parse wallet JSON")?;

        let keypair = Keypair::from_bytes(&wallet_json)
            .context("Failed to create keypair from bytes")?;

        info!("Wallet loaded: {}", keypair.pubkey());
        Ok(keypair)
    }

    /// Main bot loop
    async fn run(&mut self) -> Result<()> {
        info!("Starting ORE Arbitrage Bot main loop...");
        info!("Profit threshold: {}%", self.config.profit_threshold_percent);
        info!("Poll interval: {}s", self.config.poll_interval_seconds);

        loop {
            match self.decision_cycle().await {
                Ok(_) => {}
                Err(e) => {
                    error!("Error in decision cycle: {}", e);
                    // Don't crash, just log and continue
                }
            }

            sleep(Duration::from_secs(self.config.poll_interval_seconds)).await;
        }
    }

    /// Single decision cycle
    ///
    /// This is the core logic that:
    /// 1. Calculates mining cost
    /// 2. Fetches market price
    /// 3. Compares and decides
    /// 4. Executes action
    async fn decision_cycle(&mut self) -> Result<()> {
        info!("=== Starting decision cycle ===");

        // Step 1: Get mining cost
        let mining_cost = self.cost_engine.calculate_mining_cost().await
            .context("Failed to calculate mining cost")?;

        info!("Mining breakeven cost: {} SOL", mining_cost.breakeven_cost_sol);

        // Step 2: Get market price
        let market_price = self.price_oracle.get_ore_price().await
            .context("Failed to get market price")?;

        info!("Market price: {} SOL", market_price.price_per_ore_sol);

        // Step 3: Make decision
        let decision = self.make_decision(
            mining_cost.breakeven_cost_sol,
            market_price.price_per_ore_sol,
        );

        info!("Decision: {:?}", decision);

        // Step 4: Execute action based on decision
        self.execute_decision(decision, &mining_cost, market_price.price_per_ore_sol).await?;

        info!("=== Decision cycle complete ===\n");
        Ok(())
    }

    /// Make decision based on costs and prices
    ///
    /// Core arbitrage logic:
    /// - If mining_cost < market_price (by threshold): MINE
    /// - If market_price < mining_cost (by threshold): BUY
    /// - Otherwise: HOLD (within threshold, don't switch)
    fn make_decision(&self, mining_cost: f64, market_price: f64) -> Decision {
        let threshold = self.config.profit_threshold_percent / 100.0;

        // Calculate the difference as a percentage
        let diff_percent = (mining_cost - market_price).abs() / market_price;

        if mining_cost < market_price {
            // Mining is cheaper
            let savings = (market_price - mining_cost) / market_price;
            if savings >= threshold {
                info!(
                    "Mining is {}% cheaper than buying - MINE",
                    savings * 100.0
                );
                return Decision::Mine;
            }
        } else {
            // Buying is cheaper
            let savings = (mining_cost - market_price) / mining_cost;
            if savings >= threshold {
                info!(
                    "Buying is {}% cheaper than mining - BUY",
                    savings * 100.0
                );
                return Decision::Buy;
            }
        }

        info!(
            "Difference ({}%) within threshold ({}%) - HOLD",
            diff_percent * 100.0,
            self.config.profit_threshold_percent
        );
        Decision::Hold
    }

    /// Execute the decision
    async fn execute_decision(
        &mut self,
        decision: Decision,
        mining_cost: &MiningCostResult,
        market_price: f64,
    ) -> Result<()> {
        // Only take action if decision changed or if we need to maintain state
        match decision {
            Decision::Mine => {
                if self.current_decision != Decision::Mine {
                    info!("Switching to MINING mode");
                    self.current_decision = Decision::Mine;

                    // Stop any existing miner
                    if self.miner_control.is_running() {
                        self.miner_control.stop()?;
                    }

                    // Start miner
                    match self.miner_control.start() {
                        Ok(_) => {
                            info!("Miner started successfully");
                        }
                        Err(e) => {
                            error!("Failed to start miner: {}", e);
                            self.current_decision = Decision::Hold;
                        }
                    }
                } else {
                    // Already mining, check if still running
                    if !self.miner_control.is_running() {
                        warn!("Miner stopped unexpectedly, restarting...");
                        self.miner_control.start()?;
                    }
                }
            }

            Decision::Buy => {
                if self.current_decision != Decision::Buy {
                    info!("Switching to BUYING mode");
                    self.current_decision = Decision::Buy;

                    // Stop miner if running
                    if self.miner_control.is_running() {
                        info!("Stopping miner to switch to buying");
                        self.miner_control.stop()?;
                    }
                }

                // Execute swap
                if self.config.auto_execute_swaps {
                    info!("Executing swap: {} SOL -> ORE", self.config.swap_amount_sol);
                    let swap_amount_lamports =
                        (self.config.swap_amount_sol * 1_000_000_000.0) as u64;

                    match self.swap_executor.swap_sol_to_ore(
                        swap_amount_lamports,
                        &self.config.ore_mint,
                        &self.config.sol_mint,
                        self.config.slippage_bps,
                        Some(mining_cost.total_tx_fee_lamports),
                    ).await {
                        Ok(result) => {
                            info!("Swap executed: {}", result.signature);
                            info!("Swap details: {:?}", result);
                        }
                        Err(e) => {
                            error!("Swap failed: {}", e);
                        }
                    }
                } else {
                    info!("Auto-swap disabled. Would buy {} ORE at {} SOL",
                          self.config.swap_amount_sol / market_price,
                          market_price);
                }
            }

            Decision::Hold => {
                // Don't change current state, but ensure consistency
                if self.current_decision == Decision::Mine {
                    // Should keep mining
                    if !self.miner_control.is_running() {
                        warn!("Miner stopped in HOLD state, restarting...");
                        self.miner_control.start()?;
                    }
                } else {
                    // Make sure miner is stopped
                    if self.miner_control.is_running() {
                        self.miner_control.stop()?;
                    }
                }
            }
        }

        Ok(())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into())
        )
        .init();

    info!("ORE Arbitrage Bot starting...");

    // Load configuration
    dotenv::dotenv().ok();
    let config = BotConfig::load()?;

    // Create and run bot
    let mut bot = OreArbitrageBot::new(config).await?;

    // Run bot (this will loop forever)
    bot.run().await?;

    Ok(())
}
