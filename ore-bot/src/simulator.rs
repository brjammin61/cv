use anyhow::Result;
use rand::Rng;

use crate::analytics::{AnalyticsEngine, DecisionRecord, backtest_strategies};

/// Generate realistic market data for simulation
pub struct MarketSimulator {
    base_mining_cost: f64,
    base_market_price: f64,
    volatility: f64,
}

impl MarketSimulator {
    pub fn new(base_mining_cost: f64, base_market_price: f64, volatility: f64) -> Self {
        Self {
            base_mining_cost,
            base_market_price,
            volatility,
        }
    }

    /// Generate next data point (mining_cost, market_price)
    pub fn next(&mut self) -> (f64, f64) {
        let mut rng = rand::thread_rng();

        // Mining cost varies based on network congestion
        // Higher variance (20-50% swings)
        let mining_variance = rng.gen_range(-self.volatility * 0.4..self.volatility * 0.4);
        let mining_cost = (self.base_mining_cost * (1.0 + mining_variance)).max(0.001);

        // Market price is more stable but still varies
        // Lower variance (10-30% swings)
        let price_variance = rng.gen_range(-self.volatility * 0.2..self.volatility * 0.2);
        let market_price = (self.base_market_price * (1.0 + price_variance)).max(0.001);

        // Update base values with slight drift
        self.base_mining_cost = mining_cost;
        self.base_market_price = market_price;

        (mining_cost, market_price)
    }

    /// Generate a batch of data points
    pub fn generate_batch(&mut self, count: usize) -> Vec<(f64, f64)> {
        (0..count).map(|_| self.next()).collect()
    }
}

/// Run a live simulation
pub fn run_simulation(
    duration_minutes: usize,
    poll_interval_seconds: u64,
    profit_threshold: f64,
) -> Result<()> {
    println!("\n🎮 Starting Live Simulation");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Duration: {} minutes", duration_minutes);
    println!("Poll Interval: {}s", poll_interval_seconds);
    println!("Profit Threshold: {}%", profit_threshold);
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

    let cycles = (duration_minutes * 60) / poll_interval_seconds as usize;

    let mut simulator = MarketSimulator::new(
        0.0095, // Base mining cost: 0.0095 SOL
        0.0105, // Base market price: 0.0105 SOL
        0.3,    // 30% volatility
    );

    let mut analytics = AnalyticsEngine::new(10000);
    let mut current_mode = "STOPPED";
    let mut ore_accumulated: f64 = 0.0;
    let mut sol_spent: f64 = 0.0;

    for cycle in 1..=cycles {
        let (mining_cost, market_price) = simulator.next();

        // Make decision using the same logic as the real bot
        let decision = make_decision(mining_cost, market_price, profit_threshold);

        // Calculate profit margin
        let profit_margin = if mining_cost < market_price {
            ((market_price - mining_cost) / market_price) * 100.0
        } else {
            ((mining_cost - market_price) / mining_cost) * 100.0
        };

        // Simulate actual profit
        let simulated_profit = match decision {
            "MINE" => {
                // We mine 1 ORE at mining_cost, save (market_price - mining_cost)
                ore_accumulated += 1.0;
                sol_spent += mining_cost;
                market_price - mining_cost
            }
            "BUY" => {
                // We buy 1 ORE at market_price, save (mining_cost - market_price)
                ore_accumulated += 1.0;
                sol_spent += market_price;
                mining_cost - market_price
            }
            _ => 0.0,
        };

        // Record decision
        analytics.record_decision(DecisionRecord {
            timestamp: cycle as i64,
            mining_cost,
            market_price,
            decision: decision.to_string(),
            profit_margin,
            simulated_profit,
        });

        // Update mode
        if decision != current_mode {
            let mode_change = format!("{} → {}", current_mode, decision);
            current_mode = decision;

            println!("⚡ Mode Change: {}", mode_change);
        }

        // Print cycle info every 10 cycles
        if cycle % 10 == 0 {
            println!("\n📊 Cycle {}/{}", cycle, cycles);
            println!("   Mining Cost: {:.6} SOL", mining_cost);
            println!("   Market Price: {:.6} SOL", market_price);
            println!("   Decision: {}", decision);
            println!("   Margin: {:.2}%", profit_margin);
            println!("   Cycle Profit: {:.6} SOL", simulated_profit);
            println!("   Total ORE: {:.2}", ore_accumulated);
            println!("   Total SOL Spent: {:.6}", sol_spent);
            println!("   Avg Cost/ORE: {:.6} SOL", sol_spent / ore_accumulated.max(1.0));
        }

        // Sleep to simulate real-time
        // (commented out for fast simulation)
        // std::thread::sleep(std::time::Duration::from_secs(poll_interval_seconds));
    }

    // Final metrics
    println!("\n\n🏁 Simulation Complete!");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    let metrics = analytics.calculate_metrics("Simulated Strategy", profit_threshold);
    print_metrics(&metrics);

    println!("\n💰 Final Results:");
    println!("   Total ORE Accumulated: {:.2}", ore_accumulated);
    println!("   Total SOL Spent: {:.6}", sol_spent);
    println!("   Average Cost per ORE: {:.6} SOL", sol_spent / ore_accumulated.max(1.0));
    println!("   Total Profit: {:.6} SOL", metrics.total_simulated_profit);

    // Pattern analysis
    println!("\n🔍 Pattern Analysis:");
    let mining_patterns = analytics.analyze_mining_patterns();
    println!("\n   Mining Patterns:");
    println!("   - Times mined: {}", mining_patterns.total_mining_decisions);
    println!("   - Avg profit when mining: {:.6} SOL", mining_patterns.average_mining_profit);
    println!("   - Avg margin when mining: {:.2}%", mining_patterns.average_margin_when_mining);

    let buying_patterns = analytics.analyze_buying_patterns();
    println!("\n   Buying Patterns:");
    println!("   - Times bought: {}", buying_patterns.total_buying_decisions);
    println!("   - Avg profit when buying: {:.6} SOL", buying_patterns.average_buying_profit);
    println!("   - Avg margin when buying: {:.2}%", buying_patterns.average_margin_when_buying);

    Ok(())
}

/// Make decision using the arbitrage logic
fn make_decision(mining_cost: f64, market_price: f64, threshold: f64) -> &'static str {
    let threshold_decimal = threshold / 100.0;

    if mining_cost < market_price {
        let savings = (market_price - mining_cost) / market_price;
        if savings >= threshold_decimal {
            return "MINE";
        }
    } else {
        let savings = (mining_cost - market_price) / mining_cost;
        if savings >= threshold_decimal {
            return "BUY";
        }
    }

    "HOLD"
}

/// Run backtesting to find optimal strategy
pub fn run_backtest(num_datapoints: usize) -> Result<()> {
    println!("\n🔬 Running Strategy Backtest");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("Testing {} different profit thresholds", 7);
    println!("Simulating {} decision cycles\n", num_datapoints);

    let mut simulator = MarketSimulator::new(0.0095, 0.0105, 0.3);
    let data = simulator.generate_batch(num_datapoints);

    let results = backtest_strategies(&data);

    println!("📈 Backtest Results:\n");

    for metrics in &results {
        print_metrics(metrics);
        println!();
    }

    // Find best strategy
    let best = results.iter()
        .max_by(|a, b| a.total_simulated_profit.partial_cmp(&b.total_simulated_profit).unwrap())
        .unwrap();

    println!("\n🏆 OPTIMAL STRATEGY FOUND!");
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("   Strategy: {}", best.strategy_name);
    println!("   Profit Threshold: {}%", best.profit_threshold);
    println!("   Total Profit: {:.6} SOL", best.total_simulated_profit);
    println!("   Avg Profit/Decision: {:.6} SOL", best.average_profit_per_decision);
    println!("\n   Recommendation: Set PROFIT_THRESHOLD_PERCENT={} in .env", best.profit_threshold);

    Ok(())
}

/// Print metrics nicely
fn print_metrics(metrics: &crate::analytics::StrategyMetrics) {
    println!("Strategy: {}", metrics.strategy_name);
    println!("  Threshold: {}%", metrics.profit_threshold);
    println!("  Total Decisions: {}", metrics.total_decisions);
    println!("  ├─ Mine: {} ({:.1}%)", metrics.mine_count,
             metrics.mine_count as f64 / metrics.total_decisions as f64 * 100.0);
    println!("  ├─ Buy:  {} ({:.1}%)", metrics.buy_count,
             metrics.buy_count as f64 / metrics.total_decisions as f64 * 100.0);
    println!("  └─ Hold: {} ({:.1}%)", metrics.hold_count,
             metrics.hold_count as f64 / metrics.total_decisions as f64 * 100.0);
    println!("  Total Profit: {:.6} SOL", metrics.total_simulated_profit);
    println!("  Avg Profit/Decision: {:.6} SOL", metrics.average_profit_per_decision);
    println!("  Best Decision: {:.6} SOL", metrics.best_decision_profit);
    println!("  Worst Decision: {:.6} SOL", metrics.worst_decision_profit);
}
