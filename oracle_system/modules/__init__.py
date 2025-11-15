"""
The Oracle - Prediction Market Analysis Engine
Core Analytical Modules

This package contains all analytical modules that power
the Oracle prediction market analysis system.
"""

# Core analytical engines (Modules 1-5)
from .mod_01_bias_corrector import BiasCorrector
from .mod_02_flb_adjuster import FavoriteLongshotAdjuster
from .mod_03_rfr_adjuster import RiskFreeRateAdjuster
from .mod_04_dutchbook_detector import DutchBookDetector
from .mod_05_spatial_arb_detector import SpatialArbitrageDetector

# Data collection and validation (Modules 6-8)
from .mod_06_data_collector import DataCollector
from .mod_07_signal_tracker import SignalTracker
from .mod_08_backtester import Backtester, BacktestResult

# Automation and ML (Modules 9-10)
from .mod_09_auto_executor import AutoExecutor, ExecutionMode, RiskLevel
from .mod_10_ml_optimizer import MLOptimizer

__all__ = [
    # Core engines
    'BiasCorrector',
    'FavoriteLongshotAdjuster',
    'RiskFreeRateAdjuster',
    'DutchBookDetector',
    'SpatialArbitrageDetector',
    # Data & validation
    'DataCollector',
    'SignalTracker',
    'Backtester',
    'BacktestResult',
    # Automation & ML
    'AutoExecutor',
    'ExecutionMode',
    'RiskLevel',
    'MLOptimizer'
]

__version__ = '3.0.0'  # Now includes automated trading & ML optimization
