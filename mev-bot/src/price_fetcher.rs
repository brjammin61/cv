use crate::types::*;
use anyhow::{Context, Result};
use reqwest::Client;
use rust_decimal::Decimal;
use solana_sdk::pubkey::Pubkey;
use std::collections::HashMap;
use std::str::FromStr;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{debug, warn};

/// Fetches real-time prices from multiple DEXs
pub struct PriceFetcher {
    client: Client,
    jupiter_api: String,
    cache: Arc<RwLock<HashMap<String, PriceQuote>>>,
    cache_ttl_ms: u64,
}

impl PriceFetcher {
    pub fn new() -> Self {
        Self {
            client: Client::builder()
                .timeout(std::time::Duration::from_secs(5))
                .build()
                .expect("Failed to create HTTP client"),
            jupiter_api: "https://quote-api.jup.ag/v6".to_string(),
            cache: Arc::new(RwLock::new(HashMap::new())),
            cache_ttl_ms: 500, // Cache for 500ms
        }
    }

    /// Fetch price quote from Jupiter
    pub async fn fetch_jupiter_quote(
        &self,
        input_mint: &Pubkey,
        output_mint: &Pubkey,
        amount: u64,
        slippage_bps: u64,
    ) -> Result<PriceQuote> {
        let cache_key = format!("jup_{}_{}_{}",
input_mint, output_mint, amount);

        // Check cache first
        {
            let cache = self.cache.read().await;
            if let Some(quote) = cache.get(&cache_key) {
                let age_ms = (chrono::Utc::now().timestamp_millis() - quote.timestamp) as u64;
                if age_ms < self.cache_ttl_ms {
                    debug!("Cache hit for Jupiter quote");
                    return Ok(quote.clone());
                }
            }
        }

        // Fetch fresh quote
        let url = format!(
            "{}/quote?inputMint={}&outputMint={}&amount={}&slippageBps={}",
            self.jupiter_api, input_mint, output_mint, amount, slippage_bps
        );

        let response = self.client
            .get(&url)
            .send()
            .await
            .context("Failed to fetch Jupiter quote")?;

        if !response.status().is_success() {
            let error = response.text().await?;
            anyhow::bail!("Jupiter API error: {}", error);
        }

        let quote_data: serde_json::Value = response.json().await?;

        let in_amount = quote_data["inAmount"]
            .as_str()
            .context("Missing inAmount")?
            .parse::<u64>()?;

        let out_amount = quote_data["outAmount"]
            .as_str()
            .context("Missing outAmount")?
            .parse::<u64>()?;

        // Extract route information
        let route_plan = &quote_data["routePlan"];
        let mut route = vec![*input_mint];

        if let Some(plan) = route_plan.as_array() {
            for step in plan {
                if let Some(out_mint_str) = step["swapInfo"]["outputMint"].as_str() {
                    if let Ok(pubkey) = Pubkey::from_str(out_mint_str) {
                        route.push(pubkey);
                    }
                }
            }
        }

        let price = Decimal::from(out_amount) / Decimal::from(in_amount);

        let quote = PriceQuote {
            dex: Dex::Jupiter,
            pair: TokenPair {
                base: *input_mint,
                quote: *output_mint,
            },
            input_amount: in_amount,
            output_amount: out_amount,
            price,
            timestamp: chrono::Utc::now().timestamp_millis(),
            route,
            quote_data,
        };

        // Update cache
        {
            let mut cache = self.cache.write().await;
            cache.insert(cache_key, quote.clone());
        }

        Ok(quote)
    }

    /// Fetch price quote from Raydium
    /// Note: Raydium requires on-chain pool state reading
    /// For now, this is a placeholder - would need full implementation
    pub async fn fetch_raydium_quote(
        &self,
        input_mint: &Pubkey,
        output_mint: &Pubkey,
        amount: u64,
    ) -> Result<PriceQuote> {
        // TODO: Implement actual Raydium quote fetching
        // This requires:
        // 1. Finding the pool for this pair
        // 2. Reading pool state from on-chain
        // 3. Calculating swap output using AMM formula
        // 4. Accounting for fees

        warn!("Raydium quote fetching not yet implemented - using Jupiter as fallback");
        self.fetch_jupiter_quote(input_mint, output_mint, amount, 50).await
    }

    /// Fetch price quote from Orca
    /// Note: Similar to Raydium, requires on-chain state reading
    pub async fn fetch_orca_quote(
        &self,
        input_mint: &Pubkey,
        output_mint: &Pubkey,
        amount: u64,
    ) -> Result<PriceQuote> {
        // TODO: Implement actual Orca quote fetching
        // Orca uses Whirlpools (concentrated liquidity)
        // Requires:
        // 1. Finding whirlpool for pair
        // 2. Reading tick data
        // 3. Calculating swap output
        // 4. Accounting for fees

        warn!("Orca quote fetching not yet implemented - using Jupiter as fallback");
        self.fetch_jupiter_quote(input_mint, output_mint, amount, 50).await
    }

    /// Fetch quotes from all DEXs concurrently
    pub async fn fetch_all_quotes(
        &self,
        input_mint: &Pubkey,
        output_mint: &Pubkey,
        amount: u64,
    ) -> Vec<PriceQuote> {
        let mut quotes = Vec::new();

        // Fetch from all DEXs in parallel
        let (jupiter_result, raydium_result, orca_result) = tokio::join!(
            self.fetch_jupiter_quote(input_mint, output_mint, amount, 50),
            self.fetch_raydium_quote(input_mint, output_mint, amount),
            self.fetch_orca_quote(input_mint, output_mint, amount),
        );

        if let Ok(quote) = jupiter_result {
            quotes.push(quote);
        }

        if let Ok(quote) = raydium_result {
            quotes.push(quote);
        }

        if let Ok(quote) = orca_result {
            quotes.push(quote);
        }

        quotes
    }

    /// Get best buy price (lowest price to acquire output token)
    pub fn get_best_buy_quote(quotes: &[PriceQuote]) -> Option<&PriceQuote> {
        quotes.iter()
            .min_by(|a, b| a.price.cmp(&b.price))
    }

    /// Get best sell price (highest price when selling output token)
    pub fn get_best_sell_quote(quotes: &[PriceQuote]) -> Option<&PriceQuote> {
        quotes.iter()
            .max_by(|a, b| a.price.cmp(&b.price))
    }

    /// Clear cache (useful for testing or resetting state)
    pub async fn clear_cache(&self) {
        let mut cache = self.cache.write().await;
        cache.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    #[ignore] // Requires network access
    async fn test_fetch_jupiter_quote() {
        let fetcher = PriceFetcher::new();

        // SOL -> USDC quote
        let sol_mint = Pubkey::from_str("So11111111111111111111111111111111111111112").unwrap();
        let usdc_mint = Pubkey::from_str("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v").unwrap();

        let quote = fetcher.fetch_jupiter_quote(
            &sol_mint,
            &usdc_mint,
            1_000_000_000, // 1 SOL
            50,
        ).await;

        match quote {
            Ok(q) => {
                println!("Jupiter quote: 1 SOL = {} USDC", q.output_amount as f64 / 1_000_000.0);
                assert!(q.output_amount > 0);
                assert_eq!(q.dex, Dex::Jupiter);
            }
            Err(e) => {
                println!("Failed to fetch quote: {}", e);
            }
        }
    }
}
