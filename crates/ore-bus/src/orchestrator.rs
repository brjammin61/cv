use anyhow::Result;
use ore_common::{
    BusConfig, GridState, MiningSolution, ShadowBoardState, StrategyDecision,
    REDIS_CHANNEL_GRID_STATE, REDIS_CHANNEL_SOLUTIONS, REDIS_KEY_BEST_SOLUTION,
    ROUND_DURATION_SECS, utils,
};
use ore_jito::{BundleBuilder, JitoClient, MempoolMonitor};
use ore_state_monitor::StateManager;
use ore_strategist::DecisionEngine;
use ore_treasury::TreasuryManager;
use redis::aio::ConnectionManager;
use redis::AsyncCommands;
use solana_client::rpc_client::RpcClient;
use solana_sdk::signature::{Keypair, read_keypair_file};
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::RwLock;
use tokio::time::{interval, sleep};
use tracing::{debug, error, info, warn};

/// Central orchestrator - the "Bus" that coordinates everything
///
/// Responsibilities:
/// 1. Consume mining solutions from workers
/// 2. Monitor grid state in real-time
/// 3. Track mempool for pending transactions
/// 4. Calculate optimal strategy
/// 5. Execute Jito bundles at the perfect moment
pub struct Orchestrator {
    config: BusConfig,
    redis: ConnectionManager,
    rpc_client: RpcClient,
    jito_client: JitoClient,
    bundle_builder: BundleBuilder,
    decision_engine: DecisionEngine,
    state_manager: Arc<StateManager>,
    mempool_monitor: Option<Arc<MempoolMonitor>>,
    treasury_manager: Option<Arc<TreasuryManager>>,
    keypair: Keypair,
    current_solution: Arc<RwLock<Option<MiningSolution>>>,
}

impl Orchestrator {
    pub async fn new(config: BusConfig) -> Result<Self> {
        info!("Initializing orchestrator");

        // Load wallet
        let keypair = read_keypair_file(&config.wallet_path)
            .map_err(|e| anyhow::anyhow!("Failed to read keypair: {}", e))?;

        info!("Wallet: {}", keypair.pubkey());

        // Initialize Redis
        let client = redis::Client::open(config.redis_url.as_str())?;
        let redis = ConnectionManager::new(client).await?;

        // Initialize RPC client
        let rpc_client = RpcClient::new(config.rpc_url.clone());

        // Initialize Jito client
        let jito_client = JitoClient::new(
            config.jito_url.clone(),
            config.jito_tip_account.clone(),
        );

        // Initialize bundle builder
        let bundle_builder = BundleBuilder::new(
            keypair.pubkey(),
            config.jito_tip_account.clone(),
        )?;

        // Initialize decision engine
        let decision_engine = DecisionEngine::new(
            100_000_000,  // 0.1 SOL min stake
            config.max_stake_per_round,
            0.7,          // moderate-aggressive risk tolerance
            config.max_stake_per_round,
        );

        // Initialize state manager
        let state_manager = Arc::new(
            StateManager::new(
                config.ws_url.clone(),
                config.grid_program_id.clone(),
                config.redis_url.clone(),
            )
            .await?,
        );

        // Initialize mempool monitor
        let mempool_monitor = if config.enable_mempool_monitoring {
            Some(Arc::new(MempoolMonitor::new(
                config.rpc_url.clone(),
                config.grid_program_id.clone(),
            )))
        } else {
            None
        };

        // Treasury manager would be initialized here
        let treasury_manager = None;

        Ok(Self {
            config,
            redis,
            rpc_client,
            jito_client,
            bundle_builder,
            decision_engine,
            state_manager,
            mempool_monitor,
            treasury_manager,
            keypair,
            current_solution: Arc::new(RwLock::new(None)),
        })
    }

    /// Main run loop
    pub async fn run(&mut self) -> Result<()> {
        info!("Starting orchestrator");

        // Start state manager
        {
            let state_manager = Arc::clone(&self.state_manager);
            tokio::spawn(async move {
                if let Err(e) = state_manager.start().await {
                    error!("State manager error: {:?}", e);
                }
            });
        }

        // Start mempool monitor if enabled
        if let Some(mempool) = &self.mempool_monitor {
            let mempool = Arc::clone(mempool);
            tokio::spawn(async move {
                mempool.start().await;
            });
        }

        // Start solution consumer
        {
            let orchestrator_clone = self as *const Orchestrator;
            tokio::spawn(async move {
                // Safety: Orchestrator lives for program duration
                let orchestrator = unsafe { &*orchestrator_clone };
                orchestrator.consume_solutions().await;
            });
        }

        // Main round loop
        self.round_loop().await?;

        Ok(())
    }

    /// Main round loop - execute strategy each round
    async fn round_loop(&self) -> Result<()> {
        let mut round_interval = interval(Duration::from_secs(ROUND_DURATION_SECS));

        loop {
            round_interval.tick().await;

            if let Err(e) = self.execute_round().await {
                error!("Round execution error: {:?}", e);
            }
        }
    }

    /// Execute strategy for one round
    async fn execute_round(&self) -> Result<()> {
        info!("=== Starting new round ===");

        // Wait for grid state
        let grid_state = self.wait_for_grid_state().await?;

        info!(
            "Round {}: {} SOL total staked, {} SOL motherlode",
            grid_state.round,
            grid_state.total_staked as f64 / 1e9,
            grid_state.motherlode_size as f64 / 1e9
        );

        // Wait for a valid mining solution
        let solution = self.wait_for_solution(&grid_state).await?;

        info!(
            "Got solution: difficulty={}, time_remaining={}s",
            solution.difficulty,
            utils::time_remaining_in_round(grid_state.round_start)
        );

        // Build shadow board if mempool monitoring enabled
        let shadow_state = if let Some(mempool) = &self.mempool_monitor {
            let pending_txs = mempool.get_pending_transactions().await;
            info!("Pending transactions: {}", pending_txs.len());

            Some(
                ore_strategist::ShadowBoard::new(30)
                    .build_shadow_state(&grid_state, pending_txs)?,
            )
        } else {
            None
        };

        // Make strategic decision
        let decision = self.decision_engine.decide(&grid_state, shadow_state.as_ref())?;

        info!(
            "Strategy: block={}, stake={} SOL, EV={:.4}, mode={:?}",
            decision.target_block,
            decision.stake_amount as f64 / 1e9,
            decision.expected_value,
            decision.execution_mode
        );

        // Execute based on mode
        match decision.execution_mode {
            ore_common::ExecutionMode::Sniper | ore_common::ExecutionMode::Aggressive => {
                // Wait until the last second
                self.wait_for_sniper_window(grid_state.round_start).await;
                self.execute_bundle(&solution, &decision, &grid_state).await?;
            }
            _ => {
                // Execute immediately
                self.execute_bundle(&solution, &decision, &grid_state).await?;
            }
        }

        Ok(())
    }

    /// Wait for grid state to be available
    async fn wait_for_grid_state(&self) -> Result<GridState> {
        for _ in 0..30 {
            if let Some(state) = self.state_manager.get_current_state().await {
                return Ok(state);
            }

            debug!("Waiting for grid state...");
            sleep(Duration::from_secs(1)).await;
        }

        Err(anyhow::anyhow!("Timeout waiting for grid state"))
    }

    /// Wait for a valid mining solution
    async fn wait_for_solution(&self, grid_state: &GridState) -> Result<MiningSolution> {
        let start = utils::current_timestamp();

        loop {
            // Check if we have a solution
            if let Some(solution) = self.current_solution.read().await.clone() {
                return Ok(solution);
            }

            // Check timeout (leave time for strategy)
            let elapsed = utils::current_timestamp() - start;
            if elapsed > (ROUND_DURATION_SECS as i64 - 20) {
                return Err(anyhow::anyhow!("No solution found in time"));
            }

            sleep(Duration::from_millis(100)).await;
        }
    }

    /// Wait for sniper window
    async fn wait_for_sniper_window(&self, round_start: i64) {
        loop {
            let time_remaining = utils::time_remaining_in_round(round_start);

            if time_remaining <= ore_common::SNIPER_WINDOW_SECS {
                info!("SNIPER WINDOW - executing now!");
                break;
            }

            sleep(Duration::from_secs(1)).await;
        }
    }

    /// Execute the bundle
    async fn execute_bundle(
        &self,
        solution: &MiningSolution,
        decision: &StrategyDecision,
        grid_state: &GridState,
    ) -> Result<()> {
        info!("Executing bundle...");

        // Get recent blockhash
        let recent_blockhash = self.rpc_client.get_latest_blockhash()?;

        // Build bundle
        let bundle = self.bundle_builder.build_mining_bundle(
            solution,
            decision.target_block,
            decision.stake_amount,
            decision.jito_tip,
            recent_blockhash,
            &self.keypair,
        )?;

        // Submit via Jito
        let bundle_id = self.jito_client.send_bundle_with_retry(bundle, 3).await?;

        info!("✅ Bundle submitted: {}", bundle_id);

        // Clear current solution
        *self.current_solution.write().await = None;

        Ok(())
    }

    /// Consume solutions from Redis
    async fn consume_solutions(&self) {
        let mut pubsub = self.redis.clone().into_pubsub();

        if let Err(e) = pubsub.subscribe(REDIS_CHANNEL_SOLUTIONS).await {
            error!("Failed to subscribe to solutions: {:?}", e);
            return;
        }

        info!("Subscribed to solution channel");

        loop {
            if let Ok(msg) = pubsub.on_message().next().await {
                let payload: String = match msg.get_payload() {
                    Ok(p) => p,
                    Err(e) => {
                        error!("Failed to get payload: {:?}", e);
                        continue;
                    }
                };

                match serde_json::from_str::<MiningSolution>(&payload) {
                    Ok(solution) => {
                        info!(
                            "Received solution from {}: difficulty={}",
                            solution.worker_id, solution.difficulty
                        );

                        // Update current solution
                        *self.current_solution.write().await = Some(solution);
                    }
                    Err(e) => {
                        error!("Failed to parse solution: {:?}", e);
                    }
                }
            }
        }
    }
}
