"""
The Oracle - Configuration Management

This package handles all configuration for the Oracle system including
API keys, market definitions, and model parameters.
"""

from .parameters import OracleParameters
from .markets import MarketRegistry

__all__ = ['OracleParameters', 'MarketRegistry']

__version__ = '1.0.0'
