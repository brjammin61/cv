"""
Omega Engine - Premium API
Gated endpoints requiring subscription/API key
"""

import secrets
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from classifier import MEVClassifier
from models import OmegaSubscriber, APIUsage
from db_utils import omega_db_session

logger = logging.getLogger(__name__)

# API Key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


# Request/Response Models
class SubscriptionCreate(BaseModel):
    validator_address: str
    email: str
    subscription_tier: str  # 'basic', 'pro', 'enterprise'


class SubscriptionResponse(BaseModel):
    validator_address: str
    subscription_tier: str
    api_key: str
    is_active: bool
    expires_at: Optional[datetime]


class EfficiencyResponse(BaseModel):
    validator: str
    mev_efficiency: float
    timeframe: str


class LeaderboardEntry(BaseModel):
    rank: int
    validator: str
    efficiency: float


def create_omega_api() -> FastAPI:
    """
    Create and configure the Omega Engine premium API
    """
    app = FastAPI(
        title="Omega Engine API",
        description="Premium MEV Analytics for Monad Validators",
        version="1.0.0",
        docs_url="/omega/docs",
        redoc_url="/omega/redoc"
    )
    
    # CORS (restrict in production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict this in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize classifier
    classifier = MEVClassifier()
    
    # Dependency: Verify API key
    async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> OmegaSubscriber:
        """Verify API key and return subscriber"""
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required. Include X-API-Key header."
            )
        
        try:
            with omega_db_session() as db:
                subscriber = db.query(OmegaSubscriber).filter(
                    OmegaSubscriber.api_key == api_key
                ).first()
                
                if not subscriber:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Invalid API key"
                    )
                
                if not subscriber.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Subscription expired or inactive"
                    )
                
                # Check rate limits
                if subscriber.api_calls_today >= subscriber.api_limit_daily:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Daily API limit reached ({subscriber.api_limit_daily} calls/day)"
                    )
                
                # Increment usage
                subscriber.api_calls_today += 1
                subscriber.api_calls_month += 1
                db.commit()
                
                return subscriber
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OMEGA API: Error verifying API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            )
    
    async def log_api_usage(api_key: str, endpoint: str, method: str, response_code: int):
        """Log API usage for analytics"""
        try:
            with omega_db_session() as db:
                usage = APIUsage(
                    api_key=api_key,
                    endpoint=endpoint,
                    method=method,
                    response_code=response_code
                )
                db.add(usage)
                db.commit()
        except Exception as e:
            logger.error(f"OMEGA API: Error logging usage: {e}")
    
    # Public Endpoints (No auth required)
    
    @app.get("/omega/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "Omega Engine API"}
    
    # Premium Endpoints (Auth required)
    
    @app.get("/omega/validator/{address}/efficiency", response_model=EfficiencyResponse)
    async def get_validator_efficiency(
        address: str,
        days: int = 7,
        subscriber: OmegaSubscriber = Depends(verify_api_key)
    ):
        """
        Get MEV efficiency score for a validator
        
        **Requires**: BASIC tier or higher
        **Rate Limit**: Based on subscription tier
        """
        try:
            efficiency = classifier.calculate_mev_efficiency(address, lookback_days=days)
            
            await log_api_usage(
                subscriber.api_key,
                f"/omega/validator/{address}/efficiency",
                "GET",
                200
            )
            
            return {
                "validator": address,
                "mev_efficiency": round(efficiency, 2),
                "timeframe": f"{days}d"
            }
            
        except Exception as e:
            logger.error(f"OMEGA API: Error getting efficiency: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/omega/validator/{address}/report")
    async def get_validator_report(
        address: str,
        subscriber: OmegaSubscriber = Depends(verify_api_key)
    ):
        """
        Get comprehensive MEV report for a validator
        
        **Requires**: PRO tier or higher
        **Includes**:
        - Multi-timeframe efficiency scores
        - MEV breakdown by type
        - Missed opportunity analysis
        - Validator ranking
        - Actionable recommendations
        """
        # Check tier
        if subscriber.subscription_tier not in ['pro', 'enterprise']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PRO or ENTERPRISE subscription required for detailed reports"
            )
        
        try:
            report = classifier.generate_validator_report(address)
            
            await log_api_usage(
                subscriber.api_key,
                f"/omega/validator/{address}/report",
                "GET",
                200
            )
            
            return report
            
        except Exception as e:
            logger.error(f"OMEGA API: Error generating report: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/omega/leaderboard", response_model=List[LeaderboardEntry])
    async def get_mev_leaderboard(
        limit: int = 100,
        days: int = 7,
        subscriber: OmegaSubscriber = Depends(verify_api_key)
    ):
        """
        Get MEV efficiency leaderboard
        
        **Requires**: Any tier
        **Returns**: Top validators ranked by MEV efficiency
        """
        try:
            leaderboard = classifier.get_leaderboard(limit=limit, days=days)
            
            await log_api_usage(
                subscriber.api_key,
                "/omega/leaderboard",
                "GET",
                200
            )
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"OMEGA API: Error getting leaderboard: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/omega/opportunities/recent")
    async def get_recent_opportunities(
        limit: int = 50,
        mev_type: Optional[str] = None,
        subscriber: OmegaSubscriber = Depends(verify_api_key)
    ):
        """
        Get recent MEV opportunities
        
        **Requires**: ENTERPRISE tier only
        **Returns**: Live MEV opportunities as they're detected
        
        This is the nuclear option - real-time MEV intelligence
        """
        # Check tier
        if subscriber.subscription_tier != 'enterprise':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ENTERPRISE subscription required for live opportunities"
            )
        
        try:
            with omega_db_session() as db:
                from .models import MEVOpportunity
                
                query = db.query(MEVOpportunity).order_by(
                    MEVOpportunity.timestamp.desc()
                ).limit(limit)
                
                if mev_type:
                    query = query.filter(MEVOpportunity.mev_type == mev_type)
                
                opportunities = query.all()
                
                result = [
                    {
                        'block_number': op.block_number,
                        'tx_hash': op.tx_hash,
                        'mev_type': op.mev_type,
                        'profit_estimate': op.profit_estimate,
                        'validator': op.validator_address,
                        'timestamp': op.timestamp.isoformat()
                    }
                    for op in opportunities
                ]
                
                await log_api_usage(
                    subscriber.api_key,
                    "/omega/opportunities/recent",
                    "GET",
                    200
                )
                
                return result
                
        except Exception as e:
            logger.error(f"OMEGA API: Error getting opportunities: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Admin Endpoints (For managing subscriptions)
    
    @app.post("/omega/admin/subscribe", response_model=SubscriptionResponse)
    async def create_subscription(subscription: SubscriptionCreate):
        """
        Create a new subscription (Admin only in production)
        
        In production, this should be protected and called by your payment system
        """
        try:
            # Generate API key
            api_key = secrets.token_urlsafe(32)
            
            # Set tier-specific limits
            tier_limits = {
                'basic': 100,
                'pro': 1000,
                'enterprise': 999999  # Unlimited
            }
            
            daily_limit = tier_limits.get(subscription.subscription_tier, 100)
            
            with omega_db_session() as db:
                # Check if already exists
                existing = db.query(OmegaSubscriber).filter(
                    OmegaSubscriber.validator_address == subscription.validator_address
                ).first()
                
                if existing:
                    raise HTTPException(
                        status_code=400,
                        detail="Subscription already exists for this validator"
                    )
                
                # Create subscriber
                subscriber = OmegaSubscriber(
                    validator_address=subscription.validator_address,
                    email=subscription.email,
                    subscription_tier=subscription.subscription_tier,
                    api_key=api_key,
                    is_active=True,
                    api_limit_daily=daily_limit
                )
                
                db.add(subscriber)
                db.commit()
                
                return {
                    "validator_address": subscriber.validator_address,
                    "subscription_tier": subscriber.subscription_tier,
                    "api_key": api_key,
                    "is_active": True,
                    "expires_at": None
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OMEGA API: Error creating subscription: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/omega/admin/usage/{api_key}")
    async def get_usage_stats(api_key: str):
        """
        Get usage statistics for an API key (Admin only)
        """
        try:
            with omega_db_session() as db:
                subscriber = db.query(OmegaSubscriber).filter(
                    OmegaSubscriber.api_key == api_key
                ).first()
                
                if not subscriber:
                    raise HTTPException(status_code=404, detail="Subscriber not found")
                
                # Get usage logs
                recent_usage = db.query(APIUsage).filter(
                    APIUsage.api_key == api_key
                ).order_by(APIUsage.timestamp.desc()).limit(100).all()
                
                return {
                    "validator": subscriber.validator_address,
                    "tier": subscriber.subscription_tier,
                    "calls_today": subscriber.api_calls_today,
                    "calls_month": subscriber.api_calls_month,
                    "daily_limit": subscriber.api_limit_daily,
                    "is_active": subscriber.is_active,
                    "recent_calls": [
                        {
                            "endpoint": u.endpoint,
                            "timestamp": u.timestamp.isoformat(),
                            "response_code": u.response_code
                        }
                        for u in recent_usage
                    ]
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OMEGA API: Error getting usage stats: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    return app


# Create app instance
app = create_omega_api()


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Omega Engine API...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
