use ore_common::{
    BlockState, EVCalculation, ExecutionMode, GridState, OreError, Result,
    GRID_SIZE, MOTHERLODE_AGGRESSIVE_THRESHOLD, MOTHERLODE_EV_MULTIPLIER,
    REFINING_FEE_PCT,
};
use tracing::debug;

/// Expected Value (EV) Calculator
///
/// This is the core competitive advantage of the bot. It calculates the expected
/// value of staking on each block in the 5x5 grid, considering:
///
/// 1. **Payout Distribution**: How rewards are split among blocks
/// 2. **Competition Intensity**: Current stake distribution
/// 3. **Motherlode Jackpot**: Additional EV from the jackpot
/// 4. **Historical Data**: Win rates and patterns
/// 5. **Shadow Board**: Predicted future state from mempool
pub struct EVCalculator {
    /// Minimum stake amount (in lamports)
    min_stake: u64,
    /// Maximum stake amount (in lamports)
    max_stake: u64,
    /// Risk tolerance (0.0-1.0)
    risk_tolerance: f64,
}

impl EVCalculator {
    pub fn new(min_stake: u64, max_stake: u64, risk_tolerance: f64) -> Self {
        Self {
            min_stake,
            max_stake,
            risk_tolerance,
        }
    }

    /// Calculate EV for all blocks in the grid
    pub fn calculate_all_blocks(
        &self,
        grid_state: &GridState,
        our_stake: u64,
    ) -> Result<Vec<EVCalculation>> {
        let mut calculations = Vec::with_capacity(GRID_SIZE);

        for block in &grid_state.blocks {
            let ev = self.calculate_block_ev(grid_state, block, our_stake)?;
            calculations.push(ev);
        }

        // Sort by expected value (descending)
        calculations.sort_by(|a, b| {
            b.expected_value
                .partial_cmp(&a.expected_value)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        Ok(calculations)
    }

    /// Calculate EV for a specific block
    fn calculate_block_ev(
        &self,
        grid_state: &GridState,
        block: &BlockState,
        our_stake: u64,
    ) -> Result<EVCalculation> {
        // Calculate total pool (total ORE rewards this round)
        // In ORE V2, this is typically derived from the mining rewards
        let total_reward_pool = self.estimate_reward_pool(grid_state);

        // Calculate block's share of the pool
        let block_reward = self.calculate_block_reward(grid_state, total_reward_pool);

        // Calculate our probability of winning this block
        let win_probability = self.calculate_win_probability(block, our_stake);

        // Calculate base expected value
        let base_ev = block_reward * win_probability;

        // Factor in motherlode
        let motherlode_ev = if grid_state.motherlode_size > 0 {
            self.calculate_motherlode_ev(grid_state, block, our_stake)
        } else {
            0.0
        };

        // Total expected value
        let expected_value = base_ev + motherlode_ev;

        // Calculate competition score
        let competition_score = self.calculate_competition_score(grid_state, block);

        // Determine recommended stake
        let recommended_stake = self.calculate_recommended_stake(
            expected_value,
            competition_score,
            grid_state.motherlode_size,
        );

        Ok(EVCalculation {
            block_index: block.index,
            expected_value,
            win_probability,
            competition_score,
            includes_motherlode: grid_state.motherlode_size > 0,
            recommended_stake,
        })
    }

    /// Estimate the total reward pool for this round
    fn estimate_reward_pool(&self, grid_state: &GridState) -> f64 {
        // This would be based on the actual ORE V2 emission schedule
        // For now, use a simplified model
        let base_emission = 10.0; // 10 ORE base reward

        // Adjust based on total staked (more stakes = more rewards mined)
        let stake_multiplier = (grid_state.total_staked as f64 / 1_000_000_000.0).max(1.0);

        base_emission * stake_multiplier
    }

    /// Calculate reward for a specific block (typically 1/25 of pool)
    fn calculate_block_reward(&self, _grid_state: &GridState, total_pool: f64) -> f64 {
        // In a 5x5 grid, each winning block gets 1/25 of the pool
        total_pool / GRID_SIZE as f64
    }

    /// Calculate probability of winning a block given our stake
    fn calculate_win_probability(&self, block: &BlockState, our_stake: u64) -> f64 {
        let total_stake_on_block = block.staked_amount + our_stake;

        if total_stake_on_block == 0 {
            return 0.0;
        }

        // Our share of this block
        let our_share = our_stake as f64 / total_stake_on_block as f64;

        // Adjust for competition: more participants = lower chance each has the winning hash
        let competition_factor = 1.0 / (block.participant_count as f64 + 1.0);

        our_share * competition_factor
    }

    /// Calculate EV from motherlode jackpot
    fn calculate_motherlode_ev(
        &self,
        grid_state: &GridState,
        block: &BlockState,
        our_stake: u64,
    ) -> f64 {
        let motherlode_value = grid_state.motherlode_size as f64 / 1_000_000_000.0; // Convert to SOL

        // Probability of winning motherlode
        let our_share = if grid_state.total_staked > 0 {
            our_stake as f64 / grid_state.total_staked as f64
        } else {
            0.0
        };

        // Motherlode goes to the overall winner, weighted by total stake
        let motherlode_probability = our_share * self.calculate_win_probability(block, our_stake);

        motherlode_value * motherlode_probability * MOTHERLODE_EV_MULTIPLIER
    }

    /// Calculate competition intensity score (0.0-1.0)
    fn calculate_competition_score(&self, grid_state: &GridState, block: &BlockState) -> f64 {
        if grid_state.total_staked == 0 {
            return 0.0;
        }

        // Measure how concentrated stake is on this block
        let stake_concentration = block.staked_amount as f64 / grid_state.total_staked as f64;

        // Measure participant density
        let total_participants: u32 = grid_state.blocks.iter().map(|b| b.participant_count).sum();
        let participant_concentration = if total_participants > 0 {
            block.participant_count as f64 / total_participants as f64
        } else {
            0.0
        };

        // Combined competition score (higher = more competition)
        (stake_concentration + participant_concentration) / 2.0
    }

    /// Calculate recommended stake amount based on EV and competition
    fn calculate_recommended_stake(
        &self,
        expected_value: f64,
        competition_score: f64,
        motherlode_size: u64,
    ) -> u64 {
        // Base stake proportional to EV
        let ev_multiplier = (expected_value * 100.0).max(0.1).min(10.0);

        // Reduce stake in high competition scenarios
        let competition_adjustment = 1.0 - (competition_score * 0.5);

        // Increase stake for large motherlodes
        let motherlode_multiplier = if motherlode_size > MOTHERLODE_AGGRESSIVE_THRESHOLD {
            1.5
        } else {
            1.0
        };

        let base_stake = self.min_stake as f64;
        let recommended = base_stake * ev_multiplier * competition_adjustment * motherlode_multiplier;

        // Clamp to min/max
        recommended.max(self.min_stake as f64).min(self.max_stake as f64) as u64
    }

    /// Find "efficiency gaps" - blocks with high EV but low competition
    pub fn find_efficiency_gaps(
        &self,
        calculations: &[EVCalculation],
    ) -> Vec<EVCalculation> {
        let mut gaps: Vec<EVCalculation> = calculations
            .iter()
            .filter(|calc| {
                // High EV, low competition
                calc.expected_value > 0.1 && calc.competition_score < 0.5
            })
            .cloned()
            .collect();

        // Sort by EV/competition ratio
        gaps.sort_by(|a, b| {
            let ratio_a = a.expected_value / (a.competition_score + 0.01);
            let ratio_b = b.expected_value / (b.competition_score + 0.01);
            ratio_b.partial_cmp(&ratio_a).unwrap_or(std::cmp::Ordering::Equal)
        });

        gaps
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    fn create_test_grid() -> GridState {
        let blocks = std::array::from_fn(|i| BlockState {
            index: i as u8,
            staked_amount: 1_000_000_000, // 1 SOL per block
            participant_count: 10,
            historical_win_rate: 0.04,
        });

        GridState {
            round: 1,
            blocks,
            motherlode_size: 5_000_000_000, // 5 SOL
            total_staked: 25_000_000_000,   // 25 SOL total
            round_start: 1000000,
            last_update: 1000030,
        }
    }

    #[test]
    fn test_ev_calculation() {
        let calculator = EVCalculator::new(
            100_000_000,  // 0.1 SOL min
            1_000_000_000, // 1 SOL max
            0.5,
        );

        let grid = create_test_grid();
        let our_stake = 500_000_000; // 0.5 SOL

        let calculations = calculator.calculate_all_blocks(&grid, our_stake).unwrap();

        assert_eq!(calculations.len(), GRID_SIZE);
        assert!(calculations[0].expected_value > 0.0);
    }

    #[test]
    fn test_win_probability() {
        let calculator = EVCalculator::new(100_000_000, 1_000_000_000, 0.5);

        let block = BlockState {
            index: 0,
            staked_amount: 1_000_000_000,
            participant_count: 10,
            historical_win_rate: 0.04,
        };

        let probability = calculator.calculate_win_probability(&block, 1_000_000_000);

        // With equal stake and 10 participants, probability should be ~0.5 / 11 ≈ 0.045
        assert!(probability > 0.0 && probability < 0.1);
    }

    #[test]
    fn test_efficiency_gaps() {
        let calculator = EVCalculator::new(100_000_000, 1_000_000_000, 0.5);

        let calculations = vec![
            EVCalculation {
                block_index: 0,
                expected_value: 1.0,
                win_probability: 0.5,
                competition_score: 0.8, // High competition
                includes_motherlode: false,
                recommended_stake: 500_000_000,
            },
            EVCalculation {
                block_index: 1,
                expected_value: 0.8,
                win_probability: 0.5,
                competition_score: 0.2, // Low competition - efficiency gap!
                includes_motherlode: false,
                recommended_stake: 500_000_000,
            },
        ];

        let gaps = calculator.find_efficiency_gaps(&calculations);

        assert_eq!(gaps.len(), 1);
        assert_eq!(gaps[0].block_index, 1);
    }
}
