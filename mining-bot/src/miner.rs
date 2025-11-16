// src/miner.rs
use std::process::{Child, Command};
use serde::Deserialize;

#[derive(Debug, PartialEq, Clone, Copy)]
pub enum MiningTarget {
    ORE,
    COAL,
    SLEEP,
}

impl std::fmt::Display for MiningTarget {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            MiningTarget::ORE => write!(f, "ORE"),
            MiningTarget::COAL => write!(f, "COAL"),
            MiningTarget::SLEEP => write!(f, "SLEEP"),
        }
    }
}

/// Configuration for the mining CLIs
#[derive(Debug, Clone, Deserialize)]
pub struct MinerConfig {
    pub rpc_url: String,
    pub keypair_path: String,
    pub thread_count: usize,
    pub ore_cli_path: String,
    pub coal_cli_path: String,
}

impl Default for MinerConfig {
    fn default() -> Self {
        MinerConfig {
            rpc_url: "https://api.mainnet-beta.solana.com".to_string(),
            keypair_path: "~/.config/solana/id.json".to_string(),
            thread_count: num_cpus::get(),
            ore_cli_path: "ore".to_string(),  // Assumes ore-cli is in PATH
            coal_cli_path: "coal".to_string(), // Assumes coal-cli is in PATH
        }
    }
}

pub struct MinerManager {
    current_process: Option<Child>,
    current_target: MiningTarget,
    config: MinerConfig,
}

impl MinerManager {
    pub fn new(config: MinerConfig) -> Self {
        println!("Initializing MinerManager with config:");
        println!("  RPC: {}", config.rpc_url);
        println!("  Keypair: {}", config.keypair_path);
        println!("  Threads: {}", config.thread_count);

        MinerManager {
            current_process: None,
            current_target: MiningTarget::SLEEP,
            config,
        }
    }

    /// Updates the mining process to match the target.
    /// This will:
    /// 1. Kill the current mining process if target changed
    /// 2. Start a new mining process for the new target
    pub fn update_target(&mut self, new_target: MiningTarget, priority_fee: u64) {
        if self.current_target == new_target {
            // No change needed
            println!("Mining target unchanged: {}", new_target);
            return;
        }

        println!("\n🔄 Switching mining target: {} → {}", self.current_target, new_target);

        // 1. Kill the old process, if any
        if let Some(mut child) = self.current_process.take() {
            println!("  ⏹️  Stopping {} miner (PID: {:?})", self.current_target, child.id());
            if let Err(e) = child.kill() {
                eprintln!("  ⚠️  Error killing process: {}", e);
            } else {
                // Wait for the process to exit
                match child.wait() {
                    Ok(status) => println!("  ✅ Process stopped with status: {}", status),
                    Err(e) => eprintln!("  ⚠️  Error waiting for process: {}", e),
                }
            }
        }

        // 2. Start the new process, if needed
        self.current_target = new_target;

        match new_target {
            MiningTarget::ORE => {
                println!("  ▶️  Starting ORE miner...");
                match self.start_ore_miner(priority_fee) {
                    Ok(child) => {
                        println!("  ✅ ORE miner started (PID: {})", child.id());
                        self.current_process = Some(child);
                    }
                    Err(e) => {
                        eprintln!("  ❌ Failed to start ORE miner: {}", e);
                        eprintln!("     Make sure ore-cli is installed and in PATH");
                        self.current_target = MiningTarget::SLEEP;
                    }
                }
            }
            MiningTarget::COAL => {
                println!("  ▶️  Starting COAL miner...");
                match self.start_coal_miner(priority_fee) {
                    Ok(child) => {
                        println!("  ✅ COAL miner started (PID: {})", child.id());
                        self.current_process = Some(child);
                    }
                    Err(e) => {
                        eprintln!("  ❌ Failed to start COAL miner: {}", e);
                        eprintln!("     Make sure coal-cli is installed and in PATH");
                        self.current_target = MiningTarget::SLEEP;
                    }
                }
            }
            MiningTarget::SLEEP => {
                println!("  💤 Entering SLEEP mode. No miners running.");
            }
        }
    }

    fn start_ore_miner(&self, priority_fee: u64) -> std::io::Result<Child> {
        Command::new(&self.config.ore_cli_path)
            .args([
                "--rpc", &self.config.rpc_url,
                "--keypair", &self.config.keypair_path,
                "--priority-fee", &priority_fee.to_string(),
                "mine",
                "--threads", &self.config.thread_count.to_string(),
            ])
            .spawn()
    }

    fn start_coal_miner(&self, priority_fee: u64) -> std::io::Result<Child> {
        Command::new(&self.config.coal_cli_path)
            .args([
                "--rpc", &self.config.rpc_url,
                "--keypair", &self.config.keypair_path,
                "--priority-fee", &priority_fee.to_string(),
                "mine",
                "--threads", &self.config.thread_count.to_string(),
            ])
            .spawn()
    }

    /// Returns the current mining target
    pub fn current_target(&self) -> MiningTarget {
        self.current_target
    }

    /// Stops all mining and cleans up
    pub fn shutdown(&mut self) {
        println!("Shutting down MinerManager...");
        self.update_target(MiningTarget::SLEEP, 0);
    }
}

impl Drop for MinerManager {
    fn drop(&mut self) {
        // Ensure we clean up any running processes when the manager is dropped
        self.shutdown();
    }
}
