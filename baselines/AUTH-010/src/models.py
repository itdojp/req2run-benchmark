"""Data models for OAuth 2.1/OIDC implementation"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

class AuthorizeRequest(BaseModel):
    """OAuth authorization request"""
    response_type: str
    client_id: str
    redirect_uri: str
    scope: str
    state: str
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = "S256"
    nonce: Optional[str] = None
    prompt: Optional[str] = None
    max_age: Optional[int] = None
    
    @validator('response_type')
    def validate_response_type(cls, v):
        if v not in ['code', 'token', 'id_token']:
            raise ValueError('Invalid response_type')
        return v
    
    @validator('code_challenge_method')
    def validate_challenge_method(cls, v):
        if v and v not in ['plain', 'S256']:
            raise ValueError('Invalid code_challenge_method')
        return v

class TokenRequest(BaseModel):
    """Token exchange request"""
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: str
    client_secret: Optional[str] = None
    code_verifier: Optional[str] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    
    @validator('grant_type')
    def validate_grant_type(cls, v):
        if v not in ['authorization_code', 'refresh_token', 'client_credentials']:
            raise ValueError('Invalid grant_type')
        return v

class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None

class IntrospectionRequest(BaseModel):
    """Token introspection request"""
    token: str
    token_type_hint: Optional[str] = None

class IntrospectionResponse(BaseModel):
    """Token introspection response"""
    active: bool
    scope: Optional[str] = None
    client_id: Optional[str] = None
    username: Optional[str] = None
    token_type: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    nbf: Optional[int] = None
    sub: Optional[str] = None
    aud: Optional[List[str]] = None
    iss: Optional[str] = None
    jti: Optional[str] = None

class JWK(BaseModel):
    """JSON Web Key"""
    kty: str  # Key type (RSA, EC, etc.)
    use: str  # Key use (sig, enc)
    kid: str  # Key ID
    alg: str  # Algorithm
    n: Optional[str] = None  # RSA modulus
    e: Optional[str] = None  # RSA exponent
    x: Optional[str] = None  # EC x coordinate
    y: Optional[str] = None  # EC y coordinate
    crv: Optional[str] = None  # EC curve

class JWKSResponse(BaseModel):
    """JWKS response"""
    keys: List[JWK]

class Client(BaseModel):
    """OAuth client registration"""
    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: List[str]
    grant_types: List[str] = ["authorization_code", "refresh_token"]
    response_types: List[str] = ["code"]
    scope: str = "openid profile email"
    token_endpoint_auth_method: str = "client_secret_post"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuthorizationCode(BaseModel):
    """Authorization code storage"""
    code: str
    client_id: str
    user_id: str
    redirect_uri: str
    scope: str
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    nonce: Optional[str] = None
    expires_at: datetime
    used: bool = False

class Token(BaseModel):
    """Token storage"""
    jti: str  # Token ID
    token_type: str  # access_token, refresh_token, id_token
    client_id: str
    user_id: str
    scope: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked: bool = False
    refresh_token_id: Optional[str] = None

class Session(BaseModel):
    """User session"""
    session_id: str
    user_id: str
    client_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None