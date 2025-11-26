"""
Alpha Features Engineering Module
MIMIC V3.1 CORTEX - Advanced Feature Engineering

Implements:
- PRIORITY 1: Informational Edge (Dankoweb3 Alpha) - F.1, F.2, F.3
- PRIORITY 2: Structural Edge (bl888m_eth Alpha) - F.4, F.5, F.6
- PRIORITY 3: Risk Management Context (Gemchange Macro) - F.7, F.8

Feature Orthogonality Principle:
- Fundamental (The Why): Does the news justify the price?
- Technical (The Where): Is the price at a critical S/R level?
- Behavioral (The Who): Is the Whale using high conviction pattern?
"""

import math
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum


# =============================================================================
# PRIORITY 1: INFORMATIONAL EDGE (DANKOWEB3 ALPHA)
# =============================================================================

@dataclass
class NewsEvent:
    """Represents an external news event"""
    timestamp: datetime
    source: str
    headline: str
    sentiment: float  # -1 to +1
    novelty: float    # 0 to 1 (how new/unexpected)
    relevance: float  # 0 to 1 (relevance to market)


@dataclass
class MarketTick:
    """Represents a market price/volume tick"""
    timestamp: datetime
    price: float
    volume: float
    side: str  # 'buy' or 'sell'
    is_news_driven: bool = False


class InformationalEdgeCalculator:
    """
    Calculates Informational Edge features (F.1, F.2, F.3)

    F.1: Exogenous Info Score (EIS) - News-driven conviction
    F.2: Endogeneity Score (ERS) - Herd behavior vs news ratio
    F.3: News Latency Delta - Timing advantage in milliseconds
    """

    def __init__(
        self,
        window_minutes: int = 5,
        max_news_events: int = 100,
        max_ticks: int = 1000,
        logger: logging.Logger = None
    ):
        self.window_minutes = window_minutes
        self.logger = logger or logging.getLogger(__name__)

        # Rolling buffers
        self.news_events: deque = deque(maxlen=max_news_events)
        self.market_ticks: deque = deque(maxlen=max_ticks)

        # News-to-price mapping for latency calculation
        self.news_price_correlations: List[Dict] = []

        # Statistics
        self.stats = {
            "news_events_processed": 0,
            "latency_samples": 0,
            "avg_latency_ms": 0
        }

    def add_news_event(self, event: NewsEvent):
        """Register a news event for tracking"""
        self.news_events.append(event)
        self.stats["news_events_processed"] += 1

    def add_market_tick(self, tick: MarketTick):
        """Register a market tick"""
        self.market_ticks.append(tick)

    def calculate_eis(self, oracle_result: Any = None) -> float:
        """
        F.1: Exogenous Info Score (EIS)

        Quantifies fundamental conviction based on external data analysis.
        Score from 0.0 to 1.0.

        Components:
        - Sentiment magnitude (absolute value)
        - News novelty (how unexpected)
        - Source credibility weighting
        - Recency decay
        """
        if oracle_result is None and not self.news_events:
            return 0.5  # Neutral when no data

        # If oracle result provided, use it directly
        if oracle_result is not None:
            sentiment = getattr(oracle_result, 'score', 0.0)
            confidence = getattr(oracle_result, 'confidence', 0.5)

            # EIS = sentiment magnitude weighted by confidence
            # Transform from [-1, 1] to [0, 1]
            eis = (abs(sentiment) * confidence + 1) / 2
            return max(0.0, min(1.0, eis))

        # Calculate from recent news events
        now = datetime.utcnow()
        window = timedelta(minutes=self.window_minutes)

        recent_news = [
            n for n in self.news_events
            if now - n.timestamp < window
        ]

        if not recent_news:
            return 0.5

        # Weighted score calculation
        total_weight = 0.0
        weighted_score = 0.0

        for news in recent_news:
            # Recency weight (exponential decay)
            age_minutes = (now - news.timestamp).total_seconds() / 60
            recency_weight = math.exp(-age_minutes / self.window_minutes)

            # Novelty and relevance weight
            quality_weight = news.novelty * news.relevance

            weight = recency_weight * quality_weight

            # Contribution: sentiment magnitude * novelty
            contribution = abs(news.sentiment) * news.novelty

            weighted_score += contribution * weight
            total_weight += weight

        if total_weight == 0:
            return 0.5

        # Normalize to 0-1
        eis = weighted_score / total_weight
        return max(0.0, min(1.0, eis))

    def calculate_ers(self) -> float:
        """
        F.2: Endogeneity Score (ERS)

        Ratio of Endogenous (internal trading) volume vs Exogenous (news-driven) volume.
        High ERS suggests herd behavior / reflexivity - exploitable mispricing.

        Returns:
            Float 0.0 to 1.0 where:
            - Low (0.0-0.3): News-driven (exogenous)
            - Mid (0.3-0.7): Mixed
            - High (0.7-1.0): Herd behavior (endogenous)
        """
        now = datetime.utcnow()
        window = timedelta(minutes=self.window_minutes)

        recent_ticks = [
            t for t in self.market_ticks
            if now - t.timestamp < window
        ]

        if not recent_ticks:
            return 0.5  # Neutral when no data

        # Sum volumes
        total_volume = sum(t.volume for t in recent_ticks)
        news_driven_volume = sum(t.volume for t in recent_ticks if t.is_news_driven)

        if total_volume == 0:
            return 0.5

        # Exogenous ratio
        exogenous_ratio = news_driven_volume / total_volume

        # ERS = 1 - exogenous_ratio (high = more herd behavior)
        ers = 1.0 - exogenous_ratio

        return max(0.0, min(1.0, ers))

    def calculate_news_latency_delta(self, news_event: NewsEvent = None) -> float:
        """
        F.3: News Latency Delta (L_Delta)

        Time in milliseconds between verifiable news event and first
        corresponding price/volume change on Kalshi.

        Positive delta = we can position before market moves

        Returns:
            Normalized latency score 0.0 to 1.0 where:
            - High (>0.7): Good timing advantage (>500ms before market)
            - Mid (0.3-0.7): Moderate advantage
            - Low (<0.3): Poor timing (market already moved)
        """
        if news_event is None and not self.news_events:
            return 0.5  # Unknown timing

        # Get most recent news event if not provided
        if news_event is None:
            news_event = self.news_events[-1]

        now = datetime.utcnow()
        news_time = news_event.timestamp

        # Find first significant market move after news
        significant_moves = []
        for tick in self.market_ticks:
            if tick.timestamp > news_time:
                # Consider "significant" if volume above threshold
                if tick.volume > 100:  # Configurable threshold
                    significant_moves.append(tick)

        if not significant_moves:
            # No market reaction yet - maximum advantage
            return 1.0

        # Calculate latency to first significant move
        first_move = min(significant_moves, key=lambda t: t.timestamp)
        latency_ms = (first_move.timestamp - news_time).total_seconds() * 1000

        # Update stats
        self.stats["latency_samples"] += 1
        old_avg = self.stats["avg_latency_ms"]
        n = self.stats["latency_samples"]
        self.stats["avg_latency_ms"] = old_avg + (latency_ms - old_avg) / n

        # Normalize: 0-100ms = poor (0.0-0.3), 100-500ms = good (0.3-0.7), >500ms = excellent (0.7-1.0)
        if latency_ms < 100:
            return 0.1 + (latency_ms / 100) * 0.2
        elif latency_ms < 500:
            return 0.3 + ((latency_ms - 100) / 400) * 0.4
        else:
            # Cap at 2000ms
            bounded = min(latency_ms, 2000)
            return 0.7 + ((bounded - 500) / 1500) * 0.3


# =============================================================================
# PRIORITY 2: STRUCTURAL EDGE (BL888M_ETH ALPHA)
# =============================================================================

@dataclass
class PriceLevel:
    """Represents a support/resistance level"""
    price: float
    volume_traded: float  # Historical volume at this level
    bounce_count: int     # Times price bounced off this level
    break_count: int      # Times price broke through
    last_tested: datetime
    level_type: str       # 'support' or 'resistance'


class StructuralEdgeCalculator:
    """
    Calculates Structural Edge features (F.4, F.5, F.6)

    F.4: Pivot Point Distance (PPD) - Distance to nearest S/R
    F.5: S/R Efficacy Score (SRES) - Strength of S/R level
    F.6: Market Unidirectional Bias (MUB) - Directional consensus
    """

    def __init__(
        self,
        atr_period: int = 14,
        max_levels: int = 50,
        max_prices: int = 1000,
        logger: logging.Logger = None
    ):
        self.atr_period = atr_period
        self.logger = logger or logging.getLogger(__name__)

        # S/R levels
        self.support_levels: List[PriceLevel] = []
        self.resistance_levels: List[PriceLevel] = []

        # Price history for ATR calculation
        self.price_history: deque = deque(maxlen=max_prices)
        self.high_history: deque = deque(maxlen=atr_period + 1)
        self.low_history: deque = deque(maxlen=atr_period + 1)

        # Volume tracking by direction
        self.directional_volume: deque = deque(maxlen=100)  # (timestamp, buy_vol, sell_vol)

        # Calculated values
        self._current_atr: float = 0.0

        self.stats = {
            "levels_identified": 0,
            "bounces_tracked": 0
        }

    def add_price_bar(self, high: float, low: float, close: float, volume: float, side: str):
        """Add a price bar for ATR and level tracking"""
        now = datetime.utcnow()

        self.price_history.append(close)
        self.high_history.append(high)
        self.low_history.append(low)

        # Track directional volume
        buy_vol = volume if side == 'buy' else 0
        sell_vol = volume if side == 'sell' else 0
        self.directional_volume.append((now, buy_vol, sell_vol))

        # Update ATR
        self._update_atr()

        # Auto-detect S/R levels from price action
        self._detect_levels(high, low, close, volume)

    def _update_atr(self):
        """Calculate Average True Range"""
        if len(self.high_history) < 2:
            return

        true_ranges = []
        highs = list(self.high_history)
        lows = list(self.low_history)
        closes = list(self.price_history)

        for i in range(1, min(len(highs), self.atr_period + 1)):
            if i < len(closes):
                prev_close = closes[-(i+1)] if len(closes) > i else closes[-1]
                high = highs[-i]
                low = lows[-i]

                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                true_ranges.append(tr)

        if true_ranges:
            self._current_atr = sum(true_ranges) / len(true_ranges)

    def _detect_levels(self, high: float, low: float, close: float, volume: float):
        """Auto-detect S/R levels from price action"""
        now = datetime.utcnow()

        # Simple pivot point calculation
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high

        # Add or update resistance level
        self._update_level(r1, volume, 'resistance')

        # Add or update support level
        self._update_level(s1, volume, 'support')

    def _update_level(self, price: float, volume: float, level_type: str):
        """Update or create an S/R level"""
        levels = self.resistance_levels if level_type == 'resistance' else self.support_levels
        now = datetime.utcnow()

        # Tolerance for matching levels (5% of price)
        tolerance = price * 0.05

        # Find existing level
        existing = None
        for level in levels:
            if abs(level.price - price) < tolerance:
                existing = level
                break

        if existing:
            existing.volume_traded += volume
            existing.last_tested = now
        else:
            new_level = PriceLevel(
                price=price,
                volume_traded=volume,
                bounce_count=0,
                break_count=0,
                last_tested=now,
                level_type=level_type
            )
            levels.append(new_level)
            self.stats["levels_identified"] += 1

            # Keep only top 20 levels by volume
            levels.sort(key=lambda l: l.volume_traded, reverse=True)
            if level_type == 'resistance':
                self.resistance_levels = levels[:20]
            else:
                self.support_levels = levels[:20]

    def calculate_ppd(self, current_price: float) -> float:
        """
        F.4: Pivot Point Distance (PPD)

        Normalized distance of current price to nearest S/R level.
        Normalized by Average True Range (ATR).

        Returns:
            Float 0.0 to 1.0 where:
            - Low (<0.3): At critical decision zone (high probability signal)
            - Mid (0.3-0.7): Between levels
            - High (>0.7): Far from any S/R level
        """
        all_levels = self.support_levels + self.resistance_levels

        if not all_levels or self._current_atr == 0:
            return 0.5  # Unknown

        # Find nearest level
        nearest_distance = float('inf')
        for level in all_levels:
            distance = abs(current_price - level.price)
            if distance < nearest_distance:
                nearest_distance = distance

        # Normalize by ATR
        atr_normalized = nearest_distance / self._current_atr if self._current_atr > 0 else nearest_distance

        # Convert to 0-1 scale (0 = at level, 1 = far from level)
        # Use sigmoid-like transformation
        ppd = 1 - math.exp(-atr_normalized / 2)

        return max(0.0, min(1.0, ppd))

    def calculate_sres(self, current_price: float) -> float:
        """
        F.5: S/R Efficacy Score (SRES)

        ML-derived score quantifying strength of nearest S/R level.
        Based on:
        - Prior volume traded at level
        - Bounce history
        - Recency of last test

        Returns:
            Float 0.0 to 1.0 where:
            - High (>0.7): Strong barrier
            - Mid (0.3-0.7): Moderate strength
            - Low (<0.3): Weak level
        """
        all_levels = self.support_levels + self.resistance_levels

        if not all_levels:
            return 0.5

        # Find nearest level
        nearest = min(all_levels, key=lambda l: abs(current_price - l.price))

        # Calculate efficacy score components

        # 1. Volume component (normalized by max volume)
        max_volume = max(l.volume_traded for l in all_levels)
        volume_score = nearest.volume_traded / max_volume if max_volume > 0 else 0

        # 2. Bounce ratio (bounces vs breaks)
        total_tests = nearest.bounce_count + nearest.break_count
        bounce_score = nearest.bounce_count / total_tests if total_tests > 0 else 0.5

        # 3. Recency score
        now = datetime.utcnow()
        age_hours = (now - nearest.last_tested).total_seconds() / 3600
        recency_score = math.exp(-age_hours / 24)  # Decay over 24 hours

        # Weighted combination
        sres = (
            volume_score * 0.4 +
            bounce_score * 0.4 +
            recency_score * 0.2
        )

        return max(0.0, min(1.0, sres))

    def calculate_mub(self) -> float:
        """
        F.6: Market Unidirectional Bias (MUB)

        Ratio of exposure-increasing trade volume in dominant direction.
        High MUB = extreme market consensus = potential reversal at S/R.

        Returns:
            Float 0.0 to 1.0 where:
            - Near 0.5: Balanced market
            - Near 0.0: Strong sell bias
            - Near 1.0: Strong buy bias
        """
        if not self.directional_volume:
            return 0.5

        now = datetime.utcnow()
        window = timedelta(minutes=5)

        total_buy = 0.0
        total_sell = 0.0

        for timestamp, buy_vol, sell_vol in self.directional_volume:
            if now - timestamp < window:
                total_buy += buy_vol
                total_sell += sell_vol

        total_volume = total_buy + total_sell

        if total_volume == 0:
            return 0.5

        # MUB = buy ratio (0 = all sell, 1 = all buy)
        mub = total_buy / total_volume

        return mub


# =============================================================================
# PRIORITY 3: RISK MANAGEMENT CONTEXT (GEMCHANGE MACRO)
# =============================================================================

class MarketRegime(Enum):
    """Market regime classification"""
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGING = "RANGING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    UNKNOWN = "UNKNOWN"


class RiskContextCalculator:
    """
    Calculates Risk Management Context features (F.7, F.8)

    F.7: Trend Intensity Index (TII) - Market regime identification
    F.8: Risk/Reward Ratio (RRR) - Potential profit vs risk
    """

    def __init__(
        self,
        momentum_period: int = 14,
        volatility_period: int = 20,
        max_prices: int = 500,
        logger: logging.Logger = None
    ):
        self.momentum_period = momentum_period
        self.volatility_period = volatility_period
        self.logger = logger or logging.getLogger(__name__)

        # Price history
        self.prices: deque = deque(maxlen=max_prices)
        self.returns: deque = deque(maxlen=max_prices - 1)

        # Current regime
        self.current_regime = MarketRegime.UNKNOWN

        self.stats = {
            "regime_changes": 0,
            "avg_volatility": 0.0
        }

    def add_price(self, price: float):
        """Add a price observation"""
        if self.prices:
            ret = (price - self.prices[-1]) / self.prices[-1] if self.prices[-1] != 0 else 0
            self.returns.append(ret)
        self.prices.append(price)
        self._update_regime()

    def _update_regime(self):
        """Update market regime classification"""
        if len(self.prices) < self.momentum_period:
            return

        # Calculate momentum
        momentum = (self.prices[-1] - self.prices[-self.momentum_period]) / self.prices[-self.momentum_period]

        # Calculate volatility
        if len(self.returns) >= self.volatility_period:
            recent_returns = list(self.returns)[-self.volatility_period:]
            volatility = np.std(recent_returns) if recent_returns else 0
            self.stats["avg_volatility"] = volatility
        else:
            volatility = 0.1  # Default

        # Regime classification
        old_regime = self.current_regime

        if volatility > 0.05:  # High volatility threshold
            self.current_regime = MarketRegime.HIGH_VOLATILITY
        elif momentum > 0.02:  # Trending up
            self.current_regime = MarketRegime.TRENDING_UP
        elif momentum < -0.02:  # Trending down
            self.current_regime = MarketRegime.TRENDING_DOWN
        else:
            self.current_regime = MarketRegime.RANGING

        if old_regime != self.current_regime:
            self.stats["regime_changes"] += 1

    def calculate_tii(self) -> float:
        """
        F.7: Trend Intensity Index (TII)

        Score 0.0 to 1.0 based on momentum indicators and volatility skew.

        Returns:
            Float 0.0 to 1.0 where:
            - High (>0.7): Strong trend (favor momentum strategies)
            - Mid (0.3-0.7): Moderate trend
            - Low (<0.3): Ranging (favor mean reversion, structural features)
        """
        if len(self.prices) < self.momentum_period:
            return 0.5

        prices = list(self.prices)

        # Calculate multiple timeframe momentum
        short_mom = (prices[-1] - prices[-min(5, len(prices))]) / prices[-min(5, len(prices))] if len(prices) > 5 else 0
        med_mom = (prices[-1] - prices[-min(14, len(prices))]) / prices[-min(14, len(prices))] if len(prices) > 14 else 0

        # Calculate ADX-like indicator (simplified)
        if len(self.returns) < 10:
            return 0.5

        recent_returns = list(self.returns)[-14:]

        # Positive and negative moves
        pos_moves = [r for r in recent_returns if r > 0]
        neg_moves = [r for r in recent_returns if r < 0]

        avg_pos = sum(pos_moves) / len(pos_moves) if pos_moves else 0
        avg_neg = abs(sum(neg_moves) / len(neg_moves)) if neg_moves else 0

        # Directional index
        di_sum = avg_pos + avg_neg
        if di_sum == 0:
            dx = 0
        else:
            dx = abs(avg_pos - avg_neg) / di_sum

        # Combine momentum and direction
        momentum_magnitude = (abs(short_mom) + abs(med_mom)) / 2

        # TII = weighted combination
        tii = (
            dx * 0.5 +
            min(momentum_magnitude * 10, 1.0) * 0.3 +
            (1 if self.current_regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN] else 0) * 0.2
        )

        return max(0.0, min(1.0, tii))

    def calculate_rrr(
        self,
        entry_price: float,
        target_price: float = None,
        stop_price: float = None,
        win_prob: float = 0.5
    ) -> float:
        """
        F.8: Risk/Reward Ratio (RRR)

        Calculated potential Net Profit / Risk.
        For binary options: uses probability and payout structure.

        Args:
            entry_price: Entry price (0-1 for binary)
            target_price: Target exit (1.0 for binary win)
            stop_price: Stop loss (0.0 for binary loss)
            win_prob: Estimated win probability

        Returns:
            Float 0.0 to 1.0 normalized RRR score where:
            - High (>0.7): Excellent risk/reward
            - Mid (0.3-0.7): Acceptable
            - Low (<0.3): Poor risk/reward
        """
        # Binary options specific
        if target_price is None:
            target_price = 1.0
        if stop_price is None:
            stop_price = 0.0

        # Potential profit and loss
        potential_profit = target_price - entry_price
        potential_loss = entry_price - stop_price

        if potential_loss <= 0:
            return 1.0  # No risk

        # Raw RRR
        raw_rrr = potential_profit / potential_loss

        # Expected value RRR (incorporating probability)
        ev_profit = potential_profit * win_prob
        ev_loss = potential_loss * (1 - win_prob)

        if ev_loss <= 0:
            ev_rrr = 10.0  # Cap at 10
        else:
            ev_rrr = ev_profit / ev_loss

        # Normalize to 0-1 using sigmoid-like function
        # RRR of 1 = 0.5, RRR of 3 = ~0.75, RRR of 5+ = ~0.9
        normalized_rrr = 1 - (1 / (1 + ev_rrr))

        return max(0.0, min(1.0, normalized_rrr))

    def get_regime_multiplier(self) -> float:
        """Get position size multiplier based on regime"""
        multipliers = {
            MarketRegime.TRENDING_UP: 1.0,
            MarketRegime.TRENDING_DOWN: 1.0,
            MarketRegime.RANGING: 0.8,
            MarketRegime.HIGH_VOLATILITY: 0.6,
            MarketRegime.UNKNOWN: 0.7
        }
        return multipliers.get(self.current_regime, 0.7)


# =============================================================================
# UNIFIED ALPHA FEATURE EXTRACTOR
# =============================================================================

@dataclass
class AlphaFeatures:
    """Complete alpha feature set for River model"""

    # Informational Edge (F.1-F.3)
    exogenous_info_score: float = 0.5      # F.1: EIS
    endogeneity_score: float = 0.5          # F.2: ERS
    news_latency_delta: float = 0.5         # F.3: L_Delta

    # Structural Edge (F.4-F.6)
    pivot_point_distance: float = 0.5       # F.4: PPD
    sr_efficacy_score: float = 0.5          # F.5: SRES
    market_unidirectional_bias: float = 0.5 # F.6: MUB

    # Risk Context (F.7-F.8)
    trend_intensity_index: float = 0.5      # F.7: TII
    risk_reward_ratio: float = 0.5          # F.8: RRR

    # Market regime
    market_regime: str = "UNKNOWN"

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for River model"""
        return {
            'eis': self.exogenous_info_score,
            'ers': self.endogeneity_score,
            'news_latency': self.news_latency_delta,
            'ppd': self.pivot_point_distance,
            'sres': self.sr_efficacy_score,
            'mub': self.market_unidirectional_bias,
            'tii': self.trend_intensity_index,
            'rrr': self.risk_reward_ratio
        }


class AlphaFeatureExtractor:
    """
    Unified extractor for all alpha features.

    Coordinates the three specialized calculators to produce
    a complete feature vector for the River model.
    """

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

        # Initialize specialized calculators
        self.informational = InformationalEdgeCalculator(logger=self.logger)
        self.structural = StructuralEdgeCalculator(logger=self.logger)
        self.risk_context = RiskContextCalculator(logger=self.logger)

        self.logger.info("Alpha Feature Extractor initialized")

    def update_market_data(
        self,
        price: float,
        high: float = None,
        low: float = None,
        volume: float = 0,
        side: str = 'buy',
        is_news_driven: bool = False
    ):
        """Update all calculators with new market data"""
        now = datetime.utcnow()

        # Default high/low to price
        high = high or price
        low = low or price

        # Update structural calculator
        self.structural.add_price_bar(high, low, price, volume, side)

        # Update risk context
        self.risk_context.add_price(price)

        # Update informational with tick
        tick = MarketTick(
            timestamp=now,
            price=price,
            volume=volume,
            side=side,
            is_news_driven=is_news_driven
        )
        self.informational.add_market_tick(tick)

    def update_news(self, headline: str, sentiment: float, novelty: float = 0.5, relevance: float = 0.5):
        """Register a news event"""
        event = NewsEvent(
            timestamp=datetime.utcnow(),
            source="external",
            headline=headline,
            sentiment=sentiment,
            novelty=novelty,
            relevance=relevance
        )
        self.informational.add_news_event(event)

    def extract_features(
        self,
        current_price: float,
        oracle_result: Any = None,
        entry_price: float = None,
        win_prob: float = 0.5
    ) -> AlphaFeatures:
        """
        Extract complete alpha feature set.

        Args:
            current_price: Current market price
            oracle_result: Optional NewsOracle result
            entry_price: Entry price for RRR calculation
            win_prob: Estimated win probability

        Returns:
            AlphaFeatures dataclass with all 8 features
        """
        if entry_price is None:
            entry_price = current_price

        features = AlphaFeatures(
            # Informational Edge
            exogenous_info_score=self.informational.calculate_eis(oracle_result),
            endogeneity_score=self.informational.calculate_ers(),
            news_latency_delta=self.informational.calculate_news_latency_delta(),

            # Structural Edge
            pivot_point_distance=self.structural.calculate_ppd(current_price),
            sr_efficacy_score=self.structural.calculate_sres(current_price),
            market_unidirectional_bias=self.structural.calculate_mub(),

            # Risk Context
            trend_intensity_index=self.risk_context.calculate_tii(),
            risk_reward_ratio=self.risk_context.calculate_rrr(
                entry_price=entry_price,
                win_prob=win_prob
            ),

            # Regime
            market_regime=self.risk_context.current_regime.value
        )

        return features

    def get_stats(self) -> Dict:
        """Get combined statistics"""
        return {
            "informational": self.informational.stats,
            "structural": self.structural.stats,
            "risk_context": self.risk_context.stats
        }
