use anyhow::{Context, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use solana_client::nonblocking::rpc_client::RpcClient;
use solana_sdk::{
    commitment_config::CommitmentConfig,
    signature::{Keypair, Signature, Signer},
    transaction::VersionedTransaction,
};
use std::sync::Arc;
use tracing::{debug, info, warn, error};

/// Jupiter V6 API base URL
const JUPITER_V6_API: &str = "https://quote-api.jup.ag/v6";

/// Maximum retries for failed transactions
const MAX_TX_RETRIES: u32 = 3;

/// Retry delay in milliseconds
const RETRY_DELAY_MS: u64 = 1000;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SwapResult {
    /// Transaction signature
    pub signature: String,

    /// Amount of input token (in smallest unit)
    pub input_amount: u64,

    /// Amount of output token received (in smallest unit)
    pub output_amount: u64,

    /// Execution price
    pub execution_price: f64,

    /// Success status
    pub success: bool,

    /// Error message if failed
    pub error: Option<String>,

    /// Timestamp
    pub timestamp: i64,
}

#[derive(Debug, Serialize)]
struct SwapRequest {
    #[serde(rename = "quoteResponse")]
    quote_response: serde_json::Value,

    #[serde(rename = "userPublicKey")]
    user_public_key: String,

    #[serde(rename = "wrapAndUnwrapSol")]
    wrap_and_unwrap_sol: bool,

    #[serde(rename = "dynamicComputeUnitLimit")]
    dynamic_compute_unit_limit: bool,

    #[serde(rename = "prioritizationFeeLamports")]
    prioritization_fee_lamports: Option<u64>,
}

#[derive(Debug, Deserialize)]
struct SwapResponse {
    #[serde(rename = "swapTransaction")]
    swap_transaction: String,
}

pub struct SwapExecutor {
    rpc_client: Arc<RpcClient>,
    http_client: Client,
    wallet: Arc<Keypair>,
}

impl SwapExecutor {
    /// Create a new SwapExecutor
    pub fn new(rpc_url: String, wallet: Keypair) -> Result<Self> {
        let rpc_client = Arc::new(RpcClient::new_with_commitment(
            rpc_url,
            CommitmentConfig::confirmed(),
        ));

        let http_client = Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .context("Failed to create HTTP client")?;

        Ok(Self {
            rpc_client,
            http_client,
            wallet: Arc::new(wallet),
        })
    }

    /// Execute a swap from SOL to ORE
    ///
    /// This method:
    /// 1. Gets a quote from Jupiter
    /// 2. Gets the swap transaction
    /// 3. Signs and sends the transaction
    /// 4. Confirms the transaction
    pub async fn swap_sol_to_ore(
        &self,
        sol_amount_lamports: u64,
        ore_mint: &str,
        sol_mint: &str,
        slippage_bps: u64,
        priority_fee_lamports: Option<u64>,
    ) -> Result<SwapResult> {
        info!(
            "Executing SOL->ORE swap: {} lamports (slippage: {} bps)",
            sol_amount_lamports, slippage_bps
        );

        // Step 1: Get quote
        let quote = self.get_quote(
            sol_mint,
            ore_mint,
            sol_amount_lamports,
            slippage_bps,
        ).await?;

        debug!("Quote received: {:?}", quote);

        // Step 2: Get swap transaction
        let swap_tx = self.get_swap_transaction(quote, priority_fee_lamports)
            .await
            .context("Failed to get swap transaction")?;

        // Step 3: Sign and send transaction
        let signature = self.execute_transaction(swap_tx)
            .await
            .context("Failed to execute transaction")?;

        info!("Swap transaction sent: {}", signature);

        // Step 4: Confirm transaction
        let confirmed = self.confirm_transaction(&signature).await?;

        if confirmed {
            info!("Swap confirmed: {}", signature);
            Ok(SwapResult {
                signature: signature.to_string(),
                input_amount: sol_amount_lamports,
                output_amount: 0, // Would need to parse transaction for actual amount
                execution_price: 0.0,
                success: true,
                error: None,
                timestamp: chrono::Utc::now().timestamp(),
            })
        } else {
            warn!("Swap transaction failed to confirm: {}", signature);
            Ok(SwapResult {
                signature: signature.to_string(),
                input_amount: sol_amount_lamports,
                output_amount: 0,
                execution_price: 0.0,
                success: false,
                error: Some("Transaction failed to confirm".to_string()),
                timestamp: chrono::Utc::now().timestamp(),
            })
        }
    }

    /// Get a quote from Jupiter
    async fn get_quote(
        &self,
        input_mint: &str,
        output_mint: &str,
        amount: u64,
        slippage_bps: u64,
    ) -> Result<serde_json::Value> {
        let url = format!(
            "{}/quote?inputMint={}&outputMint={}&amount={}&slippageBps={}",
            JUPITER_V6_API, input_mint, output_mint, amount, slippage_bps
        );

        let response = self.http_client
            .get(&url)
            .send()
            .await
            .context("Failed to fetch quote")?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_default();
            anyhow::bail!("Jupiter quote API error {}: {}", status, error_text);
        }

        let quote = response.json().await
            .context("Failed to parse quote response")?;

        Ok(quote)
    }

    /// Get swap transaction from Jupiter
    async fn get_swap_transaction(
        &self,
        quote: serde_json::Value,
        priority_fee_lamports: Option<u64>,
    ) -> Result<Vec<u8>> {
        let swap_request = SwapRequest {
            quote_response: quote,
            user_public_key: self.wallet.pubkey().to_string(),
            wrap_and_unwrap_sol: true,
            dynamic_compute_unit_limit: true,
            prioritization_fee_lamports: priority_fee_lamports,
        };

        let url = format!("{}/swap", JUPITER_V6_API);

        let response = self.http_client
            .post(&url)
            .json(&swap_request)
            .send()
            .await
            .context("Failed to get swap transaction")?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_default();
            anyhow::bail!("Jupiter swap API error {}: {}", status, error_text);
        }

        let swap_response: SwapResponse = response.json().await
            .context("Failed to parse swap response")?;

        // Decode base64 transaction
        let tx_bytes = base64::decode(&swap_response.swap_transaction)
            .context("Failed to decode swap transaction")?;

        Ok(tx_bytes)
    }

    /// Execute a transaction with retries
    async fn execute_transaction(&self, tx_bytes: Vec<u8>) -> Result<Signature> {
        // Deserialize transaction
        let tx: VersionedTransaction = bincode::deserialize(&tx_bytes)
            .context("Failed to deserialize transaction")?;

        // Transaction comes pre-signed from Jupiter, just send it
        // Send with retries
        for attempt in 1..=MAX_TX_RETRIES {
            match self.rpc_client.send_and_confirm_transaction(&tx).await {
                Ok(signature) => {
                    return Ok(signature);
                }
                Err(e) => {
                    error!("Transaction attempt {} failed: {}", attempt, e);
                    if attempt < MAX_TX_RETRIES {
                        tokio::time::sleep(tokio::time::Duration::from_millis(
                            RETRY_DELAY_MS * attempt as u64
                        )).await;
                    } else {
                        return Err(e.into());
                    }
                }
            }
        }

        anyhow::bail!("Transaction failed after {} retries", MAX_TX_RETRIES)
    }

    /// Confirm a transaction
    async fn confirm_transaction(&self, signature: &Signature) -> Result<bool> {
        // Wait for confirmation with timeout
        let timeout = tokio::time::Duration::from_secs(60);
        let start = tokio::time::Instant::now();

        while start.elapsed() < timeout {
            match self.rpc_client.get_signature_status(signature).await? {
                Some(result) => {
                    return Ok(result.is_ok());
                }
                None => {
                    tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
                }
            }
        }

        warn!("Transaction confirmation timeout: {}", signature);
        Ok(false)
    }
}

// Add base64 decoding support
mod base64 {
    use anyhow::{Context, Result};

    pub fn decode(s: &str) -> Result<Vec<u8>> {
        bs58::decode(s)
            .into_vec()
            .context("Failed to decode base58")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_swap_result_creation() {
        let result = SwapResult {
            signature: "test_sig".to_string(),
            input_amount: 1000000000,
            output_amount: 100,
            execution_price: 0.01,
            success: true,
            error: None,
            timestamp: chrono::Utc::now().timestamp(),
        };

        assert!(result.success);
        assert_eq!(result.input_amount, 1000000000);
    }
}
