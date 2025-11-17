"""
Omega Engine Database Models
Proprietary MEV analytics data structures
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, BigInteger, Date, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

OmegaBase = declarative_base()


class MEVOpportunity(OmegaBase):
    """
    Individual MEV opportunities detected in blocks
    This is the raw data that powers everything else
    """
    __tablename__ = "omega_mev_opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    block_number = Column(BigInteger, nullable=False, index=True)
    tx_hash = Column(String(66), nullable=False, unique=True)
    mev_type = Column(String(50), nullable=False, index=True)  # 'arbitrage', 'liquidation', 'sandwich', 'jit'
    profit_estimate = Column(Float, default=0.0)
    validator_address = Column(String(42), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    metadata = Column(JSON)  # Store additional context (DEXes, tokens, etc.)
    
    # Indexes for fast queries
    __table_args__ = (
        Index('idx_block_validator', 'block_number', 'validator_address'),
        Index('idx_type_timestamp', 'mev_type', 'timestamp'),
    )


class ValidatorMEVScore(OmegaBase):
    """
    Daily MEV efficiency scores for validators
    This is what we sell to customers
    """
    __tablename__ = "omega_validator_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    validator_address = Column(String(42), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    efficiency_score = Column(Float, default=0.0)  # 0-100
    mev_captured = Column(Float, default=0.0)
    mev_available = Column(Float, default=0.0)
    block_count = Column(Integer, default=0)
    
    # Breakdown by MEV type
    arbitrage_count = Column(Integer, default=0)
    arbitrage_profit = Column(Float, default=0.0)
    liquidation_count = Column(Integer, default=0)
    liquidation_profit = Column(Float, default=0.0)
    sandwich_count = Column(Integer, default=0)
    sandwich_profit = Column(Float, default=0.0)
    jit_count = Column(Integer, default=0)
    jit_profit = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_validator_date', 'validator_address', 'date', unique=True),
    )


class OmegaSubscriber(OmegaBase):
    """
    Premium subscribers who pay for Omega intelligence
    """
    __tablename__ = "omega_subscribers"
    
    id = Column(Integer, primary_key=True, index=True)
    validator_address = Column(String(42), unique=True, nullable=False)
    email = Column(String(255))
    subscription_tier = Column(String(20), nullable=False)  # 'basic', 'pro', 'enterprise'
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    
    # Subscription metadata
    monthly_price = Column(Float)  # Amount they pay per month
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_payment_at = Column(DateTime)
    
    # Usage tracking
    api_calls_today = Column(Integer, default=0)
    api_calls_month = Column(Integer, default=0)
    api_limit_daily = Column(Integer, default=100)  # Varies by tier
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIUsage(OmegaBase):
    """
    Track API usage for billing and rate limiting
    """
    __tablename__ = "omega_api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String(64), nullable=False, index=True)
    endpoint = Column(String(100))
    method = Column(String(10))
    response_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_key_timestamp', 'api_key', 'timestamp'),
    )


class BlockData(OmegaBase):
    """
    Cached block data for analysis
    Stores processed block info to avoid re-fetching
    """
    __tablename__ = "omega_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    block_number = Column(BigInteger, unique=True, nullable=False, index=True)
    block_hash = Column(String(66))
    validator_address = Column(String(42), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    tx_count = Column(Integer, default=0)
    mev_opportunities = Column(Integer, default=0)
    total_mev_captured = Column(Float, default=0.0)
    
    # Raw data
    transactions = Column(JSON)  # Store tx hashes and basic info
    mev_summary = Column(JSON)  # Summary of MEV found
    
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_validator_timestamp', 'validator_address', 'timestamp'),
    )
