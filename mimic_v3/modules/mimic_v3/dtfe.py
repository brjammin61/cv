"""
Digital Twin Foresight Engine (DTFE) - Module C
MIMIC V3.1 CORTEX - Generative Alpha Intelligence

THE WORLD-CHANGING CONCEPT: Structured Counterfactual Reasoning (SCR)

The DTFE creates a synthetic "digital twin" of a Kalshi contract and simulates
market reactions to hypothetical news events, outputting a statistically
hardened probability (P_sim).

Implements:
- L.1: Tiered LLM Deployment (cost-optimized)
- L.2: Structured Output (SCR) with JSON schema
- L.3: Tsallis Entropy Calculation (F.9)
- F.10: Optimal Position Size via Fractional Kelly

Three Non-Negotiable Quantitative Disciplines:
1. Contextual Encoding (The Setup): Feed LLM a Prefix Summary Context (PSC)
2. Counterfactual Shock (The Test): Present structured hypothetical event
3. Probabilistic Output (The Result): Force CoT reasoning + raw probability

This transforms non-deterministic LLM reasoning into a structured,
auditable, and quantifiable trading signal.
"""

import os
import json
import math
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class MarketStructure(Enum):
    """Technical market structure classification"""
    BULLISH_HH_HL = "BULLISH_HH_HL"    # Higher highs, higher lows
    BEARISH_LH_LL = "BEARISH_LH_LL"    # Lower highs, lower lows
    RANGING = "RANGING"
    BREAKOUT = "BREAKOUT"
    UNKNOWN = "UNKNOWN"


@dataclass
class PrefixSummaryContext:
    """
    PSC: Prefix Summary Context
    Grounds the LLM in technical reality to prevent hallucination.
    """
    ticker: str
    title: str
    current_price: float
    market_structure: MarketStructure
    key_support: float
    key_resistance: float
    time_to_expiry_days: int
    volume_24h: float
    recent_trend: str  # "up", "down", "sideways"

    def to_prompt_string(self) -> str:
        """Convert to LLM prompt context"""
        return f"""MARKET CONTEXT:
- Contract: {self.ticker}
- Title: {self.title}
- Current Price: ${self.current_price:.2f} ({self.current_price*100:.0f}c)
- Market Structure: {self.market_structure.value}
- Key Support: ${self.key_support:.2f}
- Key Resistance: ${self.key_resistance:.2f}
- Time to Expiry: {self.time_to_expiry_days} days
- 24h Volume: ${self.volume_24h:,.0f}
- Recent Trend: {self.recent_trend}"""


@dataclass
class CounterfactualShock:
    """
    Structured hypothetical news event for SCR testing.
    """
    shock_type: str  # "POLITICAL", "ECONOMIC", "CORPORATE", "GEOPOLITICAL"
    headline: str
    description: str
    severity: str    # "MINOR", "MODERATE", "MAJOR", "BLACK_SWAN"

    def to_prompt_string(self) -> str:
        """Convert to LLM prompt"""
        return f"""HYPOTHETICAL SCENARIO ({self.shock_type} - {self.severity}):
"{self.headline}"

Details: {self.description}

INSTRUCTION: Analyze how this event would impact the contract's probability of resolving YES."""


@dataclass
class SCROutput:
    """
    Structured Counterfactual Reasoning Output
    JSON schema for LLM response.
    """
    reasoning_cot: str           # Chain of thought
    p_llm_raw: float             # Raw probability 0-1
    confidence_stated: float     # LLM's stated confidence
    key_factors: List[str]       # Driving factors
    risk_flags: List[str]        # Identified risks
    tsallis_entropy: float = 0.0 # F.9: Calculated from logprobs
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DTFEResult:
    """
    Complete DTFE output including calibrated probability.
    """
    ticker: str
    p_llm_raw: float           # Raw LLM probability
    p_llm_calibrated: float    # After Isotonic Regression
    tsallis_entropy: float     # F.9: Confidence measure
    optimal_position_size: float  # F.10: Kelly fraction
    scr_output: SCROutput
    context: PrefixSummaryContext
    shock: CounterfactualShock
    is_tradeable: bool         # Passes entropy threshold
    rejection_reason: str = ""


# =============================================================================
# L.1: TIERED LLM DEPLOYMENT
# =============================================================================

class LLMTier(Enum):
    """LLM tier for cost optimization"""
    TIER1_SUMMARIZER = "tier1"   # Cheap: DeepSeek/Mini for PSC
    TIER2_REASONER = "tier2"     # Premium: GPT-4.1/Claude for SCR


class TieredLLMClient:
    """
    Cost-optimized dual-tier LLM deployment.

    Tier 1: Low-cost model for context summarization (PSC)
    Tier 2: High-end model for Structured Counterfactual Reasoning
    """

    # API Endpoints
    OPENAI_API = "https://api.openai.com/v1/chat/completions"
    ANTHROPIC_API = "https://api.anthropic.com/v1/messages"

    def __init__(
        self,
        openai_key: str = None,
        anthropic_key: str = None,
        tier1_model: str = "gpt-4o-mini",
        tier2_model: str = "gpt-4o",
        logger: logging.Logger = None
    ):
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_key = anthropic_key or os.getenv("ANTHROPIC_API_KEY")

        self.tier1_model = tier1_model
        self.tier2_model = tier2_model

        self.logger = logger or logging.getLogger(__name__)

        # HTTP session
        self._session: Optional[aiohttp.ClientSession] = None

        # Statistics
        self.stats = {
            "tier1_calls": 0,
            "tier2_calls": 0,
            "total_tokens": 0,
            "errors": 0
        }

        # Validate credentials
        if not self.openai_key and not self.anthropic_key:
            self.logger.warning("DTFE: No LLM API keys found - running in MOCK mode")
            self.mock_mode = True
        else:
            self.mock_mode = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def tier1_summarize(self, raw_text: str) -> str:
        """
        Tier 1: Cheap model for context summarization.
        Converts raw market data into concise PSC.
        """
        if self.mock_mode:
            return self._mock_summarize(raw_text)

        self.stats["tier1_calls"] += 1

        prompt = f"""Summarize the following market data into a concise context summary for financial analysis:

{raw_text}

Output a brief, factual summary focusing on:
1. Current market state
2. Key price levels
3. Recent activity patterns"""

        try:
            response = await self._call_openai(
                model=self.tier1_model,
                messages=[
                    {"role": "system", "content": "You are a concise financial data summarizer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            return response["content"]
        except Exception as e:
            self.logger.error(f"Tier 1 error: {e}")
            self.stats["errors"] += 1
            return raw_text[:500]

    async def tier2_reason(
        self,
        context: PrefixSummaryContext,
        shock: CounterfactualShock,
        return_logprobs: bool = True
    ) -> Tuple[SCROutput, Optional[List[float]]]:
        """
        Tier 2: Premium model for Structured Counterfactual Reasoning.

        Returns:
            (SCROutput, logprobs) - logprobs for Tsallis entropy calculation
        """
        if self.mock_mode:
            return self._mock_reason(context, shock), None

        self.stats["tier2_calls"] += 1

        system_prompt = """You are an expert financial analyst performing Structured Counterfactual Reasoning (SCR) for prediction markets.

You MUST output valid JSON with this exact schema:
{
    "reasoning_cot": "<your step-by-step chain of thought analysis>",
    "p_llm_raw": <float 0.0-1.0 probability of YES outcome>,
    "confidence_stated": <float 0.0-1.0 your confidence in this prediction>,
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"],
    "risk_flags": ["<risk1>", "<risk2>"]
}

ANALYSIS FRAMEWORK:
1. First, analyze the baseline probability from the current market context
2. Then, reason through how the hypothetical shock would shift this probability
3. Consider second-order effects and market reaction dynamics
4. Identify any hidden risks or tail scenarios
5. Output your final calibrated probability

Be precise, quantitative, and avoid overconfidence."""

        user_prompt = f"""{context.to_prompt_string()}

{shock.to_prompt_string()}

Perform Structured Counterfactual Reasoning and output your analysis as JSON."""

        try:
            response = await self._call_openai(
                model=self.tier2_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1000,
                logprobs=return_logprobs
            )

            # Parse JSON output
            output_data = self._parse_scr_output(response["content"])

            # Get logprobs if available
            logprobs = response.get("logprobs", [])

            return output_data, logprobs

        except Exception as e:
            self.logger.error(f"Tier 2 error: {e}")
            self.stats["errors"] += 1
            return self._default_scr_output(), None

    async def _call_openai(
        self,
        model: str,
        messages: List[Dict],
        temperature: float = 0.2,
        max_tokens: int = 500,
        logprobs: bool = False
    ) -> Dict:
        """Call OpenAI API"""
        session = await self._get_session()

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if logprobs:
            payload["logprobs"] = True
            payload["top_logprobs"] = 5

        async with session.post(
            self.OPENAI_API,
            headers={
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            },
            json=payload
        ) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"OpenAI API error {resp.status}: {error}")

            data = await resp.json()

        choice = data["choices"][0]
        content = choice["message"]["content"]

        # Track tokens
        usage = data.get("usage", {})
        self.stats["total_tokens"] += usage.get("total_tokens", 0)

        # Extract logprobs if available
        lp_data = []
        if logprobs and "logprobs" in choice:
            lp_content = choice["logprobs"].get("content", [])
            lp_data = [item.get("logprob", 0) for item in lp_content]

        return {"content": content, "logprobs": lp_data}

    def _parse_scr_output(self, content: str) -> SCROutput:
        """Parse JSON from LLM response"""
        try:
            # Try direct parse
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown
            import re
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                except json.JSONDecodeError:
                    return self._default_scr_output()
            else:
                # Try to find JSON object
                match = re.search(r'\{[^{}]*"reasoning_cot"[^{}]*\}', content, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(0))
                    except json.JSONDecodeError:
                        return self._default_scr_output()
                else:
                    return self._default_scr_output()

        return SCROutput(
            reasoning_cot=data.get("reasoning_cot", "No reasoning provided"),
            p_llm_raw=float(data.get("p_llm_raw", 0.5)),
            confidence_stated=float(data.get("confidence_stated", 0.5)),
            key_factors=data.get("key_factors", []),
            risk_flags=data.get("risk_flags", [])
        )

    def _default_scr_output(self) -> SCROutput:
        """Default output when parsing fails"""
        return SCROutput(
            reasoning_cot="Unable to parse LLM response",
            p_llm_raw=0.5,
            confidence_stated=0.3,
            key_factors=["parsing_error"],
            risk_flags=["low_confidence"]
        )

    def _mock_summarize(self, raw_text: str) -> str:
        """Mock summarization for testing"""
        return f"[MOCK SUMMARY] Market showing normal activity. {raw_text[:100]}..."

    def _mock_reason(self, context: PrefixSummaryContext, shock: CounterfactualShock) -> SCROutput:
        """Mock reasoning for testing"""
        # Generate deterministic mock probability based on inputs
        import hashlib
        hash_input = f"{context.ticker}{shock.headline}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        mock_prob = 0.3 + (hash_val % 40) / 100

        severity_adjustment = {
            "MINOR": 0.05,
            "MODERATE": 0.15,
            "MAJOR": 0.25,
            "BLACK_SWAN": 0.35
        }.get(shock.severity, 0.1)

        final_prob = min(0.95, max(0.05, context.current_price + severity_adjustment * (0.5 - mock_prob)))

        return SCROutput(
            reasoning_cot=f"[MOCK] Analysis of {shock.shock_type} shock on {context.ticker}",
            p_llm_raw=final_prob,
            confidence_stated=0.6,
            key_factors=["mock_factor_1", "mock_factor_2"],
            risk_flags=["mock_mode_active"]
        )


# =============================================================================
# L.3: TSALLIS ENTROPY CALCULATION (F.9)
# =============================================================================

class TsallisEntropyCalculator:
    """
    F.9: Tsallis Entropy Score (S_q)

    Measures intrinsic uncertainty and heavy-tailed risk (Black Swan potential)
    in the LLM's prediction from token logprobabilities.

    High entropy = High risk -> Override LLM's stated probability
    """

    def __init__(self, q: float = 1.5, logger: logging.Logger = None):
        """
        Args:
            q: Tsallis entropic index (q > 1 emphasizes rare events)
        """
        self.q = q
        self.logger = logger or logging.getLogger(__name__)

    def calculate_from_logprobs(self, logprobs: List[float]) -> float:
        """
        Calculate Tsallis entropy from token logprobabilities.

        S_q = (1 - sum(p_i^q)) / (q - 1)

        For q -> 1, this approaches Shannon entropy.
        For q > 1, it's more sensitive to rare events (heavy tails).

        Returns:
            Normalized entropy score 0.0 to 1.0 where:
            - Low (<0.3): High confidence, low risk
            - High (>0.7): High uncertainty, potential Black Swan
        """
        if not logprobs:
            return 0.5  # Unknown confidence

        # Convert logprobs to probabilities
        probs = [math.exp(lp) for lp in logprobs if lp is not None]

        if not probs:
            return 0.5

        # Calculate Tsallis entropy
        try:
            sum_pq = sum(p ** self.q for p in probs if p > 0)
            s_q = (1 - sum_pq) / (self.q - 1) if self.q != 1 else -sum(p * math.log(p) for p in probs if p > 0)
        except (ValueError, ZeroDivisionError):
            return 0.5

        # Normalize to 0-1
        # Max Tsallis entropy for uniform distribution over N outcomes
        n = len(probs)
        if n > 1:
            max_entropy = (1 - n ** (1 - self.q)) / (self.q - 1)
            normalized = s_q / max_entropy if max_entropy > 0 else 0.5
        else:
            normalized = 0.0

        return max(0.0, min(1.0, normalized))

    def calculate_from_probability_distribution(self, probs: List[float]) -> float:
        """
        Calculate Tsallis entropy from a probability distribution.

        Alternative method when logprobs not available.
        """
        if not probs or sum(probs) == 0:
            return 0.5

        # Normalize
        total = sum(probs)
        probs = [p / total for p in probs]

        return self.calculate_from_logprobs([math.log(p) if p > 0 else -10 for p in probs])

    def is_high_risk(self, entropy: float, threshold: float = 0.7) -> bool:
        """Check if entropy indicates high risk"""
        return entropy > threshold


# =============================================================================
# F.10: OPTIMAL POSITION SIZE (FRACTIONAL KELLY)
# =============================================================================

class FractionalKellyCalculator:
    """
    F.10: Optimal Position Size (f*)

    Calculates the Fractional Kelly Criterion position size
    using the calibrated probability from DTFE.

    f* = (p * b - q) / b * fraction

    Where:
    - p = calibrated win probability
    - q = 1 - p
    - b = payout ratio
    - fraction = Kelly fraction (typically 0.25 for safety)
    """

    def __init__(
        self,
        kelly_fraction: float = 0.25,
        max_bet_fraction: float = 0.15,
        min_edge_threshold: float = 0.02,
        logger: logging.Logger = None
    ):
        self.kelly_fraction = kelly_fraction
        self.max_bet_fraction = max_bet_fraction
        self.min_edge_threshold = min_edge_threshold
        self.logger = logger or logging.getLogger(__name__)

    def calculate_optimal_size(
        self,
        p_calibrated: float,
        payout_ratio: float,
        capital: float,
        entropy_score: float = 0.0
    ) -> Tuple[float, str]:
        """
        Calculate optimal position size using Fractional Kelly.

        Args:
            p_calibrated: Calibrated win probability
            payout_ratio: Net payout (e.g., 0.9 for 52c binary)
            capital: Available capital
            entropy_score: F.9 Tsallis entropy (risk override)

        Returns:
            (size_dollars, reason_string)
        """
        q = 1 - p_calibrated

        # Edge calculation
        edge = p_calibrated - (q / payout_ratio)

        # Check minimum edge
        if edge < self.min_edge_threshold:
            return 0.0, f"Edge {edge:.2%} below threshold {self.min_edge_threshold:.2%}"

        # Basic Kelly fraction
        if payout_ratio <= 0:
            return 0.0, "Invalid payout ratio"

        kelly_f = edge / payout_ratio

        # Apply fractional Kelly
        fractional_kelly = kelly_f * self.kelly_fraction

        # Entropy-based risk adjustment
        # High entropy = reduce position size
        if entropy_score > 0.7:
            entropy_multiplier = 0.3  # Cut to 30% on high entropy
        elif entropy_score > 0.5:
            entropy_multiplier = 0.6
        else:
            entropy_multiplier = 1.0

        adjusted_kelly = fractional_kelly * entropy_multiplier

        # Cap at maximum bet fraction
        final_fraction = min(adjusted_kelly, self.max_bet_fraction)

        # Calculate dollar size
        size = capital * final_fraction

        reason = f"Kelly={kelly_f:.2%} Frac={fractional_kelly:.2%} Entropy={entropy_score:.2f} Final={final_fraction:.2%}"

        return size, reason

    def calculate_ev(
        self,
        p_calibrated: float,
        size: float,
        payout_ratio: float
    ) -> float:
        """Calculate expected value of the position"""
        win_amount = size * payout_ratio
        lose_amount = size

        ev = p_calibrated * win_amount - (1 - p_calibrated) * lose_amount
        return ev


# =============================================================================
# DIGITAL TWIN FORESIGHT ENGINE (MAIN CLASS)
# =============================================================================

class DigitalTwinForesightEngine:
    """
    DTFE: Digital Twin Foresight Engine

    The generative alpha intelligence that creates a synthetic "digital twin"
    of a Kalshi contract and performs Structured Counterfactual Reasoning (SCR)
    to generate independent, superior probability estimates (P_sim).

    Pipeline:
    1. Build Prefix Summary Context (PSC) from market data
    2. Generate or receive Counterfactual Shock
    3. Execute SCR via Tier 2 LLM
    4. Calculate Tsallis Entropy (F.9) from logprobs
    5. Apply Isotonic Regression calibration
    6. Calculate Optimal Position Size (F.10)
    7. Return tradeable signal or reject on high entropy
    """

    def __init__(
        self,
        llm_client: TieredLLMClient = None,
        calibrator = None,  # Will be CalibrationLayer
        entropy_threshold: float = 0.7,
        kelly_fraction: float = 0.25,
        logger: logging.Logger = None
    ):
        self.logger = logger or logging.getLogger(__name__)

        # Initialize components
        self.llm = llm_client or TieredLLMClient(logger=self.logger)
        self.calibrator = calibrator
        self.entropy_calc = TsallisEntropyCalculator(logger=self.logger)
        self.kelly_calc = FractionalKellyCalculator(
            kelly_fraction=kelly_fraction,
            logger=self.logger
        )

        self.entropy_threshold = entropy_threshold

        # Statistics
        self.stats = {
            "queries_processed": 0,
            "signals_generated": 0,
            "signals_rejected_entropy": 0,
            "avg_entropy": 0.0,
            "avg_p_adjustment": 0.0
        }

        self.logger.info("Digital Twin Foresight Engine initialized")

    async def analyze_contract(
        self,
        ticker: str,
        title: str,
        current_price: float,
        market_data: Dict = None,
        shock: CounterfactualShock = None,
        capital: float = 1000.0
    ) -> DTFEResult:
        """
        Main entry point: Analyze a contract with optional counterfactual shock.

        Args:
            ticker: Contract ticker
            title: Contract title
            current_price: Current market price (0-1)
            market_data: Optional raw market data for PSC enrichment
            shock: Optional pre-defined shock (generates default if None)
            capital: Available capital for position sizing

        Returns:
            DTFEResult with calibrated probability and position size
        """
        self.stats["queries_processed"] += 1

        # 1. Build Prefix Summary Context
        context = await self._build_context(
            ticker=ticker,
            title=title,
            current_price=current_price,
            market_data=market_data
        )

        # 2. Generate or use provided shock
        if shock is None:
            shock = self._generate_default_shock(ticker, title)

        # 3. Execute Structured Counterfactual Reasoning
        scr_output, logprobs = await self.llm.tier2_reason(context, shock)

        # 4. Calculate Tsallis Entropy (F.9)
        if logprobs:
            entropy = self.entropy_calc.calculate_from_logprobs(logprobs)
        else:
            # Estimate from stated confidence
            entropy = 1 - scr_output.confidence_stated

        scr_output.tsallis_entropy = entropy

        # 5. Apply calibration
        p_raw = scr_output.p_llm_raw
        if self.calibrator:
            p_calibrated = self.calibrator.calibrate(p_raw, context.time_to_expiry_days)
        else:
            # Simple adjustment without calibrator
            p_calibrated = self._simple_calibration(p_raw, entropy)

        # Track adjustment
        adjustment = abs(p_calibrated - p_raw)
        n = self.stats["queries_processed"]
        self.stats["avg_p_adjustment"] = self.stats["avg_p_adjustment"] + (adjustment - self.stats["avg_p_adjustment"]) / n
        self.stats["avg_entropy"] = self.stats["avg_entropy"] + (entropy - self.stats["avg_entropy"]) / n

        # 6. Check entropy threshold
        is_tradeable = entropy < self.entropy_threshold
        rejection_reason = ""

        if not is_tradeable:
            self.stats["signals_rejected_entropy"] += 1
            rejection_reason = f"High entropy: {entropy:.2f} > {self.entropy_threshold:.2f}"

        # 7. Calculate optimal position size (F.10)
        payout_ratio = (1 - current_price) / current_price if current_price > 0 else 1.0
        optimal_size, size_reason = self.kelly_calc.calculate_optimal_size(
            p_calibrated=p_calibrated,
            payout_ratio=payout_ratio,
            capital=capital,
            entropy_score=entropy
        )

        if is_tradeable and optimal_size > 0:
            self.stats["signals_generated"] += 1

        return DTFEResult(
            ticker=ticker,
            p_llm_raw=p_raw,
            p_llm_calibrated=p_calibrated,
            tsallis_entropy=entropy,
            optimal_position_size=optimal_size,
            scr_output=scr_output,
            context=context,
            shock=shock,
            is_tradeable=is_tradeable,
            rejection_reason=rejection_reason or size_reason
        )

    async def _build_context(
        self,
        ticker: str,
        title: str,
        current_price: float,
        market_data: Dict = None
    ) -> PrefixSummaryContext:
        """Build Prefix Summary Context for the contract"""

        # Default values
        market_structure = MarketStructure.UNKNOWN
        key_support = current_price * 0.8
        key_resistance = min(1.0, current_price * 1.2)
        tte_days = 30
        volume_24h = 10000
        trend = "sideways"

        # Extract from market data if available
        if market_data:
            # Try to get structured data
            if "market_structure" in market_data:
                try:
                    market_structure = MarketStructure(market_data["market_structure"])
                except ValueError:
                    pass

            key_support = market_data.get("support", key_support)
            key_resistance = market_data.get("resistance", key_resistance)

            # Calculate TTE from expiration
            if "expiration_time" in market_data:
                try:
                    exp_time = datetime.fromisoformat(market_data["expiration_time"].replace("Z", "+00:00"))
                    tte_days = max(1, (exp_time - datetime.utcnow()).days)
                except (ValueError, TypeError):
                    pass

            volume_24h = market_data.get("volume_24h", volume_24h)

            # Determine trend from recent price action
            if "price_history" in market_data and len(market_data["price_history"]) > 1:
                prices = market_data["price_history"]
                if prices[-1] > prices[0] * 1.05:
                    trend = "up"
                elif prices[-1] < prices[0] * 0.95:
                    trend = "down"

        return PrefixSummaryContext(
            ticker=ticker,
            title=title,
            current_price=current_price,
            market_structure=market_structure,
            key_support=key_support,
            key_resistance=key_resistance,
            time_to_expiry_days=tte_days,
            volume_24h=volume_24h,
            recent_trend=trend
        )

    def _generate_default_shock(self, ticker: str, title: str) -> CounterfactualShock:
        """Generate a default counterfactual shock based on contract type"""

        # Detect contract type from ticker/title
        title_lower = title.lower()

        if any(x in title_lower for x in ["fed", "rate", "gdp", "inflation", "cpi"]):
            return CounterfactualShock(
                shock_type="ECONOMIC",
                headline="Federal Reserve announces emergency policy shift",
                description="The Federal Reserve unexpectedly changes its policy stance due to new economic data.",
                severity="MAJOR"
            )
        elif any(x in title_lower for x in ["election", "president", "congress", "senate"]):
            return CounterfactualShock(
                shock_type="POLITICAL",
                headline="Major political development announced",
                description="A significant political event occurs that could shift election dynamics.",
                severity="MODERATE"
            )
        elif any(x in title_lower for x in ["earnings", "stock", "company"]):
            return CounterfactualShock(
                shock_type="CORPORATE",
                headline="Company announces unexpected results",
                description="The company releases surprising news that affects market expectations.",
                severity="MODERATE"
            )
        else:
            return CounterfactualShock(
                shock_type="GEOPOLITICAL",
                headline="Unexpected global event occurs",
                description="A significant global event impacts market sentiment and expectations.",
                severity="MODERATE"
            )

    def _simple_calibration(self, p_raw: float, entropy: float) -> float:
        """
        Simple calibration when full Isotonic Regression not available.

        Adjusts for typical LLM overconfidence.
        """
        # LLMs tend to be overconfident - regress toward 0.5
        regression_factor = 0.3 + entropy * 0.2  # Higher entropy = more regression

        p_calibrated = p_raw * (1 - regression_factor) + 0.5 * regression_factor

        # Ensure valid range
        return max(0.01, min(0.99, p_calibrated))

    async def generate_shock_scenarios(
        self,
        ticker: str,
        title: str,
        n_scenarios: int = 3
    ) -> List[CounterfactualShock]:
        """
        Use Tier 1 LLM to generate relevant shock scenarios for a contract.
        """
        # For now, return deterministic scenarios
        base_shock = self._generate_default_shock(ticker, title)

        scenarios = [base_shock]

        # Add variations
        severities = ["MINOR", "MODERATE", "MAJOR"]
        for i, sev in enumerate(severities[:n_scenarios-1]):
            scenarios.append(CounterfactualShock(
                shock_type=base_shock.shock_type,
                headline=f"Scenario {i+2}: {base_shock.headline}",
                description=f"Alternative scenario with {sev.lower()} impact.",
                severity=sev
            ))

        return scenarios

    def get_stats(self) -> Dict:
        """Get DTFE statistics"""
        return {
            **self.stats,
            "llm_stats": self.llm.stats,
            "mock_mode": self.llm.mock_mode
        }

    async def close(self):
        """Clean up resources"""
        await self.llm.close()


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def example_dtfe_usage():
    """Example showing DTFE usage"""
    dtfe = DigitalTwinForesightEngine()

    # Analyze a contract
    result = await dtfe.analyze_contract(
        ticker="FED-RATE-DEC",
        title="Fed Rate Cut in December",
        current_price=0.65,
        capital=1000.0
    )

    print(f"DTFE Analysis: {result.ticker}")
    print(f"  Raw P: {result.p_llm_raw:.2%}")
    print(f"  Calibrated P: {result.p_llm_calibrated:.2%}")
    print(f"  Tsallis Entropy: {result.tsallis_entropy:.3f}")
    print(f"  Tradeable: {result.is_tradeable}")
    print(f"  Optimal Size: ${result.optimal_position_size:.2f}")
    print(f"  Reasoning: {result.scr_output.reasoning_cot[:200]}...")

    await dtfe.close()


if __name__ == "__main__":
    asyncio.run(example_dtfe_usage())
