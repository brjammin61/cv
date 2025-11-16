use crate::arbitrage_detector::ArbitrageDetector;
use crate::executor::TradeExecutor;
use crate::multi_hop::MultiHopFinder;
use crate::price_fetcher::PriceFetcher;
use crate::profit_calculator::ProfitCalculator;
use crate::risk_manager::{RiskManager, RiskMetrics};
use crate::types::*;
use anyhow::Result;
use rust_decimal::Decimal;
use solana_sdk::pubkey::Pubkey;
use std::str::FromStr;
use std::sync::Arc;
use tokio::time::{interval, Duration};
use tracing::{error, info, warn};

/// Main orchestrator coordinating all MEV strategies
pub struct MevOrchestrator {
    price_fetcher: Arc<PriceFetcher>,
    arbitrage_detector: Arc<ArbitrageDetector>,
    multi_hop_finder: Arc<MultiHopFinder>,
    executor: Arc<TradeExecutor>,
    risk_manager: Arc<RiskManager>,
    profit_calculator: Arc<ProfitCalculator>,
    config: BotConfig,
    stats: Arc<tokio::sync::RwLock<BotStats>>,
}

#[derive(Debug, Clone, Default)]
pub struct BotStats {
    pub total_opportunities_found: u64,
    pub total_trades_executed: u64,
    pub successful_trades: u64,
    pub failed_trades: u64,
    pub total_profit_sol: Decimal,
    pub total_loss_sol: Decimal,
    pub uptime_seconds: u64,
    pub level1_opportunities: u64,
    pub level2_opportunities: u64,
    pub level3_opportunities: u64,
}

impl MevOrchestrator {
    pub fn new(
        rpc_url: String,
        wallet: solana_sdk::signature::Keypair,
        config: BotConfig,
    ) -> Result<Self> {
        let price_fetcher = Arc::new(PriceFetcher::new());
        let profit_calculator = Arc::new(ProfitCalculator::new(config.clone()));
        let executor = Arc::new(TradeExecutor::new(
            rpc_url.clone(),
            wallet,
            config.clone(),
        )?);
        let risk_manager = Arc::new(RiskManager::new(config.clone()));

        let arbitrage_detector = Arc::new(ArbitrageDetector::new(
            price_fetcher.clone(),
            profit_calculator.clone(),
        ));

        let multi_hop_finder = Arc::new(MultiHopFinder::new(
            price_fetcher.clone(),
            profit_calculator.clone(),
        ));

        Ok(Self {
            price_fetcher,
            arbitrage_detector,
            multi_hop_finder,
            executor,
            risk_manager,
            profit_calculator,
            config,
            stats: Arc::new(tokio::sync::RwLock::new(BotStats::default())),
        })
    }

    /// Start the MEV bot with all strategies
    pub async fn start(&self) -> Result<()> {
        info!("🚀 Starting MEV Bot with all strategies enabled");
        info!("Configuration: dry_run={}, min_profit={}%, max_trade_size={} SOL",
            self.config.dry_run,
            self.config.min_profit_percent,
            self.config.max_trade_size_sol
        );

        // Start stats printer
        let stats_clone = self.stats.clone();
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(60));
            loop {
                interval.tick().await;
                let stats = stats_clone.read().await;
                info!("📊 Bot Stats: {} opps found, {} trades ({} success, {} failed), P/L: {} SOL",
                    stats.total_opportunities_found,
                    stats.total_trades_executed,
                    stats.successful_trades,
                    stats.failed_trades,
                    stats.total_profit_sol - stats.total_loss_sol
                );
            }
        });

        // Run all strategies in parallel
        let (level1_result, level2_result) = tokio::join!(
            self.run_level1_strategy(),
            self.run_level2_strategy(),
        );

        // Check for errors
        level1_result?;
        level2_result?;

        Ok(())
    }

    /// Level 1: Cross-DEX Arbitrage
    async fn run_level1_strategy(&self) -> Result<()> {
        info!("📈 Starting Level 1: Cross-DEX Arbitrage");

        let mut interval = interval(Duration::from_millis(self.config.scan_interval_ms));

        // Popular trading pairs on Solana
        let token_pairs = self.get_token_pairs();

        loop {
            interval.tick().await;

            // Check if we can trade
            let metrics = self.risk_manager.get_metrics().await;
            if metrics.is_paused {
                warn!("⏸️  Trading paused: {:?}", metrics.pause_reason);
                tokio::time::sleep(Duration::from_secs(10)).await;
                continue;
            }

            // Scan for opportunities
            match self.arbitrage_detector.scan_cross_dex_opportunities(
                &token_pairs,
                self.config.max_trade_size_sol,
            ).await {
                Ok(opportunities) => {
                    if !opportunities.is_empty() {
                        info!("💎 Found {} Level 1 opportunities", opportunities.len());

                        let mut stats = self.stats.write().await;
                        stats.total_opportunities_found += opportunities.len() as u64;
                        stats.level1_opportunities += opportunities.len() as u64;
                        drop(stats);

                        // Execute best opportunity
                        if let Some(best) = opportunities.first() {
                            self.execute_opportunity(best).await;
                        }
                    }
                }
                Err(e) => {
                    error!("Level 1 scan error: {}", e);
                }
            }
        }
    }

    /// Level 2: Multi-Hop Arbitrage
    async fn run_level2_strategy(&self) -> Result<()> {
        info!("🔄 Starting Level 2: Multi-Hop Arbitrage");

        let mut interval = interval(Duration::from_millis(self.config.scan_interval_ms * 2));

        // Start tokens for circular paths
        let start_tokens = self.get_start_tokens();
        let intermediate_tokens = self.get_intermediate_tokens();

        loop {
            interval.tick().await;

            // Check if we can trade
            let metrics = self.risk_manager.get_metrics().await;
            if metrics.is_paused {
                continue;
            }

            // Scan each start token
            for start_token in &start_tokens {
                match self.multi_hop_finder.find_multi_hop_paths(
                    start_token,
                    &intermediate_tokens,
                    self.config.max_trade_size_sol,
                ).await {
                    Ok(paths) => {
                        if !paths.is_empty() {
                            info!("💎 Found {} Level 2 multi-hop paths", paths.len());

                            let mut stats = self.stats.write().await;
                            stats.total_opportunities_found += paths.len() as u64;
                            stats.level2_opportunities += paths.len() as u64;
                            drop(stats);

                            // TODO: Execute best path
                            // For now, just log it
                            if let Some(best) = paths.first() {
                                info!("Best path: {} hops, {} SOL profit",
                                    best.hops.len(),
                                    best.net_profit
                                );
                            }
                        }
                    }
                    Err(e) => {
                        error!("Level 2 scan error for {:?}: {}", start_token, e);
                    }
                }

                // Small delay between tokens
                tokio::time::sleep(Duration::from_millis(100)).await;
            }
        }
    }

    /// Execute a single arbitrage opportunity
    async fn execute_opportunity(&self, opportunity: &ArbitrageOpportunity) {
        info!("⚡ Executing opportunity: {} SOL profit ({:.2}%)",
            opportunity.net_profit,
            opportunity.profit_percent
        );

        // Check risk limits
        let trade_size = Decimal::from(opportunity.buy_quote.input_amount)
            / Decimal::from(1_000_000_000);

        if let Err(e) = self.risk_manager.should_allow_trade(trade_size).await {
            warn!("🛑 Trade blocked by risk manager: {}", e);
            return;
        }

        // Validate opportunity is still valid
        match self.arbitrage_detector.validate_opportunity(opportunity).await {
            Ok(false) => {
                warn!("⚠️  Opportunity no longer valid (price moved)");
                return;
            }
            Err(e) => {
                error!("Validation error: {}", e);
                return;
            }
            Ok(true) => {}
        }

        // Add exposure
        self.risk_manager.add_exposure(trade_size).await;

        // Execute the trade
        match self.executor.execute_arbitrage(opportunity).await {
            Ok(result) => {
                // Record with risk manager
                self.risk_manager.record_trade(&result).await;

                // Update stats
                let mut stats = self.stats.write().await;
                stats.total_trades_executed += 1;

                if result.success {
                    stats.successful_trades += 1;
                    if let Some(profit) = result.realized_profit {
                        if profit > Decimal::ZERO {
                            stats.total_profit_sol += profit;
                            info!("✅ Trade successful! Profit: {} SOL", profit);
                        } else {
                            stats.total_loss_sol += profit.abs();
                            warn!("⚠️  Trade succeeded but lost: {} SOL", profit);
                        }
                    }
                } else {
                    stats.failed_trades += 1;
                    error!("❌ Trade failed: {:?}", result.error);
                }
            }
            Err(e) => {
                error!("Execution error: {}", e);
                let mut stats = self.stats.write().await;
                stats.total_trades_executed += 1;
                stats.failed_trades += 1;

                // Record failed trade
                self.risk_manager.record_trade(&TradeResult {
                    success: false,
                    signature: None,
                    input_amount: opportunity.buy_quote.input_amount,
                    output_amount: 0,
                    realized_profit: None,
                    execution_time_ms: 0,
                    error: Some(e.to_string()),
                    timestamp: chrono::Utc::now().timestamp_millis(),
                }).await;
            }
        }

        // Remove exposure
        self.risk_manager.remove_exposure(trade_size).await;
    }

    /// Get popular token pairs for scanning
    fn get_token_pairs(&self) -> Vec<(Pubkey, Pubkey)> {
        vec![
            // SOL/USDC
            (
                Pubkey::from_str("So11111111111111111111111111111111111111112").unwrap(),
                Pubkey::from_str("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v").unwrap(),
            ),
            // SOL/USDT
            (
                Pubkey::from_str("So11111111111111111111111111111111111111112").unwrap(),
                Pubkey::from_str("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB").unwrap(),
            ),
            // SOL/BONK
            (
                Pubkey::from_str("So11111111111111111111111111111111111111112").unwrap(),
                Pubkey::from_str("DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263").unwrap(),
            ),
            // SOL/RAY
            (
                Pubkey::from_str("So11111111111111111111111111111111111111112").unwrap(),
                Pubkey::from_str("4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R").unwrap(),
            ),
            // SOL/JUP
            (
                Pubkey::from_str("So11111111111111111111111111111111111111112").unwrap(),
                Pubkey::from_str("JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN").unwrap(),
            ),
        ]
    }

    /// Get start tokens for multi-hop paths
    fn get_start_tokens(&self) -> Vec<Pubkey> {
        vec![
            Pubkey::from_str("So11111111111111111111111111111111111111112").unwrap(), // SOL
            Pubkey::from_str("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v").unwrap(), // USDC
        ]
    }

    /// Get intermediate tokens for multi-hop paths
    fn get_intermediate_tokens(&self) -> Vec<Pubkey> {
        vec![
            Pubkey::from_str("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v").unwrap(), // USDC
            Pubkey::from_str("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB").unwrap(), // USDT
            Pubkey::from_str("DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263").unwrap(), // BONK
            Pubkey::from_str("4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R").unwrap(), // RAY
            Pubkey::from_str("JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN").unwrap(), // JUP
        ]
    }

    /// Get current bot statistics
    pub async fn get_stats(&self) -> BotStats {
        self.stats.read().await.clone()
    }

    /// Get risk metrics
    pub async fn get_risk_metrics(&self) -> RiskMetrics {
        self.risk_manager.get_metrics().await
    }

    /// Pause the bot
    pub async fn pause(&self, reason: String) {
        self.risk_manager.pause(reason).await;
    }

    /// Resume the bot
    pub async fn resume(&self) {
        self.risk_manager.resume().await;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_orchestrator_creation() {
        let config = BotConfig {
            dry_run: true,
            ..Default::default()
        };

        let wallet = solana_sdk::signature::Keypair::new();
        let orchestrator = MevOrchestrator::new(
            "https://api.mainnet-beta.solana.com".to_string(),
            wallet,
            config,
        );

        assert!(orchestrator.is_ok());
    }

    #[tokio::test]
    async fn test_stats_tracking() {
        let config = BotConfig {
            dry_run: true,
            ..Default::default()
        };

        let wallet = solana_sdk::signature::Keypair::new();
        let orchestrator = MevOrchestrator::new(
            "https://api.mainnet-beta.solana.com".to_string(),
            wallet,
            config,
        )
        .unwrap();

        let stats = orchestrator.get_stats().await;
        assert_eq!(stats.total_opportunities_found, 0);
        assert_eq!(stats.total_trades_executed, 0);
    }
}
