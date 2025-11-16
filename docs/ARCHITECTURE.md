# Architecture Documentation

## System Overview

The ORE V2 Dominance Bot is built on a distributed "Bus" architecture that separates compute-intensive mining ("Labor") from strategic decision-making ("Management").

## Core Design Principles

1. **Separation of Concerns**: Mining and strategy are completely decoupled
2. **Horizontal Scalability**: Add more GPU workers without touching strategy code
3. **Real-Time State**: Sub-second grid state monitoring via WebSocket
4. **Information Asymmetry**: Mempool monitoring for competitive advantage
5. **Guaranteed Execution**: Jito bundles ensure transactions land

## Component Architecture

### 1. Miner Workers (`ore-miner`)

**Purpose**: Find valid Drillx hash solutions

**Technology**:
- Rust for orchestration
- C++/CUDA for GPU acceleration
- FFI bridge between Rust and CUDA

**Flow**:
```
1. Fetch current challenge from Redis
2. Run solver (GPU-accelerated)
3. Publish solution to Redis channel
4. Update heartbeat
5. Repeat
```

**Scaling**:
- Deploy N workers across different machines
- Each worker reports to the same Redis instance
- Bus selects the best solution from all workers

### 2. Bus/Dispatcher (`ore-bus`)

**Purpose**: Central orchestrator that makes all strategic decisions

**Responsibilities**:
- Consume mining solutions from workers
- Monitor grid state in real-time
- Track mempool for pending transactions
- Calculate optimal strategy
- Execute Jito bundles

**Main Loop**:
```rust
loop {
    // Wait for new round
    wait_for_round_start();

    // Get grid state
    let grid = state_monitor.get_current_state();

    // Wait for mining solution
    let solution = wait_for_solution();

    // Build shadow board from mempool
    let shadow = build_shadow_board();

    // Make strategic decision
    let decision = strategist.decide(grid, shadow);

    // Execute based on mode
    match decision.mode {
        Sniper => wait_until_last_second(),
        _ => ()
    }

    execute_bundle(solution, decision);
}
```

### 3. State Monitor (`ore-state-monitor`)

**Purpose**: Real-time grid state tracking

**Technology**:
- WebSocket for low-latency updates
- Geyser plugin support (optional, even lower latency)

**Updates**:
- Every account change triggers an update
- Parses on-chain grid state
- Publishes to Redis for Bus consumption

### 4. Strategist (`ore-strategist`)

**Purpose**: Game theory and EV calculation

**Modules**:

#### a) EV Calculator
Calculates expected value for each of 25 blocks:

```
EV = (Block_Reward × Win_Probability) + (Motherlode × Motherlode_Probability)

Win_Probability = (Your_Stake / Total_Block_Stake) / Participant_Count

Competition_Score = (Block_Stake / Total_Grid_Stake + Block_Participants / Total_Participants) / 2
```

#### b) Shadow Board
Predicts future state from mempool:

```
Confirmed_State + Pending_Transactions → Predicted_State

Confidence = f(num_pending_txs)
```

Detects:
- **Stake Traps**: Blocks with >50% stake increase
- **Hidden Gems**: Below-average stake, <2 pending txs

#### c) Decision Engine
Combines EV + Shadow Board → Strategic Decision

```
Mode Selection:
- Motherlode > 1 SOL → Aggressive
- Time remaining ≤ 5s → Sniper
- Otherwise → Normal

Block Selection:
1. Calculate EV for all blocks
2. Filter out stake traps
3. Find efficiency gaps (high EV/Competition ratio)
4. Select best block
```

### 5. Jito Integration (`ore-jito`)

**Purpose**: MEV execution and mempool monitoring

**Components**:

#### a) Bundle Builder
Constructs atomic transaction bundles:
```
Bundle = [
    Tip_Transaction(Jito),
    Mine_Transaction(solution),
    Stake_Transaction(block, amount)
]
```

#### b) Jito Client
Submits bundles with retry logic:
```rust
async fn send_bundle_with_retry(bundle, max_retries) {
    for attempt in 0..max_retries {
        match jito_client.send_bundle(bundle) {
            Ok(id) => return Ok(id),
            Err(e) => {
                sleep(exponential_backoff(attempt));
            }
        }
    }
}
```

#### c) Mempool Monitor
Tracks pending transactions:
- Subscribe to Jito mempool stream
- Filter for ORE V2 program transactions
- Parse block_index and stake_amount
- Feed to Shadow Board

### 6. Treasury Manager (`ore-treasury`)

**Purpose**: Automated profit management

**Functions**:

1. **Auto-Staking**
   ```
   Every hour:
   - Check current stake multiplier
   - If < target (2.0x):
       - Claim all ORE rewards
       - Stake to increase multiplier
   ```

2. **Metrics Tracking**
   ```
   Track:
   - Total rounds played/won
   - Total ORE earned
   - Total SOL spent
   - Current ROI
   - Win rate
   ```

3. **Profit Taking**
   ```
   If ROI > threshold:
   - Liquidate ORE for SOL
   - Maintain SOL reserve for operations
   ```

## Data Flow

```
Miners → Redis → Bus → Decision → Jito → On-Chain
  ↓                       ↑
  └────── Solutions ──────┘

WebSocket → State Monitor → Redis → Bus
                                      ↓
Mempool → Shadow Board ───────────────┘
```

## Redis Channels

| Channel | Purpose | Publisher | Subscriber |
|---------|---------|-----------|------------|
| `ore:solutions` | Mining solutions | Miners | Bus |
| `ore:grid_state` | Grid state updates | State Monitor | Bus |
| `ore:commands` | Control commands | User/Admin | All |

## Redis Keys

| Key | Type | Purpose |
|-----|------|---------|
| `ore:best_solution` | String | Current best solution |
| `ore:current_round` | String | Current round number |
| `ore:metrics` | Hash | Performance metrics |
| `ore:worker:<id>:heartbeat` | String (TTL) | Worker health |

## Concurrency Model

- **Miners**: Blocking (CPU/GPU intensive)
- **Bus**: Async/await with Tokio
- **State Monitor**: Async WebSocket streams
- **Mempool**: Async polling/streaming

## Failure Handling

### Miner Failure
- Workers send heartbeats every 30s
- Bus tracks worker health
- If worker dies, others continue
- Alert if all workers down

### Bus Failure
- Critical: Requires restart
- Redis persists state
- Can resume from last round

### State Monitor Failure
- Auto-reconnect with exponential backoff
- Falls back to polling if WebSocket fails

### Jito Submission Failure
- Retry with exponential backoff (max 3 attempts)
- Increase tip on retry
- Skip round if all retries fail

## Performance Characteristics

| Component | Latency | Throughput |
|-----------|---------|------------|
| GPU Mining | 5-15s per solution | ~10M hashes/s |
| State Updates | <100ms | 100 updates/s |
| Mempool Monitor | <500ms | 50 txs/s |
| Strategy Decision | <50ms | N/A |
| Jito Submission | 200-500ms | N/A |

## Security Considerations

### Attack Surface

1. **Redis**: Unauthenticated by default
   - **Mitigation**: Run on localhost only, or use AUTH

2. **Wallet Keys**: Stored on disk
   - **Mitigation**: Encrypt at rest, restrict file permissions

3. **Strategy Leakage**: Logs may reveal strategy
   - **Mitigation**: Disable debug logs in production

4. **RPC Rate Limiting**: May expose bot presence
   - **Mitigation**: Use multiple endpoints, run own validator

### Operational Security

1. **Network Isolation**: Run on dedicated server
2. **Access Control**: Minimal attack surface
3. **Monitoring**: Alert on anomalies
4. **Secrets Management**: Never commit .env or wallets

## Future Enhancements

### Planned
- [ ] Geyser plugin for sub-100ms state updates
- [ ] Machine learning for win probability prediction
- [ ] Multi-wallet support for position sizing
- [ ] Dynamic difficulty adjustment based on round timing

### Research
- [ ] Flash loan integration for larger stakes
- [ ] Cross-protocol arbitrage (ORE V1 ↔ V2)
- [ ] Validator integration for zero-latency mempool access

## Testing Strategy

### Unit Tests
- Each crate has comprehensive unit tests
- EV calculator validated against known scenarios
- Shadow board logic tested with synthetic data

### Integration Tests
- Full system test on devnet
- Simulated grid state updates
- Mock Jito submissions

### Load Tests
- N miners submitting solutions
- High-frequency state updates
- Mempool flood scenarios

## Deployment Architecture

### Single-Machine Setup
```
┌────────────────────────┐
│   Single Server        │
│                        │
│  ┌──────────────────┐  │
│  │  Redis           │  │
│  └──────────────────┘  │
│  ┌──────────────────┐  │
│  │  Bus             │  │
│  └──────────────────┘  │
│  ┌──────────────────┐  │
│  │  Miner (GPU 0)   │  │
│  └──────────────────┘  │
│  ┌──────────────────┐  │
│  │  Miner (GPU 1)   │  │
│  └──────────────────┘  │
└────────────────────────┘
```

### Distributed Setup
```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ GPU Server 1│      │ GPU Server 2│      │ GPU Server N│
│             │      │             │      │             │
│ Miner 1-4   │      │ Miner 5-8   │      │ Miner N...  │
└─────────────┘      └─────────────┘      └─────────────┘
       │                    │                    │
       └────────────────────┴────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Central Server│
                    │                │
                    │  Redis         │
                    │  Bus           │
                    │  State Monitor │
                    └────────────────┘
```

## Conclusion

This architecture prioritizes:
- **Performance**: GPU acceleration, low-latency state
- **Reliability**: Redundancy, failure handling
- **Security**: Minimal attack surface, OpSec best practices
- **Scalability**: Horizontal worker scaling
- **Competitive Advantage**: Information asymmetry via mempool

The "Bus" model ensures the strategic "brain" can make optimal decisions based on the freshest data from distributed "labor" (miners).
