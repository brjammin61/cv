"""
Omega Engine - MEV Classifier
Calculates MEV efficiency scores for validators
This is the secret sauce that customers pay for
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_

from .models import MEVOpportunity, ValidatorMEVScore, BlockData
from .db_utils import omega_db_session

logger = logging.getLogger(__name__)


class MEVClassifier:
    """
    Classifies and scores validators based on MEV extraction efficiency
    """
    
    def calculate_mev_efficiency(
        self, 
        validator_address: str, 
        lookback_days: int = 1
    ) -> float:
        """
        Calculate MEV Efficiency score for a validator
        
        MEV Efficiency = (Total MEV Captured) / (Total MEV Available) * 100
        
        Args:
            validator_address: Validator to score
            lookback_days: Number of days to analyze
            
        Returns:
            Efficiency score 0-100
        """
        try:
            with omega_db_session() as db:
                cutoff_date = datetime.now() - timedelta(days=lookback_days)
                
                # Get all blocks produced by this validator in timeframe
                validator_blocks = db.query(BlockData).filter(
                    and_(
                        BlockData.validator_address == validator_address,
                        BlockData.timestamp >= cutoff_date
                    )
                ).all()
                
                if not validator_blocks:
                    return 0.0
                
                # MEV captured by this validator
                mev_captured = sum(block.total_mev_captured for block in validator_blocks)
                
                # MEV available = theoretical maximum based on opportunities in their blocks
                mev_available = self._calculate_available_mev(validator_blocks, db)
                
                if mev_available == 0:
                    return 0.0 if mev_captured == 0 else 100.0
                
                efficiency = (mev_captured / mev_available) * 100
                
                return min(efficiency, 100.0)  # Cap at 100%
                
        except Exception as e:
            logger.error(f"OMEGA CLASSIFIER: Error calculating efficiency for {validator_address}: {e}")
            return 0.0
    
    def _calculate_available_mev(self, validator_blocks: List[BlockData], db) -> float:
        """
        Calculate theoretical maximum MEV available in validator's blocks
        
        This compares what the validator captured vs what was possible
        """
        total_available = 0.0
        
        for block in validator_blocks:
            # Get all MEV opportunities detected in this block
            # (from any validator, to see what was possible)
            all_mev_in_block = db.query(MEVOpportunity).filter(
                MEVOpportunity.block_number == block.block_number
            ).all()
            
            # Theoretical max = sum of all possible MEV in block
            block_max = sum(mev.profit_estimate for mev in all_mev_in_block)
            total_available += block_max
        
        return total_available
    
    def generate_validator_report(self, validator_address: str) -> Dict:
        """
        Generate comprehensive MEV report for a validator
        
        This is what PRO and ENTERPRISE customers pay for
        
        Args:
            validator_address: Validator to report on
            
        Returns:
            Complete MEV performance report
        """
        try:
            # Calculate efficiency scores for different timeframes
            efficiency_1d = self.calculate_mev_efficiency(validator_address, 1)
            efficiency_7d = self.calculate_mev_efficiency(validator_address, 7)
            efficiency_30d = self.calculate_mev_efficiency(validator_address, 30)
            
            # Get MEV breakdown by type
            mev_breakdown = self._get_mev_breakdown(validator_address)
            
            # Identify missed opportunities
            missed = self._identify_missed_opportunities(validator_address)
            
            # Get validator ranking
            ranking = self._get_validator_ranking(validator_address)
            
            # Generate actionable recommendations
            recommendations = self._generate_recommendations(validator_address, mev_breakdown)
            
            return {
                'validator': validator_address,
                'report_generated': datetime.now().isoformat(),
                'efficiency_scores': {
                    '24h': round(efficiency_1d, 2),
                    '7d': round(efficiency_7d, 2),
                    '30d': round(efficiency_30d, 2)
                },
                'mev_breakdown': mev_breakdown,
                'missed_opportunities': missed,
                'ranking': ranking,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"OMEGA CLASSIFIER: Error generating report for {validator_address}: {e}")
            return {'error': str(e)}
    
    def _get_mev_breakdown(self, validator_address: str, days: int = 30) -> Dict:
        """
        Break down MEV by type for a validator
        """
        try:
            with omega_db_session() as db:
                cutoff = datetime.now() - timedelta(days=days)
                
                mev_ops = db.query(MEVOpportunity).filter(
                    and_(
                        MEVOpportunity.validator_address == validator_address,
                        MEVOpportunity.timestamp >= cutoff
                    )
                ).all()
                
                breakdown = {
                    'arbitrage': {'count': 0, 'total_profit': 0.0},
                    'liquidation': {'count': 0, 'total_profit': 0.0},
                    'sandwich': {'count': 0, 'total_profit': 0.0},
                    'jit_liquidity': {'count': 0, 'total_profit': 0.0}
                }
                
                for mev in mev_ops:
                    if mev.mev_type in breakdown:
                        breakdown[mev.mev_type]['count'] += 1
                        breakdown[mev.mev_type]['total_profit'] += mev.profit_estimate
                
                return breakdown
                
        except Exception as e:
            logger.error(f"OMEGA CLASSIFIER: Error getting MEV breakdown: {e}")
            return {}
    
    def _identify_missed_opportunities(self, validator_address: str, limit: int = 10) -> List[Dict]:
        """
        Identify top MEV opportunities the validator MISSED
        
        This is GOLD for customers - showing them what they left on the table
        """
        try:
            with omega_db_session() as db:
                # Get blocks produced by this validator
                validator_blocks = db.query(BlockData).filter(
                    BlockData.validator_address == validator_address
                ).order_by(BlockData.timestamp.desc()).limit(1000).all()
                
                block_numbers = [b.block_number for b in validator_blocks]
                
                # Get MEV opportunities in those blocks that OTHER validators captured
                missed_mev = db.query(MEVOpportunity).filter(
                    and_(
                        MEVOpportunity.block_number.in_(block_numbers),
                        MEVOpportunity.validator_address != validator_address
                    )
                ).order_by(MEVOpportunity.profit_estimate.desc()).limit(limit).all()
                
                missed = []
                for mev in missed_mev:
                    missed.append({
                        'block_number': mev.block_number,
                        'mev_type': mev.mev_type,
                        'profit_missed': round(mev.profit_estimate, 2),
                        'captured_by': mev.validator_address,
                        'tx_hash': mev.tx_hash,
                        'timestamp': mev.timestamp.isoformat()
                    })
                
                return missed
                
        except Exception as e:
            logger.error(f"OMEGA CLASSIFIER: Error identifying missed opportunities: {e}")
            return []
    
    def _get_validator_ranking(self, validator_address: str) -> Dict:
        """
        Rank validator against all others
        """
        try:
            # Calculate efficiency for all validators
            with omega_db_session() as db:
                # Get all unique validators
                all_validators = db.query(BlockData.validator_address).distinct().all()
                all_validators = [v[0] for v in all_validators]
                
                # Calculate efficiency for each
                rankings = []
                for val in all_validators:
                    eff = self.calculate_mev_efficiency(val, lookback_days=7)
                    rankings.append({'address': val, 'efficiency': eff})
                
                # Sort by efficiency
                rankings.sort(key=lambda x: x['efficiency'], reverse=True)
                
                # Find our validator's rank
                for i, val in enumerate(rankings):
                    if val['address'] == validator_address:
                        return {
                            'rank': i + 1,
                            'percentile': round(((len(rankings) - i) / len(rankings)) * 100, 1),
                            'total_validators': len(rankings),
                            'efficiency': round(val['efficiency'], 2)
                        }
                
                return {
                    'rank': None,
                    'percentile': 0,
                    'total_validators': len(rankings),
                    'efficiency': 0.0
                }
                
        except Exception as e:
            logger.error(f"OMEGA CLASSIFIER: Error getting ranking: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, validator_address: str, mev_breakdown: Dict) -> List[str]:
        """
        Generate actionable recommendations for improving MEV efficiency
        
        This is premium value-add that justifies the subscription price
        """
        recommendations = []
        
        # Analyze breakdown
        arbitrage = mev_breakdown.get('arbitrage', {})
        liquidation = mev_breakdown.get('liquidation', {})
        sandwich = mev_breakdown.get('sandwich', {})
        jit = mev_breakdown.get('jit_liquidity', {})
        
        # Recommendation 1: Arbitrage opportunities
        if arbitrage.get('count', 0) < 5:
            recommendations.append(
                "Low arbitrage activity detected. Consider integrating DEX arbitrage "
                "detection in your MEV pipeline. Top validators capture 50+ arbitrage "
                "opportunities per month."
            )
        elif arbitrage.get('total_profit', 0) < 500:
            recommendations.append(
                "Arbitrage detection active but low profits. Optimize your price feed "
                "latency and consider multi-DEX routing for better opportunities."
            )
        
        # Recommendation 2: Liquidations
        if liquidation.get('count', 0) == 0:
            recommendations.append(
                "Zero liquidations captured. Major opportunity: Liquidation MEV is "
                "highly profitable on Monad. Integrate with lending protocols (Aave, Compound)."
            )
        
        # Recommendation 3: Sandwich attacks (controversial but profitable)
        if sandwich.get('count', 0) == 0:
            recommendations.append(
                "No sandwich MEV detected. While controversial, sandwich attacks are "
                "a significant MEV source. Top validators use ethical sandwiching with "
                "slippage limits. Consider implementing if aligned with your values."
            )
        
        # Recommendation 4: JIT Liquidity
        if jit.get('count', 0) == 0:
            recommendations.append(
                "JIT liquidity opportunities untapped. This is advanced MEV requiring "
                "real-time mempool analysis. Recommend starting with simpler strategies first."
            )
        
        # Recommendation 5: Compare to top performers
        try:
            with omega_db_session() as db:
                # Get top validator's breakdown
                top_validator = db.query(ValidatorMEVScore).order_by(
                    ValidatorMEVScore.efficiency_score.desc()
                ).first()
                
                if top_validator and top_validator.validator_address != validator_address:
                    recommendations.append(
                        f"Top performer ({top_validator.validator_address[:8]}...) "
                        f"achieves {top_validator.efficiency_score:.1f}% efficiency. "
                        f"Focus on transaction ordering optimization and mempool monitoring."
                    )
        except:
            pass
        
        # If performing well, give positive feedback
        efficiency = self.calculate_mev_efficiency(validator_address, 7)
        if efficiency >= 80:
            recommendations.append(
                f"Excellent performance! Your 7-day efficiency of {efficiency:.1f}% "
                f"puts you in the top tier. Continue monitoring for consistency."
            )
        
        return recommendations
    
    def update_daily_scores(self):
        """
        Calculate and store daily MEV scores for all validators
        Run this once per day via cron job
        """
        try:
            with omega_db_session() as db:
                # Get all validators
                validators = db.query(BlockData.validator_address).distinct().all()
                validators = [v[0] for v in validators]
                
                today = datetime.now().date()
                
                for validator in validators:
                    # Calculate metrics
                    efficiency = self.calculate_mev_efficiency(validator, lookback_days=1)
                    breakdown = self._get_mev_breakdown(validator, days=1)
                    
                    # Get block count
                    cutoff = datetime.now() - timedelta(days=1)
                    block_count = db.query(BlockData).filter(
                        and_(
                            BlockData.validator_address == validator,
                            BlockData.timestamp >= cutoff
                        )
                    ).count()
                    
                    # Calculate total MEV
                    mev_captured = sum(
                        breakdown[mev_type]['total_profit'] 
                        for mev_type in breakdown
                    )
                    
                    # Store score
                    score = ValidatorMEVScore(
                        validator_address=validator,
                        date=today,
                        efficiency_score=efficiency,
                        mev_captured=mev_captured,
                        mev_available=mev_captured / (efficiency / 100) if efficiency > 0 else 0,
                        block_count=block_count,
                        arbitrage_count=breakdown.get('arbitrage', {}).get('count', 0),
                        arbitrage_profit=breakdown.get('arbitrage', {}).get('total_profit', 0.0),
                        liquidation_count=breakdown.get('liquidation', {}).get('count', 0),
                        liquidation_profit=breakdown.get('liquidation', {}).get('total_profit', 0.0),
                        sandwich_count=breakdown.get('sandwich', {}).get('count', 0),
                        sandwich_profit=breakdown.get('sandwich', {}).get('total_profit', 0.0),
                        jit_count=breakdown.get('jit_liquidity', {}).get('count', 0),
                        jit_profit=breakdown.get('jit_liquidity', {}).get('total_profit', 0.0)
                    )
                    
                    db.add(score)
                
                db.commit()
                logger.info(f"OMEGA CLASSIFIER: Updated daily scores for {len(validators)} validators")
                
        except Exception as e:
            logger.error(f"OMEGA CLASSIFIER: Error updating daily scores: {e}")
    
    def get_leaderboard(self, limit: int = 100, days: int = 7) -> List[Dict]:
        """
        Get MEV efficiency leaderboard
        
        Args:
            limit: Number of validators to return
            days: Timeframe to calculate efficiency over
            
        Returns:
            List of validators ranked by MEV efficiency
        """
        try:
            with omega_db_session() as db:
                # Get all validators
                validators = db.query(BlockData.validator_address).distinct().all()
                validators = [v[0] for v in validators]
                
                # Calculate efficiency for each
                leaderboard = []
                for validator in validators:
                    eff = self.calculate_mev_efficiency(validator, lookback_days=days)
                    
                    if eff > 0:  # Only include validators with activity
                        leaderboard.append({
                            'validator': validator,
                            'efficiency': round(eff, 2),
                            'rank': 0  # Will be assigned after sorting
                        })
                
                # Sort by efficiency
                leaderboard.sort(key=lambda x: x['efficiency'], reverse=True)
                
                # Assign ranks
                for i, entry in enumerate(leaderboard):
                    entry['rank'] = i + 1
                
                return leaderboard[:limit]
                
        except Exception as e:
            logger.error(f"OMEGA CLASSIFIER: Error generating leaderboard: {e}")
            return []
