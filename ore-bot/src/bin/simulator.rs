use anyhow::Result;
use ore_bot::{analytics, simulator};

fn main() -> Result<()> {
    println!("\n");
    println!("╔═══════════════════════════════════════════════════════════════╗");
    println!("║         ORE ARBITRAGE BOT - STRATEGY OPTIMIZER              ║");
    println!("║                                                               ║");
    println!("║  This tool simulates trading strategies to find the optimal  ║");
    println!("║  profit threshold for maximum returns.                       ║");
    println!("╚═══════════════════════════════════════════════════════════════╝");
    println!("\n");

    let args: Vec<String> = std::env::args().collect();

    if args.len() > 1 && args[1] == "live" {
        // Live simulation mode
        let duration_minutes = args.get(2)
            .and_then(|s| s.parse().ok())
            .unwrap_or(60); // Default 60 minutes

        let poll_interval = args.get(3)
            .and_then(|s| s.parse().ok())
            .unwrap_or(30); // Default 30 seconds

        let threshold = args.get(4)
            .and_then(|s| s.parse().ok())
            .unwrap_or(5.0); // Default 5%

        simulator::run_simulation(duration_minutes, poll_interval, threshold)?;
    } else {
        // Backtest mode (default)
        let num_datapoints = args.get(1)
            .and_then(|s| s.parse().ok())
            .unwrap_or(1000); // Default 1000 cycles

        simulator::run_backtest(num_datapoints)?;
    }

    Ok(())
}
