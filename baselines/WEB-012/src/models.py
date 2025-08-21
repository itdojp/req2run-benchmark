"""Data models for rate limiting and idempotency"""
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, Float, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator

Base = declarative_base()


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class IdempotencyKey(Base):
    """Database model for idempotency keys"""
    __tablename__ = "idempotency_keys"
    
    key = Column(String(255), primary_key=True)
    user_id = Column(String(100), nullable=False)
    request_path = Column(String(500), nullable=False)
    request_method = Column(String(10), nullable=False)
    request_body_hash = Column(String(64), nullable=False)
    
    # Response data
    response_status = Column(Integer)
    response_body = Column(JSON)
    response_headers = Column(JSON)
    
    # Status tracking
    status = Column(String(20), default="pending")
    is_processing = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Lock for concurrent access
    lock_acquired_at = Column(DateTime)
    lock_holder = Column(String(100))
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_expires_at', 'expires_at'),
        Index('idx_created_at', 'created_at'),
    )


class PaymentTransaction(Base):
    """Database model for payment transactions"""
    __tablename__ = "payment_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(String(255), unique=True, nullable=False)
    user_id = Column(String(100), nullable=False)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    description = Column(String(500))
    payment_method = Column(String(50))
    
    # Status
    status = Column(String(20), default=PaymentStatus.PENDING)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Audit
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime)
    error_message = Column(String(1000))
    
    # Metadata
    metadata = Column(JSON)
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_user_id', 'user_id'),
        Index('idx_payment_status', 'status'),
        Index('idx_payment_created_at', 'created_at'),
    )


class AuditLog(Base):
    """Database model for audit logging"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Request information
    idempotency_key = Column(String(255))
    user_id = Column(String(100))
    request_id = Column(String(100))
    request_path = Column(String(500))
    request_method = Column(String(10))
    request_headers = Column(JSON)
    request_body = Column(JSON)
    
    # Response information
    response_status = Column(Integer)
    response_body = Column(JSON)
    response_time_ms = Column(Float)
    
    # Event details
    event_type = Column(String(50))  # payment_attempt, rate_limit_exceeded, etc.
    event_details = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Client information
    client_ip = Column(String(45))
    user_agent = Column(String(500))
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_idempotency_key', 'idempotency_key'),
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_event_type', 'event_type'),
    )


class RateLimitRule(BaseModel):
    """Rate limit rule configuration"""
    name: str = Field(..., description="Rule name")
    limit: int = Field(..., gt=0, description="Request limit")
    window_seconds: int = Field(..., gt=0, description="Time window in seconds")
    scope: str = Field(default="global", description="Scope: global, user, ip")
    burst_limit: Optional[int] = Field(None, description="Burst limit for token bucket")
    
    @validator('scope')
    def validate_scope(cls, v):
        allowed_scopes = ['global', 'user', 'ip', 'endpoint', 'user_endpoint']
        if v not in allowed_scopes:
            raise ValueError(f'Scope must be one of {allowed_scopes}')
        return v


class PaymentRequest(BaseModel):
    """Payment request model"""
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field(..., regex=r'^[A-Z]{3}$', description="Currency code (ISO 4217)")
    description: Optional[str] = Field(None, max_length=500)
    payment_method: str = Field(..., description="Payment method")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('currency')
    def validate_currency(cls, v):
        allowed_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'AUD', 'CAD', 'CHF']
        if v not in allowed_currencies:
            raise ValueError(f'Currency {v} not supported')
        return v
    
    @validator('payment_method')
    def validate_payment_method(cls, v):
        allowed_methods = ['credit_card', 'debit_card', 'bank_transfer', 'paypal', 'crypto']
        if v not in allowed_methods:
            raise ValueError(f'Payment method {v} not supported')
        return v


class PaymentResponse(BaseModel):
    """Payment response model"""
    transaction_id: str
    status: PaymentStatus
    amount: float
    currency: str
    description: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    idempotency_key: str
    attempts: int = 0
    
    class Config:
        use_enum_values = True


class RateLimitResponse(BaseModel):
    """Rate limit exceeded response"""
    error: str = "rate_limit_exceeded"
    message: str
    retry_after: int  # seconds
    limit: int
    remaining: int
    reset_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RetryConfig(BaseModel):
    """Retry configuration for clients"""
    max_retries: int = Field(default=3, ge=0, le=10)
    initial_delay_ms: int = Field(default=1000, ge=100, le=10000)
    max_delay_ms: int = Field(default=30000, ge=1000, le=60000)
    exponential_base: float = Field(default=2.0, ge=1.1, le=3.0)
    jitter: bool = Field(default=True)
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff"""
        if attempt <= 0:
            return 0
        
        # Calculate exponential delay
        delay = self.initial_delay_ms * (self.exponential_base ** (attempt - 1))
        
        # Apply maximum delay cap
        delay = min(delay, self.max_delay_ms)
        
        # Add jitter if enabled (±20% randomization)
        if self.jitter:
            import random
            jitter_range = delay * 0.2
            delay = delay + random.uniform(-jitter_range, jitter_range)
        
        return delay / 1000.0  # Convert to seconds


class IdempotencyConfig:
    """Configuration for idempotency handling"""
    
    # TTL for idempotency keys
    IDEMPOTENCY_KEY_TTL = timedelta(hours=24)
    
    # Lock timeout for concurrent request handling
    LOCK_TIMEOUT = timedelta(seconds=30)
    
    # Retry delay for acquiring lock
    LOCK_RETRY_DELAY = 0.1  # seconds
    LOCK_MAX_RETRIES = 100  # 10 seconds total
    
    # Header name for idempotency key
    IDEMPOTENCY_HEADER = "Idempotency-Key"
    
    # Maximum request body size for hashing
    MAX_BODY_SIZE = 1024 * 1024  # 1MB


class RateLimitConfig:
    """Configuration for rate limiting"""
    
    # Default rate limits
    DEFAULT_LIMITS = [
        RateLimitRule(
            name="global",
            limit=1000,
            window_seconds=60,
            scope="global"
        ),
        RateLimitRule(
            name="per_user",
            limit=100,
            window_seconds=60,
            scope="user"
        ),
        RateLimitRule(
            name="payment_endpoint",
            limit=10,
            window_seconds=60,
            scope="user_endpoint"
        ),
        RateLimitRule(
            name="burst",
            limit=20,
            window_seconds=1,
            scope="user",
            burst_limit=50
        )
    ]
    
    # Redis key prefixes
    REDIS_PREFIX = "rate_limit"
    REDIS_TTL = 3600  # 1 hour
    
    # Headers
    RATE_LIMIT_HEADER = "X-RateLimit-Limit"
    RATE_LIMIT_REMAINING_HEADER = "X-RateLimit-Remaining"
    RATE_LIMIT_RESET_HEADER = "X-RateLimit-Reset"
    RETRY_AFTER_HEADER = "Retry-After"


class AuditEventType(str, Enum):
    """Audit event types"""
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_RETRIED = "payment_retried"
    IDEMPOTENT_REQUEST = "idempotent_request"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CONCURRENT_REQUEST = "concurrent_request"
    LOCK_ACQUIRED = "lock_acquired"
    LOCK_RELEASED = "lock_released"
    LOCK_TIMEOUT = "lock_timeout"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"