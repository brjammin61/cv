use ore_common::{OreError, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use solana_sdk::transaction::Transaction;
use tracing::{debug, info, warn};

/// Jito client for submitting bundles
///
/// Jito provides guaranteed transaction inclusion through MEV infrastructure.
/// This is critical for our "sniper" strategy.
pub struct JitoClient {
    client: Client,
    jito_url: String,
    tip_account: String,
}

#[derive(Debug, Serialize)]
struct SendBundleRequest {
    jsonrpc: String,
    id: u64,
    method: String,
    params: Vec<Vec<String>>,
}

#[derive(Debug, Deserialize)]
struct SendBundleResponse {
    jsonrpc: String,
    result: Option<String>,
    error: Option<RpcError>,
    id: u64,
}

#[derive(Debug, Deserialize)]
struct RpcError {
    code: i64,
    message: String,
}

#[derive(Debug, Deserialize)]
struct BundleStatus {
    bundle_id: String,
    transactions: Vec<String>,
    slot: Option<u64>,
    confirmation_status: Option<String>,
}

impl JitoClient {
    pub fn new(jito_url: String, tip_account: String) -> Self {
        Self {
            client: Client::new(),
            jito_url,
            tip_account,
        }
    }

    /// Submit a bundle of transactions
    ///
    /// Bundles are guaranteed to execute atomically and in order.
    /// If any transaction in the bundle fails, the entire bundle fails.
    pub async fn send_bundle(&self, transactions: Vec<Transaction>) -> Result<String> {
        if transactions.is_empty() {
            return Err(OreError::JitoSubmission("Empty bundle".to_string()));
        }

        info!("Submitting bundle with {} transactions", transactions.len());

        // Serialize transactions to base64
        let serialized_txs: Vec<String> = transactions
            .iter()
            .map(|tx| {
                let serialized = bincode::serialize(tx).expect("Failed to serialize transaction");
                base64::encode(&serialized)
            })
            .collect();

        // Build JSON-RPC request
        let request = SendBundleRequest {
            jsonrpc: "2.0".to_string(),
            id: 1,
            method: "sendBundle".to_string(),
            params: vec![serialized_txs],
        };

        // Send request
        let response = self
            .client
            .post(&self.jito_url)
            .json(&request)
            .send()
            .await
            .map_err(|e| OreError::Network(e))?;

        if !response.status().is_success() {
            return Err(OreError::JitoSubmission(format!(
                "HTTP error: {}",
                response.status()
            )));
        }

        let bundle_response: SendBundleResponse = response
            .json()
            .await
            .map_err(|e| OreError::Network(e))?;

        if let Some(error) = bundle_response.error {
            return Err(OreError::JitoSubmission(format!(
                "RPC error {}: {}",
                error.code, error.message
            )));
        }

        let bundle_id = bundle_response.result.ok_or_else(|| {
            OreError::JitoSubmission("No bundle ID returned".to_string())
        })?;

        info!("Bundle submitted: {}", bundle_id);

        Ok(bundle_id)
    }

    /// Submit bundle with retry logic
    pub async fn send_bundle_with_retry(
        &self,
        transactions: Vec<Transaction>,
        max_retries: u32,
    ) -> Result<String> {
        let mut attempts = 0;

        loop {
            match self.send_bundle(transactions.clone()).await {
                Ok(bundle_id) => return Ok(bundle_id),
                Err(e) => {
                    attempts += 1;
                    if attempts >= max_retries {
                        return Err(e);
                    }

                    warn!(
                        "Bundle submission failed (attempt {}/{}): {:?}",
                        attempts, max_retries, e
                    );

                    // Exponential backoff
                    let delay = std::time::Duration::from_millis(100 * (2u64.pow(attempts)));
                    tokio::time::sleep(delay).await;
                }
            }
        }
    }

    /// Get bundle status
    pub async fn get_bundle_status(&self, bundle_id: &str) -> Result<Option<BundleStatus>> {
        #[derive(Serialize)]
        struct GetBundleRequest {
            jsonrpc: String,
            id: u64,
            method: String,
            params: Vec<String>,
        }

        let request = GetBundleRequest {
            jsonrpc: "2.0".to_string(),
            id: 1,
            method: "getBundleStatuses".to_string(),
            params: vec![bundle_id.to_string()],
        };

        let response = self
            .client
            .post(&self.jito_url)
            .json(&request)
            .send()
            .await
            .map_err(|e| OreError::Network(e))?;

        #[derive(Deserialize)]
        struct GetBundleResponse {
            result: Option<Vec<BundleStatus>>,
        }

        let bundle_response: GetBundleResponse = response
            .json()
            .await
            .map_err(|e| OreError::Network(e))?;

        Ok(bundle_response.result.and_then(|mut statuses| {
            if statuses.is_empty() {
                None
            } else {
                Some(statuses.remove(0))
            }
        }))
    }

    /// Get the Jito tip account pubkey
    pub fn get_tip_account(&self) -> &str {
        &self.tip_account
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_jito_client_creation() {
        let client = JitoClient::new(
            "https://mainnet.block-engine.jito.wtf/api/v1/bundles".to_string(),
            "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5".to_string(),
        );

        assert_eq!(
            client.get_tip_account(),
            "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5"
        );
    }
}
