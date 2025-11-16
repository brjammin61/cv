use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use solana_sdk::pubkey::Pubkey;
use std::fmt;

/// Supported DEXs on Solana
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Dex {
    Jupiter,
    Raydium,
    Orca,
}

impl fmt::Display for Dex {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Dex::Jupiter => write!(f, "Jupiter"),
            Dex::Raydium => write!(f, "Raydium"),
            Dex::Orca => write!(f, "Orca"),
        }
    }
}

/// Token pair for trading
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct TokenPair {
    pub base: Pubkey,  // Token you're selling
    pub quote: Pubkey, // Token you're buying
}

/// Price quote from a DEX
#[derive(Debug, Clone)]
pub struct PriceQuote {
    pub dex: Dex,
    pub pair: TokenPair,
    pub input_amount: u64,        // Amount of input token (smallest unit)
    pub output_amount: u64,       // Amount of output token (smallest unit)
    pub price: Decimal,            // Price ratio (output/input)
    pub timestamp: i64,
    pub route: Vec<Pubkey>,        // Path of tokens in route
    pub quote_data: serde_json::Value, // Raw quote data for execution
}

impl PriceQuote {
    /// Calculate effective price accounting for fees
    pub fn effective_price(&self, fee_bps: u64) -> Decimal {
        let fee_multiplier = Decimal::from(10000 - fee_bps) / Decimal::from(10000);
        self.price * fee_multiplier
    }
}

/// Arbitrage opportunity detected
#[derive(Debug, Clone)]
pub struct ArbitrageOpportunity {
    pub id: String,
    pub buy_dex: Dex,
    pub sell_dex: Dex,
    pub pair: TokenPair,
    pub buy_quote: PriceQuote,
    pub sell_quote: PriceQuote,
    pub gross_profit: Decimal,      // Before fees
    pub net_profit: Decimal,        // After ALL fees
    pub profit_percent: Decimal,
    pub execution_cost: ExecutionCost,
    pub timestamp: i64,
}

/// All costs associated with executing a trade
#[derive(Debug, Clone)]
pub struct ExecutionCost {
    pub transaction_fees: Decimal,      // Base tx fee + priority fee
    pub protocol_fees: Decimal,         // DEX protocol fees
    pub slippage_cost: Decimal,         // Expected slippage
    pub total_cost: Decimal,            // Sum of all costs
}

impl ExecutionCost {
    pub fn new(
        transaction_fees: Decimal,
        protocol_fees: Decimal,
        slippage_cost: Decimal,
    ) -> Self {
        let total_cost = transaction_fees + protocol_fees + slippage_cost;
        Self {
            transaction_fees,
            protocol_fees,
            slippage_cost,
            total_cost,
        }
    }
}

/// Result of trade execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeResult {
    pub success: bool,
    pub signature: Option<String>,
    pub input_amount: u64,
    pub output_amount: u64,
    pub realized_profit: Option<Decimal>,
    pub execution_time_ms: u64,
    pub error: Option<String>,
    pub timestamp: i64,
}

/// Multi-hop arbitrage path
#[derive(Debug, Clone)]
pub struct ArbitragePath {
    pub hops: Vec<TradeHop>,
    pub net_profit: Decimal,
    pub profit_percent: Decimal,
    pub total_cost: ExecutionCost,
}

#[derive(Debug, Clone)]
pub struct TradeHop {
    pub dex: Dex,
    pub from_token: Pubkey,
    pub to_token: Pubkey,
    pub quote: PriceQuote,
}

/// Bot configuration
#[derive(Debug, Clone)]
pub struct BotConfig {
    // Strategy toggles
    pub enable_cross_dex_arb: bool,
    pub enable_multi_hop_arb: bool,
    pub enable_mev_searcher: bool,

    // Profit thresholds
    pub min_profit_sol: Decimal,
    pub min_profit_percent: Decimal,
    pub max_slippage_bps: u64,

    // Risk management
    pub max_trade_size_sol: Decimal,
    pub max_total_exposure_sol: Decimal,
    pub max_daily_loss_sol: Decimal,

    // Performance
    pub scan_interval_ms: u64,
    pub max_concurrent_ops: usize,
    pub tx_timeout_seconds: u64,

    // Fees
    pub base_tx_fee: Decimal,
    pub priority_fee_microlamports: u64,
    pub jupiter_fee_bps: u64,
    pub raydium_fee_bps: u64,
    pub orca_fee_bps: u64,

    // Jito
    pub use_jito_bundles: bool,
    pub jito_tip_lamports: u64,

    // Safety
    pub dry_run: bool,
}

impl Default for BotConfig {
    fn default() -> Self {
        Self {
            enable_cross_dex_arb: true,
            enable_multi_hop_arb: true,
            enable_mev_searcher: false, // Start conservative

            min_profit_sol: Decimal::new(1, 3), // 0.001 SOL
            min_profit_percent: Decimal::new(5, 1), // 0.5%
            max_slippage_bps: 50,

            max_trade_size_sol: Decimal::from(10),
            max_total_exposure_sol: Decimal::from(50),
            max_daily_loss_sol: Decimal::from(1),

            scan_interval_ms: 100,
            max_concurrent_ops: 10,
            tx_timeout_seconds: 30,

            base_tx_fee: Decimal::new(5, 6), // 0.000005 SOL
            priority_fee_microlamports: 10000,
            jupiter_fee_bps: 0,
            raydium_fee_bps: 25,
            orca_fee_bps: 30,

            use_jito_bundles: false,
            jito_tip_lamports: 10000,

            dry_run: true, // SAFE DEFAULT
        }
    }
}

/// Performance metrics
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct BotMetrics {
    pub total_opportunities_found: u64,
    pub total_trades_executed: u64,
    pub successful_trades: u64,
    pub failed_trades: u64,
    pub total_profit_sol: Decimal,
    pub total_loss_sol: Decimal,
    pub net_profit_sol: Decimal,
    pub win_rate: f64,
    pub average_profit_per_trade: Decimal,
    pub uptime_seconds: u64,
}

impl BotMetrics {
    pub fn record_trade(&mut self, result: &TradeResult) {
        self.total_trades_executed += 1;

        if result.success {
            self.successful_trades += 1;
            if let Some(profit) = result.realized_profit {
                if profit > Decimal::ZERO {
                    self.total_profit_sol += profit;
                } else {
                    self.total_loss_sol += profit.abs();
                }
            }
        } else {
            self.failed_trades += 1;
        }

        self.net_profit_sol = self.total_profit_sol - self.total_loss_sol;
        self.win_rate = self.successful_trades as f64 / self.total_trades_executed as f64;

        if self.successful_trades > 0 {
            self.average_profit_per_trade = self.total_profit_sol / Decimal::from(self.successful_trades);
        }
    }
}
