use serde::{Deserialize, Serialize};
use std::collections::VecDeque;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecisionRecord {
    pub timestamp: i64,
    pub mining_cost: f64,
    pub market_price: f64,
    pub decision: String, // "MINE", "BUY", "HOLD"
    pub profit_margin: f64,
    pub simulated_profit: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyMetrics {
    pub strategy_name: String,
    pub profit_threshold: f64,
    pub total_decisions: usize,
    pub mine_count: usize,
    pub buy_count: usize,
    pub hold_count: usize,
    pub total_simulated_profit: f64,
    pub average_profit_per_decision: f64,
    pub best_decision_profit: f64,
    pub worst_decision_profit: f64,
}

pub struct AnalyticsEngine {
    decisions: VecDeque<DecisionRecord>,
    max_history: usize,
}

impl AnalyticsEngine {
    pub fn new(max_history: usize) -> Self {
        Self {
            decisions: VecDeque::new(),
            max_history,
        }
    }

    /// Record a decision
    pub fn record_decision(&mut self, record: DecisionRecord) {
        if self.decisions.len() >= self.max_history {
            self.decisions.pop_front();
        }
        self.decisions.push_back(record);
    }

    /// Calculate metrics for the current strategy
    pub fn calculate_metrics(&self, strategy_name: &str, threshold: f64) -> StrategyMetrics {
        let mine_count = self.decisions.iter().filter(|d| d.decision == "MINE").count();
        let buy_count = self.decisions.iter().filter(|d| d.decision == "BUY").count();
        let hold_count = self.decisions.iter().filter(|d| d.decision == "HOLD").count();

        let total_profit: f64 = self.decisions.iter().map(|d| d.simulated_profit).sum();
        let avg_profit = if !self.decisions.is_empty() {
            total_profit / self.decisions.len() as f64
        } else {
            0.0
        };

        let best_profit = self.decisions.iter()
            .map(|d| d.simulated_profit)
            .fold(f64::NEG_INFINITY, f64::max);

        let worst_profit = self.decisions.iter()
            .map(|d| d.simulated_profit)
            .fold(f64::INFINITY, f64::min);

        StrategyMetrics {
            strategy_name: strategy_name.to_string(),
            profit_threshold: threshold,
            total_decisions: self.decisions.len(),
            mine_count,
            buy_count,
            hold_count,
            total_simulated_profit: total_profit,
            average_profit_per_decision: avg_profit,
            best_decision_profit: best_profit,
            worst_decision_profit: worst_profit,
        }
    }

    /// Analyze patterns - when is mining most profitable?
    pub fn analyze_mining_patterns(&self) -> MiningPatternAnalysis {
        let mine_decisions: Vec<&DecisionRecord> = self.decisions.iter()
            .filter(|d| d.decision == "MINE")
            .collect();

        if mine_decisions.is_empty() {
            return MiningPatternAnalysis::default();
        }

        let avg_mining_profit: f64 = mine_decisions.iter()
            .map(|d| d.simulated_profit)
            .sum::<f64>() / mine_decisions.len() as f64;

        let avg_mining_margin: f64 = mine_decisions.iter()
            .map(|d| d.profit_margin)
            .sum::<f64>() / mine_decisions.len() as f64;

        MiningPatternAnalysis {
            total_mining_decisions: mine_decisions.len(),
            average_mining_profit: avg_mining_profit,
            average_margin_when_mining: avg_mining_margin,
        }
    }

    /// Analyze patterns - when is buying most profitable?
    pub fn analyze_buying_patterns(&self) -> BuyingPatternAnalysis {
        let buy_decisions: Vec<&DecisionRecord> = self.decisions.iter()
            .filter(|d| d.decision == "BUY")
            .collect();

        if buy_decisions.is_empty() {
            return BuyingPatternAnalysis::default();
        }

        let avg_buying_profit: f64 = buy_decisions.iter()
            .map(|d| d.simulated_profit)
            .sum::<f64>() / buy_decisions.len() as f64;

        let avg_buying_margin: f64 = buy_decisions.iter()
            .map(|d| d.profit_margin)
            .sum::<f64>() / buy_decisions.len() as f64;

        BuyingPatternAnalysis {
            total_buying_decisions: buy_decisions.len(),
            average_buying_profit: avg_buying_profit,
            average_margin_when_buying: avg_buying_margin,
        }
    }

    /// Get recent decisions
    pub fn get_recent_decisions(&self, count: usize) -> Vec<DecisionRecord> {
        self.decisions.iter()
            .rev()
            .take(count)
            .cloned()
            .collect()
    }

    /// Export all decisions for analysis
    pub fn export_decisions(&self) -> Vec<DecisionRecord> {
        self.decisions.iter().cloned().collect()
    }
}

#[derive(Debug, Clone, Default)]
pub struct MiningPatternAnalysis {
    pub total_mining_decisions: usize,
    pub average_mining_profit: f64,
    pub average_margin_when_mining: f64,
}

#[derive(Debug, Clone, Default)]
pub struct BuyingPatternAnalysis {
    pub total_buying_decisions: usize,
    pub average_buying_profit: f64,
    pub average_margin_when_buying: f64,
}

/// Backtest different strategies to find the optimal one
pub fn backtest_strategies(
    simulated_data: &[(f64, f64)], // (mining_cost, market_price)
) -> Vec<StrategyMetrics> {
    let thresholds = vec![1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0];
    let mut results = Vec::new();

    for threshold in thresholds {
        let mut analytics = AnalyticsEngine::new(10000);

        for (i, (mining_cost, market_price)) in simulated_data.iter().enumerate() {
            let profit_margin = ((mining_cost - market_price).abs() / market_price) * 100.0;

            let decision = if mining_cost < market_price {
                let savings = (market_price - mining_cost) / market_price * 100.0;
                if savings >= threshold {
                    "MINE"
                } else {
                    "HOLD"
                }
            } else {
                let savings = (mining_cost - market_price) / mining_cost * 100.0;
                if savings >= threshold {
                    "BUY"
                } else {
                    "HOLD"
                }
            };

            // Simulate profit: if we made the right decision, we save money
            let simulated_profit = if decision == "MINE" {
                market_price - mining_cost
            } else if decision == "BUY" {
                mining_cost - market_price
            } else {
                0.0
            };

            analytics.record_decision(DecisionRecord {
                timestamp: i as i64,
                mining_cost: *mining_cost,
                market_price: *market_price,
                decision: decision.to_string(),
                profit_margin,
                simulated_profit,
            });
        }

        results.push(analytics.calculate_metrics(
            &format!("Threshold {}%", threshold),
            threshold,
        ));
    }

    results
}
