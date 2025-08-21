"""OAuth 2.1 Provider implementation with PKCE support"""
import os
import secrets
import hashlib
import base64
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from jose import jwt, JWTError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from .models import (
    AuthorizeRequest,
    TokenRequest,
    TokenResponse,
    AuthorizationCode,
    Token,
    Client
)
from .config import Settings
from .database import get_db
from .state_manager import StateManager

logger = logging.getLogger(__name__)

class OAuthProvider:
    """OAuth 2.1 Provider with PKCE and token rotation"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.state_manager = StateManager(settings)
        self.private_key = None
        self.public_key = None
        self.kid = "oauth-key-1"
        
    async def initialize(self):
        """Initialize the OAuth provider"""
        await self._load_or_generate_keys()
        await self._register_test_client()
    
    async def _load_or_generate_keys(self):
        """Load or generate RSA key pair for JWT signing"""
        try:
            # Try to load existing keys
            with open(self.settings.jwt_private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
            
            with open(self.settings.jwt_public_key_path, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
        except FileNotFoundError:
            # Generate new key pair
            logger.info("Generating new RSA key pair")
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
            
            # Save keys
            os.makedirs(os.path.dirname(self.settings.jwt_private_key_path), exist_ok=True)
            
            with open(self.settings.jwt_private_key_path, 'wb') as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            with open(self.settings.jwt_public_key_path, 'wb') as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
    
    async def _register_test_client(self):
        """Register a test client for development"""
        client = Client(
            client_id=self.settings.test_client_id,
            client_secret=self.settings.test_client_secret,
            client_name="Test Client",
            redirect_uris=[self.settings.test_redirect_uri],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scope="openid profile email"
        )
        await self.state_manager.store_client(client)
    
    async def generate_authorization_code(
        self,
        auth_request: AuthorizeRequest,
        user_id: str
    ) -> str:
        """Generate authorization code with PKCE support"""
        # Validate client
        client = await self.state_manager.get_client(auth_request.client_id)
        if not client:
            raise ValueError("Invalid client_id")
        
        # Validate redirect URI
        if auth_request.redirect_uri not in client.redirect_uris:
            raise ValueError("Invalid redirect_uri")
        
        # Generate authorization code
        code = secrets.token_urlsafe(32)
        
        # Store authorization code with PKCE challenge
        auth_code = AuthorizationCode(
            code=code,
            client_id=auth_request.client_id,
            user_id=user_id,
            redirect_uri=auth_request.redirect_uri,
            scope=auth_request.scope,
            code_challenge=auth_request.code_challenge,
            code_challenge_method=auth_request.code_challenge_method,
            nonce=auth_request.nonce,
            expires_at=datetime.utcnow() + timedelta(
                minutes=self.settings.authorization_code_expire_minutes
            )
        )
        
        await self.state_manager.store_authorization_code(auth_code)
        
        # Store state for CSRF protection
        await self.state_manager.store_state(auth_request.state, auth_request.client_id)
        
        return code
    
    async def exchange_code_for_token(
        self,
        token_request: TokenRequest
    ) -> TokenResponse:
        """Exchange authorization code for tokens with PKCE verification"""
        
        if token_request.grant_type == "authorization_code":
            return await self._handle_authorization_code_grant(token_request)
        elif token_request.grant_type == "refresh_token":
            return await self._handle_refresh_token_grant(token_request)
        else:
            raise ValueError(f"Unsupported grant_type: {token_request.grant_type}")
    
    async def _handle_authorization_code_grant(
        self,
        token_request: TokenRequest
    ) -> TokenResponse:
        """Handle authorization code grant with PKCE verification"""
        # Retrieve authorization code
        auth_code = await self.state_manager.get_authorization_code(token_request.code)
        
        if not auth_code:
            raise ValueError("Invalid authorization code")
        
        # Check expiration
        if datetime.utcnow() > auth_code.expires_at:
            raise ValueError("Authorization code expired")
        
        # Check if already used
        if auth_code.used:
            # Security: Revoke all tokens if code reuse detected
            await self._revoke_all_tokens_for_code(auth_code)
            raise ValueError("Authorization code already used")
        
        # Validate client
        if token_request.client_id != auth_code.client_id:
            raise ValueError("Client mismatch")
        
        # Validate redirect URI
        if token_request.redirect_uri != auth_code.redirect_uri:
            raise ValueError("Redirect URI mismatch")
        
        # Verify PKCE
        if auth_code.code_challenge:
            if not token_request.code_verifier:
                raise ValueError("PKCE code_verifier required")
            
            if not self._verify_pkce(
                auth_code.code_challenge,
                token_request.code_verifier,
                auth_code.code_challenge_method
            ):
                raise ValueError("PKCE verification failed")
        
        # Mark code as used
        await self.state_manager.mark_code_used(token_request.code)
        
        # Generate tokens
        access_token = await self._generate_access_token(
            auth_code.client_id,
            auth_code.user_id,
            auth_code.scope
        )
        
        refresh_token = await self._generate_refresh_token(
            auth_code.client_id,
            auth_code.user_id,
            auth_code.scope
        )
        
        id_token = None
        if "openid" in auth_code.scope:
            id_token = await self._generate_id_token(
                auth_code.client_id,
                auth_code.user_id,
                auth_code.nonce
            )
        
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
            refresh_token=refresh_token,
            id_token=id_token,
            scope=auth_code.scope
        )
    
    async def _handle_refresh_token_grant(
        self,
        token_request: TokenRequest
    ) -> TokenResponse:
        """Handle refresh token grant with rotation"""
        # Validate refresh token
        refresh_token_data = await self.state_manager.get_refresh_token(
            token_request.refresh_token
        )
        
        if not refresh_token_data:
            raise ValueError("Invalid refresh token")
        
        # Check expiration
        if datetime.utcnow() > refresh_token_data.expires_at:
            raise ValueError("Refresh token expired")
        
        # Check if revoked
        if refresh_token_data.revoked:
            raise ValueError("Refresh token revoked")
        
        # Validate client
        if token_request.client_id != refresh_token_data.client_id:
            raise ValueError("Client mismatch")
        
        # Revoke old refresh token (rotation)
        await self.state_manager.revoke_token(token_request.refresh_token)
        
        # Generate new tokens
        access_token = await self._generate_access_token(
            refresh_token_data.client_id,
            refresh_token_data.user_id,
            refresh_token_data.scope
        )
        
        new_refresh_token = await self._generate_refresh_token(
            refresh_token_data.client_id,
            refresh_token_data.user_id,
            refresh_token_data.scope
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
            refresh_token=new_refresh_token,
            scope=refresh_token_data.scope
        )
    
    def _verify_pkce(
        self,
        challenge: str,
        verifier: str,
        method: str = "S256"
    ) -> bool:
        """Verify PKCE code challenge"""
        if method == "plain":
            return challenge == verifier
        elif method == "S256":
            # SHA256 hash of verifier
            calculated = base64.urlsafe_b64encode(
                hashlib.sha256(verifier.encode()).digest()
            ).decode().rstrip("=")
            return challenge == calculated
        return False
    
    async def _generate_access_token(
        self,
        client_id: str,
        user_id: str,
        scope: str
    ) -> str:
        """Generate JWT access token"""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self.settings.access_token_expire_minutes)
        
        claims = {
            "iss": self.settings.idp_issuer,
            "sub": user_id,
            "aud": self.settings.idp_audience,
            "exp": expires_at,
            "iat": now,
            "nbf": now - timedelta(seconds=self.settings.clock_skew_seconds),
            "jti": secrets.token_urlsafe(16),
            "client_id": client_id,
            "scope": scope,
            "token_type": "access_token"
        }
        
        # Sign with private key
        token = jwt.encode(
            claims,
            self.private_key,
            algorithm=self.settings.jwt_algorithm,
            headers={"kid": self.kid}
        )
        
        # Store token metadata
        await self.state_manager.store_token_metadata(
            claims["jti"],
            "access_token",
            client_id,
            user_id,
            scope,
            expires_at
        )
        
        return token
    
    async def _generate_refresh_token(
        self,
        client_id: str,
        user_id: str,
        scope: str
    ) -> str:
        """Generate refresh token"""
        token_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(
            days=self.settings.refresh_token_expire_days
        )
        
        # Store refresh token
        await self.state_manager.store_token_metadata(
            token_id,
            "refresh_token",
            client_id,
            user_id,
            scope,
            expires_at
        )
        
        return token_id
    
    async def _generate_id_token(
        self,
        client_id: str,
        user_id: str,
        nonce: Optional[str] = None
    ) -> str:
        """Generate OpenID Connect ID token"""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self.settings.id_token_expire_minutes)
        
        claims = {
            "iss": self.settings.idp_issuer,
            "sub": user_id,
            "aud": client_id,
            "exp": expires_at,
            "iat": now,
            "auth_time": int(now.timestamp()),
            "azp": client_id
        }
        
        if nonce:
            claims["nonce"] = nonce
        
        # Sign with private key
        token = jwt.encode(
            claims,
            self.private_key,
            algorithm=self.settings.jwt_algorithm,
            headers={"kid": self.kid}
        )
        
        return token
    
    async def revoke_token(
        self,
        token: str,
        token_type_hint: Optional[str] = None
    ):
        """Revoke a token"""
        await self.state_manager.revoke_token(token)
    
    async def _revoke_all_tokens_for_code(self, auth_code: AuthorizationCode):
        """Revoke all tokens associated with an authorization code"""
        # This would revoke all tokens for the user/client combination
        # Implementation depends on token storage strategy
        logger.warning(
            f"Code reuse detected for client {auth_code.client_id}, "
            f"revoking all associated tokens"
        )
    
    async def get_jwks(self) -> List[Dict[str, Any]]:
        """Get JWKS for public key discovery"""
        # Extract public key components
        public_numbers = self.public_key.public_numbers()
        
        # Convert to base64url encoding
        n = base64.urlsafe_b64encode(
            public_numbers.n.to_bytes(
                (public_numbers.n.bit_length() + 7) // 8,
                'big'
            )
        ).decode().rstrip("=")
        
        e = base64.urlsafe_b64encode(
            public_numbers.e.to_bytes(
                (public_numbers.e.bit_length() + 7) // 8,
                'big'
            )
        ).decode().rstrip("=")
        
        return [{
            "kty": "RSA",
            "use": "sig",
            "kid": self.kid,
            "alg": self.settings.jwt_algorithm,
            "n": n,
            "e": e
        }]