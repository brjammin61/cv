use crate::types::*;
use rust_decimal::Decimal;
use std::collections::VecDeque;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::info;

/// Real-time metrics and monitoring system
pub struct MetricsCollector {
    state: Arc<RwLock<MetricsState>>,
    config: MetricsConfig,
}

#[derive(Debug, Clone)]
pub struct MetricsConfig {
    /// How many historical trades to keep
    pub max_trade_history: usize,
    /// How many performance samples to keep (for moving averages)
    pub max_performance_samples: usize,
}

impl Default for MetricsConfig {
    fn default() -> Self {
        Self {
            max_trade_history: 1000,
            max_performance_samples: 100,
        }
    }
}

#[derive(Debug, Clone)]
struct MetricsState {
    /// Historical trades
    trade_history: VecDeque<TradeMetric>,

    /// Performance metrics
    total_opportunities_scanned: u64,
    total_opportunities_found: u64,
    total_trades_attempted: u64,
    total_trades_successful: u64,
    total_trades_failed: u64,

    /// Financial metrics
    total_volume_sol: Decimal,
    total_profit_sol: Decimal,
    total_loss_sol: Decimal,
    largest_win_sol: Decimal,
    largest_loss_sol: Decimal,

    /// Strategy breakdown
    level1_trades: u64,
    level2_trades: u64,
    level3_trades: u64,

    /// Execution metrics
    avg_execution_time_ms: f64,
    execution_times: VecDeque<u64>,

    /// Gas/fee metrics
    total_fees_paid_sol: Decimal,
    total_tips_paid_sol: Decimal,

    /// Start time
    start_time: i64,
}

#[derive(Debug, Clone)]
pub struct TradeMetric {
    pub timestamp: i64,
    pub strategy: Strategy,
    pub pair: String,
    pub input_amount_sol: Decimal,
    pub output_amount_sol: Decimal,
    pub profit_sol: Decimal,
    pub profit_percent: Decimal,
    pub execution_time_ms: u64,
    pub gas_paid_sol: Decimal,
    pub success: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Strategy {
    Level1CrossDex,
    Level2MultiHop,
    Level3Backrun,
    Level3Liquidation,
}

impl MetricsCollector {
    pub fn new(config: MetricsConfig) -> Self {
        Self {
            state: Arc::new(RwLock::new(MetricsState {
                trade_history: VecDeque::with_capacity(config.max_trade_history),
                total_opportunities_scanned: 0,
                total_opportunities_found: 0,
                total_trades_attempted: 0,
                total_trades_successful: 0,
                total_trades_failed: 0,
                total_volume_sol: Decimal::ZERO,
                total_profit_sol: Decimal::ZERO,
                total_loss_sol: Decimal::ZERO,
                largest_win_sol: Decimal::ZERO,
                largest_loss_sol: Decimal::ZERO,
                level1_trades: 0,
                level2_trades: 0,
                level3_trades: 0,
                avg_execution_time_ms: 0.0,
                execution_times: VecDeque::with_capacity(config.max_performance_samples),
                total_fees_paid_sol: Decimal::ZERO,
                total_tips_paid_sol: Decimal::ZERO,
                start_time: chrono::Utc::now().timestamp(),
            })),
            config,
        }
    }

    /// Record a new trade
    pub async fn record_trade(&self, metric: TradeMetric) {
        let mut state = self.state.write().await;

        // Update trade counts
        state.total_trades_attempted += 1;
        if metric.success {
            state.total_trades_successful += 1;

            // Update financial metrics
            state.total_volume_sol += metric.input_amount_sol;

            if metric.profit_sol > Decimal::ZERO {
                state.total_profit_sol += metric.profit_sol;
                if metric.profit_sol > state.largest_win_sol {
                    state.largest_win_sol = metric.profit_sol;
                }
            } else {
                let loss = metric.profit_sol.abs();
                state.total_loss_sol += loss;
                if loss > state.largest_loss_sol {
                    state.largest_loss_sol = loss;
                }
            }

            // Update strategy breakdown
            match metric.strategy {
                Strategy::Level1CrossDex => state.level1_trades += 1,
                Strategy::Level2MultiHop => state.level2_trades += 1,
                Strategy::Level3Backrun => state.level3_trades += 1,
                Strategy::Level3Liquidation => state.level3_trades += 1,
            }
        } else {
            state.total_trades_failed += 1;
        }

        // Update execution time metrics
        state.execution_times.push_back(metric.execution_time_ms);
        if state.execution_times.len() > self.config.max_performance_samples {
            state.execution_times.pop_front();
        }

        // Recalculate average execution time
        let sum: u64 = state.execution_times.iter().sum();
        state.avg_execution_time_ms = sum as f64 / state.execution_times.len() as f64;

        // Update fees
        state.total_fees_paid_sol += metric.gas_paid_sol;

        // Add to history
        state.trade_history.push_back(metric);
        if state.trade_history.len() > self.config.max_trade_history {
            state.trade_history.pop_front();
        }
    }

    /// Record opportunities scanned
    pub async fn record_scan(&self, opportunities_found: u64) {
        let mut state = self.state.write().await;
        state.total_opportunities_scanned += 1;
        state.total_opportunities_found += opportunities_found;
    }

    /// Get comprehensive metrics summary
    pub async fn get_summary(&self) -> MetricsSummary {
        let state = self.state.read().await;

        let uptime_seconds = chrono::Utc::now().timestamp() - state.start_time;
        let uptime_hours = uptime_seconds as f64 / 3600.0;

        let net_profit = state.total_profit_sol - state.total_loss_sol;
        let net_after_fees = net_profit - state.total_fees_paid_sol - state.total_tips_paid_sol;

        let success_rate = if state.total_trades_attempted > 0 {
            (state.total_trades_successful as f64 / state.total_trades_attempted as f64) * 100.0
        } else {
            0.0
        };

        let opportunity_hit_rate = if state.total_opportunities_scanned > 0 {
            (state.total_opportunities_found as f64 / state.total_opportunities_scanned as f64)
                * 100.0
        } else {
            0.0
        };

        let hourly_profit = if uptime_hours > 0.0 {
            net_after_fees / Decimal::from_f64_retain(uptime_hours).unwrap_or(Decimal::ONE)
        } else {
            Decimal::ZERO
        };

        MetricsSummary {
            // Time
            uptime_seconds: uptime_seconds as u64,
            uptime_hours,

            // Scanning
            total_scans: state.total_opportunities_scanned,
            total_opportunities: state.total_opportunities_found,
            opportunity_hit_rate,

            // Trading
            total_trades: state.total_trades_attempted,
            successful_trades: state.total_trades_successful,
            failed_trades: state.total_trades_failed,
            success_rate,

            // Financial
            total_volume_sol: state.total_volume_sol,
            gross_profit_sol: state.total_profit_sol,
            gross_loss_sol: state.total_loss_sol,
            net_profit_sol: net_profit,
            fees_paid_sol: state.total_fees_paid_sol,
            tips_paid_sol: state.total_tips_paid_sol,
            net_after_fees_sol: net_after_fees,
            largest_win_sol: state.largest_win_sol,
            largest_loss_sol: state.largest_loss_sol,
            hourly_profit_sol: hourly_profit,

            // Performance
            avg_execution_time_ms: state.avg_execution_time_ms,

            // Strategy
            level1_trades: state.level1_trades,
            level2_trades: state.level2_trades,
            level3_trades: state.level3_trades,
        }
    }

    /// Print a nice dashboard to console
    pub async fn print_dashboard(&self) {
        let summary = self.get_summary().await;

        info!("╔═══════════════════════════════════════════════════════════════╗");
        info!("║                    MEV BOT METRICS DASHBOARD                  ║");
        info!("╠═══════════════════════════════════════════════════════════════╣");
        info!("║ UPTIME                                                        ║");
        info!("║   Runtime: {:.2} hours ({} seconds)                     ║", summary.uptime_hours, summary.uptime_seconds);
        info!("╠═══════════════════════════════════════════════════════════════╣");
        info!("║ SCANNING                                                      ║");
        info!("║   Total Scans: {}                                         ║", summary.total_scans);
        info!("║   Opportunities Found: {}                                 ║", summary.total_opportunities);
        info!("║   Hit Rate: {:.2}%                                        ║", summary.opportunity_hit_rate);
        info!("╠═══════════════════════════════════════════════════════════════╣");
        info!("║ TRADING                                                       ║");
        info!("║   Total Trades: {}                                        ║", summary.total_trades);
        info!("║   Successful: {}                                          ║", summary.successful_trades);
        info!("║   Failed: {}                                              ║", summary.failed_trades);
        info!("║   Success Rate: {:.2}%                                    ║", summary.success_rate);
        info!("╠═══════════════════════════════════════════════════════════════╣");
        info!("║ FINANCIAL (SOL)                                               ║");
        info!("║   Volume: {} SOL                                          ║", summary.total_volume_sol);
        info!("║   Gross Profit: {} SOL                                    ║", summary.gross_profit_sol);
        info!("║   Gross Loss: {} SOL                                      ║", summary.gross_loss_sol);
        info!("║   Net P/L: {} SOL                                         ║", summary.net_profit_sol);
        info!("║   Fees Paid: {} SOL                                       ║", summary.fees_paid_sol);
        info!("║   Tips Paid: {} SOL                                       ║", summary.tips_paid_sol);
        info!("║   NET AFTER FEES: {} SOL                                  ║", summary.net_after_fees_sol);
        info!("║   Largest Win: {} SOL                                     ║", summary.largest_win_sol);
        info!("║   Largest Loss: {} SOL                                    ║", summary.largest_loss_sol);
        info!("║   Hourly Profit: {} SOL/hour                              ║", summary.hourly_profit_sol);
        info!("╠═══════════════════════════════════════════════════════════════╣");
        info!("║ PERFORMANCE                                                   ║");
        info!("║   Avg Execution Time: {:.2} ms                            ║", summary.avg_execution_time_ms);
        info!("╠═══════════════════════════════════════════════════════════════╣");
        info!("║ STRATEGY BREAKDOWN                                            ║");
        info!("║   Level 1 (Cross-DEX): {} trades                          ║", summary.level1_trades);
        info!("║   Level 2 (Multi-Hop): {} trades                          ║", summary.level2_trades);
        info!("║   Level 3 (MEV): {} trades                                ║", summary.level3_trades);
        info!("╚═══════════════════════════════════════════════════════════════╝");
    }

    /// Get recent trade history
    pub async fn get_recent_trades(&self, limit: usize) -> Vec<TradeMetric> {
        let state = self.state.read().await;
        state
            .trade_history
            .iter()
            .rev()
            .take(limit)
            .cloned()
            .collect()
    }

    /// Export metrics to JSON
    pub async fn export_json(&self) -> Result<String, serde_json::Error> {
        let summary = self.get_summary().await;
        serde_json::to_string_pretty(&summary)
    }
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct MetricsSummary {
    // Time
    pub uptime_seconds: u64,
    pub uptime_hours: f64,

    // Scanning
    pub total_scans: u64,
    pub total_opportunities: u64,
    pub opportunity_hit_rate: f64,

    // Trading
    pub total_trades: u64,
    pub successful_trades: u64,
    pub failed_trades: u64,
    pub success_rate: f64,

    // Financial
    pub total_volume_sol: Decimal,
    pub gross_profit_sol: Decimal,
    pub gross_loss_sol: Decimal,
    pub net_profit_sol: Decimal,
    pub fees_paid_sol: Decimal,
    pub tips_paid_sol: Decimal,
    pub net_after_fees_sol: Decimal,
    pub largest_win_sol: Decimal,
    pub largest_loss_sol: Decimal,
    pub hourly_profit_sol: Decimal,

    // Performance
    pub avg_execution_time_ms: f64,

    // Strategy
    pub level1_trades: u64,
    pub level2_trades: u64,
    pub level3_trades: u64,
}

/// Start a background task that prints the dashboard periodically
pub async fn start_dashboard_printer(
    metrics: Arc<MetricsCollector>,
    interval_seconds: u64,
) {
    let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(interval_seconds));

    loop {
        interval.tick().await;
        metrics.print_dashboard().await;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_metrics_recording() {
        let metrics = MetricsCollector::new(MetricsConfig::default());

        let trade = TradeMetric {
            timestamp: chrono::Utc::now().timestamp(),
            strategy: Strategy::Level1CrossDex,
            pair: "SOL/USDC".to_string(),
            input_amount_sol: Decimal::from(1),
            output_amount_sol: Decimal::from_str("1.05").unwrap(),
            profit_sol: Decimal::from_str("0.05").unwrap(),
            profit_percent: Decimal::from(5),
            execution_time_ms: 250,
            gas_paid_sol: Decimal::from_str("0.001").unwrap(),
            success: true,
        };

        metrics.record_trade(trade).await;

        let summary = metrics.get_summary().await;
        assert_eq!(summary.total_trades, 1);
        assert_eq!(summary.successful_trades, 1);
        assert_eq!(summary.level1_trades, 1);
        assert!(summary.gross_profit_sol > Decimal::ZERO);
    }
}
