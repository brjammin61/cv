// src/economics.rs
use reqwest::Client;
use serde::Deserialize;
use super::onchain::OnChainState;

#[derive(Deserialize, Debug)]
struct JupiterPriceResponse {
    data: serde_json::Value,
}

/// Fetches the real-time USDC price for a token from Jupiter.
///
/// Supported symbols: ORE, COAL, SOL (and others on Jupiter)
pub async fn fetch_token_price(
    http_client: &Client,
    token_symbol: &str
) -> Result<f64, Box<dyn std::error::Error>> {
    // Jupiter Price API v4
    let url = format!("https://price.jup.ag/v4/price?ids={}", token_symbol);

    let response = http_client
        .get(&url)
        .timeout(std::time::Duration::from_secs(10))
        .send()
        .await?;

    let json: JupiterPriceResponse = response.json().await?;

    // Navigate the JSON structure: data -> {token_symbol} -> price
    let price_str = json.data
        .get(token_symbol)
        .and_then(|v| v.get("price"))
        .and_then(|v| v.as_str())
        .ok_or(format!("Could not find price for symbol {}", token_symbol))?;

    let price = price_str.parse::<f64>()?;

    println!("Fetched {} price: ${:.6}", token_symbol, price);

    Ok(price)
}

#[derive(Debug, Clone)]
pub struct ProfitabilityReport {
    pub token: String,
    pub gross_revenue_usd: f64,
    pub operational_cost_usd: f64,
    pub net_profit_usd: f64,
    pub expected_reward_per_min: f64,
    pub tx_fee_cost_usd: f64,
    pub energy_cost_usd: f64,
}

/// Configuration for energy cost calculation
#[derive(Debug, Clone)]
pub struct EnergyConfig {
    pub hardware_watts: f64,      // Power consumption in watts
    pub electricity_cost_kwh: f64, // Cost per kWh in USD
}

impl Default for EnergyConfig {
    fn default() -> Self {
        EnergyConfig {
            hardware_watts: 50.0,    // Default: Apple M2 chip (~50W under load)
            electricity_cost_kwh: 0.10, // Default: $0.10 per kWh (US average)
        }
    }
}

impl EnergyConfig {
    /// Calculate energy cost per minute
    pub fn cost_per_minute(&self) -> f64 {
        // Convert watts to kW, then calculate cost per minute
        let kw = self.hardware_watts / 1000.0;
        let kwh_per_minute = kw / 60.0;
        kwh_per_minute * self.electricity_cost_kwh
    }
}

/// The core economic logic from your analysis.
///
/// Calculates the profitability of mining a given token based on:
/// - Local hashrate (hpm)
/// - Current token price
/// - SOL price (for fee calculations)
/// - On-chain difficulty and reward rate
/// - Staking multiplier (if applicable)
/// - Energy costs
pub async fn calculate_profitability(
    local_hpm: u64,
    sol_price_usd: f64,
    staking_multiplier: f64,
    state: &OnChainState,
    token_price_usd: f64,
    energy_config: &EnergyConfig,
) -> ProfitabilityReport {

    // 1. Calculate expected reward per minute
    // Formula: (local_hashrate / global_difficulty) * reward_rate
    let hashrate_ratio = local_hpm as f64 / state.global_difficulty as f64;

    // Determine token decimals: ORE uses 11 decimals, COAL uses estimated 11 decimals
    let decimals_divisor = if state.token == "ORE" || state.token == "COAL" {
        100_000_000_000.0 // 11 decimals (10^11)
    } else {
        1_000_000_000.0 // 9 decimals fallback (10^9)
    };

    let reward_per_min_raw = hashrate_ratio * (state.reward_rate as f64 / decimals_divisor);
    let expected_reward_per_min = reward_per_min_raw * staking_multiplier;

    // 2. Calculate gross revenue
    let gross_revenue = expected_reward_per_min * token_price_usd;

    // 3. Calculate transaction fee cost
    let base_fee_lamports = 5_000; // Solana base transaction fee
    let total_fee_lamports = base_fee_lamports + state.priority_fee;
    let total_fee_sol = total_fee_lamports as f64 / 1_000_000_000.0; // Convert lamports to SOL
    let tx_fee_cost = total_fee_sol * sol_price_usd;

    // 4. Calculate energy cost
    let energy_cost = energy_config.cost_per_minute();

    // 5. Calculate net profit
    let operational_cost = tx_fee_cost + energy_cost;
    let net_profit = gross_revenue - operational_cost;

    ProfitabilityReport {
        token: state.token.clone(),
        gross_revenue_usd: gross_revenue,
        operational_cost_usd: operational_cost,
        net_profit_usd: net_profit,
        expected_reward_per_min: expected_reward_per_min,
        tx_fee_cost_usd: tx_fee_cost,
        energy_cost_usd: energy_cost,
    }
}

/// Prints a formatted profitability report
pub fn print_report(report: &ProfitabilityReport) {
    println!("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("📊 {} PROFITABILITY REPORT", report.token);
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("  Expected Reward: {:.9} {}/min", report.expected_reward_per_min, report.token);
    println!("  Gross Revenue:   ${:.6}/min", report.gross_revenue_usd);
    println!("  ─────────────────────────────");
    println!("  Costs:");
    println!("    TX Fees:       ${:.6}/min", report.tx_fee_cost_usd);
    println!("    Energy:        ${:.6}/min", report.energy_cost_usd);
    println!("  Total Cost:      ${:.6}/min", report.operational_cost_usd);
    println!("  ─────────────────────────────");

    if report.net_profit_usd > 0.0 {
        println!("  ✅ NET PROFIT:   ${:.6}/min", report.net_profit_usd);
        println!("     (${:.2}/hour, ${:.2}/day)", report.net_profit_usd * 60.0, report.net_profit_usd * 60.0 * 24.0);
    } else {
        println!("  ❌ NET LOSS:     ${:.6}/min", report.net_profit_usd.abs());
    }
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
}
