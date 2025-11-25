"""
ContextParser.py - Kalshi Event Metadata & Settlement Parser
MIMIC V3.1 - Production Ready
Merged from Oracle Development Team patterns
"""

import re
from datetime import datetime
from typing import Dict, Optional, Tuple


class KalshiContextParser:
    """
    Optimized parser for Kalshi event metadata extraction and compression.
    Reduces verbose Kalshi data to LLM-friendly structured format.

    Strategy:
    - Uses "Anchor Patterning" - looks for Agency Anchors to isolate sources
    - Treats tickers as composite codes: CATEGORY-DATE-STRIKE
    - Non-blocking, synchronous parser downstream of async API fetcher
    """

    def __init__(self):
        # Ticker prefix -> Human readable name
        self.ticker_map = {
            "FED": "Federal Funds Rate",
            "CPI": "Consumer Price Index (CPI)",
            "KXCPI": "Consumer Price Index (CPI)",
            "INX": "S&P 500 Index",
            "KXINX": "S&P 500 Index",
            "PPI": "Producer Price Index",
            "UNEMP": "U3 Unemployment Rate",
            "KXU3": "U3 Unemployment Rate",
            "GDP": "US GDP Growth",
            "KXGDP": "US GDP Growth",
            "KXHIGH": "Daily High Temperature",
            "KXLOW": "Daily Low Temperature",
            "WTI": "WTI Crude Oil Prices",
            "TR": "Total Returns",
            "CONTROL": "Congressional Control",
            "PRES": "Presidential Election",
        }

        # Domain -> Agency name mapping
        self.agency_map = {
            "bls.gov": "Bureau of Labor Statistics",
            "federalreserve.gov": "Federal Reserve",
            "commerce.gov": "Department of Commerce",
            "noaa.gov": "National Weather Service",
            "cmegroup.com": "CME FedWatch",
            "treasury.gov": "US Treasury",
            "bea.gov": "Bureau of Economic Analysis",
            "census.gov": "US Census Bureau",
        }

        # Regex to extract Agency from legalese
        # Matches: "released by the Bureau of Labor Statistics"
        self.agency_regex = re.compile(
            r"(?:released|published|reported|announced)\s+by\s+(?:the\s+)?([A-Z][a-zA-Z\s&]+?)(?:\.|,|;|\s+in\s+)",
            re.IGNORECASE
        )

        # Ticker pattern templates for search query generation
        self.ticker_patterns = {
            r"KXCPI-(\d{2})([A-Z]{3})-T([\d.]+)": ("CPI", "{month} {year}", "above {value}%"),
            r"CPI-(\d{2})([A-Z]{3})-T?([\d.]+)": ("CPI", "{month} {year}", "above {value}%"),
            r"KXU3-(\d{2})([A-Z]{3})-T([\d.]+)": ("Unemployment", "{month} {year}", "above {value}%"),
            r"FED-(\d{2})([A-Z]{3})-T([\d.]+)": ("Fed Rate", "{month} {year}", "at {value}%"),
            r"KXHIGH([A-Z]{2,4})-(\d{2})([A-Z]{3})(\d{2})-([BT])([\d.]+)": ("Temperature", "{city} {date}", "{dir} {value}F"),
            r"INX-(\d{2})([A-Z]{3})(\d{2})?": ("S&P 500", "{month} {day} {year}", "closing price"),
            r"CONTROL([HS])-(\d{4})-([DR])": ("Congress", "{chamber} {year}", "{party} control"),
        }

        # City code mapping for weather tickers
        self.city_map = {
            "NY": "New York",
            "NYC": "New York",
            "LAX": "Los Angeles",
            "LA": "Los Angeles",
            "CHI": "Chicago",
            "MIA": "Miami",
            "DEN": "Denver",
            "PHX": "Phoenix",
            "SEA": "Seattle",
            "ATL": "Atlanta",
            "BOS": "Boston",
            "DFW": "Dallas",
        }

        # Month abbreviation mapping
        self.months = {
            'JAN': ('January', '01'), 'FEB': ('February', '02'),
            'MAR': ('March', '03'), 'APR': ('April', '04'),
            'MAY': ('May', '05'), 'JUN': ('June', '06'),
            'JUL': ('July', '07'), 'AUG': ('August', '08'),
            'SEP': ('September', '09'), 'OCT': ('October', '10'),
            'NOV': ('November', '11'), 'DEC': ('December', '12')
        }

    def parse_market_context(self, market_json: Dict) -> Dict:
        """
        Main entry point. Ingests raw API JSON, returns structured Context.

        Args:
            market_json: Raw response from /markets/{ticker} endpoint

        Returns:
            Dict with ticker, event_name, source_agency, condition_value,
            search_query, and llm_prompt_string
        """
        ticker = market_json.get("ticker", "")
        title = market_json.get("title", "")
        subtitle = market_json.get("subtitle", "")
        rules = market_json.get("rules_primary", "")
        settlement_sources = market_json.get("settlement_sources", [])

        # 1. Extract Source Agency (try multiple methods)
        agency = self._extract_agency(rules, settlement_sources)

        # 2. Extract Condition/Strike
        condition = title if title else self._parse_condition_from_ticker(ticker)

        # 3. Determine threshold and direction
        threshold_info = self._extract_threshold(rules, title)

        # 4. Generate Natural Language Search Query
        search_query = self._generate_search_query(ticker, title, subtitle)

        return {
            "ticker": ticker,
            "event_name": f"{title} - {subtitle}" if subtitle else title,
            "source_agency": agency,
            "condition_value": condition,
            "threshold": threshold_info.get("value"),
            "direction": threshold_info.get("direction", "above"),
            "search_query": search_query,
            "llm_prompt_string": self._compress_for_llm(title, agency, condition, subtitle),
            "raw_rules_truncated": rules[:200] if rules else None
        }

    def _extract_agency(self, rules_text: str, settlement_sources: list = None) -> str:
        """
        Extracts the governing body from rules text and settlement sources.
        Uses multiple fallback strategies.
        """
        # Strategy 1: Check settlement_sources first (most reliable)
        if settlement_sources:
            for source in settlement_sources:
                source_str = str(source).lower() if isinstance(source, dict) else source.lower()
                for domain, agency in self.agency_map.items():
                    if domain in source_str:
                        return agency

        # Strategy 2: Regex extraction from rules
        if rules_text:
            match = self.agency_regex.search(rules_text)
            if match:
                return match.group(1).strip()

            # Strategy 3: Keyword fallbacks
            text_lower = rules_text.lower()
            if "census" in text_lower:
                return "US Census Bureau"
            if "bls" in text_lower or "labor statistics" in text_lower:
                return "Bureau of Labor Statistics"
            if "fed" in text_lower or "federal reserve" in text_lower or "fomc" in text_lower:
                return "Federal Reserve"
            if "noaa" in text_lower or "weather" in text_lower or "nws" in text_lower:
                return "NOAA/NWS"
            if "bea" in text_lower or "economic analysis" in text_lower:
                return "Bureau of Economic Analysis"
            if "commerce" in text_lower:
                return "Department of Commerce"

        return "Official Issuer"

    def _extract_threshold(self, rules: str, title: str) -> Dict:
        """
        Extracts threshold value and direction from rules/title.
        """
        combined_text = f"{title} {rules}"

        # Pattern to find threshold values
        pattern = r"(?:above|below|greater than|less than|at least|exceeds?|over|under)\s*([\d.]+)%?"
        match = re.search(pattern, combined_text, re.IGNORECASE)

        direction = "above"
        if match:
            context = combined_text[max(0, match.start()-20):match.start()].lower()
            if any(word in context for word in ["below", "under", "less"]):
                direction = "below"
            return {"value": match.group(1), "direction": direction}

        return {"value": None, "direction": direction}

    def _generate_search_query(self, ticker: str, title: str, subtitle: str) -> str:
        """
        Converts Tickers into search-engine ready queries.

        Input: KXINX-24DEC-T4500
        Output: "S&P 500 closing price December 24 2024 forecast"
        """
        ticker_upper = ticker.upper()

        # 1. Identify Category from ticker prefix
        category = "Market Event"
        for prefix, name in self.ticker_map.items():
            if ticker_upper.startswith(prefix):
                category = name
                break

        # 2. Try to parse date from ticker
        date_str = self._parse_ticker_date(ticker_upper, subtitle)

        # 3. Extract strike/target if present
        strike_info = ""
        parts = ticker_upper.split('-')
        if len(parts) >= 3:
            strike_part = parts[-1]
            if strike_part.startswith('T'):
                strike_info = f"above {strike_part[1:]}"
            elif strike_part.startswith('B'):
                strike_info = f"range {strike_part[1:]}"

        # 4. Construct query
        query_parts = [category, "official data release", date_str, "forecast"]
        if strike_info:
            query_parts.insert(2, strike_info)

        return " ".join(filter(None, query_parts))

    def _parse_ticker_date(self, ticker: str, fallback_subtitle: str) -> str:
        """
        Parses date from various ticker formats.
        Handles: 24DEC, 25DEC18, 25NOV21, etc.
        """
        try:
            parts = ticker.split('-')
            if len(parts) >= 2:
                raw_date = parts[1]

                # Format: 25NOV (year + month)
                if len(raw_date) == 5 and raw_date[:2].isdigit():
                    year = f"20{raw_date[:2]}"
                    month_abbr = raw_date[2:5].upper()
                    if month_abbr in self.months:
                        month_name = self.months[month_abbr][0]
                        return f"{month_name} {year}"

                # Format: 25NOV21 (year + month + day)
                if len(raw_date) == 7 and raw_date[:2].isdigit():
                    year = f"20{raw_date[:2]}"
                    month_abbr = raw_date[2:5].upper()
                    day = raw_date[5:7]
                    if month_abbr in self.months:
                        month_name = self.months[month_abbr][0]
                        return f"{month_name} {day} {year}"

                # Format: DEC25 or NOV24 (month + year)
                for month_abbr in self.months:
                    if raw_date.startswith(month_abbr):
                        month_name = self.months[month_abbr][0]
                        year_part = raw_date[3:]
                        if year_part.isdigit():
                            year = f"20{year_part}" if len(year_part) == 2 else year_part
                            return f"{month_name} {year}"

        except Exception:
            pass

        return fallback_subtitle if fallback_subtitle else ""

    def _compress_for_llm(self, title: str, agency: str, condition: str, subtitle: str) -> str:
        """
        Creates token-efficient string for LLM consumption.
        Format: Event: {Name} | Source: {Agency} | Condition: {Value}
        """
        event_name = f"{title} ({subtitle})" if subtitle else title
        return f"Event: {event_name} | Source: {agency} | Condition: {condition}"

    def _parse_condition_from_ticker(self, ticker: str) -> str:
        """
        Extracts strike info from ticker if title is missing.

        Input: KXINX-24DEC-T4500
        Output: Target > 4500
        """
        parts = ticker.upper().split('-')
        if len(parts) > 2:
            strike_part = parts[-1]
            if strike_part.startswith('T'):
                return f"Target > {strike_part[1:]}"
            if strike_part.startswith('B'):
                return f"Band {strike_part[1:]}"
        return "Unknown Condition"

    def ticker_to_natural_language(self, ticker: str) -> str:
        """
        Converts raw ticker to fully natural language description.
        Useful for display and logging.
        """
        ticker_upper = ticker.upper()

        # Weather tickers
        if ticker_upper.startswith("KXHIGH") or ticker_upper.startswith("KXLOW"):
            return self._parse_weather_ticker(ticker_upper)

        # Economic tickers
        for prefix, name in self.ticker_map.items():
            if ticker_upper.startswith(prefix):
                date_str = self._parse_ticker_date(ticker_upper, "")
                parts = ticker_upper.split('-')

                strike = ""
                if len(parts) >= 3:
                    strike_part = parts[-1]
                    if strike_part.startswith('T'):
                        strike = f" above {strike_part[1:]}%"

                return f"{name} {date_str}{strike}".strip()

        return ticker

    def _parse_weather_ticker(self, ticker: str) -> str:
        """
        Special parser for weather tickers.
        KXHIGHNY-25NOV21-T52 -> New York high temperature November 21 2025 above 52F
        """
        try:
            # Extract city code (after KXHIGH/KXLOW, before dash)
            prefix = "KXHIGH" if "KXHIGH" in ticker else "KXLOW"
            temp_type = "high" if prefix == "KXHIGH" else "low"

            remainder = ticker[len(prefix):]
            parts = remainder.split('-')

            city_code = parts[0]
            city = self.city_map.get(city_code, city_code)

            date_str = self._parse_ticker_date(f"X-{parts[1]}", "") if len(parts) > 1 else ""

            threshold = ""
            direction = "above"
            if len(parts) > 2:
                strike = parts[2]
                if strike.startswith('T'):
                    threshold = strike[1:]
                elif strike.startswith('B'):
                    threshold = strike[1:]
                    direction = "below"

            return f"{city} {temp_type} temperature {date_str} {direction} {threshold}F".strip()

        except Exception:
            return ticker
