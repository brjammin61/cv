use crate::price_fetcher::PriceFetcher;
use crate::profit_calculator::ProfitCalculator;
use crate::types::*;
use anyhow::Result;
use rust_decimal::Decimal;
use rust_decimal::prelude::ToPrimitive;
use solana_sdk::pubkey::Pubkey;
use std::collections::HashMap;
use std::str::FromStr;
use std::sync::Arc;
use tracing::{debug, info};

/// Finds multi-hop arbitrage paths
///
/// Example: SOL → USDC → BONK → SOL
/// If you end with more SOL than you started, it's profitable!
pub struct MultiHopFinder {
    price_fetcher: Arc<PriceFetcher>,
    profit_calculator: Arc<ProfitCalculator>,
    max_hops: usize,
}

impl MultiHopFinder {
    pub fn new(
        price_fetcher: Arc<PriceFetcher>,
        profit_calculator: Arc<ProfitCalculator>,
    ) -> Self {
        Self {
            price_fetcher,
            profit_calculator,
            max_hops: 4, // SOL→A→B→C→SOL = 4 hops max
        }
    }

    /// Find circular arbitrage paths
    ///
    /// This explores paths like:
    /// - 2-hop: SOL → USDC → SOL
    /// - 3-hop: SOL → USDC → BONK → SOL
    /// - 4-hop: SOL → USDC → BONK → WIF → SOL
    pub async fn find_multi_hop_paths(
        &self,
        start_token: &Pubkey,
        intermediate_tokens: &[Pubkey],
        trade_size_sol: Decimal,
    ) -> Result<Vec<ArbitragePath>> {
        let mut profitable_paths = Vec::new();

        // Generate all possible paths
        let paths = self.generate_paths(start_token, intermediate_tokens);

        info!("Exploring {} potential paths", paths.len());

        for path_tokens in paths {
            if let Some(profitable_path) = self
                .evaluate_path(&path_tokens, trade_size_sol)
                .await?
            {
                info!(
                    "Found profitable path: {:?} | Profit: {} SOL ({:.2}%)",
                    path_tokens
                        .iter()
                        .map(|t| t.to_string()[..8].to_string())
                        .collect::<Vec<_>>(),
                    profitable_path.net_profit,
                    profitable_path.profit_percent
                );

                profitable_paths.push(profitable_path);
            }
        }

        // Sort by profit
        profitable_paths.sort_by(|a, b| {
            b.net_profit
                .partial_cmp(&a.net_profit)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        Ok(profitable_paths)
    }

    /// Generate all possible circular paths
    fn generate_paths(
        &self,
        start_token: &Pubkey,
        intermediate_tokens: &[Pubkey],
    ) -> Vec<Vec<Pubkey>> {
        let mut all_paths = Vec::new();

        // 2-hop: A → B → A
        for token in intermediate_tokens {
            if token != start_token {
                all_paths.push(vec![*start_token, *token, *start_token]);
            }
        }

        // 3-hop: A → B → C → A
        for token1 in intermediate_tokens {
            for token2 in intermediate_tokens {
                if token1 != start_token
                    && token2 != start_token
                    && token1 != token2
                {
                    all_paths.push(vec![
                        *start_token,
                        *token1,
                        *token2,
                        *start_token,
                    ]);
                }
            }
        }

        // 4-hop: A → B → C → D → A (only if max_hops >= 4)
        if self.max_hops >= 4 {
            for token1 in intermediate_tokens {
                for token2 in intermediate_tokens {
                    for token3 in intermediate_tokens {
                        if token1 != start_token
                            && token2 != start_token
                            && token3 != start_token
                            && token1 != token2
                            && token2 != token3
                            && token1 != token3
                        {
                            all_paths.push(vec![
                                *start_token,
                                *token1,
                                *token2,
                                *token3,
                                *start_token,
                            ]);
                        }
                    }
                }
            }
        }

        debug!("Generated {} total paths to explore", all_paths.len());
        all_paths
    }

    /// Evaluate if a path is profitable
    async fn evaluate_path(
        &self,
        path: &[Pubkey],
        start_amount_sol: Decimal,
    ) -> Result<Option<ArbitragePath>> {
        let mut hops = Vec::new();
        let mut current_amount = (start_amount_sol * Decimal::from(1_000_000_000))
            .to_u64()
            .unwrap();

        // Execute path hop by hop
        for i in 0..path.len() - 1 {
            let from_token = &path[i];
            let to_token = &path[i + 1];

            // Fetch quotes for this hop
            let quotes = self
                .price_fetcher
                .fetch_all_quotes(from_token, to_token, current_amount)
                .await;

            if quotes.is_empty() {
                debug!("No quotes available for {}/{}", from_token, to_token);
                return Ok(None);
            }

            // Use best quote
            let best_quote = PriceFetcher::get_best_buy_quote(&quotes)
                .ok_or_else(|| anyhow::anyhow!("No best quote found"))?;

            // Apply fees and slippage
            let output_with_fees = self.apply_swap_costs(
                best_quote.output_amount,
                best_quote.dex,
            );

            hops.push(TradeHop {
                dex: best_quote.dex,
                from_token: *from_token,
                to_token: *to_token,
                quote: best_quote.clone(),
            });

            current_amount = output_with_fees;
        }

        // Calculate final profit
        let start_amount_lamports = (start_amount_sol * Decimal::from(1_000_000_000))
            .to_u64()
            .unwrap();

        if current_amount <= start_amount_lamports {
            return Ok(None); // No profit
        }

        let gross_profit = Decimal::from(current_amount - start_amount_lamports)
            / Decimal::from(1_000_000_000);

        // Calculate execution costs
        let execution_cost = self.calculate_multi_hop_costs(&hops);

        let net_profit = gross_profit - execution_cost.total_cost;
        let profit_percent = (net_profit / start_amount_sol) * Decimal::from(100);

        // Return None if not profitable (caller can filter further)
        if net_profit <= Decimal::ZERO {
            return Ok(None);
        }

        Ok(Some(ArbitragePath {
            hops,
            net_profit,
            profit_percent,
            total_cost: execution_cost,
        }))
    }

    /// Apply swap costs (fees + slippage)
    fn apply_swap_costs(&self, amount: u64, dex: Dex) -> u64 {
        // Get protocol fee for this DEX (in basis points)
        let fee_bps = match dex {
            Dex::Jupiter => 0,   // Jupiter has no protocol fee
            Dex::Raydium => 25,  // 0.25%
            Dex::Orca => 30,     // 0.30%
        };

        // Apply protocol fee
        let after_fee = amount - (amount * fee_bps as u64) / 10000;

        // Apply slippage (50 bps = 0.5%)
        let slippage_bps = 50;
        let after_slippage =
            after_fee - (after_fee * slippage_bps as u64) / 10000;

        after_slippage
    }

    /// Calculate execution costs for multi-hop path
    fn calculate_multi_hop_costs(&self, hops: &[TradeHop]) -> ExecutionCost {
        let num_transactions = hops.len() as u64;

        // Transaction fees (Solana base fee ~5000 lamports)
        let base_tx_fee_sol = Decimal::from_str("0.000005").unwrap();
        let base_fees = base_tx_fee_sol * Decimal::from(num_transactions);

        // Priority fee (default 100,000 microlamports = 0.0001 SOL)
        let priority_fee_per_tx = Decimal::from_str("0.0001").unwrap();
        let priority_fees = priority_fee_per_tx * Decimal::from(num_transactions);

        let transaction_fees = base_fees + priority_fees;

        // Protocol fees (already accounted for in path evaluation)
        let protocol_fees = Decimal::ZERO;

        // Slippage (already accounted for in path evaluation)
        let slippage_cost = Decimal::ZERO;

        ExecutionCost::new(transaction_fees, protocol_fees, slippage_cost)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::str::FromStr;

    #[test]
    fn test_path_generation() {
        let config = BotConfig::default();
        let finder = MultiHopFinder::new(config);

        let sol = Pubkey::from_str("So11111111111111111111111111111111111111112").unwrap();
        let usdc = Pubkey::from_str("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v").unwrap();
        let bonk = Pubkey::new_unique();

        let intermediates = vec![usdc, bonk];

        let paths = finder.generate_paths(&sol, &intermediates);

        // Should have:
        // - 2 two-hop paths (SOL→USDC→SOL, SOL→BONK→SOL)
        // - 2 three-hop paths (SOL→USDC→BONK→SOL, SOL→BONK→USDC→SOL)
        // - 0 four-hop paths (need 3+ intermediates)

        assert_eq!(paths.len(), 4);

        println!("Generated paths:");
        for path in paths {
            println!("{:?}", path);
        }
    }

    #[tokio::test]
    #[ignore] // Requires network
    async fn test_find_multi_hop_paths() {
        let config = BotConfig::default();
        let finder = MultiHopFinder::new(config);

        let sol = Pubkey::from_str("So11111111111111111111111111111111111111112").unwrap();
        let usdc = Pubkey::from_str("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v").unwrap();

        let intermediates = vec![usdc];

        let paths = finder
            .find_multi_hop_paths(&sol, &intermediates, Decimal::from(1))
            .await
            .unwrap();

        println!("Found {} profitable paths", paths.len());

        for path in paths {
            println!("{:#?}", path);
        }
    }
}
