// src/main.rs
//
// Project IronPick: Solana Mining Profitability Bot
//
// This bot continuously monitors the profitability of mining ORE and COAL
// on Solana, and automatically switches to mine the most profitable asset
// or sleeps if neither is profitable.

mod hardware;
mod onchain;
mod economics;
mod miner;

use solana_client::rpc_client::RpcClient;
use std::time::Duration;
use miner::{MinerManager, MiningTarget, MinerConfig};
use economics::EnergyConfig;

/// Configuration constants
/// Developers should modify these or move to a config file
const SOLANA_RPC_URL: &str = "https://api.mainnet-beta.solana.com";
const BENCHMARK_DURATION_SECS: u64 = 60;
const EPOCH_DURATION_SECS: u64 = 60;
const DEFAULT_STAKING_MULTIPLIER: f64 = 1.5; // Adjust based on actual staking

#[tokio::main]
async fn main() {
    println!("╔════════════════════════════════════════════════════════════╗");
    println!("║        🪨 PROJECT IRONPICK: SOLANA MINING ADVISOR 🪨       ║");
    println!("║                                                            ║");
    println!("║  Automated profitability engine for ORE and COAL mining   ║");
    println!("╚════════════════════════════════════════════════════════════╝\n");

    // --- Load Configuration ---
    let miner_config = load_miner_config();
    let energy_config = load_energy_config();

    println!("⚙️  Configuration loaded:");
    println!("   RPC: {}", SOLANA_RPC_URL);
    println!("   Staking Multiplier: {}", DEFAULT_STAKING_MULTIPLIER);
    println!("   Hardware: {}W @ ${}/kWh",
        energy_config.hardware_watts,
        energy_config.electricity_cost_kwh
    );

    // --- Initialize Clients ---
    println!("\n🔌 Connecting to Solana...");
    let rpc_client = RpcClient::new_with_timeout(
        SOLANA_RPC_URL.to_string(),
        Duration::from_secs(30)
    );
    let http_client = reqwest::Client::new();

    // Test RPC connection
    match rpc_client.get_version() {
        Ok(version) => println!("   ✅ Connected to Solana RPC (version: {})", version.solana_core),
        Err(e) => {
            eprintln!("   ❌ Failed to connect to RPC: {}", e);
            eprintln!("   Please check your RPC URL and internet connection");
            return;
        }
    }

    // --- Initialize Miner Manager ---
    let mut miner_manager = MinerManager::new(miner_config);

    // --- Hardware Benchmarking ---
    println!("\n🔧 Running hardware benchmark...");
    println!("   This will take {} seconds to measure your hashrate...", BENCHMARK_DURATION_SECS);
    let local_hpm = hardware::run_quick_benchmark(BENCHMARK_DURATION_SECS);

    if local_hpm == 0 {
        eprintln!("❌ Benchmark failed. Exiting.");
        return;
    }

    println!("   ✅ Benchmark complete: {} hashes/minute", local_hpm);

    // --- Main Advisor Loop ---
    println!("\n🚀 Starting main advisor loop...");
    println!("   Checking profitability every {} seconds\n", EPOCH_DURATION_SECS);
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

    let mut epoch_number = 0;

    loop {
        epoch_number += 1;
        println!("╭─────────────────────────────────────────────────╮");
        println!("│  EPOCH #{:<42} │", epoch_number);
        println!("╰─────────────────────────────────────────────────╯");

        // --- Fetch all data concurrently ---
        let ore_state_future = onchain::fetch_onchain_state(&rpc_client, "ORE");
        let coal_state_future = onchain::fetch_onchain_state(&rpc_client, "COAL");
        let ore_price_future = economics::fetch_token_price(&http_client, "ORE");
        let coal_price_future = economics::fetch_token_price(&http_client, "COAL");
        let sol_price_future = economics::fetch_token_price(&http_client, "SOL");

        let (ore_state_res, coal_state_res, ore_price_res, coal_price_res, sol_price_res) =
            tokio::join!(
                ore_state_future,
                coal_state_future,
                ore_price_future,
                coal_price_future,
                sol_price_future
            );

        // --- Process results and make decision ---
        match (ore_state_res, coal_state_res, ore_price_res, coal_price_res, sol_price_res) {
            (Ok(ore_state), Ok(coal_state), Ok(ore_price), Ok(coal_price), Ok(sol_price)) => {

                // Calculate profitability for both assets
                let ore_report = economics::calculate_profitability(
                    local_hpm,
                    sol_price,
                    DEFAULT_STAKING_MULTIPLIER,
                    &ore_state,
                    ore_price,
                    &energy_config,
                ).await;

                let coal_report = economics::calculate_profitability(
                    local_hpm,
                    sol_price,
                    1.0, // COAL typically doesn't have staking multiplier
                    &coal_state,
                    coal_price,
                    &energy_config,
                ).await;

                // Print detailed reports
                economics::print_report(&ore_report);
                economics::print_report(&coal_report);

                // --- Decision Logic ---
                let (best_target, best_profit, fee_for_miner) = determine_best_target(
                    &ore_report,
                    &coal_report,
                    &ore_state,
                    &coal_state,
                );

                // Print recommendation
                print_recommendation(best_target, best_profit);

                // Execute the decision
                miner_manager.update_target(best_target, fee_for_miner);
            }
            _ => {
                eprintln!("⚠️  Error fetching data. Retrying in {} seconds...", EPOCH_DURATION_SECS);
                eprintln!("   If this persists, check:");
                eprintln!("   - RPC connection");
                eprintln!("   - Internet connectivity");
                eprintln!("   - Jupiter API availability");
            }
        }

        println!("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

        // Wait for next epoch
        tokio::time::sleep(Duration::from_secs(EPOCH_DURATION_SECS)).await;
    }
}

/// Determines which asset to mine based on profitability
fn determine_best_target(
    ore_report: &economics::ProfitabilityReport,
    coal_report: &economics::ProfitabilityReport,
    ore_state: &onchain::OnChainState,
    coal_state: &onchain::OnChainState,
) -> (MiningTarget, f64, u64) {
    let mut best_target = MiningTarget::SLEEP;
    let mut best_profit = 0.0;
    let mut fee_for_miner = 10_000;

    if ore_report.net_profit_usd > 0.0 && ore_report.net_profit_usd >= coal_report.net_profit_usd {
        best_target = MiningTarget::ORE;
        best_profit = ore_report.net_profit_usd;
        fee_for_miner = ore_state.priority_fee;
    } else if coal_report.net_profit_usd > 0.0 {
        best_target = MiningTarget::COAL;
        best_profit = coal_report.net_profit_usd;
        fee_for_miner = coal_state.priority_fee;
    }

    (best_target, best_profit, fee_for_miner)
}

/// Prints the mining recommendation
fn print_recommendation(target: MiningTarget, profit: f64) {
    println!("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓");

    match target {
        MiningTarget::ORE => {
            println!("┃  🎯 RECOMMENDATION: MINE ORE                    ┃");
            println!("┃  ✅ Profit: ${:.6}/min                        ┃", profit);
            println!("┃     (${:.2}/hour, ${:.2}/day)                 ┃",
                profit * 60.0, profit * 60.0 * 24.0);
        }
        MiningTarget::COAL => {
            println!("┃  🎯 RECOMMENDATION: MINE COAL                   ┃");
            println!("┃  ✅ Profit: ${:.6}/min                        ┃", profit);
            println!("┃     (${:.2}/hour, ${:.2}/day)                 ┃",
                profit * 60.0, profit * 60.0 * 24.0);
        }
        MiningTarget::SLEEP => {
            println!("┃  🎯 RECOMMENDATION: SLEEP                       ┃");
            println!("┃  ⛔ No profitable mining opportunities          ┃");
            println!("┃     Waiting for better market conditions...     ┃");
        }
    }

    println!("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛");
}

/// Loads miner configuration
/// TODO: Load from config file instead of using defaults
fn load_miner_config() -> MinerConfig {
    MinerConfig::default()
}

/// Loads energy configuration
/// TODO: Load from config file instead of using defaults
fn load_energy_config() -> EnergyConfig {
    EnergyConfig::default()
}
