use anyhow::{Context, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use tracing::{debug, info};

/// Jupiter V6 API base URL
const JUPITER_V6_API: &str = "https://quote-api.jup.ag/v6";

/// SOL mint address (wrapped SOL)
const SOL_MINT: &str = "So11111111111111111111111111111111111111112";

/// ORE token mint address (replace with actual ORE mint)
const ORE_MINT: &str = "oreoU2P8bN6jkk3jbaiVxYnG1dCXcYxwhwyK9jSybcp"; // Placeholder

/// Amount of SOL to quote for (in lamports) - 1 SOL
const QUOTE_AMOUNT_LAMPORTS: u64 = 1_000_000_000;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PriceQuote {
    /// Price of 1 ORE in SOL
    pub price_per_ore_sol: f64,

    /// Amount of SOL input (lamports)
    pub input_amount_lamports: u64,

    /// Amount of ORE output (smallest unit)
    pub output_amount: u64,

    /// Price impact percentage
    pub price_impact_pct: f64,

    /// Route information
    pub route_label: String,

    /// Timestamp of quote
    pub timestamp: i64,
}

#[derive(Debug, Deserialize)]
struct JupiterQuoteResponse {
    #[serde(rename = "inputMint")]
    input_mint: String,

    #[serde(rename = "inAmount")]
    in_amount: String,

    #[serde(rename = "outputMint")]
    output_mint: String,

    #[serde(rename = "outAmount")]
    out_amount: String,

    #[serde(rename = "otherAmountThreshold")]
    other_amount_threshold: String,

    #[serde(rename = "swapMode")]
    swap_mode: String,

    #[serde(rename = "slippageBps")]
    slippage_bps: u64,

    #[serde(rename = "priceImpactPct")]
    price_impact_pct: String,

    #[serde(rename = "routePlan")]
    route_plan: Vec<serde_json::Value>,
}

pub struct PriceOracle {
    client: Client,
    ore_mint: String,
    sol_mint: String,
}

impl PriceOracle {
    /// Create a new PriceOracle instance
    pub fn new() -> Result<Self> {
        let client = Client::builder()
            .timeout(std::time::Duration::from_secs(10))
            .build()
            .context("Failed to create HTTP client")?;

        Ok(Self {
            client,
            ore_mint: ORE_MINT.to_string(),
            sol_mint: SOL_MINT.to_string(),
        })
    }

    /// Create a new PriceOracle with custom token mints
    pub fn with_mints(ore_mint: String, sol_mint: String) -> Result<Self> {
        let client = Client::builder()
            .timeout(std::time::Duration::from_secs(10))
            .build()
            .context("Failed to create HTTP client")?;

        Ok(Self {
            client,
            ore_mint,
            sol_mint,
        })
    }

    /// Get the current market price for ORE in SOL
    ///
    /// Queries Jupiter V6 API to get the best swap price
    pub async fn get_ore_price(&self) -> Result<PriceQuote> {
        info!("Fetching ORE price from Jupiter V6...");

        let quote = self.fetch_jupiter_quote().await
            .context("Failed to fetch quote from Jupiter")?;

        Ok(quote)
    }

    /// Fetch quote from Jupiter V6 API
    async fn fetch_jupiter_quote(&self) -> Result<PriceQuote> {
        let url = format!(
            "{}/quote?inputMint={}&outputMint={}&amount={}&slippageBps=50",
            JUPITER_V6_API,
            self.sol_mint,
            self.ore_mint,
            QUOTE_AMOUNT_LAMPORTS
        );

        debug!("Jupiter API request: {}", url);

        let response = self.client
            .get(&url)
            .send()
            .await
            .context("Failed to send request to Jupiter API")?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_default();
            anyhow::bail!("Jupiter API error {}: {}", status, error_text);
        }

        let jupiter_quote: JupiterQuoteResponse = response
            .json()
            .await
            .context("Failed to parse Jupiter response")?;

        // Calculate price per ORE
        let in_amount = jupiter_quote.in_amount.parse::<u64>()
            .context("Failed to parse input amount")?;
        let out_amount = jupiter_quote.out_amount.parse::<u64>()
            .context("Failed to parse output amount")?;

        // Price per ORE in SOL
        // (SOL input in lamports) / (ORE output) = lamports per ORE
        // Convert to SOL by dividing by 1e9
        let lamports_per_ore = in_amount as f64 / out_amount as f64;
        let price_per_ore_sol = lamports_per_ore / 1_000_000_000.0;

        let price_impact = jupiter_quote.price_impact_pct
            .parse::<f64>()
            .unwrap_or(0.0);

        let route_label = jupiter_quote.route_plan
            .first()
            .and_then(|r| r.get("swapInfo"))
            .and_then(|s| s.get("label"))
            .and_then(|l| l.as_str())
            .unwrap_or("unknown")
            .to_string();

        let quote = PriceQuote {
            price_per_ore_sol,
            input_amount_lamports: in_amount,
            output_amount: out_amount,
            price_impact_pct: price_impact,
            route_label,
            timestamp: chrono::Utc::now().timestamp(),
        };

        info!(
            "ORE price: {} SOL (via {}, impact: {:.4}%)",
            quote.price_per_ore_sol,
            quote.route_label,
            quote.price_impact_pct
        );

        Ok(quote)
    }

    /// Get quote for a specific amount of ORE to buy
    pub async fn get_quote_for_ore_amount(&self, ore_amount: u64) -> Result<PriceQuote> {
        let url = format!(
            "{}/quote?inputMint={}&outputMint={}&amount={}&slippageBps=50&swapMode=ExactOut",
            JUPITER_V6_API,
            self.sol_mint,
            self.ore_mint,
            ore_amount
        );

        debug!("Jupiter API request (exact out): {}", url);

        let response = self.client
            .get(&url)
            .send()
            .await
            .context("Failed to send request to Jupiter API")?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_default();
            anyhow::bail!("Jupiter API error {}: {}", status, error_text);
        }

        let jupiter_quote: JupiterQuoteResponse = response
            .json()
            .await
            .context("Failed to parse Jupiter response")?;

        let in_amount = jupiter_quote.in_amount.parse::<u64>()
            .context("Failed to parse input amount")?;
        let out_amount = jupiter_quote.out_amount.parse::<u64>()
            .context("Failed to parse output amount")?;

        let lamports_per_ore = in_amount as f64 / out_amount as f64;
        let price_per_ore_sol = lamports_per_ore / 1_000_000_000.0;

        let price_impact = jupiter_quote.price_impact_pct
            .parse::<f64>()
            .unwrap_or(0.0);

        let route_label = jupiter_quote.route_plan
            .first()
            .and_then(|r| r.get("swapInfo"))
            .and_then(|s| s.get("label"))
            .and_then(|l| l.as_str())
            .unwrap_or("unknown")
            .to_string();

        Ok(PriceQuote {
            price_per_ore_sol,
            input_amount_lamports: in_amount,
            output_amount: out_amount,
            price_impact_pct: price_impact,
            route_label,
            timestamp: chrono::Utc::now().timestamp(),
        })
    }
}

impl Default for PriceOracle {
    fn default() -> Self {
        Self::new().expect("Failed to create default PriceOracle")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    #[ignore] // Requires network access
    async fn test_get_ore_price() {
        let oracle = PriceOracle::new().unwrap();
        let quote = oracle.get_ore_price().await;

        // This test will fail if Jupiter API is unavailable
        // or if the ORE token isn't listed
        match quote {
            Ok(q) => {
                println!("ORE price: {} SOL", q.price_per_ore_sol);
                assert!(q.price_per_ore_sol > 0.0);
            }
            Err(e) => {
                println!("Quote failed (expected if ORE not on Jupiter): {}", e);
            }
        }
    }
}
