"""
NewsOracle.py - AI-Powered News Sentiment Analysis
MIMIC V3.1 - Production Ready

Implements:
- Perplexity API integration for real-time news search
- Sentiment extraction and scoring
- Context-aware market analysis
- Caching and rate limiting
"""

import os
import asyncio
import aiohttp
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .context_parser import KalshiContextParser


@dataclass
class SentimentResult:
    """Result from sentiment analysis"""
    score: float  # -1 (bearish) to +1 (bullish)
    confidence: float  # 0-1
    summary: str
    sources: List[str]
    query_used: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cached: bool = False


@dataclass
class CacheEntry:
    """Cache entry for sentiment results"""
    result: SentimentResult
    expires_at: datetime


class NewsOracle:
    """
    AI-powered news and sentiment analysis.

    Uses Perplexity API for:
    1. Real-time news search relevant to markets
    2. Sentiment extraction from news
    3. Forecast aggregation

    Includes:
    - Response caching (TTL-based)
    - Rate limiting
    - Fallback to mock data for testing
    """

    PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

    def __init__(
        self,
        api_key: str = None,
        cache_ttl_minutes: int = 15,
        rate_limit_rpm: int = 20,
        mock_mode: bool = False,
        logger: logging.Logger = None
    ):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.rate_limit_rpm = rate_limit_rpm
        self.mock_mode = mock_mode or not self.api_key
        self.logger = logger or logging.getLogger(__name__)

        self.parser = KalshiContextParser()

        # Cache for sentiment results
        self._cache: Dict[str, CacheEntry] = {}

        # Rate limiting
        self._request_times: List[datetime] = []

        # Session for HTTP requests
        self._session: Optional[aiohttp.ClientSession] = None

        # Statistics
        self.stats = {
            "queries_made": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "errors": 0
        }

        if self.mock_mode:
            self.logger.warning("NewsOracle running in MOCK mode (no Perplexity API key)")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Clean up resources"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.lower().encode()).hexdigest()

    def _check_cache(self, query: str) -> Optional[SentimentResult]:
        """Check if we have a valid cached result"""
        key = self._get_cache_key(query)
        if key in self._cache:
            entry = self._cache[key]
            if datetime.utcnow() < entry.expires_at:
                self.stats["cache_hits"] += 1
                result = entry.result
                result.cached = True
                return result
            else:
                del self._cache[key]
        return None

    def _store_cache(self, query: str, result: SentimentResult):
        """Store result in cache"""
        key = self._get_cache_key(query)
        self._cache[key] = CacheEntry(
            result=result,
            expires_at=datetime.utcnow() + self.cache_ttl
        )

        # Clean old entries
        now = datetime.utcnow()
        expired = [k for k, v in self._cache.items() if v.expires_at < now]
        for k in expired:
            del self._cache[k]

    async def _check_rate_limit(self):
        """Enforce rate limiting"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Remove old timestamps
        self._request_times = [t for t in self._request_times if t > minute_ago]

        if len(self._request_times) >= self.rate_limit_rpm:
            # Wait until oldest request expires
            wait_time = (self._request_times[0] - minute_ago).total_seconds()
            if wait_time > 0:
                self.logger.debug(f"Rate limit: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

        self._request_times.append(now)

    async def get_sentiment_snapshot(
        self,
        raw_market_data: Dict,
        additional_context: str = None
    ) -> SentimentResult:
        """
        Get sentiment analysis for a market.

        Args:
            raw_market_data: Market data from Kalshi API
            additional_context: Optional extra context to include

        Returns:
            SentimentResult with score, confidence, and summary
        """
        self.stats["queries_made"] += 1

        # Parse market context
        context = self.parser.parse_market_context(raw_market_data)
        query = context["search_query"]

        # Check cache first
        cached = self._check_cache(query)
        if cached:
            return cached

        # Use mock mode if no API key
        if self.mock_mode:
            return await self._mock_sentiment(context)

        # Rate limit check
        await self._check_rate_limit()

        # Call Perplexity API
        try:
            result = await self._call_perplexity(context, additional_context)
            self._store_cache(query, result)
            return result
        except Exception as e:
            self.logger.error(f"Perplexity API error: {e}")
            self.stats["errors"] += 1
            return await self._mock_sentiment(context)

    async def _call_perplexity(
        self,
        context: Dict,
        additional_context: str = None
    ) -> SentimentResult:
        """
        Call Perplexity API for sentiment analysis.
        """
        self.stats["api_calls"] += 1

        # Build the prompt
        llm_context = context["llm_prompt_string"]
        search_query = context["search_query"]

        system_prompt = """You are a financial analyst AI. Analyze the latest news and data to provide sentiment analysis for prediction market events.

Your response must be valid JSON with this exact format:
{
    "sentiment_score": <float from -1.0 to 1.0>,
    "confidence": <float from 0.0 to 1.0>,
    "summary": "<brief 1-2 sentence summary>",
    "key_factors": ["<factor1>", "<factor2>"]
}

Sentiment scale:
- -1.0: Strongly bearish (event very unlikely)
- 0.0: Neutral/uncertain
- +1.0: Strongly bullish (event very likely)

Be concise and focus on recent, relevant information."""

        user_prompt = f"""Analyze the following prediction market event:

{llm_context}

Search for: {search_query}

{f"Additional context: {additional_context}" if additional_context else ""}

What is the current sentiment and likelihood based on recent news and data?"""

        session = await self._get_session()

        async with session.post(
            self.PERPLEXITY_API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 500,
                "return_citations": True
            }
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"API returned {response.status}: {error_text}")

            data = await response.json()

        # Parse response
        content = data["choices"][0]["message"]["content"]
        citations = data.get("citations", [])

        # Extract JSON from response
        result_data = self._parse_llm_response(content)

        return SentimentResult(
            score=result_data.get("sentiment_score", 0.0),
            confidence=result_data.get("confidence", 0.5),
            summary=result_data.get("summary", "Unable to analyze"),
            sources=citations[:5] if citations else [],
            query_used=search_query
        )

    def _parse_llm_response(self, content: str) -> Dict:
        """Parse JSON from LLM response, handling various formats"""
        # Try direct JSON parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in text
        json_match = re.search(r'\{[^{}]*"sentiment_score"[^{}]*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Fallback: try to extract sentiment from text
        self.logger.warning(f"Could not parse JSON from: {content[:200]}")
        return {
            "sentiment_score": 0.0,
            "confidence": 0.3,
            "summary": content[:200] if content else "Parse error"
        }

    async def _mock_sentiment(self, context: Dict) -> SentimentResult:
        """
        Generate mock sentiment for testing.
        Uses deterministic hashing for consistency.
        """
        # Create deterministic "sentiment" based on query
        query = context["search_query"]
        hash_val = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)

        # Map to -1 to 1 range
        score = ((hash_val % 1000) / 500) - 1.0

        # Add some time-based variation
        hour = datetime.utcnow().hour
        score += (hour - 12) / 100  # Small hourly drift

        # Clamp to valid range
        score = max(-1.0, min(1.0, score))

        # Mock confidence based on how "strong" the score is
        confidence = 0.3 + abs(score) * 0.4

        await asyncio.sleep(0.1)  # Simulate API latency

        return SentimentResult(
            score=round(score, 3),
            confidence=round(confidence, 2),
            summary=f"[MOCK] Simulated sentiment for: {context['event_name'][:50]}",
            sources=["mock_source"],
            query_used=query
        )

    async def batch_sentiment(
        self,
        markets: List[Dict],
        max_concurrent: int = 5
    ) -> Dict[str, SentimentResult]:
        """
        Get sentiment for multiple markets concurrently.

        Args:
            markets: List of market data dicts
            max_concurrent: Max concurrent API calls

        Returns:
            Dict mapping ticker -> SentimentResult
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_market(market: Dict) -> Tuple[str, SentimentResult]:
            ticker = market.get("ticker", "unknown")
            async with semaphore:
                result = await self.get_sentiment_snapshot(market)
            return ticker, result

        tasks = [process_market(m) for m in markets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Batch sentiment error: {result}")
            else:
                ticker, sentiment = result
                output[ticker] = sentiment

        return output

    def get_stats(self) -> Dict:
        """Get oracle statistics"""
        return {
            **self.stats,
            "cache_size": len(self._cache),
            "mode": "mock" if self.mock_mode else "live"
        }


# ==================== USAGE EXAMPLE ====================

async def example_usage():
    """Example showing NewsOracle usage"""

    oracle = NewsOracle(mock_mode=True)  # Use mock for demo

    # Example market data
    market = {
        "ticker": "KXCPI-25DEC-T0.3",
        "title": "CPI > 3.0%",
        "subtitle": "December 2025",
        "rules_primary": "Settlement based on data released by the Bureau of Labor Statistics..."
    }

    try:
        result = await oracle.get_sentiment_snapshot(market)
        print(f"Sentiment: {result.score:.2f}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Summary: {result.summary}")
        print(f"Query: {result.query_used}")
    finally:
        await oracle.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
