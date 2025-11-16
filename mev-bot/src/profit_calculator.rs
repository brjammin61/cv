use crate::types::*;
use rust_decimal::Decimal;
use rust_decimal::prelude::ToPrimitive;
use rust_decimal_macros::dec;

/// Calculate actual profit accounting for ALL fees and slippage
/// This is the CRITICAL component that prevents sim-only profits
pub struct ProfitCalculator {
    config: BotConfig,
}

impl ProfitCalculator {
    pub fn new(config: BotConfig) -> Self {
        Self { config }
    }

    /// Calculate net profit for a cross-DEX arbitrage
    ///
    /// Returns None if not profitable after all costs
    pub fn calculate_arbitrage_profit(
        &self,
        buy_quote: &PriceQuote,
        sell_quote: &PriceQuote,
        trade_size_sol: Decimal,
    ) -> Option<(Decimal, ExecutionCost)> {
        // Convert SOL to lamports for calculations
        let lamports = (trade_size_sol * dec!(1_000_000_000)).to_u64().unwrap();

        // Calculate buy side (what we get)
        let buy_output = self.calculate_swap_output(
            buy_quote,
            lamports,
            buy_quote.dex,
        )?;

        // Calculate sell side (what we pay)
        let sell_output = self.calculate_swap_output(
            sell_quote,
            buy_output,
            sell_quote.dex,
        )?;

        // Calculate execution costs
        let execution_cost = self.calculate_execution_cost(
            buy_quote.dex,
            sell_quote.dex,
            lamports,
        );

        // Gross profit = sell output - buy input
        let gross_profit_lamports = sell_output as i64 - lamports as i64;
        let gross_profit = Decimal::from(gross_profit_lamports) / dec!(1_000_000_000);

        // Net profit = gross profit - all costs
        let net_profit = gross_profit - execution_cost.total_cost;

        // Check if meets minimum thresholds
        if net_profit < self.config.min_profit_sol {
            return None;
        }

        let profit_percent = (net_profit / trade_size_sol) * dec!(100);
        if profit_percent < self.config.min_profit_percent {
            return None;
        }

        Some((net_profit, execution_cost))
    }

    /// Calculate actual output of a swap accounting for fees and slippage
    fn calculate_swap_output(
        &self,
        quote: &PriceQuote,
        input_amount: u64,
        dex: Dex,
    ) -> Option<u64> {
        // Get protocol fee for this DEX
        let protocol_fee_bps = match dex {
            Dex::Jupiter => self.config.jupiter_fee_bps,
            Dex::Raydium => self.config.raydium_fee_bps,
            Dex::Orca => self.config.orca_fee_bps,
        };

        // Calculate expected output from quote
        let price_ratio = Decimal::from(quote.output_amount) / Decimal::from(quote.input_amount);
        let expected_output = (Decimal::from(input_amount) * price_ratio).to_u64()?;

        // Apply protocol fee
        let after_protocol_fee = self.apply_fee(expected_output, protocol_fee_bps);

        // Apply slippage (conservative estimate)
        let after_slippage = self.apply_slippage(after_protocol_fee, self.config.max_slippage_bps);

        Some(after_slippage)
    }

    /// Calculate all execution costs for a cross-DEX arbitrage
    fn calculate_execution_cost(
        &self,
        buy_dex: Dex,
        sell_dex: Dex,
        trade_size_lamports: u64,
    ) -> ExecutionCost {
        // Transaction fees (2 transactions: buy + sell)
        let num_transactions = 2;
        let base_fees = self.config.base_tx_fee * Decimal::from(num_transactions);

        // Priority fees
        let priority_fee_per_tx = Decimal::from(self.config.priority_fee_microlamports)
            / dec!(1_000_000); // Convert micro-lamports to SOL
        let priority_fees = priority_fee_per_tx * Decimal::from(num_transactions);

        let transaction_fees = base_fees + priority_fees;

        // Protocol fees
        let buy_protocol_fee = self.calculate_protocol_fee(buy_dex, trade_size_lamports);
        let sell_protocol_fee = self.calculate_protocol_fee(sell_dex, trade_size_lamports);
        let protocol_fees = buy_protocol_fee + sell_protocol_fee;

        // Slippage cost (both sides)
        let buy_slippage = self.calculate_slippage_cost(trade_size_lamports);
        let sell_slippage = self.calculate_slippage_cost(trade_size_lamports);
        let slippage_cost = buy_slippage + sell_slippage;

        ExecutionCost::new(transaction_fees, protocol_fees, slippage_cost)
    }

    /// Calculate protocol fee for a DEX
    fn calculate_protocol_fee(&self, dex: Dex, amount_lamports: u64) -> Decimal {
        let fee_bps = match dex {
            Dex::Jupiter => self.config.jupiter_fee_bps,
            Dex::Raydium => self.config.raydium_fee_bps,
            Dex::Orca => self.config.orca_fee_bps,
        };

        let amount_sol = Decimal::from(amount_lamports) / dec!(1_000_000_000);
        amount_sol * Decimal::from(fee_bps) / dec!(10000)
    }

    /// Calculate expected slippage cost
    fn calculate_slippage_cost(&self, amount_lamports: u64) -> Decimal {
        let amount_sol = Decimal::from(amount_lamports) / dec!(1_000_000_000);
        amount_sol * Decimal::from(self.config.max_slippage_bps) / dec!(10000)
    }

    /// Apply fee to an amount
    fn apply_fee(&self, amount: u64, fee_bps: u64) -> u64 {
        let fee = (amount as u128 * fee_bps as u128) / 10000;
        amount - fee as u64
    }

    /// Apply slippage to an amount (conservative)
    fn apply_slippage(&self, amount: u64, slippage_bps: u64) -> u64 {
        let slippage = (amount as u128 * slippage_bps as u128) / 10000;
        amount - slippage as u64
    }

    /// Validate if trade is worth executing (final check before execution)
    pub fn validate_execution(
        &self,
        opportunity: &ArbitrageOpportunity,
        current_prices: (&PriceQuote, &PriceQuote),
    ) -> Result<(), String> {
        let (buy_quote, sell_quote) = current_prices;

        // Re-calculate profit with current prices (they may have changed!)
        let trade_size = Decimal::from(opportunity.buy_quote.input_amount) / dec!(1_000_000_000);

        match self.calculate_arbitrage_profit(buy_quote, sell_quote, trade_size) {
            Some((net_profit, _)) => {
                if net_profit < self.config.min_profit_sol {
                    return Err(format!(
                        "Profit dropped below threshold: {} < {}",
                        net_profit, self.config.min_profit_sol
                    ));
                }
                Ok(())
            }
            None => Err("No longer profitable after price update".to_string()),
        }
    }

    /// Calculate break-even price needed for profitability
    pub fn calculate_breakeven_spread(&self, trade_size_sol: Decimal) -> Decimal {
        let lamports = (trade_size_sol * dec!(1_000_000_000)).to_u64().unwrap();

        // Calculate minimum spread needed to cover all costs
        let execution_cost = self.calculate_execution_cost(
            Dex::Jupiter,  // Assume best case (lowest fees)
            Dex::Jupiter,
            lamports,
        );

        // Add minimum profit requirement
        let total_needed = execution_cost.total_cost + self.config.min_profit_sol;

        // Return as percentage of trade size
        (total_needed / trade_size_sol) * dec!(100)
    }

    /// Estimate realistic daily profit potential
    pub fn estimate_daily_profit(
        &self,
        opportunities_per_day: u64,
        avg_profit_per_op: Decimal,
        success_rate: f64,
    ) -> Decimal {
        let expected_successful = Decimal::from(opportunities_per_day) * Decimal::from_f64_retain(success_rate).unwrap();
        expected_successful * avg_profit_per_op
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_profit_calculation_with_fees() {
        let config = BotConfig::default();
        let calculator = ProfitCalculator::new(config);

        // Simulate a quote
        let buy_quote = PriceQuote {
            dex: Dex::Jupiter,
            pair: TokenPair {
                base: solana_sdk::pubkey::Pubkey::new_unique(),
                quote: solana_sdk::pubkey::Pubkey::new_unique(),
            },
            input_amount: 1_000_000_000, // 1 SOL
            output_amount: 100_000_000,  // 0.1 token
            price: dec!(0.1),
            timestamp: 0,
            route: vec![],
            quote_data: serde_json::json!({}),
        };

        let sell_quote = PriceQuote {
            dex: Dex::Raydium,
            pair: TokenPair {
                base: solana_sdk::pubkey::Pubkey::new_unique(),
                quote: solana_sdk::pubkey::Pubkey::new_unique(),
            },
            input_amount: 100_000_000,   // 0.1 token
            output_amount: 1_100_000_000, // 1.1 SOL (10% profit gross)
            price: dec!(11.0),
            timestamp: 0,
            route: vec![],
            quote_data: serde_json::json!({}),
        };

        // Calculate profit
        let result = calculator.calculate_arbitrage_profit(
            &buy_quote,
            &sell_quote,
            dec!(1.0),
        );

        // Should have some profit after fees
        assert!(result.is_some());

        if let Some((net_profit, costs)) = result {
            println!("Net profit: {} SOL", net_profit);
            println!("Total costs: {} SOL", costs.total_cost);
            println!("Transaction fees: {} SOL", costs.transaction_fees);
            println!("Protocol fees: {} SOL", costs.protocol_fees);
            println!("Slippage cost: {} SOL", costs.slippage_cost);

            // Profit should be less than gross (10%) due to fees
            assert!(net_profit < dec!(0.1));
            // But should still be positive
            assert!(net_profit > dec!(0.0));
        }
    }

    #[test]
    fn test_breakeven_calculation() {
        let config = BotConfig::default();
        let calculator = ProfitCalculator::new(config);

        let breakeven = calculator.calculate_breakeven_spread(dec!(1.0));
        println!("Breakeven spread: {}%", breakeven);

        // Breakeven should be positive and reasonable
        assert!(breakeven > dec!(0.0));
        assert!(breakeven < dec!(10.0)); // Less than 10% spread needed
    }
}
