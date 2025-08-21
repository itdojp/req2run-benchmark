"""
AUTH-010: OAuth 2.1/OIDC with PKCE Mock IdP Integration
Main application entry point
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import uvicorn

from .oauth_provider import OAuthProvider
from .token_validator import TokenValidator
from .models import (
    AuthorizeRequest,
    TokenRequest,
    TokenResponse,
    IntrospectionRequest,
    IntrospectionResponse,
    JWKSResponse
)
from .config import Settings
from .database import init_db, get_db
from .security import SecurityManager
from .state_manager import StateManager
from .metrics import (
    auth_requests_total,
    token_validations_total,
    auth_latency_histogram
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

# Initialize components
oauth_provider = OAuthProvider(settings)
token_validator = TokenValidator(settings)
security_manager = SecurityManager(settings)
state_manager = StateManager(settings)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting OAuth 2.1/OIDC Provider")
    await init_db()
    await state_manager.initialize()
    await oauth_provider.initialize()
    yield
    # Shutdown
    logger.info("Shutting down OAuth 2.1/OIDC Provider")
    await state_manager.cleanup()

# Create FastAPI app
app = FastAPI(
    title="OAuth 2.1/OIDC Provider",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "oauth-provider",
        "version": "1.0.0"
    }

@app.get("/authorize")
async def authorize(
    request: Request,
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None,
    nonce: Optional[str] = None
):
    """OAuth 2.1 Authorization endpoint with PKCE support"""
    auth_requests_total.inc()
    
    try:
        auth_request = AuthorizeRequest(
            response_type=response_type,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            nonce=nonce
        )
        
        # Validate PKCE is present (required in OAuth 2.1)
        if not code_challenge:
            raise HTTPException(
                status_code=400,
                detail="PKCE code_challenge is required"
            )
        
        # Generate authorization code
        auth_code = await oauth_provider.generate_authorization_code(
            auth_request,
            user_id="test_user"  # In production, get from session
        )
        
        # Build redirect URL
        redirect_url = f"{redirect_uri}?code={auth_code}&state={state}"
        
        return Response(
            status_code=302,
            headers={"Location": redirect_url}
        )
        
    except Exception as e:
        logger.error(f"Authorization error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/token", response_model=TokenResponse)
async def token(request: TokenRequest):
    """Token endpoint for code exchange and refresh"""
    try:
        with auth_latency_histogram.time():
            token_response = await oauth_provider.exchange_code_for_token(request)
        return token_response
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/introspect", response_model=IntrospectionResponse)
async def introspect(
    request: IntrospectionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Token introspection endpoint"""
    token_validations_total.inc()
    
    try:
        # Validate client credentials
        if not await security_manager.validate_client_credentials(
            credentials.credentials
        ):
            raise HTTPException(status_code=401, detail="Invalid client credentials")
        
        # Introspect token
        result = await token_validator.introspect_token(request.token)
        return IntrospectionResponse(**result)
        
    except Exception as e:
        logger.error(f"Introspection error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/.well-known/jwks.json", response_model=JWKSResponse)
async def jwks():
    """JWKS endpoint for public key discovery"""
    try:
        keys = await oauth_provider.get_jwks()
        return JWKSResponse(keys=keys)
    except Exception as e:
        logger.error(f"JWKS error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve JWKS")

@app.get("/.well-known/openid-configuration")
async def openid_configuration():
    """OpenID Connect discovery endpoint"""
    base_url = settings.base_url
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "jwks_uri": f"{base_url}/.well-known/jwks.json",
        "introspection_endpoint": f"{base_url}/introspect",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "claims_supported": ["sub", "aud", "exp", "iat", "iss", "nonce"],
        "code_challenge_methods_supported": ["S256", "plain"]
    }

@app.post("/revoke")
async def revoke_token(
    token: str,
    token_type_hint: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Token revocation endpoint"""
    try:
        # Validate client credentials
        if not await security_manager.validate_client_credentials(
            credentials.credentials
        ):
            raise HTTPException(status_code=401, detail="Invalid client credentials")
        
        # Revoke token
        await oauth_provider.revoke_token(token, token_type_hint)
        return {"status": "revoked"}
        
    except Exception as e:
        logger.error(f"Revocation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.api_route("/userinfo", methods=["GET", "POST"])
async def userinfo(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """UserInfo endpoint for OIDC"""
    try:
        # Validate access token
        token_data = await token_validator.validate_jwt(credentials.credentials)
        
        # Return user info
        return {
            "sub": token_data.get("sub"),
            "name": "Test User",
            "email": "test@example.com",
            "email_verified": True
        }
        
    except Exception as e:
        logger.error(f"UserInfo error: {e}")
        raise HTTPException(status_code=401, detail="Invalid access token")

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )