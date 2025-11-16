use anyhow::Result;
use ndarray::{Array1, Array2};
use ore_common::GridState;
use tracing::info;

use crate::data_collector::HistoricalRound;

/// ML-based win probability predictor
///
/// Uses historical data to predict which blocks are most likely to win
pub struct WinPredictor {
    /// Trained model weights
    weights: Option<Array1<f64>>,
    /// Feature means for normalization
    feature_means: Option<Array1<f64>>,
    /// Feature standard deviations for normalization
    feature_stds: Option<Array1<f64>>,
}

impl WinPredictor {
    pub fn new() -> Self {
        Self {
            weights: None,
            feature_means: None,
            feature_stds: None,
        }
    }

    /// Train the model on historical data
    pub fn train(&mut self, historical_rounds: &[HistoricalRound]) -> Result<()> {
        if historical_rounds.is_empty() {
            return Ok(());
        }

        info!("Training win predictor on {} rounds", historical_rounds.len());

        // Extract features and labels
        let n_samples = historical_rounds.len() * 25; // 25 blocks per round
        let n_features = 8;

        let mut features = Array2::<f64>::zeros((n_samples, n_features));
        let mut labels = Array1::<f64>::zeros(n_samples);

        let mut sample_idx = 0;
        for round in historical_rounds {
            for block_idx in 0..25 {
                // Feature engineering
                let stake_on_block = round.block_stakes.get(block_idx).copied().unwrap_or(0);
                let participants = round.participant_counts.get(block_idx).copied().unwrap_or(0);

                let stake_ratio = if round.total_staked > 0 {
                    stake_on_block as f64 / round.total_staked as f64
                } else {
                    0.0
                };

                let participant_ratio = if round.participant_counts.iter().sum::<u32>() > 0 {
                    participants as f64 / round.participant_counts.iter().sum::<u32>() as f64
                } else {
                    0.0
                };

                // Features:
                // 0: Block index (position)
                // 1: Stake ratio
                // 2: Participant ratio
                // 3: Average stake per participant
                // 4: Motherlode size (normalized)
                // 5: Total staked (normalized)
                // 6: Competition intensity (stake * participants)
                // 7: Block neighborhood effect (average of adjacent blocks)

                features[[sample_idx, 0]] = block_idx as f64 / 25.0;
                features[[sample_idx, 1]] = stake_ratio;
                features[[sample_idx, 2]] = participant_ratio;
                features[[sample_idx, 3]] = if participants > 0 {
                    stake_on_block as f64 / participants as f64
                } else {
                    0.0
                };
                features[[sample_idx, 4]] = (round.motherlode_size as f64).ln() / 20.0; // log scale
                features[[sample_idx, 5]] = (round.total_staked as f64).ln() / 20.0; // log scale
                features[[sample_idx, 6]] = stake_ratio * participant_ratio;

                // Neighborhood effect
                let mut neighbor_stakes = 0.0;
                let mut neighbor_count = 0;
                for neighbor_offset in [-5i32, -1, 1, 5] {
                    let neighbor_idx = block_idx as i32 + neighbor_offset;
                    if neighbor_idx >= 0 && neighbor_idx < 25 {
                        if let Some(&stake) = round.block_stakes.get(neighbor_idx as usize) {
                            neighbor_stakes += stake as f64;
                            neighbor_count += 1;
                        }
                    }
                }
                features[[sample_idx, 7]] = if neighbor_count > 0 {
                    neighbor_stakes / (neighbor_count as f64 * round.total_staked as f64)
                } else {
                    0.0
                };

                // Label: 1 if this block won, 0 otherwise
                labels[sample_idx] = if block_idx as u8 == round.winning_block {
                    1.0
                } else {
                    0.0
                };

                sample_idx += 1;
            }
        }

        // Normalize features
        let feature_means = features.mean_axis(ndarray::Axis(0)).unwrap();
        let feature_stds = features.std_axis(ndarray::Axis(0), 1.0);

        for i in 0..n_samples {
            for j in 0..n_features {
                if feature_stds[j] > 0.0 {
                    features[[i, j]] = (features[[i, j]] - feature_means[j]) / feature_stds[j];
                }
            }
        }

        // Train logistic regression using gradient descent
        let mut weights = Array1::<f64>::zeros(n_features);
        let learning_rate = 0.01;
        let n_iterations = 1000;

        for iteration in 0..n_iterations {
            let mut gradient = Array1::<f64>::zeros(n_features);

            for i in 0..n_samples {
                let features_i = features.row(i);
                let prediction = sigmoid(features_i.dot(&weights));
                let error = prediction - labels[i];

                for j in 0..n_features {
                    gradient[j] += error * features_i[j];
                }
            }

            // Update weights
            for j in 0..n_features {
                weights[j] -= learning_rate * gradient[j] / n_samples as f64;
            }

            // Log progress
            if iteration % 100 == 0 {
                let loss = self.calculate_loss(&features, &labels, &weights);
                info!("Iteration {}: Loss = {:.4}", iteration, loss);
            }
        }

        self.weights = Some(weights);
        self.feature_means = Some(feature_means);
        self.feature_stds = Some(feature_stds);

        info!("Training complete");

        Ok(())
    }

    /// Predict win probabilities for all blocks in current grid state
    pub fn predict(&self, grid_state: &GridState) -> Result<Vec<f64>> {
        let weights = self.weights.as_ref()
            .ok_or_else(|| anyhow::anyhow!("Model not trained yet"))?;
        let means = self.feature_means.as_ref().unwrap();
        let stds = self.feature_stds.as_ref().unwrap();

        let mut probabilities = Vec::with_capacity(25);

        for block_idx in 0..25 {
            let block = &grid_state.blocks[block_idx];

            // Extract features (same as training)
            let stake_ratio = if grid_state.total_staked > 0 {
                block.staked_amount as f64 / grid_state.total_staked as f64
            } else {
                0.0
            };

            let total_participants: u32 = grid_state.blocks.iter()
                .map(|b| b.participant_count)
                .sum();

            let participant_ratio = if total_participants > 0 {
                block.participant_count as f64 / total_participants as f64
            } else {
                0.0
            };

            let mut features = Array1::<f64>::zeros(8);
            features[0] = block_idx as f64 / 25.0;
            features[1] = stake_ratio;
            features[2] = participant_ratio;
            features[3] = if block.participant_count > 0 {
                block.staked_amount as f64 / block.participant_count as f64
            } else {
                0.0
            };
            features[4] = (grid_state.motherlode_size as f64).ln() / 20.0;
            features[5] = (grid_state.total_staked as f64).ln() / 20.0;
            features[6] = stake_ratio * participant_ratio;

            // Neighborhood effect
            let mut neighbor_stakes = 0.0;
            let mut neighbor_count = 0;
            for neighbor_offset in [-5i32, -1, 1, 5] {
                let neighbor_idx = block_idx as i32 + neighbor_offset;
                if neighbor_idx >= 0 && neighbor_idx < 25 {
                    let neighbor = &grid_state.blocks[neighbor_idx as usize];
                    neighbor_stakes += neighbor.staked_amount as f64;
                    neighbor_count += 1;
                }
            }
            features[7] = if neighbor_count > 0 && grid_state.total_staked > 0 {
                neighbor_stakes / (neighbor_count as f64 * grid_state.total_staked as f64)
            } else {
                0.0
            };

            // Normalize
            for j in 0..8 {
                if stds[j] > 0.0 {
                    features[j] = (features[j] - means[j]) / stds[j];
                }
            }

            // Predict
            let probability = sigmoid(features.dot(weights));
            probabilities.push(probability);
        }

        // Normalize probabilities to sum to 1
        let sum: f64 = probabilities.iter().sum();
        if sum > 0.0 {
            for p in &mut probabilities {
                *p /= sum;
            }
        }

        Ok(probabilities)
    }

    fn calculate_loss(&self, features: &Array2<f64>, labels: &Array1<f64>, weights: &Array1<f64>) -> f64 {
        let n_samples = features.nrows();
        let mut loss = 0.0;

        for i in 0..n_samples {
            let prediction = sigmoid(features.row(i).dot(weights));
            loss += -(labels[i] * prediction.ln() + (1.0 - labels[i]) * (1.0 - prediction).ln());
        }

        loss / n_samples as f64
    }

    /// Get model performance metrics
    pub fn get_accuracy(&self, historical_rounds: &[HistoricalRound]) -> Result<f64> {
        if self.weights.is_none() {
            return Ok(0.0);
        }

        let mut correct = 0;
        let total = historical_rounds.len();

        // This is a simplified accuracy check
        // In production, you'd use a proper train/test split

        info!("Model accuracy: Would be calculated on test set");

        Ok(0.0) // Placeholder
    }
}

fn sigmoid(x: f64) -> f64 {
    1.0 / (1.0 + (-x).exp())
}
