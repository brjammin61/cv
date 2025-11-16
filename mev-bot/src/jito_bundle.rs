use anyhow::{Context, Result};
use reqwest::Client;
use rust_decimal::Decimal;
use rust_decimal::prelude::ToPrimitive;
use solana_sdk::{
    signature::{Keypair, Signer},
    transaction::VersionedTransaction,
};
use std::sync::Arc;
use tracing::{debug, info, warn};

/// Jito Bundle Manager for MEV transactions
///
/// Jito allows submitting bundles of transactions that execute atomically
/// This is critical for MEV because:
/// 1. Guarantees transaction ordering
/// 2. Prevents front-running of our own MEV trades
/// 3. Allows atomic multi-step operations
/// 4. Provides MEV profit sharing with validators
pub struct JitoBundleManager {
    http_client: Client,
    jito_api_url: String,
    wallet: Arc<Keypair>,
    tip_account: String,
}

#[derive(Debug, Clone)]
pub struct Bundle {
    pub transactions: Vec<VersionedTransaction>,
    pub tip_lamports: u64,
}

#[derive(serde::Deserialize, Debug)]
struct BundleResponse {
    jsonrpc: String,
    id: u64,
    result: Option<BundleResult>,
    error: Option<serde_json::Value>,
}

#[derive(serde::Deserialize, Debug)]
struct BundleResult {
    bundle_id: String,
}

impl JitoBundleManager {
    pub fn new(wallet: Keypair) -> Self {
        // Jito Block Engine endpoints
        let jito_api_url = "https://mainnet.block-engine.jito.wtf/api/v1".to_string();

        // Jito tip accounts (rotate between them)
        let tip_account = "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5".to_string();

        Self {
            http_client: Client::builder()
                .timeout(std::time::Duration::from_secs(10))
                .build()
                .expect("Failed to create HTTP client"),
            jito_api_url,
            wallet: Arc::new(wallet),
            tip_account,
        }
    }

    /// Submit a bundle of transactions to Jito
    ///
    /// Transactions in a bundle are executed atomically in order
    /// If any transaction fails, the entire bundle fails
    pub async fn submit_bundle(&self, bundle: &Bundle) -> Result<String> {
        info!(
            "📦 Submitting Jito bundle with {} transactions, tip: {} lamports",
            bundle.transactions.len(),
            bundle.tip_lamports
        );

        // Serialize transactions to base58
        let mut serialized_txs = Vec::new();
        for tx in &bundle.transactions {
            let tx_bytes = bincode::serialize(tx)?;
            let tx_base58 = bs58::encode(&tx_bytes).into_string();
            serialized_txs.push(tx_base58);
        }

        // Build bundle request
        #[derive(serde::Serialize)]
        struct BundleRequest {
            jsonrpc: String,
            id: u64,
            method: String,
            params: Vec<serde_json::Value>,
        }

        let request = BundleRequest {
            jsonrpc: "2.0".to_string(),
            id: 1,
            method: "sendBundle".to_string(),
            params: vec![serde_json::json!(serialized_txs)],
        };

        // Submit to Jito
        let response = self
            .http_client
            .post(&format!("{}/bundles", self.jito_api_url))
            .json(&request)
            .send()
            .await
            .context("Failed to submit bundle to Jito")?;

        if !response.status().is_success() {
            let error = response.text().await?;
            anyhow::bail!("Jito bundle submission failed: {}", error);
        }

        let bundle_response: BundleResponse = response.json().await?;

        if let Some(error) = bundle_response.error {
            anyhow::bail!("Jito API error: {}", error);
        }

        let bundle_id = bundle_response
            .result
            .context("Missing bundle result")?
            .bundle_id;

        info!("✅ Bundle submitted successfully: {}", bundle_id);
        Ok(bundle_id)
    }

    /// Create a tip transaction to incentivize validators
    ///
    /// Higher tips = higher chance of bundle inclusion
    pub async fn create_tip_transaction(
        &self,
        tip_lamports: u64,
        recent_blockhash: solana_sdk::hash::Hash,
    ) -> Result<VersionedTransaction> {
        use solana_sdk::{
            message::{v0, VersionedMessage},
            pubkey::Pubkey,
            system_instruction,
        };
        use std::str::FromStr;

        let tip_account = Pubkey::from_str(&self.tip_account)?;

        // Create transfer instruction
        let instruction = system_instruction::transfer(
            &self.wallet.pubkey(),
            &tip_account,
            tip_lamports,
        );

        // Build v0 message
        let message = v0::Message::try_compile(
            &self.wallet.pubkey(),
            &[instruction],
            &[],
            recent_blockhash,
        )?;

        let versioned_message = VersionedMessage::V0(message);

        // Sign transaction
        let signature = self.wallet.sign_message(versioned_message.serialize().as_slice());

        let tx = VersionedTransaction {
            signatures: vec![signature],
            message: versioned_message,
        };

        Ok(tx)
    }

    /// Create a bundle for atomic arbitrage execution
    ///
    /// Bundle structure:
    /// 1. Tip transaction (to incentivize validator)
    /// 2. Buy transaction (on cheaper DEX)
    /// 3. Sell transaction (on expensive DEX)
    pub async fn create_arbitrage_bundle(
        &self,
        buy_tx: VersionedTransaction,
        sell_tx: VersionedTransaction,
        tip_lamports: u64,
        recent_blockhash: solana_sdk::hash::Hash,
    ) -> Result<Bundle> {
        let tip_tx = self.create_tip_transaction(tip_lamports, recent_blockhash).await?;

        Ok(Bundle {
            transactions: vec![tip_tx, buy_tx, sell_tx],
            tip_lamports,
        })
    }

    /// Calculate optimal tip amount based on expected profit
    ///
    /// Strategy: Pay 5-10% of expected profit as tip
    pub fn calculate_optimal_tip(&self, expected_profit_sol: Decimal) -> u64 {
        let profit_lamports = (expected_profit_sol * Decimal::from(1_000_000_000))
            .to_u64()
            .unwrap_or(0);

        // Pay 7.5% of profit as tip
        let tip = (profit_lamports * 75) / 1000;

        // Minimum tip: 10,000 lamports (0.00001 SOL)
        // Maximum tip: 10,000,000 lamports (0.01 SOL)
        tip.max(10_000).min(10_000_000)
    }

    /// Get bundle status
    pub async fn get_bundle_status(&self, bundle_id: &str) -> Result<String> {
        #[derive(serde::Serialize)]
        struct StatusRequest {
            jsonrpc: String,
            id: u64,
            method: String,
            params: Vec<String>,
        }

        let request = StatusRequest {
            jsonrpc: "2.0".to_string(),
            id: 1,
            method: "getBundleStatuses".to_string(),
            params: vec![bundle_id.to_string()],
        };

        let response = self
            .http_client
            .post(&format!("{}/bundles", self.jito_api_url))
            .json(&request)
            .send()
            .await?;

        let status: serde_json::Value = response.json().await?;
        debug!("Bundle status: {:?}", status);

        Ok(format!("{:?}", status))
    }

    /// Wait for bundle confirmation
    pub async fn wait_for_bundle_confirmation(
        &self,
        bundle_id: &str,
        timeout_seconds: u64,
    ) -> Result<bool> {
        let start = std::time::Instant::now();
        let timeout = std::time::Duration::from_secs(timeout_seconds);

        while start.elapsed() < timeout {
            let status = self.get_bundle_status(bundle_id).await?;

            // Check if bundle was included
            if status.contains("\"confirmation_status\":\"confirmed\"")
                || status.contains("\"confirmation_status\":\"finalized\"")
            {
                info!("✅ Bundle confirmed: {}", bundle_id);
                return Ok(true);
            }

            // Check if bundle failed
            if status.contains("\"confirmation_status\":\"failed\"") {
                warn!("❌ Bundle failed: {}", bundle_id);
                return Ok(false);
            }

            // Wait before checking again
            tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
        }

        warn!("⏱️  Bundle confirmation timeout: {}", bundle_id);
        Ok(false)
    }

    /// Get Jito tip accounts (rotate for better distribution)
    pub fn get_tip_accounts() -> Vec<String> {
        vec![
            "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5".to_string(),
            "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe".to_string(),
            "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY".to_string(),
            "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49".to_string(),
            "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh".to_string(),
            "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt".to_string(),
            "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL".to_string(),
            "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT".to_string(),
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_optimal_tip_calculation() {
        let wallet = Keypair::new();
        let manager = JitoBundleManager::new(wallet);

        // 1 SOL profit should give ~0.075 SOL tip (75,000,000 lamports)
        let tip = manager.calculate_optimal_tip(Decimal::from(1));
        assert!(tip > 70_000_000);
        assert!(tip < 80_000_000);

        // Very small profit should give minimum tip
        let small_tip = manager.calculate_optimal_tip(Decimal::from_str("0.0001").unwrap());
        assert_eq!(small_tip, 10_000);

        // Very large profit should cap at maximum tip
        let large_tip = manager.calculate_optimal_tip(Decimal::from(100));
        assert_eq!(large_tip, 10_000_000);
    }

    #[test]
    fn test_tip_accounts() {
        let accounts = JitoBundleManager::get_tip_accounts();
        assert_eq!(accounts.len(), 8);
        assert!(accounts[0].starts_with("96gYZGLn"));
    }

    #[tokio::test]
    async fn test_bundle_creation() {
        let wallet = Keypair::new();
        let manager = JitoBundleManager::new(wallet);

        // Create mock transactions (in production these would be real swap txs)
        use solana_sdk::{
            hash::Hash,
            message::{v0, VersionedMessage},
            system_instruction,
        };

        let recent_blockhash = Hash::new_unique();

        let instruction = system_instruction::transfer(
            &manager.wallet.pubkey(),
            &solana_sdk::pubkey::Pubkey::new_unique(),
            1000,
        );

        let message = v0::Message::try_compile(
            &manager.wallet.pubkey(),
            &[instruction],
            &[],
            recent_blockhash,
        )
        .unwrap();

        let versioned_message = VersionedMessage::V0(message);
        let signature = manager.wallet.sign_message(versioned_message.serialize().as_slice());

        let mock_tx = VersionedTransaction {
            signatures: vec![signature],
            message: versioned_message.clone(),
        };

        let bundle = manager
            .create_arbitrage_bundle(mock_tx.clone(), mock_tx, 100_000, recent_blockhash)
            .await
            .unwrap();

        assert_eq!(bundle.transactions.len(), 3); // tip + buy + sell
        assert_eq!(bundle.tip_lamports, 100_000);
    }
}
