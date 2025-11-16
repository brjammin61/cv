use futures::{SinkExt, StreamExt};
use ore_common::{GridState, BlockState, OreError, Result, GRID_SIZE};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio::time::{sleep, Duration};
use tokio_tungstenite::{connect_async, tungstenite::Message};
use tracing::{debug, error, info, warn};

/// WebSocket monitor for real-time account updates
pub struct WebSocketMonitor {
    ws_url: String,
    grid_program_id: String,
    state: Arc<RwLock<Option<GridState>>>,
}

#[derive(Debug, Serialize, Deserialize)]
struct SubscriptionRequest {
    jsonrpc: String,
    id: u64,
    method: String,
    params: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct NotificationResponse {
    jsonrpc: String,
    method: String,
    params: NotificationParams,
}

#[derive(Debug, Serialize, Deserialize)]
struct NotificationParams {
    result: NotificationResult,
    subscription: u64,
}

#[derive(Debug, Serialize, Deserialize)]
struct NotificationResult {
    context: Context,
    value: AccountInfo,
}

#[derive(Debug, Serialize, Deserialize)]
struct Context {
    slot: u64,
}

#[derive(Debug, Serialize, Deserialize)]
struct AccountInfo {
    data: Vec<String>,
    executable: bool,
    lamports: u64,
    owner: String,
    #[serde(rename = "rentEpoch")]
    rent_epoch: u64,
}

impl WebSocketMonitor {
    pub fn new(ws_url: String, grid_program_id: String) -> Self {
        Self {
            ws_url,
            grid_program_id,
            state: Arc::new(RwLock::new(None)),
        }
    }

    /// Get the current grid state
    pub async fn get_state(&self) -> Option<GridState> {
        self.state.read().await.clone()
    }

    /// Start monitoring the grid state
    pub async fn start(&self) -> Result<()> {
        loop {
            match self.run_monitor().await {
                Ok(_) => {
                    info!("WebSocket monitor stopped gracefully");
                    break;
                }
                Err(e) => {
                    error!("WebSocket error: {:?}, reconnecting in 5s...", e);
                    sleep(Duration::from_secs(5)).await;
                }
            }
        }
        Ok(())
    }

    async fn run_monitor(&self) -> Result<()> {
        info!("Connecting to WebSocket: {}", self.ws_url);

        let (ws_stream, _) = connect_async(&self.ws_url)
            .await
            .map_err(|e| OreError::StateMonitoring(format!("Failed to connect: {}", e)))?;

        info!("WebSocket connected");

        let (mut write, mut read) = ws_stream.split();

        // Subscribe to program account updates
        let subscribe_request = SubscriptionRequest {
            jsonrpc: "2.0".to_string(),
            id: 1,
            method: "programSubscribe".to_string(),
            params: json!([
                self.grid_program_id,
                {
                    "encoding": "base64",
                    "commitment": "confirmed"
                }
            ]),
        };

        let subscribe_msg = serde_json::to_string(&subscribe_request)
            .map_err(|e| OreError::Serialization(e))?;

        write
            .send(Message::Text(subscribe_msg))
            .await
            .map_err(|e| OreError::StateMonitoring(format!("Failed to subscribe: {}", e)))?;

        info!("Subscribed to program: {}", self.grid_program_id);

        // Process incoming messages
        while let Some(msg) = read.next().await {
            match msg {
                Ok(Message::Text(text)) => {
                    if let Err(e) = self.process_message(&text).await {
                        warn!("Failed to process message: {:?}", e);
                    }
                }
                Ok(Message::Ping(data)) => {
                    write
                        .send(Message::Pong(data))
                        .await
                        .map_err(|e| OreError::Network(e.into()))?;
                }
                Ok(Message::Close(_)) => {
                    info!("WebSocket closed by server");
                    break;
                }
                Err(e) => {
                    return Err(OreError::StateMonitoring(format!(
                        "WebSocket error: {}",
                        e
                    )));
                }
                _ => {}
            }
        }

        Ok(())
    }

    async fn process_message(&self, text: &str) -> Result<()> {
        debug!("Received message: {}", text);

        // Try to parse as notification
        if let Ok(notification) = serde_json::from_str::<NotificationResponse>(text) {
            let account_data = &notification.params.result.value.data[0];

            // Decode base64 data
            let decoded = base64::decode(account_data)
                .map_err(|e| OreError::StateMonitoring(format!("Failed to decode: {}", e)))?;

            // Parse grid state from account data
            let grid_state = self.parse_grid_state(&decoded)?;

            // Update state
            let mut state = self.state.write().await;
            *state = Some(grid_state.clone());

            info!(
                "Grid state updated: round={}, total_staked={}, motherlode={}",
                grid_state.round, grid_state.total_staked, grid_state.motherlode_size
            );

            debug!("Grid blocks: {:?}", grid_state.blocks);
        }

        Ok(())
    }

    /// Parse grid state from raw account data
    ///
    /// This is a simplified parser - in production, this would use the actual
    /// ORE V2 program's account structure
    fn parse_grid_state(&self, data: &[u8]) -> Result<GridState> {
        if data.len() < 8 {
            return Err(OreError::StateMonitoring("Invalid account data".to_string()));
        }

        // Example parsing (this would match the actual on-chain data structure)
        let round = u64::from_le_bytes(data[0..8].try_into().unwrap());
        let motherlode_size = if data.len() >= 16 {
            u64::from_le_bytes(data[8..16].try_into().unwrap())
        } else {
            0
        };

        let mut blocks = [BlockState {
            index: 0,
            staked_amount: 0,
            participant_count: 0,
            historical_win_rate: 0.04, // 1/25 baseline
        }; GRID_SIZE];

        // Parse block data (starting at offset 16)
        let mut offset = 16;
        for i in 0..GRID_SIZE {
            if offset + 16 <= data.len() {
                let staked_amount = u64::from_le_bytes(
                    data[offset..offset + 8].try_into().unwrap()
                );
                let participant_count = u32::from_le_bytes(
                    data[offset + 8..offset + 12].try_into().unwrap()
                );

                blocks[i] = BlockState {
                    index: i as u8,
                    staked_amount,
                    participant_count,
                    historical_win_rate: 0.04,
                };

                offset += 16;
            }
        }

        let total_staked: u64 = blocks.iter().map(|b| b.staked_amount).sum();
        let now = ore_common::utils::current_timestamp();

        Ok(GridState {
            round,
            blocks,
            motherlode_size,
            total_staked,
            round_start: now - 30, // Estimate (would be in actual account data)
            last_update: now,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_grid_state() {
        let monitor = WebSocketMonitor::new(
            "ws://localhost:8900".to_string(),
            "ore111111111111111111111111111111111111111".to_string(),
        );

        // Create minimal test data
        let mut data = vec![0u8; 16 + GRID_SIZE * 16];
        data[0..8].copy_from_slice(&100u64.to_le_bytes()); // round
        data[8..16].copy_from_slice(&5_000_000_000u64.to_le_bytes()); // motherlode

        let result = monitor.parse_grid_state(&data);
        assert!(result.is_ok());

        let state = result.unwrap();
        assert_eq!(state.round, 100);
        assert_eq!(state.motherlode_size, 5_000_000_000);
    }
}
