"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Todo REST API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./todos.db"
    
    # Authentication
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API Settings
    api_prefix: str = "/api/v1"
    max_page_size: int = 100
    default_page_size: int = 10
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()