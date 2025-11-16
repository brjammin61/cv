use crate::price_fetcher::PriceFetcher;
use crate::profit_calculator::ProfitCalculator;
use crate::types::*;
use anyhow::Result;
use rust_decimal::Decimal;
use rust_decimal::prelude::ToPrimitive;
use solana_sdk::pubkey::Pubkey;
use std::sync::Arc;
use tracing::{debug, info};

/// Detects arbitrage opportunities across DEXs
pub struct ArbitrageDetector {
    price_fetcher: Arc<PriceFetcher>,
    profit_calculator: Arc<ProfitCalculator>,
}

impl ArbitrageDetector {
    pub fn new(
        price_fetcher: Arc<PriceFetcher>,
        profit_calculator: Arc<ProfitCalculator>,
    ) -> Self {
        Self {
            price_fetcher,
            profit_calculator,
        }
    }

    /// Scan for cross-DEX arbitrage opportunities
    ///
    /// This is Level 1: Simple cross-DEX arbitrage
    /// Buy on one DEX, sell on another
    pub async fn scan_cross_dex_opportunities(
        &self,
        token_pairs: &[(Pubkey, Pubkey)],
        trade_size_sol: Decimal,
    ) -> Result<Vec<ArbitrageOpportunity>> {
        let mut opportunities = Vec::new();

        for (base_token, quote_token) in token_pairs {
            // Fetch quotes from all DEXs
            let amount = (trade_size_sol * Decimal::from(1_000_000_000))
                .to_u64()
                .unwrap_or(1_000_000_000);

            let quotes = self.price_fetcher
                .fetch_all_quotes(base_token, quote_token, amount)
                .await;

            if quotes.len() < 2 {
                debug!("Not enough quotes for {}/{}", base_token, quote_token);
                continue;
            }

            // Find best buy and sell prices
            let best_buy = PriceFetcher::get_best_buy_quote(&quotes);
            let best_sell = PriceFetcher::get_best_sell_quote(&quotes);

            if let (Some(buy_quote), Some(sell_quote)) = (best_buy, best_sell) {
                // Don't arb on same DEX
                if buy_quote.dex == sell_quote.dex {
                    continue;
                }

                // Calculate profit
                if let Some((net_profit, execution_cost)) = self.profit_calculator
                    .calculate_arbitrage_profit(buy_quote, sell_quote, trade_size_sol)
                {
                    let gross_profit = (sell_quote.price - buy_quote.price) * trade_size_sol;
                    let profit_percent = (net_profit / trade_size_sol) * Decimal::from(100);

                    let opportunity = ArbitrageOpportunity {
                        id: format!(
                            "{}-{}-{}-{}",
                            buy_quote.dex,
                            sell_quote.dex,
                            base_token,
                            chrono::Utc::now().timestamp_millis()
                        ),
                        buy_dex: buy_quote.dex,
                        sell_dex: sell_quote.dex,
                        pair: buy_quote.pair.clone(),
                        buy_quote: buy_quote.clone(),
                        sell_quote: sell_quote.clone(),
                        gross_profit,
                        net_profit,
                        profit_percent,
                        execution_cost,
                        timestamp: chrono::Utc::now().timestamp_millis(),
                    };

                    info!(
                        "Found opportunity: Buy {} on {}, Sell on {} | Profit: {} SOL ({:.2}%)",
                        base_token,
                        opportunity.buy_dex,
                        opportunity.sell_dex,
                        net_profit,
                        profit_percent
                    );

                    opportunities.push(opportunity);
                }
            }
        }

        // Sort by profit (highest first)
        opportunities.sort_by(|a, b| {
            b.net_profit
                .partial_cmp(&a.net_profit)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        Ok(opportunities)
    }

    /// Filter opportunities that meet minimum thresholds
    /// Note: This is now done by ProfitCalculator, this method is kept for compatibility
    pub fn filter_profitable(
        &self,
        opportunities: Vec<ArbitrageOpportunity>,
    ) -> Vec<ArbitrageOpportunity> {
        // Already filtered by profit calculator
        opportunities
    }

    /// Re-validate an opportunity before execution
    ///
    /// CRITICAL: Prices change fast! Always re-check before executing
    pub async fn validate_opportunity(
        &self,
        opportunity: &ArbitrageOpportunity,
    ) -> Result<bool> {
        // Fetch fresh quotes for this pair
        let amount = opportunity.buy_quote.input_amount;

        let fresh_quotes = self.price_fetcher
            .fetch_all_quotes(
                &opportunity.pair.base,
                &opportunity.pair.quote,
                amount,
            )
            .await;

        // Find current best buy and sell
        let current_buy = fresh_quotes
            .iter()
            .find(|q| q.dex == opportunity.buy_dex);

        let current_sell = fresh_quotes
            .iter()
            .find(|q| q.dex == opportunity.sell_dex);

        match (current_buy, current_sell) {
            (Some(buy), Some(sell)) => {
                // Use profit calculator to validate
                match self.profit_calculator.validate_execution(
                    opportunity,
                    (buy, sell),
                ) {
                    Ok(_) => {
                        info!("Opportunity validated - still profitable");
                        Ok(true)
                    }
                    Err(e) => {
                        info!("Opportunity no longer profitable: {}", e);
                        Ok(false)
                    }
                }
            }
            _ => {
                info!("Could not fetch current quotes for validation");
                Ok(false)
            }
        }
    }

    /// Get breakeven analysis for a token pair
    pub fn analyze_breakeven(&self, trade_size_sol: Decimal) -> Decimal {
        self.profit_calculator.calculate_breakeven_spread(trade_size_sol)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::str::FromStr;

    #[tokio::test]
    #[ignore] // Requires network
    async fn test_scan_opportunities() {
        let config = BotConfig::default();
        let price_fetcher = Arc::new(PriceFetcher::new());
        let profit_calculator = Arc::new(ProfitCalculator::new(config));
        let detector = ArbitrageDetector::new(price_fetcher, profit_calculator);

        // Test with SOL/USDC pair
        let sol = Pubkey::from_str("So11111111111111111111111111111111111111112").unwrap();
        let usdc = Pubkey::from_str("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v").unwrap();

        let pairs = vec![(sol, usdc)];

        let opportunities = detector
            .scan_cross_dex_opportunities(&pairs, Decimal::from(1))
            .await
            .unwrap();

        println!("Found {} opportunities", opportunities.len());

        for opp in opportunities {
            println!("{:#?}", opp);
        }
    }
}
