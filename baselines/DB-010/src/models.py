"""Data models for financial transaction system"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator


class TransactionState(str, Enum):
    """Transaction states"""
    PENDING = "pending"
    PREPARED = "prepared"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class Account(BaseModel):
    """Account model"""
    id: UUID = Field(default_factory=uuid4)
    balance: Decimal = Field(decimal_places=2)
    currency: str = "USD"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 0  # For optimistic locking
    
    @validator('balance')
    def validate_balance(cls, v):
        if v < 0:
            raise ValueError("Balance cannot be negative")
        return v
    
    class Config:
        json_encoders = {
            UUID: str,
            Decimal: float,
            datetime: lambda v: v.isoformat()
        }


class TransferRequest(BaseModel):
    """Transfer request model"""
    from_account_id: UUID
    to_account_id: UUID
    amount: Decimal = Field(gt=0, decimal_places=2)
    idempotency_key: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v > Decimal("1000000"):  # Max transfer limit
            raise ValueError("Amount exceeds maximum transfer limit")
        return v
    
    @validator('to_account_id')
    def validate_different_accounts(cls, v, values):
        if 'from_account_id' in values and v == values['from_account_id']:
            raise ValueError("Cannot transfer to the same account")
        return v


class TransferResponse(BaseModel):
    """Transfer response model"""
    transaction_id: UUID
    from_account_id: UUID
    to_account_id: UUID
    amount: Decimal
    status: TransactionState
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            UUID: str,
            Decimal: float,
            datetime: lambda v: v.isoformat()
        }


class TransactionStatus(BaseModel):
    """Transaction status model"""
    transaction_id: UUID
    status: TransactionState
    from_account_id: UUID
    to_account_id: UUID
    amount: Decimal
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    class Config:
        json_encoders = {
            UUID: str,
            Decimal: float,
            datetime: lambda v: v.isoformat()
        }


class AccountBalance(BaseModel):
    """Account balance model"""
    account_id: UUID
    balance: Decimal
    currency: str = "USD"
    as_of: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            UUID: str,
            Decimal: float,
            datetime: lambda v: v.isoformat()
        }


class AuditLog(BaseModel):
    """Audit log entry"""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transaction_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    action: str
    amount: Optional[Decimal] = None
    balance_before: Optional[Decimal] = None
    balance_after: Optional[Decimal] = None
    status: str
    error_message: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            UUID: str,
            Decimal: float,
            datetime: lambda v: v.isoformat()
        }


class IdempotencyRecord(BaseModel):
    """Idempotency record for exactly-once processing"""
    idempotency_key: str
    transaction_id: UUID
    result: dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }