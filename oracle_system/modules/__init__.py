"""
The Oracle - Prediction Market Analysis Engine
Core Analytical Modules

This package contains the five core analytical modules that power
the Oracle prediction market analysis system.
"""

from .mod_01_bias_corrector import BiasCorrector
from .mod_02_flb_adjuster import FavoriteLongshotAdjuster
from .mod_03_rfr_adjuster import RiskFreeRateAdjuster
from .mod_04_dutchbook_detector import DutchBookDetector
from .mod_05_spatial_arb_detector import SpatialArbitrageDetector

__all__ = [
    'BiasCorrector',
    'FavoriteLongshotAdjuster',
    'RiskFreeRateAdjuster',
    'DutchBookDetector',
    'SpatialArbitrageDetector'
]

__version__ = '1.0.0'
