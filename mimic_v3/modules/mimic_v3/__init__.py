# MIMIC V3.1 CORTEX - Core Package
# Enhanced with Alpha Feature Engineering

__version__ = "3.1.1"

# Core modules
from .brain import MimicBrain
from .scanner import ShadowScanner, WhaleSignal, StrategyType
from .risk_engine import InstitutionalRiskManager, RiskState
from .news_oracle import NewsOracle
from .persistence import MimicDB
from .maker import PassiveMarketMaker
from .kalshi_client import KalshiClient

# Alpha Feature Engineering (F.1-F.8)
from .alpha_features import (
    AlphaFeatureExtractor,
    AlphaFeatures,
    InformationalEdgeCalculator,
    StructuralEdgeCalculator,
    RiskContextCalculator,
    MarketRegime
)

# Digital Twin Foresight Engine (F.9-F.10, L.1-L.3)
from .dtfe import (
    DigitalTwinForesightEngine,
    TieredLLMClient,
    TsallisEntropyCalculator,
    FractionalKellyCalculator,
    PrefixSummaryContext,
    CounterfactualShock,
    SCROutput,
    DTFEResult
)

# Calibration Layer (C.1-C.2)
from .calibration import (
    CalibrationLayer,
    IsotonicRegressor,
    TTEBiasCorrector,
    CalibrationDiagnostics
)

__all__ = [
    # Version
    "__version__",

    # Core
    "MimicBrain",
    "ShadowScanner",
    "WhaleSignal",
    "StrategyType",
    "InstitutionalRiskManager",
    "RiskState",
    "NewsOracle",
    "MimicDB",
    "PassiveMarketMaker",
    "KalshiClient",

    # Alpha Features
    "AlphaFeatureExtractor",
    "AlphaFeatures",
    "InformationalEdgeCalculator",
    "StructuralEdgeCalculator",
    "RiskContextCalculator",
    "MarketRegime",

    # DTFE
    "DigitalTwinForesightEngine",
    "TieredLLMClient",
    "TsallisEntropyCalculator",
    "FractionalKellyCalculator",
    "PrefixSummaryContext",
    "CounterfactualShock",
    "SCROutput",
    "DTFEResult",

    # Calibration
    "CalibrationLayer",
    "IsotonicRegressor",
    "TTEBiasCorrector",
    "CalibrationDiagnostics"
]
