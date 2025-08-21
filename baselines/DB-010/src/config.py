"""Configuration settings for financial transaction system"""
import os
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Financial Transaction System"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/transactions",
        env="DATABASE_URL"
    )
    pool_min_size: int = Field(default=10, env="DB_POOL_MIN")
    pool_max_size: int = Field(default=20, env="DB_POOL_MAX")
    query_timeout: float = Field(default=10.0, env="DB_QUERY_TIMEOUT")
    
    # Transaction settings
    transaction_timeout_seconds: int = Field(default=30, env="TRANSACTION_TIMEOUT")
    max_retry_attempts: int = Field(default=3, env="MAX_RETRY_ATTEMPTS")
    retry_delay_ms: int = Field(default=100, env="RETRY_DELAY_MS")
    
    # Idempotency
    idempotency_ttl_seconds: int = Field(default=86400, env="IDEMPOTENCY_TTL")  # 24 hours
    
    # Limits
    max_transfer_amount: float = Field(default=1000000.0, env="MAX_TRANSFER_AMOUNT")
    min_transfer_amount: float = Field(default=0.01, env="MIN_TRANSFER_AMOUNT")
    
    # Performance
    max_concurrent_transactions: int = Field(default=20, env="MAX_CONCURRENT_TRANSACTIONS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"