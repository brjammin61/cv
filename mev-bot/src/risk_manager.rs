use crate::types::*;
use rust_decimal::Decimal;
use rust_decimal::prelude::ToPrimitive;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{error, info, warn};

/// Manages risk and prevents losses
///
/// Features:
/// - Position size limits
/// - Daily loss limits
/// - Circuit breakers
/// - Exposure tracking
pub struct RiskManager {
    config: BotConfig,
    state: Arc<RwLock<RiskState>>,
}

#[derive(Debug, Clone)]
struct RiskState {
    daily_profit_loss: Decimal,
    total_exposure: Decimal,
    consecutive_failures: u32,
    is_paused: bool,
    pause_reason: Option<String>,
    trades_today: u64,
    last_reset_timestamp: i64,
}

impl RiskManager {
    pub fn new(config: BotConfig) -> Self {
        Self {
            config,
            state: Arc::new(RwLock::new(RiskState {
                daily_profit_loss: Decimal::ZERO,
                total_exposure: Decimal::ZERO,
                consecutive_failures: 0,
                is_paused: false,
                pause_reason: None,
                trades_today: 0,
                last_reset_timestamp: chrono::Utc::now().timestamp(),
            })),
        }
    }

    /// Check if a trade should be allowed
    pub async fn should_allow_trade(
        &self,
        trade_size: Decimal,
    ) -> Result<(), String> {
        let state = self.state.read().await;

        // Check if paused
        if state.is_paused {
            return Err(format!(
                "Trading paused: {}",
                state.pause_reason.as_ref().unwrap_or(&"Unknown reason".to_string())
            ));
        }

        // Check daily loss limit
        if state.daily_profit_loss < -self.config.max_daily_loss_sol {
            return Err(format!(
                "Daily loss limit exceeded: {} < -{}",
                state.daily_profit_loss, self.config.max_daily_loss_sol
            ));
        }

        // Check trade size limit
        if trade_size > self.config.max_trade_size_sol {
            return Err(format!(
                "Trade size too large: {} > {}",
                trade_size, self.config.max_trade_size_sol
            ));
        }

        // Check total exposure limit
        if state.total_exposure + trade_size > self.config.max_total_exposure_sol {
            return Err(format!(
                "Total exposure limit would be exceeded: {} + {} > {}",
                state.total_exposure,
                trade_size,
                self.config.max_total_exposure_sol
            ));
        }

        // Check consecutive failures (circuit breaker)
        if state.consecutive_failures >= 10 {
            return Err(format!(
                "Circuit breaker triggered: {} consecutive failures",
                state.consecutive_failures
            ));
        }

        Ok(())
    }

    /// Record a trade result
    pub async fn record_trade(&self, result: &TradeResult) {
        let mut state = self.state.write().await;

        // Reset daily stats if new day
        self.check_daily_reset(&mut state);

        state.trades_today += 1;

        if result.success {
            state.consecutive_failures = 0;

            if let Some(profit) = result.realized_profit {
                state.daily_profit_loss += profit;

                info!(
                    "Trade successful | Profit: {} SOL | Daily P/L: {} SOL",
                    profit, state.daily_profit_loss
                );
            }
        } else {
            state.consecutive_failures += 1;

            warn!(
                "Trade failed ({} consecutive failures) | Reason: {:?}",
                state.consecutive_failures, result.error
            );

            // Auto-pause after too many failures
            if state.consecutive_failures >= 10 {
                state.is_paused = true;
                state.pause_reason = Some(
                    "Circuit breaker: 10 consecutive failures".to_string()
                );

                error!("CIRCUIT BREAKER TRIGGERED - Trading paused!");
            }
        }

        // Check if daily loss limit hit
        if state.daily_profit_loss < -self.config.max_daily_loss_sol {
            state.is_paused = true;
            state.pause_reason = Some(format!(
                "Daily loss limit hit: {} SOL",
                state.daily_profit_loss
            ));

            error!("DAILY LOSS LIMIT HIT - Trading paused!");
        }
    }

    /// Add exposure (when opening position)
    pub async fn add_exposure(&self, amount: Decimal) {
        let mut state = self.state.write().await;
        state.total_exposure += amount;
        info!("Exposure increased: {} SOL", state.total_exposure);
    }

    /// Remove exposure (when closing position)
    pub async fn remove_exposure(&self, amount: Decimal) {
        let mut state = self.state.write().await;
        state.total_exposure -= amount;
        if state.total_exposure < Decimal::ZERO {
            state.total_exposure = Decimal::ZERO;
        }
        info!("Exposure decreased: {} SOL", state.total_exposure);
    }

    /// Get current risk metrics
    pub async fn get_metrics(&self) -> RiskMetrics {
        let state = self.state.read().await;

        RiskMetrics {
            daily_pnl: state.daily_profit_loss,
            total_exposure: state.total_exposure,
            consecutive_failures: state.consecutive_failures,
            is_paused: state.is_paused,
            pause_reason: state.pause_reason.clone(),
            trades_today: state.trades_today,
            utilization_percent: if self.config.max_total_exposure_sol > Decimal::ZERO {
                (state.total_exposure / self.config.max_total_exposure_sol * Decimal::from(100))
                    .to_f64()
                    .unwrap_or(0.0)
            } else {
                0.0
            },
        }
    }

    /// Manually pause trading
    pub async fn pause(&self, reason: String) {
        let mut state = self.state.write().await;
        state.is_paused = true;
        state.pause_reason = Some(reason.clone());
        warn!("Trading manually paused: {}", reason);
    }

    /// Resume trading
    pub async fn resume(&self) {
        let mut state = self.state.write().await;
        state.is_paused = false;
        state.pause_reason = None;
        state.consecutive_failures = 0;
        info!("Trading resumed");
    }

    /// Check if we need to reset daily stats
    fn check_daily_reset(&self, state: &mut RiskState) {
        let now = chrono::Utc::now().timestamp();
        let hours_since_reset = (now - state.last_reset_timestamp) / 3600;

        if hours_since_reset >= 24 {
            info!(
                "Resetting daily stats | Previous P/L: {} SOL",
                state.daily_profit_loss
            );

            state.daily_profit_loss = Decimal::ZERO;
            state.trades_today = 0;
            state.last_reset_timestamp = now;

            // Reset pause if it was due to daily loss
            if state.is_paused
                && state
                    .pause_reason
                    .as_ref()
                    .map(|r| r.contains("Daily loss"))
                    .unwrap_or(false)
            {
                state.is_paused = false;
                state.pause_reason = None;
                info!("Auto-resuming after daily reset");
            }
        }
    }
}

#[derive(Debug, Clone)]
pub struct RiskMetrics {
    pub daily_pnl: Decimal,
    pub total_exposure: Decimal,
    pub consecutive_failures: u32,
    pub is_paused: bool,
    pub pause_reason: Option<String>,
    pub trades_today: u64,
    pub utilization_percent: f64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_trade_size_limit() {
        let config = BotConfig {
            max_trade_size_sol: Decimal::from(10),
            ..Default::default()
        };

        let risk_manager = RiskManager::new(config);

        // Should allow trade within limit
        assert!(risk_manager
            .should_allow_trade(Decimal::from(5))
            .await
            .is_ok());

        // Should reject trade above limit
        assert!(risk_manager
            .should_allow_trade(Decimal::from(15))
            .await
            .is_err());
    }

    #[tokio::test]
    async fn test_daily_loss_limit() {
        let config = BotConfig {
            max_daily_loss_sol: Decimal::from(1),
            ..Default::default()
        };

        let risk_manager = RiskManager::new(config);

        // Record a losing trade
        risk_manager
            .record_trade(&TradeResult {
                success: true,
                signature: Some("test".to_string()),
                input_amount: 0,
                output_amount: 0,
                realized_profit: Some(Decimal::from(-2)), // Lose 2 SOL
                execution_time_ms: 0,
                error: None,
                timestamp: 0,
            })
            .await;

        // Should be paused due to daily loss
        let metrics = risk_manager.get_metrics().await;
        assert!(metrics.is_paused);
    }

    #[tokio::test]
    async fn test_circuit_breaker() {
        let config = BotConfig::default();
        let risk_manager = RiskManager::new(config);

        // Record 10 failed trades
        for _ in 0..10 {
            risk_manager
                .record_trade(&TradeResult {
                    success: false,
                    signature: None,
                    input_amount: 0,
                    output_amount: 0,
                    realized_profit: None,
                    execution_time_ms: 0,
                    error: Some("Test failure".to_string()),
                    timestamp: 0,
                })
                .await;
        }

        // Should be paused due to circuit breaker
        let metrics = risk_manager.get_metrics().await;
        assert!(metrics.is_paused);
        assert_eq!(metrics.consecutive_failures, 10);
    }
}
