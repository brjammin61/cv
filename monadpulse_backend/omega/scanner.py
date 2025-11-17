"""
Omega Engine - Block Scanner
Scans Monad blocks in real-time for MEV opportunities
"""

import asyncio
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from web3 import Web3
from web3.types import BlockData, TxData

from .models import MEVOpportunity, BlockData as BlockDataModel
from .db_utils import omega_db_session

logger = logging.getLogger(__name__)


class OmegaScanner:
    """
    Real-time block scanner for MEV opportunity detection
    """
    
    def __init__(self, rpc_url: str = None):
        """
        Initialize scanner with Monad RPC connection
        
        Args:
            rpc_url: Monad RPC endpoint (defaults to env var)
        """
        self.rpc_url = rpc_url or os.environ.get('MONAD_RPC_URL', 'http://localhost:8545')
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.latest_scanned_block = 0
        self.is_scanning = False
        
        # MEV detection configuration
        self.min_arbitrage_profit = 10.0  # Minimum profit to consider (USD)
        self.min_liquidation_profit = 50.0
        self.min_sandwich_profit = 5.0
        
        logger.info(f"OMEGA SCANNER: Initialized with RPC: {self.rpc_url}")
    
    async def start_continuous_scan(self, start_block: int = None):
        """
        Start continuous block scanning
        
        Args:
            start_block: Block number to start from (None = latest)
        """
        if self.is_scanning:
            logger.warning("OMEGA SCANNER: Already scanning")
            return
        
        self.is_scanning = True
        
        if start_block is None:
            try:
                start_block = self.w3.eth.block_number
            except Exception as e:
                logger.error(f"OMEGA SCANNER: Failed to get latest block: {e}")
                start_block = 0
        
        self.latest_scanned_block = start_block
        
        logger.info(f"OMEGA SCANNER: Starting continuous scan from block {start_block}")
        
        while self.is_scanning:
            try:
                current_block = self.w3.eth.block_number
                
                # Scan any new blocks
                while self.latest_scanned_block < current_block:
                    self.latest_scanned_block += 1
                    
                    await self.scan_block(self.latest_scanned_block)
                    
                    # Log progress every 100 blocks
                    if self.latest_scanned_block % 100 == 0:
                        logger.info(f"OMEGA SCANNER: Processed block {self.latest_scanned_block}")
                
                # Wait for next block (2 seconds on Monad)
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"OMEGA SCANNER: Error in continuous scan: {e}")
                await asyncio.sleep(5)
    
    def stop_scan(self):
        """Stop continuous scanning"""
        self.is_scanning = False
        logger.info("OMEGA SCANNER: Stopped")
    
    async def scan_block(self, block_number: int) -> Dict:
        """
        Scan a single block for MEV opportunities
        
        Args:
            block_number: Block number to scan
            
        Returns:
            Dictionary with scan results
        """
        try:
            # Fetch full block with transactions
            block = self.w3.eth.get_block(block_number, full_transactions=True)
            
            validator_address = self._get_block_validator(block)
            mev_opportunities = []
            
            # Analyze each transaction for MEV patterns
            for i, tx in enumerate(block.transactions):
                # Check for different MEV types
                mev = self._detect_mev_in_tx(tx, i, block.transactions)
                
                if mev:
                    mev['block_number'] = block_number
                    mev['validator_address'] = validator_address
                    mev['timestamp'] = datetime.fromtimestamp(block.timestamp)
                    mev_opportunities.append(mev)
            
            # Store results in database
            await self._store_block_data(block, validator_address, mev_opportunities)
            
            if mev_opportunities:
                logger.info(
                    f"OMEGA SCANNER: Block {block_number} - "
                    f"Found {len(mev_opportunities)} MEV opportunities"
                )
            
            return {
                'block_number': block_number,
                'validator': validator_address,
                'mev_count': len(mev_opportunities),
                'total_profit': sum(mev['profit_estimate'] for mev in mev_opportunities)
            }
            
        except Exception as e:
            logger.error(f"OMEGA SCANNER: Error scanning block {block_number}: {e}")
            return {'block_number': block_number, 'error': str(e)}
    
    def _detect_mev_in_tx(self, tx: TxData, index: int, all_txs: List[TxData]) -> Optional[Dict]:
        """
        Detect MEV patterns in a transaction
        
        Args:
            tx: Transaction to analyze
            index: Position in block
            all_txs: All transactions in block
            
        Returns:
            MEV opportunity dict or None
        """
        # Pattern 1: Arbitrage
        arb = self._detect_arbitrage(tx, all_txs)
        if arb and arb['profit_estimate'] >= self.min_arbitrage_profit:
            return arb
        
        # Pattern 2: Liquidation
        liq = self._detect_liquidation(tx)
        if liq and liq['profit_estimate'] >= self.min_liquidation_profit:
            return liq
        
        # Pattern 3: Sandwich attack
        sandwich = self._detect_sandwich(tx, index, all_txs)
        if sandwich and sandwich['profit_estimate'] >= self.min_sandwich_profit:
            return sandwich
        
        # Pattern 4: JIT Liquidity
        jit = self._detect_jit_liquidity(tx, index, all_txs)
        if jit:
            return jit
        
        return None
    
    def _detect_arbitrage(self, tx: TxData, all_txs: List[TxData]) -> Optional[Dict]:
        """
        Detect arbitrage opportunities
        
        Arbitrage = buying asset on DEX A and selling on DEX B in same block
        """
        # Look for DEX swap function signatures
        swap_signatures = [
            '0x38ed1739',  # swapExactTokensForTokens (Uniswap V2)
            '0x8803dbee',  # swapTokensForExactTokens
            '0x7ff36ab5',  # swapExactETHForTokens
            '0x18cbafe5',  # swapExactTokensForETH
        ]
        
        if not tx.input or len(tx.input) < 10:
            return None
        
        func_sig = tx.input[:10]
        
        if func_sig not in swap_signatures:
            return None
        
        # Check if same address made multiple swaps in this block
        same_sender_swaps = [
            t for t in all_txs 
            if t['from'] == tx['from'] and len(t.input) >= 10 and t.input[:10] in swap_signatures
        ]
        
        if len(same_sender_swaps) >= 2:
            # Likely arbitrage - estimate profit
            # (In production, decode the swap amounts and calculate actual profit)
            estimated_profit = self._estimate_arbitrage_profit(same_sender_swaps)
            
            return {
                'tx_hash': tx.hash.hex(),
                'mev_type': 'arbitrage',
                'profit_estimate': estimated_profit,
                'metadata': {
                    'swap_count': len(same_sender_swaps),
                    'from': tx['from'],
                    'gas_price': tx.gasPrice
                }
            }
        
        return None
    
    def _detect_liquidation(self, tx: TxData) -> Optional[Dict]:
        """
        Detect liquidation transactions
        
        Liquidations = calling liquidate() on lending protocols
        """
        # Common liquidation function signatures
        liquidation_signatures = [
            '0x96cd4ddb',  # liquidate (Compound)
            '0xf5e3c462',  # liquidateBorrow
            '0x0f4c06d9',  # liquidationCall (Aave)
        ]
        
        if not tx.input or len(tx.input) < 10:
            return None
        
        func_sig = tx.input[:10]
        
        if func_sig in liquidation_signatures:
            # Liquidation detected - estimate profit from liquidation bonus
            # (Typically 5-10% of liquidated amount)
            estimated_profit = self._estimate_liquidation_profit(tx)
            
            return {
                'tx_hash': tx.hash.hex(),
                'mev_type': 'liquidation',
                'profit_estimate': estimated_profit,
                'metadata': {
                    'function': func_sig,
                    'gas_price': tx.gasPrice,
                    'to': tx.to
                }
            }
        
        return None
    
    def _detect_sandwich(self, tx: TxData, index: int, all_txs: List[TxData]) -> Optional[Dict]:
        """
        Detect sandwich attacks
        
        Sandwich = front-run + victim + back-run
        Pattern: Tx[i-1] and Tx[i+1] from same address, Tx[i] from different address
        """
        if index == 0 or index >= len(all_txs) - 1:
            return None
        
        prev_tx = all_txs[index - 1]
        next_tx = all_txs[index + 1]
        
        # Check if prev and next are from same address (sandwicher)
        # and current tx is from different address (victim)
        if (prev_tx['from'] == next_tx['from'] and 
            prev_tx['from'] != tx['from'] and
            self._is_swap_tx(prev_tx) and 
            self._is_swap_tx(next_tx)):
            
            # Sandwich detected - estimate profit
            estimated_profit = self._estimate_sandwich_profit(prev_tx, tx, next_tx)
            
            return {
                'tx_hash': tx.hash.hex(),
                'mev_type': 'sandwich',
                'profit_estimate': estimated_profit,
                'metadata': {
                    'victim_tx': tx.hash.hex(),
                    'front_run_tx': prev_tx.hash.hex(),
                    'back_run_tx': next_tx.hash.hex(),
                    'sandwicher': prev_tx['from']
                }
            }
        
        return None
    
    def _detect_jit_liquidity(self, tx: TxData, index: int, all_txs: List[TxData]) -> Optional[Dict]:
        """
        Detect Just-In-Time liquidity provision
        
        JIT = add liquidity right before large swap, remove after
        """
        # Look for addLiquidity followed by removeLiquidity
        add_liq_sigs = ['0xe8e33700', '0xf305d719']  # addLiquidity functions
        remove_liq_sigs = ['0xbaa2abde', '0x02751cec']  # removeLiquidity functions
        
        if not tx.input or len(tx.input) < 10:
            return None
        
        func_sig = tx.input[:10]
        
        # Check if this is addLiquidity followed by removeLiquidity in same block
        if func_sig in add_liq_sigs:
            # Look for matching removeLiquidity from same address
            for future_tx in all_txs[index+1:]:
                if (future_tx['from'] == tx['from'] and 
                    len(future_tx.input) >= 10 and 
                    future_tx.input[:10] in remove_liq_sigs):
                    
                    return {
                        'tx_hash': tx.hash.hex(),
                        'mev_type': 'jit_liquidity',
                        'profit_estimate': 50.0,  # Placeholder
                        'metadata': {
                            'add_tx': tx.hash.hex(),
                            'remove_tx': future_tx.hash.hex(),
                            'provider': tx['from']
                        }
                    }
        
        return None
    
    def _is_swap_tx(self, tx: TxData) -> bool:
        """Check if transaction is a DEX swap"""
        swap_signatures = ['0x38ed1739', '0x8803dbee', '0x7ff36ab5', '0x18cbafe5']
        return (tx.input and len(tx.input) >= 10 and tx.input[:10] in swap_signatures)
    
    def _estimate_arbitrage_profit(self, swaps: List[TxData]) -> float:
        """
        Estimate profit from arbitrage
        (Placeholder - in production, decode swap amounts and calculate)
        """
        # For now, estimate based on gas price (higher gas = higher profit expected)
        avg_gas_price = sum(s.gasPrice for s in swaps) / len(swaps)
        estimated_profit = avg_gas_price / 1e9 * 100  # Convert gwei to rough USD estimate
        return min(max(estimated_profit, 10.0), 10000.0)  # Clamp between $10-$10k
    
    def _estimate_liquidation_profit(self, tx: TxData) -> float:
        """
        Estimate profit from liquidation
        (Placeholder - in production, decode liquidation amount and bonus)
        """
        # Estimate based on gas price (liquidators pay more gas for larger profits)
        gas_price_gwei = tx.gasPrice / 1e9
        estimated_profit = gas_price_gwei * 50  # Rough heuristic
        return min(max(estimated_profit, 50.0), 50000.0)  # Clamp between $50-$50k
    
    def _estimate_sandwich_profit(self, front: TxData, victim: TxData, back: TxData) -> float:
        """
        Estimate profit from sandwich attack
        (Placeholder - in production, calculate actual price impact)
        """
        # Estimate based on victim's transaction size (larger victim = more profit)
        victim_value_eth = victim.value / 1e18
        estimated_profit = victim_value_eth * 0.005  # ~0.5% of victim's trade
        return min(max(estimated_profit, 5.0), 5000.0)  # Clamp between $5-$5k
    
    def _get_block_validator(self, block: BlockData) -> str:
        """
        Extract validator address from block
        (In Monad, this might be in block.miner or a custom field)
        """
        return block.miner if hasattr(block, 'miner') else '0x0000000000000000000000000000000000000000'
    
    async def _store_block_data(self, block: BlockData, validator: str, mev_ops: List[Dict]):
        """
        Store scanned block data and MEV opportunities in database
        """
        try:
            with omega_db_session() as db:
                # Store block data
                block_data = BlockDataModel(
                    block_number=block.number,
                    block_hash=block.hash.hex() if block.hash else None,
                    validator_address=validator,
                    timestamp=datetime.fromtimestamp(block.timestamp),
                    tx_count=len(block.transactions),
                    mev_opportunities=len(mev_ops),
                    total_mev_captured=sum(mev['profit_estimate'] for mev in mev_ops),
                    transactions=[tx.hash.hex() for tx in block.transactions],
                    mev_summary={'count': len(mev_ops), 'types': [mev['mev_type'] for mev in mev_ops]}
                )
                db.add(block_data)
                
                # Store MEV opportunities
                for mev in mev_ops:
                    mev_record = MEVOpportunity(
                        block_number=mev['block_number'],
                        tx_hash=mev['tx_hash'],
                        mev_type=mev['mev_type'],
                        profit_estimate=mev['profit_estimate'],
                        validator_address=mev['validator_address'],
                        timestamp=mev['timestamp'],
                        metadata=mev.get('metadata', {})
                    )
                    db.add(mev_record)
                
                db.commit()
                
        except Exception as e:
            logger.error(f"OMEGA SCANNER: Failed to store block data: {e}")
