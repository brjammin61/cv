use anyhow::Result;
use ore_common::{GridState, OreError};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use sqlx::{SqlitePool, Row};
use tracing::{info, warn};

/// Collects historical data from ORE.supply and on-chain events
pub struct DataCollector {
    client: Client,
    db: SqlitePool,
    ore_supply_api: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HistoricalRound {
    pub round_number: u64,
    pub winning_block: u8,
    pub total_staked: u64,
    pub motherlode_size: u64,
    pub block_stakes: Vec<u64>,
    pub participant_counts: Vec<u32>,
    pub winner_address: String,
    pub timestamp: i64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WinnerProfile {
    pub address: String,
    pub total_wins: u64,
    pub total_rounds_played: u64,
    pub average_stake: u64,
    pub preferred_blocks: Vec<u8>,
    pub win_rate: f64,
    pub strategy_pattern: StrategyPattern,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub enum StrategyPattern {
    Conservative,      // Low stakes, diverse blocks
    Aggressive,        // High stakes, focused blocks
    Sniper,           // Last-second entries
    Follower,         // Copies popular blocks
    Contrarian,       // Avoids popular blocks
    Unknown,
}

impl DataCollector {
    pub async fn new(ore_supply_api: String, db_path: &str) -> Result<Self> {
        let db = SqlitePool::connect(db_path).await?;

        // Initialize database schema
        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS historical_rounds (
                round_number INTEGER PRIMARY KEY,
                winning_block INTEGER NOT NULL,
                total_staked INTEGER NOT NULL,
                motherlode_size INTEGER NOT NULL,
                block_stakes TEXT NOT NULL,
                participant_counts TEXT NOT NULL,
                winner_address TEXT NOT NULL,
                timestamp INTEGER NOT NULL
            )
            "#,
        )
        .execute(&db)
        .await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS winner_profiles (
                address TEXT PRIMARY KEY,
                total_wins INTEGER NOT NULL,
                total_rounds_played INTEGER NOT NULL,
                average_stake INTEGER NOT NULL,
                preferred_blocks TEXT NOT NULL,
                win_rate REAL NOT NULL,
                strategy_pattern TEXT NOT NULL,
                last_updated INTEGER NOT NULL
            )
            "#,
        )
        .execute(&db)
        .await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS our_performance (
                round_number INTEGER PRIMARY KEY,
                predicted_block INTEGER NOT NULL,
                actual_block INTEGER NOT NULL,
                our_block INTEGER NOT NULL,
                won BOOLEAN NOT NULL,
                predicted_ev REAL NOT NULL,
                actual_return REAL NOT NULL,
                stake_amount INTEGER NOT NULL,
                timestamp INTEGER NOT NULL
            )
            "#,
        )
        .execute(&db)
        .await?;

        info!("DataCollector initialized with database at {}", db_path);

        Ok(Self {
            client: Client::new(),
            db,
            ore_supply_api,
        })
    }

    /// Fetch historical data from ORE.supply API
    pub async fn fetch_historical_rounds(&self, limit: usize) -> Result<Vec<HistoricalRound>> {
        info!("Fetching {} historical rounds from ORE.supply", limit);

        let url = format!("{}/api/rounds?limit={}", self.ore_supply_api, limit);

        let response = self.client.get(&url).send().await?;

        if !response.status().is_success() {
            warn!("Failed to fetch from ORE.supply: {}", response.status());
            return Ok(Vec::new());
        }

        let rounds: Vec<HistoricalRound> = response.json().await?;

        info!("Fetched {} rounds from ORE.supply", rounds.len());

        // Store in database
        for round in &rounds {
            self.store_historical_round(round).await?;
        }

        Ok(rounds)
    }

    /// Store historical round in database
    async fn store_historical_round(&self, round: &HistoricalRound) -> Result<()> {
        let block_stakes_json = serde_json::to_string(&round.block_stakes)?;
        let participant_counts_json = serde_json::to_string(&round.participant_counts)?;

        sqlx::query(
            r#"
            INSERT OR REPLACE INTO historical_rounds
            (round_number, winning_block, total_staked, motherlode_size,
             block_stakes, participant_counts, winner_address, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(round.round_number as i64)
        .bind(round.winning_block as i64)
        .bind(round.total_staked as i64)
        .bind(round.motherlode_size as i64)
        .bind(block_stakes_json)
        .bind(participant_counts_json)
        .bind(&round.winner_address)
        .bind(round.timestamp)
        .execute(&self.db)
        .await?;

        Ok(())
    }

    /// Analyze winner and update profile
    pub async fn analyze_winner(&self, address: &str) -> Result<WinnerProfile> {
        info!("Analyzing winner profile: {}", address);

        // Fetch all rounds this address won
        let rows = sqlx::query(
            "SELECT * FROM historical_rounds WHERE winner_address = ? ORDER BY round_number DESC"
        )
        .bind(address)
        .fetch_all(&self.db)
        .await?;

        if rows.is_empty() {
            return Ok(WinnerProfile {
                address: address.to_string(),
                total_wins: 0,
                total_rounds_played: 0,
                average_stake: 0,
                preferred_blocks: vec![],
                win_rate: 0.0,
                strategy_pattern: StrategyPattern::Unknown,
            });
        }

        let total_wins = rows.len() as u64;

        // Calculate statistics
        let mut total_stake = 0u64;
        let mut block_frequency = vec![0u32; 25];
        let mut timestamps = Vec::new();

        for row in &rows {
            let winning_block: i64 = row.get("winning_block");
            let total_staked: i64 = row.get("total_staked");
            let timestamp: i64 = row.get("timestamp");

            block_frequency[winning_block as usize] += 1;
            total_stake += total_staked as u64;
            timestamps.push(timestamp);
        }

        let average_stake = total_stake / total_wins;

        // Find preferred blocks (most frequent wins)
        let mut block_prefs: Vec<(u8, u32)> = block_frequency
            .iter()
            .enumerate()
            .map(|(idx, &count)| (idx as u8, count))
            .collect();
        block_prefs.sort_by(|a, b| b.1.cmp(&a.1));

        let preferred_blocks: Vec<u8> = block_prefs
            .iter()
            .take(5)
            .filter(|(_, count)| *count > 0)
            .map(|(block, _)| *block)
            .collect();

        // Detect strategy pattern
        let strategy_pattern = self.detect_strategy_pattern(
            &block_frequency,
            average_stake,
            &timestamps,
        );

        // Estimate total rounds played (wins / estimated win rate)
        let estimated_win_rate = self.estimate_win_rate(&strategy_pattern);
        let total_rounds_played = (total_wins as f64 / estimated_win_rate) as u64;

        let profile = WinnerProfile {
            address: address.to_string(),
            total_wins,
            total_rounds_played,
            average_stake,
            preferred_blocks,
            win_rate: total_wins as f64 / total_rounds_played as f64,
            strategy_pattern,
        };

        // Store profile
        self.store_winner_profile(&profile).await?;

        Ok(profile)
    }

    /// Detect strategy pattern from historical behavior
    fn detect_strategy_pattern(
        &self,
        block_frequency: &[u32],
        average_stake: u64,
        timestamps: &[i64],
    ) -> StrategyPattern {
        // Calculate block diversity (Shannon entropy)
        let total_wins: u32 = block_frequency.iter().sum();
        let mut entropy = 0.0;

        for &freq in block_frequency {
            if freq > 0 {
                let p = freq as f64 / total_wins as f64;
                entropy -= p * p.log2();
            }
        }

        // High entropy = diverse blocks (Conservative)
        // Low entropy = focused blocks (Aggressive)

        let is_diverse = entropy > 2.5;
        let is_high_stakes = average_stake > 500_000_000; // > 0.5 SOL

        // Check for sniper pattern (last-second entries)
        let is_sniper = self.detect_sniper_pattern(timestamps);

        match (is_diverse, is_high_stakes, is_sniper) {
            (true, false, _) => StrategyPattern::Conservative,
            (false, true, _) => StrategyPattern::Aggressive,
            (_, _, true) => StrategyPattern::Sniper,
            (true, true, _) => StrategyPattern::Contrarian,
            _ => StrategyPattern::Follower,
        }
    }

    fn detect_sniper_pattern(&self, _timestamps: &[i64]) -> bool {
        // In production, analyze transaction timing within rounds
        // For now, return false
        false
    }

    fn estimate_win_rate(&self, pattern: &StrategyPattern) -> f64 {
        match pattern {
            StrategyPattern::Aggressive => 0.10,      // 10% win rate
            StrategyPattern::Sniper => 0.12,          // 12% win rate
            StrategyPattern::Contrarian => 0.08,      // 8% win rate
            StrategyPattern::Conservative => 0.04,    // 4% win rate (1/25 baseline)
            StrategyPattern::Follower => 0.03,        // 3% win rate
            StrategyPattern::Unknown => 0.04,
        }
    }

    async fn store_winner_profile(&self, profile: &WinnerProfile) -> Result<()> {
        let preferred_blocks_json = serde_json::to_string(&profile.preferred_blocks)?;
        let strategy_pattern_json = serde_json::to_string(&profile.strategy_pattern)?;

        sqlx::query(
            r#"
            INSERT OR REPLACE INTO winner_profiles
            (address, total_wins, total_rounds_played, average_stake,
             preferred_blocks, win_rate, strategy_pattern, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(&profile.address)
        .bind(profile.total_wins as i64)
        .bind(profile.total_rounds_played as i64)
        .bind(profile.average_stake as i64)
        .bind(preferred_blocks_json)
        .bind(profile.win_rate)
        .bind(strategy_pattern_json)
        .bind(ore_common::utils::current_timestamp())
        .execute(&self.db)
        .await?;

        Ok(())
    }

    /// Record our performance for self-learning
    pub async fn record_our_performance(
        &self,
        round_number: u64,
        predicted_block: u8,
        actual_winning_block: u8,
        our_block: u8,
        won: bool,
        predicted_ev: f64,
        actual_return: f64,
        stake_amount: u64,
    ) -> Result<()> {
        sqlx::query(
            r#"
            INSERT INTO our_performance
            (round_number, predicted_block, actual_block, our_block, won,
             predicted_ev, actual_return, stake_amount, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            "#,
        )
        .bind(round_number as i64)
        .bind(predicted_block as i64)
        .bind(actual_winning_block as i64)
        .bind(our_block as i64)
        .bind(won)
        .bind(predicted_ev)
        .bind(actual_return)
        .bind(stake_amount as i64)
        .bind(ore_common::utils::current_timestamp())
        .execute(&self.db)
        .await?;

        info!(
            "Recorded performance: Round {} - Predicted: {}, Actual: {}, Ours: {}, Won: {}",
            round_number, predicted_block, actual_winning_block, our_block, won
        );

        Ok(())
    }

    /// Get our prediction accuracy over time
    pub async fn get_prediction_accuracy(&self, last_n_rounds: usize) -> Result<f64> {
        let row = sqlx::query(
            r#"
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN predicted_block = actual_block THEN 1 ELSE 0 END) as correct
            FROM our_performance
            ORDER BY round_number DESC
            LIMIT ?
            "#,
        )
        .bind(last_n_rounds as i64)
        .fetch_one(&self.db)
        .await?;

        let total: i64 = row.get("total");
        let correct: i64 = row.get("correct");

        if total == 0 {
            return Ok(0.0);
        }

        Ok(correct as f64 / total as f64)
    }

    /// Get all historical rounds for ML training
    pub async fn get_all_historical_rounds(&self) -> Result<Vec<HistoricalRound>> {
        let rows = sqlx::query("SELECT * FROM historical_rounds ORDER BY round_number DESC")
            .fetch_all(&self.db)
            .await?;

        let mut rounds = Vec::new();

        for row in rows {
            let block_stakes_json: String = row.get("block_stakes");
            let participant_counts_json: String = row.get("participant_counts");

            let round = HistoricalRound {
                round_number: row.get::<i64, _>("round_number") as u64,
                winning_block: row.get::<i64, _>("winning_block") as u8,
                total_staked: row.get::<i64, _>("total_staked") as u64,
                motherlode_size: row.get::<i64, _>("motherlode_size") as u64,
                block_stakes: serde_json::from_str(&block_stakes_json)?,
                participant_counts: serde_json::from_str(&participant_counts_json)?,
                winner_address: row.get("winner_address"),
                timestamp: row.get("timestamp"),
            };

            rounds.push(round);
        }

        Ok(rounds)
    }
}
