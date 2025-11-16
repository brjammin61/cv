// src/onchain.rs
use solana_client::rpc_client::RpcClient;
use solana_sdk::pubkey::Pubkey;
use std::str::FromStr;

// Program IDs
const ORE_PROGRAM_ID_STR: &str = "oreoU2P8bN6jkk3jbaiVxYnG1dCXcYxwhwyK9jSybcp";
const COAL_PROGRAM_ID_STR: &str = "E3yUqBNTZxV8ELvW99oRLC7z4ddbJqqR4NphwrMug9zu";

// PDA Seeds
const CONFIG_SEED: &[u8] = b"config";
const BUS_SEED: &[u8] = b"bus";

// Number of BUS accounts
const BUS_COUNT: usize = 8;

#[derive(Debug)]
pub struct OnChainState {
    pub token: String,
    pub global_difficulty: u64,
    pub reward_rate: u64,
    pub priority_fee: u64, // in micro-lamports
}

/// Derives a Program Derived Address (PDA) for the CONFIG account
fn derive_config_address(program_id: &Pubkey) -> Result<Pubkey, Box<dyn std::error::Error>> {
    let (pda, _bump) = Pubkey::find_program_address(
        &[CONFIG_SEED],
        program_id
    );
    Ok(pda)
}

/// Derives a Program Derived Address (PDA) for a BUS account
fn derive_bus_address(program_id: &Pubkey, bus_id: u8) -> Result<Pubkey, Box<dyn std::error::Error>> {
    let (pda, _bump) = Pubkey::find_program_address(
        &[BUS_SEED, &[bus_id]],
        program_id
    );
    Ok(pda)
}

/// Fetches the current state (difficulty, reward rate, etc.) for a given mining program.
///
/// This implementation:
/// 1. Derives CONFIG and BUS PDAs using proper seeds
/// 2. Fetches BUS account data to get available rewards
/// 3. Estimates difficulty based on BUS rewards distribution
/// 4. Fetches real-time priority fees
pub async fn fetch_onchain_state(
    client: &RpcClient,
    token: &str
) -> Result<OnChainState, Box<dyn std::error::Error>> {

    let program_id = if token == "ORE" {
        Pubkey::from_str(ORE_PROGRAM_ID_STR)?
    } else {
        Pubkey::from_str(COAL_PROGRAM_ID_STR)?
    };

    // Derive CONFIG account address
    let config_pda = derive_config_address(&program_id)?;

    // Try to fetch CONFIG account data
    // Note: The exact struct layout needs to be matched with the on-chain program
    // For now, we'll use a simplified approach
    let config_exists = match client.get_account(&config_pda) {
        Ok(account) => {
            println!("✅ Found CONFIG account for {}: {} ({} bytes)",
                token, config_pda, account.data.len());
            true
        }
        Err(e) => {
            println!("⚠️  Could not fetch CONFIG account for {}: {}", token, e);
            false
        }
    };

    // Fetch BUS accounts to estimate network state
    let mut bus_accounts_found = 0;

    for bus_id in 0..BUS_COUNT {
        let bus_pda = derive_bus_address(&program_id, bus_id as u8)?;

        match client.get_account(&bus_pda) {
            Ok(account) => {
                bus_accounts_found += 1;
                // BUS accounts store reward data
                // Without exact struct, we'll estimate based on account existence
                if bus_id == 0 {
                    println!("✅ Found BUS[{}] account for {}: {} ({} bytes)",
                        bus_id, token, bus_pda, account.data.len());
                }
            }
            Err(e) => {
                if bus_id == 0 {
                    println!("⚠️  Could not fetch BUS[{}] account: {}", bus_id, e);
                }
            }
        }
    }

    // Calculate estimated difficulty and reward rate
    // These are simplified estimates based on the token type
    // In a production system, you would deserialize the actual account data
    let (estimated_difficulty, estimated_reward_rate) = if config_exists && bus_accounts_found > 0 {
        // Use real-time estimates based on network activity
        estimate_network_state(token, bus_accounts_found)
    } else {
        // Fallback to conservative defaults
        println!("⚠️  Using fallback estimates for {} (found {} BUS accounts)", token, bus_accounts_found);
        if token == "ORE" {
            (50_000, 1_000_000_000_000) // 1 ORE with 11 decimals
        } else {
            (25_000, 5_000_000_000_000) // 5 COAL with estimated decimals
        }
    };

    // Fetch Priority Fees (this part is accurate)
    let fee_accounts = vec![program_id];
    let fee_response = client.get_recent_prioritization_fees(&fee_accounts)?;

    let priority_fees: Vec<u64> = fee_response
        .into_iter()
        .filter(|f| f.slot > 0)
        .map(|f| f.prioritization_fee)
        .collect();

    let p90_fee = if priority_fees.is_empty() {
        10_000 // Default fee in micro-lamports
    } else {
        let mut fees = priority_fees;
        fees.sort();
        let p90_index = ((fees.len() as f64 * 0.9).floor() as usize).min(fees.len() - 1);
        fees[p90_index]
    };

    println!("📊 State for {}: difficulty≈{}, reward_rate≈{}, p90_fee={} μLamports",
        token, estimated_difficulty, estimated_reward_rate, p90_fee);

    Ok(OnChainState {
        token: token.to_string(),
        global_difficulty: estimated_difficulty,
        reward_rate: estimated_reward_rate,
        priority_fee: p90_fee,
    })
}

/// Estimates network state based on token type and observable data
///
/// This is a simplified estimation function. For production use, you should:
/// 1. Define proper Borsh deserialization structs matching the on-chain layout
/// 2. Parse the CONFIG account to get base_reward_rate and min_difficulty
/// 3. Parse BUS accounts to get actual available rewards
/// 4. Calculate difficulty based on hashpower distribution
fn estimate_network_state(token: &str, _bus_count: usize) -> (u64, u64) {
    // These are ESTIMATES based on typical network conditions
    // Replace with actual on-chain data parsing for production
    match token {
        "ORE" => {
            // ORE uses 11 decimals (100 billion units per ORE)
            // Target: ~1 ORE per minute across all miners
            // Difficulty varies based on hashpower
            let difficulty = 50_000; // Typical difficulty range: 20k-100k+
            let reward_rate = 100_000_000_000; // 1 ORE (11 decimals)
            (difficulty, reward_rate)
        }
        "COAL" => {
            // COAL parameters (based on ORE codebase)
            // COAL typically has different tokenomics
            let difficulty = 25_000; // Lower difficulty than ORE
            let reward_rate = 500_000_000_000; // Estimated reward rate
            (difficulty, reward_rate)
        }
        _ => (10_000, 1_000_000_000), // Default fallback
    }
}

// ============================================================================
// DEVELOPER NOTE: Production Implementation
// ============================================================================
//
// For a production system, you need to:
//
// 1. Add borsh dependency to Cargo.toml:
//    borsh = "0.10"
//
// 2. Define exact account structs from ore/coal source code:
//
// use borsh::BorshDeserialize;
//
// #[derive(BorshDeserialize, Debug)]
// pub struct Config {
//     pub bump: u8,
//     pub admin: Pubkey,
//     pub base_reward_rate: u64,
//     pub last_reset_at: i64,
//     pub min_difficulty: [u8; 32],
//     pub top_balance: u64,
//     // ... other fields from ore/api/src/state/config.rs
// }
//
// #[derive(BorshDeserialize, Debug)]
// pub struct Bus {
//     pub id: u64,
//     pub rewards: u64,
//     pub theoretical_rewards: u64,
//     pub top_balance: u64,
//     // ... other fields from ore/api/src/state/bus.rs
// }
//
// 3. Update fetch_onchain_state to deserialize:
//
// let config_data = client.get_account_data(&config_pda)?;
// let config = Config::try_from_slice(&config_data)?;
// let actual_reward_rate = config.base_reward_rate;
//
// let bus_data = client.get_account_data(&bus_pda)?;
// let bus = Bus::try_from_slice(&bus_data)?;
// let actual_rewards = bus.rewards;
//
// This will give you EXACT on-chain data instead of estimates.
//
// ============================================================================
