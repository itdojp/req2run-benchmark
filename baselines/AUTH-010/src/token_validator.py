"""Token validation and introspection"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from jose import jwt, JWTError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from .config import Settings
from .state_manager import StateManager

logger = logging.getLogger(__name__)

class TokenValidator:
    """JWT token validation with security checks"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.state_manager = StateManager(settings)
        self.public_key = None
        self._load_public_key()
    
    def _load_public_key(self):
        """Load public key for token validation"""
        try:
            with open(self.settings.jwt_public_key_path, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
        except FileNotFoundError:
            logger.warning("Public key not found, validation will fail")
    
    async def validate_jwt(
        self,
        token: str,
        validate_exp: bool = True
    ) -> Dict[str, Any]:
        """Validate JWT token with security checks"""
        try:
            # Decode and verify signature
            claims = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.settings.jwt_algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": validate_exp,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "require_exp": True,
                    "require_iat": True,
                    "require_nbf": False
                },
                audience=self.settings.idp_audience,
                issuer=self.settings.idp_issuer,
                leeway=self.settings.clock_skew_seconds
            )
            
            # Additional security checks
            
            # Check algorithm (prevent alg=none attack)
            header = jwt.get_unverified_header(token)
            if header.get("alg") == "none" or header.get("alg") != self.settings.jwt_algorithm:
                raise ValueError("Invalid algorithm")
            
            # Check token revocation
            jti = claims.get("jti")
            if jti and await self.state_manager.is_token_revoked(jti):
                raise ValueError("Token has been revoked")
            
            # Validate token type
            token_type = claims.get("token_type")
            if token_type and token_type != "access_token":
                raise ValueError(f"Invalid token type: {token_type}")
            
            return claims
            
        except JWTError as e:
            logger.error(f"JWT validation error: {e}")
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise ValueError(f"Token validation failed: {str(e)}")
    
    async def introspect_token(self, token: str) -> Dict[str, Any]:
        """Introspect token and return metadata"""
        try:
            # Try to decode as JWT
            try:
                claims = await self.validate_jwt(token, validate_exp=False)
                
                # Check if expired
                exp = claims.get("exp")
                active = True
                if exp:
                    active = datetime.fromtimestamp(exp) > datetime.utcnow()
                
                return {
                    "active": active,
                    "scope": claims.get("scope"),
                    "client_id": claims.get("client_id"),
                    "username": claims.get("sub"),
                    "token_type": "Bearer",
                    "exp": exp,
                    "iat": claims.get("iat"),
                    "nbf": claims.get("nbf"),
                    "sub": claims.get("sub"),
                    "aud": claims.get("aud"),
                    "iss": claims.get("iss"),
                    "jti": claims.get("jti")
                }
            except:
                # Not a JWT, might be a refresh token
                token_data = await self.state_manager.get_token_metadata(token)
                if token_data:
                    active = not token_data.revoked and datetime.utcnow() < token_data.expires_at
                    return {
                        "active": active,
                        "scope": token_data.scope,
                        "client_id": token_data.client_id,
                        "username": token_data.user_id,
                        "token_type": token_data.token_type,
                        "exp": int(token_data.expires_at.timestamp()) if token_data.expires_at else None,
                        "iat": int(token_data.created_at.timestamp()) if token_data.created_at else None
                    }
                
                # Token not found
                return {"active": False}
                
        except Exception as e:
            logger.error(f"Introspection error: {e}")
            return {"active": False}
    
    def validate_nonce(self, token_nonce: str, expected_nonce: str) -> bool:
        """Validate nonce to prevent replay attacks"""
        if not token_nonce or not expected_nonce:
            return False
        return token_nonce == expected_nonce
    
    def validate_audience(self, token_aud: Any, expected_aud: str) -> bool:
        """Validate audience claim"""
        if isinstance(token_aud, list):
            return expected_aud in token_aud
        return token_aud == expected_aud
    
    def validate_issuer(self, token_iss: str, expected_iss: str) -> bool:
        """Validate issuer claim"""
        return token_iss == expected_iss
    
    def validate_expiry(self, token_exp: int) -> bool:
        """Validate token expiry with clock skew"""
        now = datetime.utcnow()
        exp_time = datetime.fromtimestamp(token_exp)
        # Add clock skew tolerance
        return exp_time > (now - timedelta(seconds=self.settings.clock_skew_seconds))
    
    def validate_not_before(self, token_nbf: int) -> bool:
        """Validate not-before claim with clock skew"""
        now = datetime.utcnow()
        nbf_time = datetime.fromtimestamp(token_nbf)
        # Add clock skew tolerance
        return nbf_time <= (now + timedelta(seconds=self.settings.clock_skew_seconds))