"""Idempotency key handling and management"""
import hashlib
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from uuid import uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from fastapi import Request, Response, HTTPException

from models import (
    IdempotencyKey, PaymentTransaction, AuditLog,
    IdempotencyConfig, AuditEventType
)

logger = structlog.get_logger()


class IdempotencyManager:
    """Manages idempotency key operations"""
    
    def __init__(self, db_session_factory, redis_client=None):
        self.db_session_factory = db_session_factory
        self.redis_client = redis_client
        self.config = IdempotencyConfig()
    
    async def process_request(
        self,
        idempotency_key: str,
        user_id: str,
        request: Request,
        handler_func
    ) -> Tuple[Response, bool]:
        """
        Process request with idempotency key handling
        Returns: (response, is_replay)
        """
        
        # Calculate request hash
        request_hash = await self._calculate_request_hash(request)
        
        async with self.db_session_factory() as session:
            # Try to acquire lock on idempotency key
            lock_acquired = await self._acquire_lock(
                session, idempotency_key, user_id, request, request_hash
            )
            
            if not lock_acquired:
                # Another request is processing or completed
                return await self._handle_existing_key(
                    session, idempotency_key, user_id, request_hash
                )
            
            try:
                # Process the request
                response = await handler_func()
                
                # Store the response
                await self._store_response(
                    session, idempotency_key, response
                )
                
                # Audit log
                await self._audit_log(
                    session,
                    idempotency_key=idempotency_key,
                    user_id=user_id,
                    event_type=AuditEventType.PAYMENT_COMPLETED,
                    request=request,
                    response=response
                )
                
                return response, False
                
            except Exception as e:
                # Release lock on error
                await self._release_lock(session, idempotency_key)
                
                # Audit error
                await self._audit_log(
                    session,
                    idempotency_key=idempotency_key,
                    user_id=user_id,
                    event_type=AuditEventType.PAYMENT_FAILED,
                    request=request,
                    event_details={"error": str(e)}
                )
                
                raise
            
            finally:
                # Always release lock
                await self._release_lock(session, idempotency_key)
    
    async def _calculate_request_hash(self, request: Request) -> str:
        """Calculate hash of request for comparison"""
        # Get request body
        body = await request.body()
        
        # Limit body size
        if len(body) > self.config.MAX_BODY_SIZE:
            body = body[:self.config.MAX_BODY_SIZE]
        
        # Create hash components
        hash_data = {
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query),
            "body": body.decode('utf-8') if body else ""
        }
        
        # Calculate SHA-256 hash
        hash_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()
    
    async def _acquire_lock(
        self,
        session: AsyncSession,
        idempotency_key: str,
        user_id: str,
        request: Request,
        request_hash: str
    ) -> bool:
        """Try to acquire lock on idempotency key"""
        
        lock_holder = str(uuid4())
        now = datetime.utcnow()
        expires_at = now + self.config.IDEMPOTENCY_KEY_TTL
        
        # Try to insert new idempotency key
        try:
            new_key = IdempotencyKey(
                key=idempotency_key,
                user_id=user_id,
                request_path=str(request.url.path),
                request_method=request.method,
                request_body_hash=request_hash,
                status="processing",
                is_processing=True,
                created_at=now,
                expires_at=expires_at,
                lock_acquired_at=now,
                lock_holder=lock_holder
            )
            
            session.add(new_key)
            await session.commit()
            
            logger.info("Acquired lock on idempotency key",
                       key=idempotency_key, user_id=user_id)
            
            return True
            
        except Exception:
            # Key already exists, check if we can acquire lock
            await session.rollback()
            
            # Try to acquire lock on existing key
            for attempt in range(self.config.LOCK_MAX_RETRIES):
                result = await session.execute(
                    select(IdempotencyKey).where(
                        IdempotencyKey.key == idempotency_key
                    ).with_for_update(skip_locked=True)
                )
                
                existing_key = result.scalar_one_or_none()
                
                if existing_key is None:
                    # Another process has lock, wait and retry
                    await asyncio.sleep(self.config.LOCK_RETRY_DELAY)
                    continue
                
                # Check if key has expired
                if existing_key.expires_at < now:
                    # Key expired, update it
                    existing_key.user_id = user_id
                    existing_key.request_body_hash = request_hash
                    existing_key.status = "processing"
                    existing_key.is_processing = True
                    existing_key.created_at = now
                    existing_key.expires_at = expires_at
                    existing_key.lock_acquired_at = now
                    existing_key.lock_holder = lock_holder
                    existing_key.response_status = None
                    existing_key.response_body = None
                    
                    await session.commit()
                    
                    logger.info("Acquired lock on expired key",
                               key=idempotency_key, user_id=user_id)
                    
                    return True
                
                # Check if processing is complete
                if not existing_key.is_processing and existing_key.status == "completed":
                    # Request already processed
                    await session.commit()
                    return False
                
                # Check if lock has timed out
                if existing_key.lock_acquired_at:
                    lock_age = now - existing_key.lock_acquired_at
                    if lock_age > self.config.LOCK_TIMEOUT:
                        # Lock timed out, acquire it
                        existing_key.lock_acquired_at = now
                        existing_key.lock_holder = lock_holder
                        
                        await session.commit()
                        
                        logger.warning("Acquired timed out lock",
                                     key=idempotency_key, user_id=user_id,
                                     previous_holder=existing_key.lock_holder)
                        
                        return True
                
                # Lock is held by another process
                await session.commit()
                await asyncio.sleep(self.config.LOCK_RETRY_DELAY)
            
            logger.warning("Failed to acquire lock after retries",
                         key=idempotency_key, user_id=user_id)
            
            return False
    
    async def _handle_existing_key(
        self,
        session: AsyncSession,
        idempotency_key: str,
        user_id: str,
        request_hash: str
    ) -> Tuple[Response, bool]:
        """Handle request with existing idempotency key"""
        
        # Wait for processing to complete
        for attempt in range(self.config.LOCK_MAX_RETRIES):
            result = await session.execute(
                select(IdempotencyKey).where(
                    IdempotencyKey.key == idempotency_key
                )
            )
            
            existing_key = result.scalar_one_or_none()
            
            if not existing_key:
                raise HTTPException(
                    status_code=500,
                    detail="Idempotency key disappeared"
                )
            
            # Check if processing is complete
            if not existing_key.is_processing and existing_key.status == "completed":
                # Verify request hash matches
                if existing_key.request_body_hash != request_hash:
                    raise HTTPException(
                        status_code=422,
                        detail="Request body does not match previous request with same idempotency key"
                    )
                
                # Verify user matches
                if existing_key.user_id != user_id:
                    raise HTTPException(
                        status_code=403,
                        detail="Idempotency key belongs to different user"
                    )
                
                # Return cached response
                response = Response(
                    content=json.dumps(existing_key.response_body),
                    status_code=existing_key.response_status,
                    headers=existing_key.response_headers or {},
                    media_type="application/json"
                )
                
                # Add idempotency replay header
                response.headers["X-Idempotent-Replay"] = "true"
                
                logger.info("Returning cached response for idempotency key",
                           key=idempotency_key, user_id=user_id)
                
                # Audit log
                await self._audit_log(
                    session,
                    idempotency_key=idempotency_key,
                    user_id=user_id,
                    event_type=AuditEventType.IDEMPOTENT_REQUEST,
                    response=response
                )
                
                return response, True
            
            # Still processing, wait
            await asyncio.sleep(self.config.LOCK_RETRY_DELAY)
        
        # Timeout waiting for processing
        raise HTTPException(
            status_code=503,
            detail="Request processing timeout"
        )
    
    async def _store_response(
        self,
        session: AsyncSession,
        idempotency_key: str,
        response: Response
    ):
        """Store response for idempotency key"""
        
        # Get response body
        response_body = None
        if hasattr(response, 'body'):
            try:
                response_body = json.loads(response.body)
            except:
                response_body = response.body.decode('utf-8') if isinstance(response.body, bytes) else str(response.body)
        
        # Update idempotency key with response
        await session.execute(
            update(IdempotencyKey)
            .where(IdempotencyKey.key == idempotency_key)
            .values(
                response_status=response.status_code,
                response_body=response_body,
                response_headers=dict(response.headers),
                status="completed",
                is_processing=False,
                completed_at=datetime.utcnow()
            )
        )
        
        await session.commit()
        
        logger.info("Stored response for idempotency key",
                   key=idempotency_key, status_code=response.status_code)
    
    async def _release_lock(
        self,
        session: AsyncSession,
        idempotency_key: str
    ):
        """Release lock on idempotency key"""
        
        await session.execute(
            update(IdempotencyKey)
            .where(IdempotencyKey.key == idempotency_key)
            .values(
                is_processing=False,
                lock_acquired_at=None,
                lock_holder=None
            )
        )
        
        await session.commit()
        
        logger.debug("Released lock on idempotency key", key=idempotency_key)
    
    async def _audit_log(
        self,
        session: AsyncSession,
        idempotency_key: str,
        user_id: str,
        event_type: AuditEventType,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
        event_details: Optional[Dict[str, Any]] = None
    ):
        """Create audit log entry"""
        
        audit_entry = AuditLog(
            idempotency_key=idempotency_key,
            user_id=user_id,
            event_type=event_type.value,
            event_details=event_details or {},
            created_at=datetime.utcnow()
        )
        
        if request:
            audit_entry.request_path = str(request.url.path)
            audit_entry.request_method = request.method
            audit_entry.client_ip = request.client.host if request.client else None
            audit_entry.user_agent = request.headers.get("user-agent")
        
        if response:
            audit_entry.response_status = response.status_code
        
        session.add(audit_entry)
        await session.commit()
    
    async def cleanup_expired_keys(self) -> int:
        """Clean up expired idempotency keys"""
        
        async with self.db_session_factory() as session:
            # Delete expired keys
            result = await session.execute(
                select(IdempotencyKey).where(
                    IdempotencyKey.expires_at < datetime.utcnow()
                )
            )
            
            expired_keys = result.scalars().all()
            
            for key in expired_keys:
                session.delete(key)
            
            await session.commit()
            
            if expired_keys:
                logger.info("Cleaned up expired idempotency keys",
                           count=len(expired_keys))
            
            return len(expired_keys)
    
    async def get_key_info(
        self,
        idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get information about an idempotency key"""
        
        async with self.db_session_factory() as session:
            result = await session.execute(
                select(IdempotencyKey).where(
                    IdempotencyKey.key == idempotency_key
                )
            )
            
            key = result.scalar_one_or_none()
            
            if not key:
                return None
            
            return {
                "key": key.key,
                "user_id": key.user_id,
                "status": key.status,
                "is_processing": key.is_processing,
                "created_at": key.created_at.isoformat() if key.created_at else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "completed_at": key.completed_at.isoformat() if key.completed_at else None,
                "response_status": key.response_status,
                "lock_holder": key.lock_holder
            }