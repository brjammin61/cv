"""
The Oracle - Data Connectors

This package handles connections to prediction market exchanges
(Kalshi and Polymarket) for real-time data ingestion.
"""

from .kalshi_connector import KalshiConnector
from .polymarket_connector import PolymarketConnector
from .data_models import OrderBookData, MarketData, TradeData

__all__ = [
    'KalshiConnector',
    'PolymarketConnector',
    'OrderBookData',
    'MarketData',
    'TradeData'
]

__version__ = '1.0.0'
