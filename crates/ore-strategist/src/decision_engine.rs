use ore_common::{
    ExecutionMode, GridState, ShadowBoardState, StrategyDecision, Result, OreError,
    AGGRESSIVE_JITO_TIP, DEFAULT_JITO_TIP, MOTHERLODE_AGGRESSIVE_THRESHOLD,
    SNIPER_WINDOW_SECS, utils,
};
use tracing::{info, warn};

use crate::{EVCalculator, ShadowBoard};

/// Decision Engine - the "brain" that makes the final strategic call
///
/// This combines:
/// - EV calculations
/// - Shadow board predictions
/// - Motherlode jackpot size
/// - Time remaining in round
///
/// To make the optimal decision on which block to stake and how much.
pub struct DecisionEngine {
    ev_calculator: EVCalculator,
    shadow_board: ShadowBoard,
    max_stake_per_round: u64,
}

impl DecisionEngine {
    pub fn new(
        min_stake: u64,
        max_stake: u64,
        risk_tolerance: f64,
        max_stake_per_round: u64,
    ) -> Self {
        Self {
            ev_calculator: EVCalculator::new(min_stake, max_stake, risk_tolerance),
            shadow_board: ShadowBoard::new(30), // 30 second prediction window
            max_stake_per_round,
        }
    }

    /// Make the strategic decision for this round
    pub fn decide(
        &self,
        grid_state: &GridState,
        shadow_state: Option<&ShadowBoardState>,
    ) -> Result<StrategyDecision> {
        info!("Making strategic decision for round {}", grid_state.round);

        // Determine execution mode based on time and motherlode
        let execution_mode = self.determine_execution_mode(grid_state);

        // Use shadow board state if available, otherwise use confirmed state
        let state_to_analyze = if let Some(shadow) = shadow_state {
            if shadow.confidence > 0.6 {
                info!("Using shadow board predictions (confidence: {:.2})", shadow.confidence);
                &shadow.predicted_state
            } else {
                warn!("Shadow board confidence too low, using confirmed state");
                grid_state
            }
        } else {
            grid_state
        };

        // Calculate stake amount
        let stake_amount = self.calculate_stake_amount(grid_state, &execution_mode);

        // Calculate EV for all blocks
        let mut ev_calculations = self.ev_calculator
            .calculate_all_blocks(state_to_analyze, stake_amount)?;

        // Filter out "stake traps" if we have shadow board data
        if let Some(shadow) = shadow_state {
            let traps = self.shadow_board.detect_stake_traps(shadow);
            ev_calculations.retain(|calc| !traps.contains(&calc.block_index));

            // Prioritize "hidden gems"
            let gems = self.shadow_board.find_hidden_gems(shadow);
            if !gems.is_empty() {
                info!("Found {} hidden gems", gems.len());
            }
        }

        // Find efficiency gaps
        let gaps = self.ev_calculator.find_efficiency_gaps(&ev_calculations);

        // Select best block
        let best_calculation = if !gaps.is_empty() {
            info!("Targeting efficiency gap");
            gaps[0].clone()
        } else if !ev_calculations.is_empty() {
            ev_calculations[0].clone()
        } else {
            return Err(OreError::Strategy("No valid blocks found".to_string()));
        };

        // Determine Jito tip
        let jito_tip = self.calculate_jito_tip(&execution_mode, grid_state.motherlode_size);

        let decision = StrategyDecision {
            target_block: best_calculation.block_index,
            stake_amount,
            expected_value: best_calculation.expected_value,
            confidence: best_calculation.win_probability,
            execution_mode,
            jito_tip,
        };

        info!(
            "Decision: block={}, stake={}, EV={:.4}, mode={:?}",
            decision.target_block,
            decision.stake_amount,
            decision.expected_value,
            decision.execution_mode
        );

        Ok(decision)
    }

    /// Determine execution mode based on round state
    fn determine_execution_mode(&self, grid_state: &GridState) -> ExecutionMode {
        let time_remaining = utils::time_remaining_in_round(grid_state.round_start);

        // Aggressive mode for large motherlodes
        if grid_state.motherlode_size > MOTHERLODE_AGGRESSIVE_THRESHOLD {
            return ExecutionMode::Aggressive;
        }

        // Sniper mode in last few seconds
        if time_remaining <= SNIPER_WINDOW_SECS {
            return ExecutionMode::Sniper;
        }

        // Normal mode otherwise
        ExecutionMode::Normal
    }

    /// Calculate optimal stake amount
    fn calculate_stake_amount(&self, grid_state: &GridState, mode: &ExecutionMode) -> u64 {
        let base_stake = match mode {
            ExecutionMode::Aggressive => self.max_stake_per_round,
            ExecutionMode::Sniper => self.max_stake_per_round * 3 / 4,
            ExecutionMode::Normal => self.max_stake_per_round / 2,
            ExecutionMode::Conservative => self.max_stake_per_round / 4,
        };

        // Adjust for motherlode size
        if grid_state.motherlode_size > 0 {
            let motherlode_multiplier =
                (grid_state.motherlode_size as f64 / 1_000_000_000.0).sqrt().min(2.0);
            (base_stake as f64 * motherlode_multiplier) as u64
        } else {
            base_stake
        }
    }

    /// Calculate appropriate Jito tip
    fn calculate_jito_tip(&self, mode: &ExecutionMode, motherlode_size: u64) -> u64 {
        match mode {
            ExecutionMode::Aggressive => AGGRESSIVE_JITO_TIP,
            ExecutionMode::Sniper => {
                if motherlode_size > MOTHERLODE_AGGRESSIVE_THRESHOLD {
                    AGGRESSIVE_JITO_TIP
                } else {
                    DEFAULT_JITO_TIP * 2
                }
            }
            ExecutionMode::Normal => DEFAULT_JITO_TIP,
            ExecutionMode::Conservative => DEFAULT_JITO_TIP / 2,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ore_common::BlockState;

    fn create_test_grid() -> GridState {
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
            round_start: utils::current_timestamp() - 30,
            last_update: utils::current_timestamp(),
        }
    }

    #[test]
    fn test_decision_making() {
        let engine = DecisionEngine::new(
            100_000_000,   // 0.1 SOL min
            1_000_000_000, // 1 SOL max
            0.5,           // moderate risk
            500_000_000,   // 0.5 SOL max per round
        );

        let grid = create_test_grid();
        let decision = engine.decide(&grid, None).unwrap();

        assert!(decision.target_block < 25);
        assert!(decision.stake_amount > 0);
        assert!(decision.jito_tip > 0);
    }

    #[test]
    fn test_aggressive_mode_for_motherlode() {
        let engine = DecisionEngine::new(100_000_000, 1_000_000_000, 0.5, 500_000_000);

        let mut grid = create_test_grid();
        grid.motherlode_size = 2_000_000_000; // 2 SOL motherlode

        let decision = engine.decide(&grid, None).unwrap();

        assert_eq!(decision.execution_mode, ExecutionMode::Aggressive);
        assert!(decision.jito_tip >= AGGRESSIVE_JITO_TIP);
    }
}
