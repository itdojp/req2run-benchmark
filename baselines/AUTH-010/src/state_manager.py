"""State management for OAuth provider"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import aioredis
from redis.asyncio import Redis

from .models import AuthorizationCode, Token, Client
from .config import Settings

logger = logging.getLogger(__name__)

class StateManager:
    """Manage OAuth state in Redis"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.redis: Optional[Redis] = None
        self._in_memory_store = {}  # Fallback for testing
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}, using in-memory store")
            self.redis = None
    
    async def cleanup(self):
        """Cleanup connections"""
        if self.redis:
            await self.redis.close()
    
    async def store_authorization_code(self, auth_code: AuthorizationCode):
        """Store authorization code"""
        key = f"auth_code:{auth_code.code}"
        value = auth_code.model_dump_json()
        ttl = int((auth_code.expires_at - datetime.utcnow()).total_seconds())
        
        if self.redis:
            await self.redis.setex(key, ttl, value)
        else:
            self._in_memory_store[key] = value
    
    async def get_authorization_code(self, code: str) -> Optional[AuthorizationCode]:
        """Retrieve authorization code"""
        key = f"auth_code:{code}"
        
        if self.redis:
            value = await self.redis.get(key)
        else:
            value = self._in_memory_store.get(key)
        
        if value:
            return AuthorizationCode.model_validate_json(value)
        return None
    
    async def mark_code_used(self, code: str):
        """Mark authorization code as used"""
        auth_code = await self.get_authorization_code(code)
        if auth_code:
            auth_code.used = True
            await self.store_authorization_code(auth_code)
    
    async def store_token_metadata(
        self,
        jti: str,
        token_type: str,
        client_id: str,
        user_id: str,
        scope: str,
        expires_at: datetime
    ):
        """Store token metadata"""
        token = Token(
            jti=jti,
            token_type=token_type,
            client_id=client_id,
            user_id=user_id,
            scope=scope,
            expires_at=expires_at
        )
        
        key = f"token:{jti}"
        value = token.model_dump_json()
        ttl = int((expires_at - datetime.utcnow()).total_seconds())
        
        if self.redis:
            await self.redis.setex(key, ttl, value)
        else:
            self._in_memory_store[key] = value
    
    async def get_token_metadata(self, jti: str) -> Optional[Token]:
        """Get token metadata"""
        key = f"token:{jti}"
        
        if self.redis:
            value = await self.redis.get(key)
        else:
            value = self._in_memory_store.get(key)
        
        if value:
            return Token.model_validate_json(value)
        return None
    
    async def get_refresh_token(self, token: str) -> Optional[Token]:
        """Get refresh token metadata"""
        return await self.get_token_metadata(token)
    
    async def is_token_revoked(self, jti: str) -> bool:
        """Check if token is revoked"""
        token = await self.get_token_metadata(jti)
        return token.revoked if token else False
    
    async def revoke_token(self, jti: str):
        """Revoke a token"""
        token = await self.get_token_metadata(jti)
        if token:
            token.revoked = True
            key = f"token:{jti}"
            value = token.model_dump_json()
            
            if self.redis:
                await self.redis.set(key, value)
            else:
                self._in_memory_store[key] = value
    
    async def store_state(self, state: str, client_id: str):
        """Store state for CSRF protection"""
        key = f"state:{state}"
        ttl = 600  # 10 minutes
        
        if self.redis:
            await self.redis.setex(key, ttl, client_id)
        else:
            self._in_memory_store[key] = client_id
    
    async def validate_state(self, state: str) -> Optional[str]:
        """Validate and retrieve state"""
        key = f"state:{state}"
        
        if self.redis:
            client_id = await self.redis.get(key)
            if client_id:
                await self.redis.delete(key)  # Single use
        else:
            client_id = self._in_memory_store.pop(key, None)
        
        return client_id
    
    async def store_client(self, client: Client):
        """Store client registration"""
        key = f"client:{client.client_id}"
        value = client.model_dump_json()
        
        if self.redis:
            await self.redis.set(key, value)
        else:
            self._in_memory_store[key] = value
    
    async def get_client(self, client_id: str) -> Optional[Client]:
        """Get client registration"""
        key = f"client:{client_id}"
        
        if self.redis:
            value = await self.redis.get(key)
        else:
            value = self._in_memory_store.get(key)
        
        if value:
            return Client.model_validate_json(value)
        return None