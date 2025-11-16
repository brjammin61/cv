use anyhow::Result;
use serde::{Deserialize, Serialize};

/// Mineable token configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MineableToken {
    pub name: String,
    pub symbol: String,
    pub mint_address: String,
    pub miner_command: String,
    pub protocol_fee_percent: f64,
    pub estimated_difficulty: f64,
}

/// Token profitability metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenProfitability {
    pub token: MineableToken,
    pub mining_cost_sol: f64,
    pub market_price_sol: f64,
    pub profit_margin_percent: f64,
    pub estimated_daily_profit: f64,
    pub liquidity_score: u8, // 1-10
    pub recommendation_score: f64,
}

impl TokenProfitability {
    /// Calculate overall recommendation score
    pub fn calculate_score(&mut self) {
        // Weighted scoring:
        // - 50% profit margin
        // - 30% liquidity
        // - 20% absolute profit
        let margin_score = self.profit_margin_percent / 100.0;
        let liquidity_score = self.liquidity_score as f64 / 10.0;
        let profit_score = (self.estimated_daily_profit / 10.0).min(1.0);

        self.recommendation_score =
            (margin_score * 0.5) +
            (liquidity_score * 0.3) +
            (profit_score * 0.2);
    }
}

/// Available mineable tokens on Solana
pub fn get_supported_tokens() -> Vec<MineableToken> {
    vec![
        MineableToken {
            name: "ORE".to_string(),
            symbol: "ORE".to_string(),
            mint_address: "oreoU2P8bN6jkk3jbaiVxYnG1dCXcYxwhwyK9jSybcp".to_string(),
            miner_command: "ore mine".to_string(),
            protocol_fee_percent: 10.0,
            estimated_difficulty: 1.0, // baseline
        },
        MineableToken {
            name: "COAL".to_string(),
            symbol: "COAL".to_string(),
            mint_address: "coaLSkmFF3pGFba8qCHhexfPaULBssTEeKxQjHFWPtn".to_string(),
            miner_command: "coal mine".to_string(),
            protocol_fee_percent: 10.0,
            estimated_difficulty: 0.6, // typically lower than ORE
        },
    ]
}

/// Analyze profitability of all supported tokens
pub fn analyze_all_tokens() -> Result<Vec<TokenProfitability>> {
    let tokens = get_supported_tokens();
    let mut results = Vec::new();

    for token in tokens {
        let profitability = analyze_token_profitability(token)?;
        results.push(profitability);
    }

    // Sort by recommendation score (highest first)
    results.sort_by(|a, b| {
        b.recommendation_score
            .partial_cmp(&a.recommendation_score)
            .unwrap()
    });

    Ok(results)
}

/// Analyze profitability of a specific token
fn analyze_token_profitability(token: MineableToken) -> Result<TokenProfitability> {
    // Simulate mining cost based on difficulty
    // In production, this would query actual network data
    let base_mining_cost = 0.0095; // Base cost in SOL
    let mining_cost_sol = base_mining_cost * token.estimated_difficulty;

    // Simulate market price
    // In production, this would query Jupiter/DEX
    let market_price_sol = match token.symbol.as_str() {
        "ORE" => 0.0105,  // Simulated ORE price
        "COAL" => 0.0080, // Simulated COAL price
        _ => 0.0100,
    };

    // Calculate profit margin
    let profit_margin_percent = if mining_cost_sol < market_price_sol {
        ((market_price_sol - mining_cost_sol) / market_price_sol) * 100.0
    } else {
        0.0
    };

    // Estimate daily profit (assuming 120 cycles per hour, 24 hours)
    let cycles_per_day = 120 * 24;
    let profit_per_cycle = (market_price_sol - mining_cost_sol).max(0.0);
    let estimated_daily_profit = profit_per_cycle * cycles_per_day as f64;

    // Liquidity score (1-10)
    let liquidity_score = match token.symbol.as_str() {
        "ORE" => 9,  // High liquidity
        "COAL" => 6, // Medium liquidity
        _ => 3,      // Low liquidity
    };

    let mut profitability = TokenProfitability {
        token,
        mining_cost_sol,
        market_price_sol,
        profit_margin_percent,
        estimated_daily_profit,
        liquidity_score,
        recommendation_score: 0.0,
    };

    profitability.calculate_score();

    Ok(profitability)
}

/// Print profitability comparison
pub fn print_token_comparison(tokens: &[TokenProfitability]) {
    println!("\n╔═══════════════════════════════════════════════════════════════╗");
    println!("║       MULTI-TOKEN MINING PROFITABILITY ANALYSIS             ║");
    println!("╚═══════════════════════════════════════════════════════════════╝\n");

    for (i, token) in tokens.iter().enumerate() {
        let rank_emoji = match i {
            0 => "🏆",
            1 => "🥈",
            2 => "🥉",
            _ => "  ",
        };

        println!("{} {} ({})", rank_emoji, token.token.name, token.token.symbol);
        println!("   Mint: {}", token.token.mint_address);
        println!("   Mining Cost:      {:.6} SOL", token.mining_cost_sol);
        println!("   Market Price:     {:.6} SOL", token.market_price_sol);
        println!("   Profit Margin:    {:.2}%", token.profit_margin_percent);
        println!("   Daily Profit Est: {:.6} SOL", token.estimated_daily_profit);
        println!("   Liquidity:        {}/10", token.liquidity_score);
        println!("   Score:            {:.3} ★", token.recommendation_score);

        if i == 0 {
            println!("\n   🎯 RECOMMENDED: This is the most profitable token!");
        }

        println!();
    }

    // Summary
    if tokens.len() >= 2 {
        let best = &tokens[0];
        let second = &tokens[1];

        let profit_difference = best.estimated_daily_profit - second.estimated_daily_profit;
        let margin_difference = best.profit_margin_percent - second.profit_margin_percent;

        println!("📊 COMPARISON:");
        println!("   {} is {:.2}% MORE profitable than {}",
                 best.token.symbol,
                 margin_difference,
                 second.token.symbol);
        println!("   Expected additional profit: {:.6} SOL/day\n",
                 profit_difference);
    }

    // Recommendations
    println!("💡 RECOMMENDATIONS:\n");

    let best = &tokens[0];
    println!("1. Mine {} for maximum profit", best.token.symbol);
    println!("2. Use this miner command: {}", best.token.miner_command);
    println!("3. Update .env file:");
    println!("   ORE_MINT={}", best.token.mint_address);
    println!("   MINER_PATH={}", best.token.miner_command.split_whitespace().next().unwrap());
    println!("   MINER_ARGS=mine --keypair wallet.json\n");

    // Risk assessment
    if best.liquidity_score < 7 {
        println!("⚠️  WARNING: Lower liquidity - test with small amounts first!");
    }
}

/// Generate configuration for best token
pub fn generate_optimal_config(tokens: &[TokenProfitability]) -> String {
    if tokens.is_empty() {
        return "No tokens available".to_string();
    }

    let best = &tokens[0];
    let miner_path = best.token.miner_command.split_whitespace().next().unwrap();

    format!(
        r#"# Optimal Configuration (Auto-Generated)
# Based on multi-token profitability analysis

# RECOMMENDED TOKEN: {} (Highest profit margin: {:.2}%)
ORE_MINT={}
MINER_PATH={}
MINER_ARGS=mine --keypair wallet.json

# Optimization settings
PROFIT_THRESHOLD_PERCENT=1.0
POLL_INTERVAL_SECONDS=15
SWAP_AMOUNT_SOL=0.5

# Expected performance:
# - Daily profit: ~{:.6} SOL
# - Profit margin: {:.2}%
# - Liquidity: {}/10
"#,
        best.token.symbol,
        best.profit_margin_percent,
        best.token.mint_address,
        miner_path,
        best.estimated_daily_profit,
        best.profit_margin_percent,
        best.liquidity_score
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_analyze_tokens() {
        let results = analyze_all_tokens().unwrap();
        assert!(!results.is_empty());

        // Should be sorted by score
        if results.len() >= 2 {
            assert!(results[0].recommendation_score >= results[1].recommendation_score);
        }
    }

    #[test]
    fn test_score_calculation() {
        let token = MineableToken {
            name: "TEST".to_string(),
            symbol: "TEST".to_string(),
            mint_address: "test123".to_string(),
            miner_command: "test mine".to_string(),
            protocol_fee_percent: 10.0,
            estimated_difficulty: 1.0,
        };

        let mut prof = TokenProfitability {
            token,
            mining_cost_sol: 0.009,
            market_price_sol: 0.011,
            profit_margin_percent: 18.18,
            estimated_daily_profit: 5.0,
            liquidity_score: 8,
            recommendation_score: 0.0,
        };

        prof.calculate_score();
        assert!(prof.recommendation_score > 0.0);
        assert!(prof.recommendation_score <= 1.0);
    }
}
