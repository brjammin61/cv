use crate::types::*;
use anyhow::{Context, Result};
use reqwest::Client;
use rust_decimal::Decimal;
use solana_client::nonblocking::rpc_client::RpcClient;
use solana_sdk::{
    commitment_config::CommitmentConfig,
    signature::{Keypair, Signature, Signer},
    transaction::VersionedTransaction,
};
use std::sync::Arc;
use std::time::Instant;
use tracing::{debug, error, info, warn};

const MAX_RETRIES: u32 = 3;
const RETRY_DELAY_MS: u64 = 1000;

/// Executes arbitrage trades
pub struct TradeExecutor {
    rpc_client: Arc<RpcClient>,
    http_client: Client,
    wallet: Arc<Keypair>,
    config: BotConfig,
}

impl TradeExecutor {
    pub fn new(rpc_url: String, wallet: Keypair, config: BotConfig) -> Result<Self> {
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
            config,
        })
    }

    /// Execute a cross-DEX arbitrage opportunity
    ///
    /// This performs TWO trades:
    /// 1. Buy on cheaper DEX
    /// 2. Sell on more expensive DEX
    pub async fn execute_arbitrage(
        &self,
        opportunity: &ArbitrageOpportunity,
    ) -> Result<TradeResult> {
        if self.config.dry_run {
            info!("DRY RUN: Would execute arbitrage");
            return Ok(self.simulate_trade(opportunity));
        }

        let start_time = Instant::now();

        info!(
            "Executing arbitrage: Buy on {}, Sell on {}",
            opportunity.buy_dex, opportunity.sell_dex
        );

        // Step 1: Buy on cheaper DEX
        let buy_result = self.execute_swap(
            &opportunity.buy_quote,
            "BUY",
        ).await?;

        if !buy_result.success {
            error!("Buy trade failed: {:?}", buy_result.error);
            return Ok(buy_result);
        }

        info!("Buy successful: {}", buy_result.signature.as_ref().unwrap());

        // Step 2: Sell on more expensive DEX
        let sell_result = self.execute_swap(
            &opportunity.sell_quote,
            "SELL",
        ).await?;

        if !sell_result.success {
            error!("Sell trade failed: {:?}", sell_result.error);
            // TODO: Handle partial execution (bought but couldn't sell)
            return Ok(sell_result);
        }

        info!("Sell successful: {}", sell_result.signature.as_ref().unwrap());

        // Calculate realized profit
        let input_lamports = buy_result.input_amount;
        let output_lamports = sell_result.output_amount;

        let realized_profit = if output_lamports > input_lamports {
            Some(
                Decimal::from(output_lamports - input_lamports)
                    / Decimal::from(1_000_000_000),
            )
        } else {
            Some(Decimal::ZERO)
        };

        let execution_time = start_time.elapsed().as_millis() as u64;

        Ok(TradeResult {
            success: true,
            signature: sell_result.signature,
            input_amount: input_lamports,
            output_amount: output_lamports,
            realized_profit,
            execution_time_ms: execution_time,
            error: None,
            timestamp: chrono::Utc::now().timestamp_millis(),
        })
    }

    /// Execute a single swap via Jupiter
    async fn execute_swap(
        &self,
        quote: &PriceQuote,
        label: &str,
    ) -> Result<TradeResult> {
        info!("{}: Executing swap on {}", label, quote.dex);

        match quote.dex {
            Dex::Jupiter => self.execute_jupiter_swap(quote).await,
            Dex::Raydium => {
                // TODO: Implement direct Raydium swap
                warn!("Raydium direct swap not implemented, using Jupiter");
                self.execute_jupiter_swap(quote).await
            }
            Dex::Orca => {
                // TODO: Implement direct Orca swap
                warn!("Orca direct swap not implemented, using Jupiter");
                self.execute_jupiter_swap(quote).await
            }
        }
    }

    /// Execute swap via Jupiter V6 API
    async fn execute_jupiter_swap(&self, quote: &PriceQuote) -> Result<TradeResult> {
        // Build swap transaction via Jupiter API
        let swap_tx = self.get_jupiter_swap_transaction(quote).await?;

        // Sign and send with retries
        for attempt in 1..=MAX_RETRIES {
            match self.send_and_confirm_transaction(swap_tx.clone()).await {
                Ok(signature) => {
                    info!("Swap confirmed: {}", signature);

                    return Ok(TradeResult {
                        success: true,
                        signature: Some(signature.to_string()),
                        input_amount: quote.input_amount,
                        output_amount: quote.output_amount,
                        realized_profit: None, // Calculated at arbitrage level
                        execution_time_ms: 0,  // Calculated at arbitrage level
                        error: None,
                        timestamp: chrono::Utc::now().timestamp_millis(),
                    });
                }
                Err(e) => {
                    error!("Swap attempt {} failed: {}", attempt, e);

                    if attempt < MAX_RETRIES {
                        tokio::time::sleep(tokio::time::Duration::from_millis(
                            RETRY_DELAY_MS * attempt as u64,
                        ))
                        .await;
                    } else {
                        return Ok(TradeResult {
                            success: false,
                            signature: None,
                            input_amount: quote.input_amount,
                            output_amount: 0,
                            realized_profit: None,
                            execution_time_ms: 0,
                            error: Some(e.to_string()),
                            timestamp: chrono::Utc::now().timestamp_millis(),
                        });
                    }
                }
            }
        }

        unreachable!()
    }

    /// Get swap transaction from Jupiter API
    async fn get_jupiter_swap_transaction(
        &self,
        quote: &PriceQuote,
    ) -> Result<VersionedTransaction> {
        #[derive(serde::Serialize)]
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
            prioritization_fee_lamports: u64,
        }

        #[derive(serde::Deserialize)]
        struct SwapResponse {
            #[serde(rename = "swapTransaction")]
            swap_transaction: String,
        }

        let url = "https://quote-api.jup.ag/v6/swap";

        let request = SwapRequest {
            quote_response: quote.quote_data.clone(),
            user_public_key: self.wallet.pubkey().to_string(),
            wrap_and_unwrap_sol: true,
            dynamic_compute_unit_limit: true,
            prioritization_fee_lamports: self.config.priority_fee_microlamports,
        };

        let response = self
            .http_client
            .post(url)
            .json(&request)
            .send()
            .await
            .context("Failed to get swap transaction")?;

        if !response.status().is_success() {
            let error = response.text().await?;
            anyhow::bail!("Jupiter swap API error: {}", error);
        }

        let swap_response: SwapResponse = response.json().await?;

        // Decode the transaction (it's base64 encoded)
        let tx_bytes = base64_decode(&swap_response.swap_transaction)?;

        let mut tx: VersionedTransaction =
            bincode::deserialize(&tx_bytes).context("Failed to deserialize transaction")?;

        // Sign the transaction
        let recent_blockhash = self.rpc_client.get_latest_blockhash().await?;
        tx.message.set_recent_blockhash(recent_blockhash);

        // Sign with our wallet
        let signature = self.wallet.sign_message(tx.message.serialize().as_slice());
        tx.signatures = vec![signature];

        Ok(tx)
    }

    /// Send and confirm a transaction
    async fn send_and_confirm_transaction(
        &self,
        tx: VersionedTransaction,
    ) -> Result<Signature> {
        // Send transaction
        let signature = self
            .rpc_client
            .send_transaction(&tx)
            .await
            .context("Failed to send transaction")?;

        debug!("Transaction sent: {}", signature);

        // Wait for confirmation with timeout
        let timeout = std::time::Duration::from_secs(self.config.tx_timeout_seconds);
        let start = Instant::now();

        while start.elapsed() < timeout {
            match self.rpc_client.get_signature_status(&signature).await? {
                Some(result) => {
                    if let Err(e) = result {
                        anyhow::bail!("Transaction failed: {:?}", e);
                    }
                    return Ok(signature);
                }
                None => {
                    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
                }
            }
        }

        anyhow::bail!("Transaction confirmation timeout")
    }

    /// Simulate a trade (for dry run mode)
    fn simulate_trade(&self, opportunity: &ArbitrageOpportunity) -> TradeResult {
        info!(
            "SIMULATION: Arbitrage would profit {} SOL ({:.2}%)",
            opportunity.net_profit, opportunity.profit_percent
        );

        TradeResult {
            success: true,
            signature: Some("SIMULATED".to_string()),
            input_amount: opportunity.buy_quote.input_amount,
            output_amount: opportunity.sell_quote.output_amount,
            realized_profit: Some(opportunity.net_profit),
            execution_time_ms: 0,
            error: None,
            timestamp: chrono::Utc::now().timestamp_millis(),
        }
    }
}

/// Base64 decode helper
fn base64_decode(s: &str) -> Result<Vec<u8>> {
    // Jupiter returns base64, not base58
    use base64::{engine::general_purpose, Engine as _};
    general_purpose::STANDARD
        .decode(s)
        .context("Failed to decode base64")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dry_run_simulation() {
        let config = BotConfig {
            dry_run: true,
            ..Default::default()
        };

        let wallet = Keypair::new();
        let executor = TradeExecutor::new(
            "https://api.mainnet-beta.solana.com".to_string(),
            wallet,
            config,
        )
        .unwrap();

        // Create a mock opportunity
        let opportunity = ArbitrageOpportunity {
            id: "test".to_string(),
            buy_dex: Dex::Jupiter,
            sell_dex: Dex::Raydium,
            pair: TokenPair {
                base: solana_sdk::pubkey::Pubkey::new_unique(),
                quote: solana_sdk::pubkey::Pubkey::new_unique(),
            },
            buy_quote: PriceQuote {
                dex: Dex::Jupiter,
                pair: TokenPair {
                    base: solana_sdk::pubkey::Pubkey::new_unique(),
                    quote: solana_sdk::pubkey::Pubkey::new_unique(),
                },
                input_amount: 1_000_000_000,
                output_amount: 100_000_000,
                price: Decimal::from(1),
                timestamp: 0,
                route: vec![],
                quote_data: serde_json::json!({}),
            },
            sell_quote: PriceQuote {
                dex: Dex::Raydium,
                pair: TokenPair {
                    base: solana_sdk::pubkey::Pubkey::new_unique(),
                    quote: solana_sdk::pubkey::Pubkey::new_unique(),
                },
                input_amount: 100_000_000,
                output_amount: 1_100_000_000,
                price: Decimal::from(1),
                timestamp: 0,
                route: vec![],
                quote_data: serde_json::json!({}),
            },
            gross_profit: Decimal::from(1),
            net_profit: Decimal::from(1),
            profit_percent: Decimal::from(10),
            execution_cost: ExecutionCost::new(
                Decimal::ZERO,
                Decimal::ZERO,
                Decimal::ZERO,
            ),
            timestamp: 0,
        };

        let result = executor.simulate_trade(&opportunity);
        assert!(result.success);
    }
}
