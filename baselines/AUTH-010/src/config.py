"""Configuration settings for OAuth 2.1/OIDC provider"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "OAuth 2.1/OIDC Provider"
    debug: bool = Field(default=False, env="DEBUG")
    base_url: str = Field(default="http://localhost:8000", env="BASE_URL")
    
    # Security
    secret_key: str = Field(
        default="change-me-in-production-use-strong-secret-key",
        env="SECRET_KEY"
    )
    jwt_algorithm: str = "RS256"
    jwt_private_key_path: str = Field(
        default="config/private_key.pem",
        env="JWT_PRIVATE_KEY_PATH"
    )
    jwt_public_key_path: str = Field(
        default="config/public_key.pem",
        env="JWT_PUBLIC_KEY_PATH"
    )
    
    # Token settings
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    authorization_code_expire_minutes: int = 10
    id_token_expire_minutes: int = 60
    
    # PKCE
    pkce_required: bool = True
    pkce_plain_allowed: bool = False
    
    # Clock skew tolerance
    clock_skew_seconds: int = 60
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./oauth.db",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # IdP Configuration
    idp_issuer: str = Field(
        default="http://localhost:8000",
        env="IDP_ISSUER"
    )
    idp_audience: List[str] = Field(
        default=["http://localhost:8000"],
        env="IDP_AUDIENCE"
    )
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    # Session
    session_expire_minutes: int = 30
    session_cookie_name: str = "oauth_session"
    session_cookie_secure: bool = False  # Set to True in production with HTTPS
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "lax"
    
    # Client settings (for testing)
    test_client_id: str = "test-client-id"
    test_client_secret: str = "test-client-secret"
    test_redirect_uri: str = "http://localhost:3000/callback"
    
    # Performance
    max_connections: int = 100
    connection_timeout: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False