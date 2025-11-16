// src/onchain.rs
use solana_client::rpc_client::RpcClient;
use solana_sdk::pubkey::Pubkey;
use std::str::FromStr;

// Program IDs from the research document
const ORE_PROGRAM_ID_STR: &str = "oreoU2P8bN6jkk3jbaiVxYnG1dCXcYxwhwyK9jSybcp";
const COAL_PROGRAM_ID_STR: &str = "E3yUqBNTZxV8ELvW99oRLC7z4ddbJqqR4NphwrMug9zu";

// Known state account addresses (these need to be found/verified)
// These are PDAs (Program Derived Addresses) that can be calculated
// For now, using placeholders - developer needs to find the correct seeds
const ORE_TREASURY_ADDR: &str = "3GgKgJwWzrEAaWkS35MoY7TpLjWFQo3ZjGMAQQEKJw9G";  // Placeholder
const COAL_CONFIG_ADDR: &str = "CoaLmine5pGdKCvppB51RPmxmV3MXpLwL7pFJhqjj4BK";  // Placeholder

#[derive(Debug)]
pub struct OnChainState {
    pub token: String,
    pub global_difficulty: u64,
    pub reward_rate: u64,
    pub priority_fee: u64, // in micro-lamports
}

/// Fetches the current state (difficulty, etc.) for a given mining program.
///
/// NOTE: This is a simplified version that uses mock data for difficulty/rewards.
/// Developer needs to:
/// 1. Find the correct state account addresses (Treasury for ORE, Config for COAL)
/// 2. Define the Borsh deserialization structs matching the on-chain layout
/// 3. Update this function to deserialize the real account data
pub async fn fetch_onchain_state(
    client: &RpcClient,
    token: &str
) -> Result<OnChainState, Box<dyn std::error::Error>> {

    let program_id = if token == "ORE" {
        Pubkey::from_str(ORE_PROGRAM_ID_STR)?
    } else {
        Pubkey::from_str(COAL_PROGRAM_ID_STR)?
    };

    // TODO: Developer needs to uncomment and implement this section
    //
    // Step 1: Get the state account address
    // let state_account_pubkey = if token == "ORE" {
    //     Pubkey::from_str(ORE_TREASURY_ADDR)?
    // } else {
    //     Pubkey::from_str(COAL_CONFIG_ADDR)?
    // };
    //
    // Step 2: Fetch the account data
    // let account_data = client.get_account_data(&state_account_pubkey)?;
    //
    // Step 3: Deserialize using the correct struct
    // let state = if token == "ORE" {
    //     OreTreasuryState::try_from_slice(&account_data)?
    // } else {
    //     CoalConfigState::try_from_slice(&account_data)?
    // };

    // --- Mock Data (DEVELOPER: REPLACE THIS) ---
    let (mock_difficulty, mock_reward_rate) = if token == "ORE" {
        (24_500, 1_000_000_000) // 1 ORE (9 decimals)
    } else {
        (11_200, 5_000_000_000) // 5 COAL (9 decimals)
    };
    println!("⚠️  Using MOCK on-chain data for {} - developer must implement real fetching", token);
    // --- End Mock Data ---

    // Fetch Priority Fees (this part is real)
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

    println!("Fetched state for {}: difficulty={}, reward_rate={}, p90_fee={}",
        token, mock_difficulty, mock_reward_rate, p90_fee);

    Ok(OnChainState {
        token: token.to_string(),
        global_difficulty: mock_difficulty,
        reward_rate: mock_reward_rate,
        priority_fee: p90_fee,
    })
}

// TODO: Developer needs to define these structs based on the actual on-chain layout
//
// Example structure (needs to be verified against ore-cli source):
//
// #[derive(BorshDeserialize, Debug)]
// pub struct OreTreasuryState {
//     pub bump: u8,
//     pub admin: Pubkey,
//     pub difficulty: [u8; 32],
//     pub last_reset_at: i64,
//     pub reward_rate: u64,
//     pub total_claimed_rewards: u64,
//     // ... other fields
// }
//
// #[derive(BorshDeserialize, Debug)]
// pub struct CoalConfigState {
//     pub base_reward_rate: u64,
//     pub last_reset_at: i64,
//     pub min_difficulty: [u8; 32],
//     pub top_balance: u64,
//     // ... other fields
// }
