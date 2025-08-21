"""
WEB-012: Rate Limiting and Retry Design with Idempotency Keys
Main FastAPI application
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import uvicorn
from decouple import config as env_config
import structlog

from models import (
    Base, PaymentRequest, PaymentResponse, PaymentTransaction,
    PaymentStatus, RateLimitResponse, RetryConfig, IdempotencyConfig,
    AuditEventType, AuditLog
)
from idempotency import IdempotencyManager
from rate_limiter import DistributedRateLimiter

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Configuration
DATABASE_URL = env_config('DATABASE_URL', default='postgresql+asyncpg://user:pass@localhost/payments')
REDIS_URL = env_config('REDIS_URL', default='redis://localhost:6379')
API_KEY = env_config('API_KEY', default='test-api-key')

# Global instances
redis_client: Optional[redis.Redis] = None
engine = None
SessionLocal = None
idempotency_manager: Optional[IdempotencyManager] = None
rate_limiter: Optional[DistributedRateLimiter] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_client, engine, SessionLocal, idempotency_manager, rate_limiter
    
    # Startup
    logger.info("Starting application")
    
    # Initialize Redis
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    await redis_client.ping()
    logger.info("Redis connected")
    
    # Initialize database
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")
    
    # Initialize managers
    idempotency_manager = IdempotencyManager(SessionLocal, redis_client)
    rate_limiter = DistributedRateLimiter(redis_client, SessionLocal)
    
    # Start background tasks
    cleanup_task = asyncio.create_task(cleanup_expired_keys())
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Cancel background tasks
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    # Close connections
    if redis_client:
        await redis_client.close()
    
    if engine:
        await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Payment Processing API with Idempotency",
    description="Advanced rate limiting and retry design with idempotency keys",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def cleanup_expired_keys():
    """Background task to cleanup expired idempotency keys"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            
            if idempotency_manager:
                deleted = await idempotency_manager.cleanup_expired_keys()
                logger.info("Cleaned up expired idempotency keys", count=deleted)
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Error in cleanup task", error=str(e))


async def get_db() -> AsyncSession:
    """Get database session"""
    async with SessionLocal() as session:
        yield session


def get_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        # For demo, generate a user ID from IP
        return "anonymous"
    
    # In production, validate JWT token and extract user ID
    token = authorization.replace("Bearer ", "")
    
    # Simplified validation - in production use proper JWT validation
    if token == API_KEY:
        return "test-user"
    
    raise HTTPException(status_code=401, detail="Invalid authorization")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    
    # Skip rate limiting for certain paths
    if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    # Get user ID (simplified)
    user_id = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        if token == API_KEY:
            user_id = "test-user"
    
    # Check rate limits
    is_allowed, rate_limit_response = await rate_limiter.check_rate_limit(
        request, user_id
    )
    
    if not is_allowed:
        # Return 429 with retry-after header
        response = JSONResponse(
            status_code=429,
            content=rate_limit_response.dict(),
            headers={
                "Retry-After": str(rate_limit_response.retry_after),
                "X-RateLimit-Limit": str(rate_limit_response.limit),
                "X-RateLimit-Remaining": str(rate_limit_response.remaining),
                "X-RateLimit-Reset": rate_limit_response.reset_at.isoformat()
            }
        )
        return response
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers to successful responses
    if user_id:
        limits = await rate_limiter.get_current_limits(request, user_id)
        
        # Add headers for the most restrictive limit
        most_restrictive = min(limits.values(), key=lambda x: x['remaining'])
        response.headers["X-RateLimit-Limit"] = str(most_restrictive['limit'])
        response.headers["X-RateLimit-Remaining"] = str(most_restrictive['remaining'])
        response.headers["X-RateLimit-Reset"] = most_restrictive['reset_at']
    
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "ok" if engine else "error",
            "redis": "ok" if redis_client else "error"
        }
    }


@app.post("/api/v1/payments", response_model=PaymentResponse)
async def process_payment(
    payment_request: PaymentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Process payment with idempotency support"""
    
    # Validate idempotency key
    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header is required for payment requests"
        )
    
    # Validate idempotency key format
    if len(idempotency_key) < 16 or len(idempotency_key) > 255:
        raise HTTPException(
            status_code=400,
            detail="Invalid Idempotency-Key format (must be 16-255 characters)"
        )
    
    async def process_payment_handler():
        """Handler function for payment processing"""
        
        # Create payment transaction
        transaction = PaymentTransaction(
            idempotency_key=idempotency_key,
            user_id=user_id,
            amount=payment_request.amount,
            currency=payment_request.currency,
            description=payment_request.description,
            payment_method=payment_request.payment_method,
            metadata=payment_request.metadata,
            status=PaymentStatus.PROCESSING,
            created_at=datetime.utcnow()
        )
        
        db.add(transaction)
        await db.commit()
        
        try:
            # Simulate payment processing
            await asyncio.sleep(0.5)  # Simulate API call to payment gateway
            
            # Random success/failure for demo (80% success rate)
            import random
            if random.random() < 0.8:
                transaction.status = PaymentStatus.COMPLETED
                transaction.processed_at = datetime.utcnow()
            else:
                transaction.status = PaymentStatus.FAILED
                transaction.error_message = "Payment gateway declined the transaction"
            
            transaction.attempts += 1
            transaction.last_attempt_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(transaction)
            
            # Create response
            response_data = PaymentResponse(
                transaction_id=str(transaction.id),
                status=transaction.status,
                amount=transaction.amount,
                currency=transaction.currency,
                description=transaction.description,
                created_at=transaction.created_at,
                processed_at=transaction.processed_at,
                idempotency_key=idempotency_key,
                attempts=transaction.attempts
            )
            
            # Create FastAPI response
            if transaction.status == PaymentStatus.COMPLETED:
                status_code = 200
            else:
                status_code = 402  # Payment Required
            
            response = Response(
                content=response_data.json(),
                status_code=status_code,
                media_type="application/json"
            )
            
            return response
            
        except Exception as e:
            logger.error("Payment processing error", 
                        error=str(e), 
                        transaction_id=str(transaction.id))
            
            transaction.status = PaymentStatus.FAILED
            transaction.error_message = str(e)
            await db.commit()
            
            raise HTTPException(status_code=500, detail="Payment processing failed")
    
    # Process with idempotency
    response, is_replay = await idempotency_manager.process_request(
        idempotency_key=idempotency_key,
        user_id=user_id,
        request=request,
        handler_func=process_payment_handler
    )
    
    return response


@app.get("/api/v1/payments/{transaction_id}", response_model=PaymentResponse)
async def get_payment(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """Get payment transaction details"""
    
    # Validate UUID
    try:
        transaction_uuid = uuid.UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID format")
    
    # Get transaction
    from sqlalchemy import select
    result = await db.execute(
        select(PaymentTransaction).where(
            PaymentTransaction.id == transaction_uuid,
            PaymentTransaction.user_id == user_id
        )
    )
    
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return PaymentResponse(
        transaction_id=str(transaction.id),
        status=transaction.status,
        amount=transaction.amount,
        currency=transaction.currency,
        description=transaction.description,
        created_at=transaction.created_at,
        processed_at=transaction.processed_at,
        idempotency_key=transaction.idempotency_key,
        attempts=transaction.attempts
    )


@app.get("/api/v1/retry-config")
async def get_retry_config():
    """Get recommended retry configuration for clients"""
    
    config = RetryConfig()
    
    return {
        "retry_config": config.dict(),
        "recommended_headers": {
            "Idempotency-Key": "Unique key for each payment request (required)",
            "Authorization": "Bearer <token> (required)"
        },
        "exponential_backoff_formula": "delay = initial_delay * (exponential_base ^ attempt)",
        "example_delays_ms": [
            config.get_delay(i) * 1000 for i in range(1, config.max_retries + 1)
        ]
    }


@app.get("/api/v1/rate-limits")
async def get_rate_limits(
    request: Request,
    user_id: str = Depends(get_user_id)
):
    """Get current rate limit status"""
    
    limits = await rate_limiter.get_current_limits(request, user_id)
    
    return {
        "user_id": user_id,
        "limits": limits,
        "retry_config": RetryConfig().dict()
    }


@app.get("/api/v1/audit-logs")
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
    event_type: Optional[str] = None,
    limit: int = 100
):
    """Get audit logs for user"""
    
    from sqlalchemy import select, desc
    
    query = select(AuditLog).where(AuditLog.user_id == user_id)
    
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    
    query = query.order_by(desc(AuditLog.created_at)).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "user_id": user_id,
        "logs": [
            {
                "id": str(log.id),
                "event_type": log.event_type,
                "created_at": log.created_at.isoformat(),
                "idempotency_key": log.idempotency_key,
                "request_path": log.request_path,
                "response_status": log.response_status,
                "event_details": log.event_details
            }
            for log in logs
        ]
    }


@app.post("/api/v1/simulate-concurrent")
async def simulate_concurrent_requests(
    payment_request: PaymentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_user_id),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    concurrent_count: int = 5
):
    """Simulate concurrent requests with same idempotency key for testing"""
    
    if not idempotency_key:
        idempotency_key = str(uuid.uuid4())
    
    async def make_request():
        try:
            # Create a new request object
            test_request = Request(
                scope={
                    "type": "http",
                    "method": "POST",
                    "path": "/api/v1/payments",
                    "headers": [(b"idempotency-key", idempotency_key.encode())],
                    "query_string": b"",
                }
            )
            
            # Process payment with same idempotency key
            response, is_replay = await idempotency_manager.process_request(
                idempotency_key=idempotency_key,
                user_id=user_id,
                request=test_request,
                handler_func=lambda: process_payment_handler(payment_request, db, user_id, idempotency_key)
            )
            
            return {
                "status": "success",
                "is_replay": is_replay,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Execute concurrent requests
    tasks = [make_request() for _ in range(concurrent_count)]
    results = await asyncio.gather(*tasks)
    
    # Count replays
    replay_count = sum(1 for r in results if r.get("is_replay"))
    
    return {
        "idempotency_key": idempotency_key,
        "concurrent_requests": concurrent_count,
        "replay_count": replay_count,
        "unique_processing": concurrent_count - replay_count,
        "results": results
    }


async def process_payment_handler(payment_request, db, user_id, idempotency_key):
    """Simplified payment handler for testing"""
    transaction = PaymentTransaction(
        idempotency_key=idempotency_key,
        user_id=user_id,
        amount=payment_request.amount,
        currency=payment_request.currency,
        status=PaymentStatus.COMPLETED,
        created_at=datetime.utcnow(),
        processed_at=datetime.utcnow()
    )
    
    db.add(transaction)
    await db.commit()
    
    return Response(
        content={"status": "completed", "transaction_id": str(transaction.id)},
        status_code=200
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )