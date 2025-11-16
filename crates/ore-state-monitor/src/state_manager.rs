use ore_common::{GridState, Result, OreError, REDIS_CHANNEL_GRID_STATE};
use redis::aio::ConnectionManager;
use redis::AsyncCommands;
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio::time::{interval, Duration};
use tracing::{debug, error, info};

use crate::WebSocketMonitor;

/// Central state manager that coordinates state monitoring and broadcasting
pub struct StateManager {
    monitor: WebSocketMonitor,
    redis: ConnectionManager,
    state: Arc<RwLock<Option<GridState>>>,
}

impl StateManager {
    pub async fn new(
        ws_url: String,
        grid_program_id: String,
        redis_url: String,
    ) -> Result<Self> {
        let client = redis::Client::open(redis_url.as_str())
            .map_err(|e| OreError::Redis(e))?;

        let redis = ConnectionManager::new(client)
            .await
            .map_err(|e| OreError::Redis(e))?;

        let monitor = WebSocketMonitor::new(ws_url, grid_program_id);

        Ok(Self {
            monitor,
            redis,
            state: Arc::new(RwLock::new(None)),
        })
    }

    /// Start the state manager
    pub async fn start(self: Arc<Self>) -> Result<()> {
        info!("Starting StateManager");

        // Spawn WebSocket monitoring task
        let monitor_handle = {
            let manager = Arc::clone(&self);
            tokio::spawn(async move {
                if let Err(e) = manager.monitor.start().await {
                    error!("Monitor error: {:?}", e);
                }
            })
        };

        // Spawn state broadcasting task
        let broadcast_handle = {
            let manager = Arc::clone(&self);
            tokio::spawn(async move {
                manager.broadcast_state_updates().await;
            })
        };

        // Wait for both tasks
        tokio::select! {
            _ = monitor_handle => {
                info!("Monitor task completed");
            }
            _ = broadcast_handle => {
                info!("Broadcast task completed");
            }
        }

        Ok(())
    }

    /// Periodically broadcast state updates to Redis
    async fn broadcast_state_updates(&self) {
        let mut interval = interval(Duration::from_secs(1));

        loop {
            interval.tick().await;

            // Get current state from monitor
            if let Some(grid_state) = self.monitor.get_state().await {
                // Update local state
                {
                    let mut state = self.state.write().await;
                    *state = Some(grid_state.clone());
                }

                // Publish to Redis
                if let Err(e) = self.publish_state(&grid_state).await {
                    error!("Failed to publish state: {:?}", e);
                }
            }
        }
    }

    async fn publish_state(&self, state: &GridState) -> Result<()> {
        let mut conn = self.redis.clone();

        let serialized = serde_json::to_string(state)
            .map_err(|e| OreError::Serialization(e))?;

        conn.publish(REDIS_CHANNEL_GRID_STATE, serialized)
            .await
            .map_err(|e| OreError::Redis(e))?;

        debug!("Published grid state for round {}", state.round);

        Ok(())
    }

    /// Get the current grid state
    pub async fn get_current_state(&self) -> Option<GridState> {
        self.state.read().await.clone()
    }
}
