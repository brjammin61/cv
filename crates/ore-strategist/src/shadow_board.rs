use ore_common::{GridState, PendingTransaction, ShadowBoardState, Result, GRID_SIZE};
use tracing::{debug, info};

/// Shadow Board - maintains predicted state based on mempool
///
/// This is our "information asymmetry" advantage. By monitoring pending
/// transactions, we can predict where the crowd is moving and find blocks
/// that will have better risk/reward ratios.
pub struct ShadowBoard {
    /// Time window for considering pending transactions (seconds)
    prediction_window: i64,
}

impl ShadowBoard {
    pub fn new(prediction_window: i64) -> Self {
        Self { prediction_window }
    }

    /// Build shadow board state from current state + pending transactions
    pub fn build_shadow_state(
        &self,
        confirmed_state: &GridState,
        pending_txs: Vec<PendingTransaction>,
    ) -> Result<ShadowBoardState> {
        let now = ore_common::utils::current_timestamp();

        // Filter recent pending transactions
        let recent_txs: Vec<PendingTransaction> = pending_txs
            .into_iter()
            .filter(|tx| now - tx.timestamp <= self.prediction_window)
            .collect();

        // Clone confirmed state as base
        let mut predicted_state = confirmed_state.clone();

        // Apply pending transactions to predict future state
        for tx in &recent_txs {
            if let Some(block) = predicted_state.blocks.get_mut(tx.block_index as usize) {
                block.staked_amount += tx.stake_amount;
                block.participant_count += 1;
            }
        }

        // Recalculate total staked
        predicted_state.total_staked = predicted_state
            .blocks
            .iter()
            .map(|b| b.staked_amount)
            .sum();

        // Calculate confidence score based on number of pending txs
        let confidence = self.calculate_confidence(&recent_txs);

        info!(
            "Shadow board built: {} pending txs, confidence: {:.2}",
            recent_txs.len(),
            confidence
        );

        Ok(ShadowBoardState {
            confirmed_state: confirmed_state.clone(),
            predicted_state,
            pending_transactions: recent_txs,
            confidence,
        })
    }

    /// Calculate confidence in our predictions
    fn calculate_confidence(&self, pending_txs: &[PendingTransaction]) -> f64 {
        // More pending transactions = higher confidence in predictions
        // But cap at 0.95 since we can never be 100% certain

        let base_confidence = 0.5;
        let tx_count = pending_txs.len() as f64;

        // Logarithmic scale: more txs = higher confidence, but diminishing returns
        let confidence = base_confidence + (tx_count.ln() / 10.0);

        confidence.min(0.95).max(0.0)
    }

    /// Identify blocks with sudden stake increases (potential traps)
    pub fn detect_stake_traps(&self, shadow_state: &ShadowBoardState) -> Vec<u8> {
        let mut traps = Vec::new();

        for i in 0..GRID_SIZE {
            let confirmed_stake = shadow_state.confirmed_state.blocks[i].staked_amount;
            let predicted_stake = shadow_state.predicted_state.blocks[i].staked_amount;

            // If stake increased by more than 50%, it might be a trap
            if confirmed_stake > 0 {
                let increase_ratio = predicted_stake as f64 / confirmed_stake as f64;

                if increase_ratio > 1.5 {
                    debug!(
                        "Detected stake trap on block {}: {}x increase",
                        i, increase_ratio
                    );
                    traps.push(i as u8);
                }
            }
        }

        traps
    }

    /// Find blocks that are likely to remain undervalued
    pub fn find_hidden_gems(&self, shadow_state: &ShadowBoardState) -> Vec<u8> {
        let mut gems = Vec::new();

        // Calculate average stake per block
        let avg_stake = shadow_state.predicted_state.total_staked / GRID_SIZE as u64;

        for block in &shadow_state.predicted_state.blocks {
            // Blocks with below-average stake and few pending transactions are "hidden gems"
            if block.staked_amount < avg_stake {
                let pending_on_block = shadow_state
                    .pending_transactions
                    .iter()
                    .filter(|tx| tx.block_index == block.index)
                    .count();

                if pending_on_block <= 1 {
                    debug!(
                        "Found hidden gem on block {}: stake {} vs avg {}",
                        block.index, block.staked_amount, avg_stake
                    );
                    gems.push(block.index);
                }
            }
        }

        gems
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ore_common::BlockState;

    fn create_test_state() -> GridState {
        let blocks = std::array::from_fn(|i| BlockState {
            index: i as u8,
            staked_amount: 1_000_000_000,
            participant_count: 5,
            historical_win_rate: 0.04,
        });

        GridState {
            round: 1,
            blocks,
            motherlode_size: 0,
            total_staked: 25_000_000_000,
            round_start: 1000000,
            last_update: 1000030,
        }
    }

    #[test]
    fn test_shadow_board_building() {
        let shadow_board = ShadowBoard::new(10);
        let state = create_test_state();

        let pending_txs = vec![
            PendingTransaction {
                signature: "sig1".to_string(),
                block_index: 0,
                stake_amount: 500_000_000,
                timestamp: 1000035,
            },
            PendingTransaction {
                signature: "sig2".to_string(),
                block_index: 0,
                stake_amount: 500_000_000,
                timestamp: 1000036,
            },
        ];

        let shadow_state = shadow_board
            .build_shadow_state(&state, pending_txs)
            .unwrap();

        // Block 0 should have increased stake
        assert_eq!(
            shadow_state.predicted_state.blocks[0].staked_amount,
            2_000_000_000
        );

        // Total staked should have increased
        assert!(shadow_state.predicted_state.total_staked > state.total_staked);
    }

    #[test]
    fn test_stake_trap_detection() {
        let shadow_board = ShadowBoard::new(10);
        let mut state = create_test_state();

        // Create a shadow state with a stake trap on block 5
        let mut shadow_state = ShadowBoardState {
            confirmed_state: state.clone(),
            predicted_state: state.clone(),
            pending_transactions: vec![],
            confidence: 0.8,
        };

        // Simulate 3x stake increase on block 5
        shadow_state.predicted_state.blocks[5].staked_amount = 3_000_000_000;

        let traps = shadow_board.detect_stake_traps(&shadow_state);

        assert!(traps.contains(&5));
    }
}
