use anyhow::Result;
use config::Config;
use ore_common::{
    MiningSolution, MinerConfig, OreError, REDIS_CHANNEL_SOLUTIONS,
    REDIS_KEY_BEST_SOLUTION, WORKER_HEARTBEAT_INTERVAL_SECS,
};
use ore_solver_ffi::DrillxSolver;
use redis::aio::ConnectionManager;
use redis::AsyncCommands;
use std::time::Instant;
use tokio::time::{interval, Duration};
use tracing::{error, info, warn};

/// Distributed miner worker
///
/// This is the "labor" component of the system. It runs on GPU instances
/// and continuously searches for valid hash solutions.
///
/// When a solution is found, it pushes it to Redis for the Bus to consume.
struct MinerWorker {
    config: MinerConfig,
    solver: DrillxSolver,
    redis: ConnectionManager,
}

impl MinerWorker {
    async fn new(config: MinerConfig) -> Result<Self> {
        info!("Initializing miner worker: {}", config.worker_id);

        // Initialize solver
        let solver = DrillxSolver::new(config.gpu_enabled, config.gpu_device_id)
            .map_err(|e| anyhow::anyhow!("Failed to initialize solver: {:?}", e))?;

        // Connect to Redis
        let client = redis::Client::open(config.redis_url.as_str())?;
        let redis = ConnectionManager::new(client).await?;

        Ok(Self {
            config,
            solver,
            redis,
        })
    }

    /// Start mining
    async fn run(&mut self) -> Result<()> {
        info!("Worker {} starting mining loop", self.config.worker_id);

        // Spawn heartbeat task
        let heartbeat_handle = {
            let worker_id = self.config.worker_id.clone();
            let mut redis = self.redis.clone();

            tokio::spawn(async move {
                let mut interval = interval(Duration::from_secs(WORKER_HEARTBEAT_INTERVAL_SECS));

                loop {
                    interval.tick().await;

                    let heartbeat_key = format!("ore:worker:{}:heartbeat", worker_id);
                    let timestamp = ore_common::utils::current_timestamp();

                    if let Err(e) = redis.set_ex::<_, _, ()>(
                        heartbeat_key,
                        timestamp,
                        WORKER_HEARTBEAT_INTERVAL_SECS * 2,
                    ).await {
                        error!("Failed to send heartbeat: {:?}", e);
                    }
                }
            })
        };

        // Main mining loop
        loop {
            // Get current mining challenge
            // In production, this would fetch from the ORE V2 program
            let challenge = self.get_current_challenge().await?;

            // Mine for a solution
            match self.mine_solution(&challenge).await {
                Ok(solution) => {
                    info!(
                        "Worker {} found solution: nonce={}, difficulty={}",
                        self.config.worker_id, solution.nonce, solution.difficulty
                    );

                    // Publish solution to Redis
                    if let Err(e) = self.publish_solution(&solution).await {
                        error!("Failed to publish solution: {:?}", e);
                    }
                }
                Err(e) => {
                    warn!("Mining failed: {:?}", e);
                }
            }
        }
    }

    /// Get current mining challenge
    async fn get_current_challenge(&self) -> Result<[u8; 32]> {
        // In production, fetch from on-chain program state
        // For now, use a placeholder

        let mut redis = self.redis.clone();
        let challenge_key = "ore:current_challenge";

        if let Ok(Some(challenge_bytes)) = redis.get::<_, Option<Vec<u8>>>(challenge_key).await {
            if challenge_bytes.len() == 32 {
                let mut challenge = [0u8; 32];
                challenge.copy_from_slice(&challenge_bytes);
                return Ok(challenge);
            }
        }

        // Default challenge if none exists
        Ok([0u8; 32])
    }

    /// Mine for a solution
    async fn mine_solution(&self, challenge: &[u8; 32]) -> Result<MiningSolution> {
        info!("Mining with target difficulty: {}", self.config.target_difficulty);

        let start = Instant::now();

        // Run solver (this is CPU/GPU intensive)
        let solution = tokio::task::spawn_blocking({
            let solver = &self.solver as *const DrillxSolver;
            let challenge = *challenge;
            let difficulty = self.config.target_difficulty;
            let worker_id = self.config.worker_id.clone();

            move || {
                // Safety: We're in a blocking task and the solver lives for the program duration
                let solver = unsafe { &*solver };

                solver.solve(
                    &challenge,
                    difficulty,
                    0, // unlimited iterations
                    worker_id,
                )
            }
        })
        .await??;

        let elapsed = start.elapsed();

        info!(
            "Solution found in {:.2}s (difficulty: {}, hashrate: {:.0} H/s)",
            elapsed.as_secs_f64(),
            solution.difficulty,
            solution.nonce as f64 / elapsed.as_secs_f64()
        );

        Ok(solution)
    }

    /// Publish solution to Redis
    async fn publish_solution(&self, solution: &MiningSolution) -> Result<()> {
        let mut redis = self.redis.clone();

        // Serialize solution
        let serialized = serde_json::to_string(solution)?;

        // Publish to channel
        redis.publish(REDIS_CHANNEL_SOLUTIONS, &serialized).await?;

        // Also update "best solution" key if this is better
        if let Ok(Some(current_best)) = redis.get::<_, Option<String>>(REDIS_KEY_BEST_SOLUTION).await {
            if let Ok(current_solution) = serde_json::from_str::<MiningSolution>(&current_best) {
                if solution.difficulty <= current_solution.difficulty {
                    // Current best is better or equal
                    return Ok(());
                }
            }
        }

        // This is the new best solution
        redis.set(REDIS_KEY_BEST_SOLUTION, serialized).await?;

        info!("New best solution: difficulty {}", solution.difficulty);

        Ok(())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into()),
        )
        .init();

    // Load configuration
    dotenv::dotenv().ok();

    let config_builder = Config::builder()
        .set_default("worker_id", hostname::get()?.to_string_lossy().to_string())?
        .set_default("redis_url", "redis://127.0.0.1:6379")?
        .set_default("gpu_enabled", true)?
        .set_default("target_difficulty", 8)?
        .add_source(config::Environment::with_prefix("ORE_MINER"));

    let config: MinerConfig = config_builder.build()?.try_deserialize()?;

    info!("Starting ORE miner worker: {}", config.worker_id);
    info!("GPU enabled: {}", config.gpu_enabled);
    info!("Target difficulty: {}", config.target_difficulty);

    // Create and run worker
    let mut worker = MinerWorker::new(config).await?;
    worker.run().await?;

    Ok(())
}
