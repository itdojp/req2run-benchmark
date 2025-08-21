"""Security utilities for OAuth provider"""
import hashlib
import hmac
import secrets
import base64
from typing import Optional
import logging

from passlib.context import CryptContext

from .config import Settings
from .state_manager import StateManager

logger = logging.getLogger(__name__)

class SecurityManager:
    """Security utilities and client credential validation"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.state_manager = StateManager(settings)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def validate_client_credentials(
        self,
        credentials: str,
        client_id: Optional[str] = None
    ) -> bool:
        """Validate client credentials (basic auth or secret)"""
        try:
            # Try to decode as Basic auth
            if credentials.startswith("Basic "):
                encoded = credentials.replace("Basic ", "")
                decoded = base64.b64decode(encoded).decode("utf-8")
                parts = decoded.split(":", 1)
                if len(parts) == 2:
                    client_id, client_secret = parts
                    return await self._verify_client_secret(client_id, client_secret)
            
            # Otherwise treat as bearer token for client
            if client_id:
                client = await self.state_manager.get_client(client_id)
                if client and client.client_secret == credentials:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Client credential validation error: {e}")
            return False
    
    async def _verify_client_secret(
        self,
        client_id: str,
        client_secret: str
    ) -> bool:
        """Verify client secret"""
        client = await self.state_manager.get_client(client_id)
        if not client:
            return False
        
        # In production, use hashed comparison
        # For baseline, using simple comparison
        return client.client_secret == client_secret
    
    def generate_state_token(self) -> str:
        """Generate CSRF state token"""
        return secrets.token_urlsafe(32)
    
    def hash_client_secret(self, secret: str) -> str:
        """Hash client secret for storage"""
        return self.pwd_context.hash(secret)
    
    def verify_client_secret_hash(self, secret: str, hashed: str) -> bool:
        """Verify client secret against hash"""
        return self.pwd_context.verify(secret, hashed)
    
    def constant_time_compare(self, val1: str, val2: str) -> bool:
        """Constant time string comparison to prevent timing attacks"""
        return hmac.compare_digest(val1.encode(), val2.encode())
    
    def generate_client_credentials(self) -> tuple[str, str]:
        """Generate new client ID and secret"""
        client_id = f"client_{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(32)
        return client_id, client_secret