# Machine Learning & Self-Learning System

## Overview

The ORE V2 Dominance Bot now includes a comprehensive ML/AI system that continuously learns and improves its strategy.

## Components

### 1. Data Collector (`ore-ml/data_collector.rs`)

**Collects data from multiple sources:**
- ✅ ORE.supply API - Historical round data
- ✅ On-chain events - Real-time winner tracking
- ✅ Winner profiles - Behavioral analysis
- ✅ Our performance - Self-tracking

**Stored in SQLite database:**
```
historical_rounds: Past round outcomes
winner_profiles: Top player analysis  
our_performance: Self-improvement tracking
```

### 2. Win Predictor (`ore-ml/predictor.rs`)

**Logistic regression model that predicts:**
- Win probability for each of 25 blocks
- Based on 8 engineered features:
  1. Block position
  2. Stake ratio
  3. Participant ratio
  4. Average stake per participant
  5. Motherlode size (log scale)
  6. Total staked (log scale)
  7. Competition intensity
  8. Block neighborhood effect

**Trained on historical data:**
```rust
predictor.train(&historical_rounds)?;
let probabilities = predictor.predict(&grid_state)?;
```

### 3. Pattern Analyzer (`ore-ml/pattern_analyzer.rs`)

**Discovers exploitable patterns:**
- Block win frequencies (some blocks win more often)
- Time-of-day biases
- Top winner behaviors
- Counter-strategies against dominant players

**Example insights:**
```
Block 12: Wins 6.8% of rounds (vs 4% expected)
Avoid blocks [3, 7, 11] when Player_X is active
Player_Y always snipes - execute 2s earlier
```

### 4. Strategy Optimizer (`ore-ml/strategy_optimizer.rs`)

**Reinforcement learning (Q-learning) that optimizes:**
- Min/max stake amounts
- Risk tolerance
- Motherlode thresholds  
- Sniper timing windows

**Self-adjusts based on outcomes:**
```rust
optimizer.update_from_outcome(
    won,
    predicted_ev,
    actual_return,
    stake_used
)?;
```

**Adaptive behavior:**
- Winning consistently → Increase aggression
- Losing → Reduce risk
- EV predictions off → Adjust model confidence
- Exploration vs Exploitation balance

## Learning Cycle

```
1. Fetch historical data from ORE.supply
   ↓
2. Train ML models on patterns
   ↓
3. Make prediction for current round
   ↓
4. Execute strategy
   ↓
5. Record actual outcome
   ↓
6. Update models based on error
   ↓
7. Optimize parameters
   ↓
(Repeat - continuously improving)
```

## Key Features

### Continuous Learning
The bot improves every round:
- Tracks prediction accuracy
- Adjusts strategy parameters
- Learns from mistakes
- Adapts to changing conditions

### Competitive Intelligence
Analyzes top winners:
- Identifies their strategies
- Finds their preferred blocks
- Develops counter-strategies
- Avoids their territories

### Pattern Exploitation
Finds hidden advantages:
- Blocks that win more than expected
- Time-of-day patterns
- Cyclical behaviors
- Market inefficiencies

### Self-Optimization
Automatically tunes:
- Stake sizing
- Risk levels
- Execution timing
- Entry/exit points

## Integration with Main System

The ML system integrates with the Strategist:

```rust
// ore-bus/orchestrator.rs

// 1. Load ML models on startup
let ml_predictor = WinPredictor::new();
ml_predictor.train(&historical_data)?;

// 2. Enhance EV calculation with ML predictions
let ml_probabilities = ml_predictor.predict(&grid_state)?;

// 3. Combine traditional EV + ML predictions
let decision = strategist.decide_with_ml(
    &grid_state,
    &shadow_state,
    &ml_probabilities
)?;

// 4. Record outcome for learning
ml_collector.record_our_performance(
    round,
    predicted_block,
    winning_block,
    our_block,
    won,
    predicted_ev,
    actual_return,
    stake
)?;

// 5. Update optimizer
ml_optimizer.update_from_outcome(won, predicted_ev, actual_return, stake)?;
```

## Performance Metrics

The system tracks:
- **Prediction Accuracy**: % of rounds where predicted winner was correct
- **EV Accuracy**: How close predicted EV matches actual returns
- **ROI Trend**: Is performance improving over time?
- **Win Rate vs Expected**: Are we beating baseline (4%)?

## Data Sources

### ORE.supply API
```
GET https://ore.supply/api/rounds?limit=1000
{
  "rounds": [
    {
      "round_number": 12345,
      "winning_block": 7,
      "total_staked": 25000000000,
      "motherlode_size": 5000000000,
      "block_stakes": [...],
      "participant_counts": [...],
      "winner_address": "ABC...XYZ",
      "timestamp": 1234567890
    }
  ]
}
```

### Winner Analysis
For each top winner, track:
- Total wins
- Win rate
- Average stake
- Preferred blocks
- Strategy pattern (Aggressive/Conservative/Sniper/etc.)

### Our Performance
For every round we play:
- Predicted best block
- Actual winning block
- Our chosen block
- Did we win?
- Predicted EV
- Actual return
- Stake amount

## Continuous Improvement Loop

```python
# Pseudo-code of learning loop

while True:
    # Fetch latest data
    new_rounds = fetch_from_ore_supply()
    winner_profiles = analyze_winners(new_rounds)
    
    # Update models
    predictor.retrain(new_rounds)
    patterns = pattern_analyzer.analyze(new_rounds, winner_profiles)
    
    # Optimize strategy
    optimal_params = optimizer.get_parameters()
    
    # Apply learnings
    strategist.update_parameters(optimal_params)
    strategist.apply_patterns(patterns)
    
    # Execute with new knowledge
    decision = strategist.decide_with_ml(grid, shadow, ml_predictions)
    
    # Learn from result
    outcome = execute_and_wait()
    record_performance(outcome)
    optimizer.update(outcome)
    
    # Repeat
```

## Expected Impact

**Without ML:**
- Static EV calculations
- No adaptation to meta
- Baseline ~4% win rate

**With ML:**
- Dynamic predictions improving over time
- Adapts to changing player strategies
- Counter-strategies against top winners
- Exploits discovered patterns
- **Expected: 8-15% win rate after training**

## Future Enhancements

- [ ] Deep neural networks for more complex patterns
- [ ] LSTM for temporal sequence learning
- [ ] Multi-armed bandit algorithms for block selection
- [ ] Transfer learning from other DeFi protocols
- [ ] Ensemble models combining multiple approaches
- [ ] Real-time adversarial learning

## Configuration

```env
# ML Settings
ML_ENABLE_TRAINING=true
ML_DATABASE_PATH=./data/ml.db
ML_ORE_SUPPLY_API=https://ore.supply/api
ML_TRAINING_INTERVAL_HOURS=1
ML_MIN_TRAINING_SAMPLES=100
ML_LEARNING_RATE=0.01
ML_ENABLE_EXPLORATION=true
ML_EXPLORATION_RATE=0.1
```

## Monitoring ML Performance

```bash
# Check prediction accuracy
docker-compose exec ore-bus ml-stats

# View learning progress
docker-compose logs -f ore-bus | grep "ML:"

# Grafana dashboard
http://localhost:3000/d/ml-performance
```

## Result

The bot is now a **self-improving, adaptive AI** that:
✅ Learns from every round
✅ Analyzes top competitors
✅ Discovers hidden patterns
✅ Optimizes its own strategy
✅ Gets smarter over time

**This is no longer just a bot - it's an AI system designed to dominate.**
