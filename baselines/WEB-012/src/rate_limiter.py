"""Rate limiting implementation with Redis backend"""
import time
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import hashlib
import json

import redis.asyncio as redis
from fastapi import Request, Response, HTTPException
import structlog

from models import (
    RateLimitRule, RateLimitResponse, RateLimitConfig,
    AuditLog, AuditEventType
)

logger = structlog.get_logger()


class RateLimiter:
    """Rate limiter with multiple strategies"""
    
    def __init__(self, redis_client: redis.Redis, db_session_factory=None):
        self.redis = redis_client
        self.db_session_factory = db_session_factory
        self.config = RateLimitConfig()
        self.rules = self.config.DEFAULT_LIMITS
    
    async def check_rate_limit(
        self,
        request: Request,
        user_id: Optional[str] = None,
        custom_rules: Optional[List[RateLimitRule]] = None
    ) -> Tuple[bool, Optional[RateLimitResponse]]:
        """
        Check if request is within rate limits
        Returns: (is_allowed, rate_limit_response)
        """
        
        rules_to_check = custom_rules or self.rules
        
        for rule in rules_to_check:
            key = self._generate_key(rule, request, user_id)
            
            if rule.burst_limit:
                # Use token bucket algorithm for burst handling
                is_allowed, remaining, reset_at = await self._check_token_bucket(
                    key, rule
                )
            else:
                # Use sliding window algorithm
                is_allowed, remaining, reset_at = await self._check_sliding_window(
                    key, rule
                )
            
            if not is_allowed:
                # Rate limit exceeded
                retry_after = int((reset_at - datetime.utcnow()).total_seconds())
                
                response = RateLimitResponse(
                    message=f"Rate limit exceeded for {rule.name}",
                    retry_after=max(retry_after, 1),
                    limit=rule.limit,
                    remaining=remaining,
                    reset_at=reset_at
                )
                
                # Audit log
                await self._audit_rate_limit_exceeded(
                    request, user_id, rule, response
                )
                
                logger.warning("Rate limit exceeded",
                             rule=rule.name, user_id=user_id,
                             key=key, remaining=remaining)
                
                return False, response
        
        return True, None
    
    def _generate_key(
        self,
        rule: RateLimitRule,
        request: Request,
        user_id: Optional[str]
    ) -> str:
        """Generate Redis key for rate limit tracking"""
        
        parts = [self.config.REDIS_PREFIX]
        
        if rule.scope == "global":
            parts.append("global")
        elif rule.scope == "user":
            if not user_id:
                # Fall back to IP-based limiting
                parts.append(f"ip:{request.client.host}")
            else:
                parts.append(f"user:{user_id}")
        elif rule.scope == "ip":
            parts.append(f"ip:{request.client.host}")
        elif rule.scope == "endpoint":
            endpoint = f"{request.method}:{request.url.path}"
            endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()[:8]
            parts.append(f"endpoint:{endpoint_hash}")
        elif rule.scope == "user_endpoint":
            if user_id:
                endpoint = f"{request.method}:{request.url.path}"
                endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()[:8]
                parts.append(f"user_endpoint:{user_id}:{endpoint_hash}")
            else:
                parts.append(f"ip_endpoint:{request.client.host}")
        
        parts.append(rule.name)
        
        return ":".join(parts)
    
    async def _check_sliding_window(
        self,
        key: str,
        rule: RateLimitRule
    ) -> Tuple[bool, int, datetime]:
        """Check rate limit using sliding window algorithm"""
        
        now = time.time()
        window_start = now - rule.window_seconds
        
        # Use Redis sorted set for sliding window
        pipe = self.redis.pipeline()
        
        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count requests in current window
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        
        # Set TTL
        pipe.expire(key, rule.window_seconds + 60)
        
        # Get the oldest entry to calculate reset time
        pipe.zrange(key, 0, 0, withscores=True)
        
        results = await pipe.execute()
        
        # results[1] is the count before adding current request
        count = results[1]
        
        # Calculate remaining requests
        remaining = max(0, rule.limit - count - 1)
        
        # Calculate reset time
        if results[4]:  # Oldest entry exists
            oldest_timestamp = results[4][0][1]
            reset_at = datetime.utcfromtimestamp(oldest_timestamp + rule.window_seconds)
        else:
            reset_at = datetime.utcnow() + timedelta(seconds=rule.window_seconds)
        
        # Check if limit exceeded
        if count >= rule.limit:
            # Remove the current request we just added
            await self.redis.zrem(key, str(now))
            return False, 0, reset_at
        
        return True, remaining, reset_at
    
    async def _check_token_bucket(
        self,
        key: str,
        rule: RateLimitRule
    ) -> Tuple[bool, int, datetime]:
        """Check rate limit using token bucket algorithm"""
        
        now = time.time()
        
        # Token bucket keys
        tokens_key = f"{key}:tokens"
        last_refill_key = f"{key}:last_refill"
        
        # Get current state
        pipe = self.redis.pipeline()
        pipe.get(tokens_key)
        pipe.get(last_refill_key)
        results = await pipe.execute()
        
        current_tokens = float(results[0]) if results[0] else rule.burst_limit
        last_refill = float(results[1]) if results[1] else now
        
        # Calculate tokens to add based on time passed
        time_passed = now - last_refill
        refill_rate = rule.limit / rule.window_seconds
        tokens_to_add = time_passed * refill_rate
        
        # Update token count (capped at burst limit)
        current_tokens = min(rule.burst_limit, current_tokens + tokens_to_add)
        
        # Check if we have tokens available
        if current_tokens >= 1:
            # Consume a token
            current_tokens -= 1
            
            # Update state
            pipe = self.redis.pipeline()
            pipe.set(tokens_key, current_tokens, ex=rule.window_seconds + 60)
            pipe.set(last_refill_key, now, ex=rule.window_seconds + 60)
            await pipe.execute()
            
            # Calculate reset time (when bucket will be full)
            tokens_needed = rule.burst_limit - current_tokens
            seconds_to_full = tokens_needed / refill_rate
            reset_at = datetime.utcfromtimestamp(now + seconds_to_full)
            
            return True, int(current_tokens), reset_at
        
        else:
            # No tokens available
            # Calculate when next token will be available
            seconds_to_token = (1 - current_tokens) / refill_rate
            reset_at = datetime.utcfromtimestamp(now + seconds_to_token)
            
            return False, 0, reset_at
    
    async def get_current_limits(
        self,
        request: Request,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get current rate limit status for all rules"""
        
        limits_status = {}
        
        for rule in self.rules:
            key = self._generate_key(rule, request, user_id)
            
            if rule.burst_limit:
                is_allowed, remaining, reset_at = await self._check_token_bucket(
                    key, rule
                )
            else:
                # Check without adding request
                now = time.time()
                window_start = now - rule.window_seconds
                
                # Count requests in current window
                count = await self.redis.zcount(key, window_start, now)
                remaining = max(0, rule.limit - count)
                
                # Get oldest entry for reset time
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_timestamp = oldest[0][1]
                    reset_at = datetime.utcfromtimestamp(
                        oldest_timestamp + rule.window_seconds
                    )
                else:
                    reset_at = datetime.utcnow() + timedelta(seconds=rule.window_seconds)
            
            limits_status[rule.name] = {
                "limit": rule.limit,
                "remaining": remaining,
                "reset_at": reset_at.isoformat(),
                "window_seconds": rule.window_seconds
            }
        
        return limits_status
    
    def add_rate_limit_headers(
        self,
        response: Response,
        rule: RateLimitRule,
        remaining: int,
        reset_at: datetime
    ):
        """Add rate limit headers to response"""
        
        response.headers[self.config.RATE_LIMIT_HEADER] = str(rule.limit)
        response.headers[self.config.RATE_LIMIT_REMAINING_HEADER] = str(remaining)
        response.headers[self.config.RATE_LIMIT_RESET_HEADER] = str(int(reset_at.timestamp()))
    
    async def _audit_rate_limit_exceeded(
        self,
        request: Request,
        user_id: Optional[str],
        rule: RateLimitRule,
        response: RateLimitResponse
    ):
        """Create audit log for rate limit exceeded"""
        
        if not self.db_session_factory:
            return
        
        async with self.db_session_factory() as session:
            audit_entry = AuditLog(
                user_id=user_id,
                request_path=str(request.url.path),
                request_method=request.method,
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                event_type=AuditEventType.RATE_LIMIT_EXCEEDED.value,
                event_details={
                    "rule_name": rule.name,
                    "limit": rule.limit,
                    "window_seconds": rule.window_seconds,
                    "retry_after": response.retry_after
                },
                created_at=datetime.utcnow()
            )
            
            session.add(audit_entry)
            await session.commit()
    
    async def reset_limits(
        self,
        user_id: Optional[str] = None,
        scope: Optional[str] = None
    ) -> int:
        """Reset rate limits for a user or scope"""
        
        pattern = f"{self.config.REDIS_PREFIX}:"
        
        if user_id:
            pattern += f"user:{user_id}:*"
        elif scope:
            pattern += f"{scope}:*"
        else:
            pattern += "*"
        
        # Find all matching keys
        keys = []
        async for key in self.redis.scan_iter(pattern):
            keys.append(key)
        
        # Delete keys
        if keys:
            await self.redis.delete(*keys)
            logger.info("Reset rate limits", 
                       user_id=user_id, scope=scope, keys_deleted=len(keys))
        
        return len(keys)


class DistributedRateLimiter(RateLimiter):
    """Distributed rate limiter using Redis with Lua scripts for atomicity"""
    
    def __init__(self, redis_client: redis.Redis, db_session_factory=None):
        super().__init__(redis_client, db_session_factory)
        
        # Lua script for atomic sliding window check
        self.sliding_window_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        
        local window_start = now - window
        
        -- Remove old entries
        redis.call('zremrangebyscore', key, 0, window_start)
        
        -- Count current requests
        local count = redis.call('zcard', key)
        
        if count < limit then
            -- Add current request
            redis.call('zadd', key, now, now)
            redis.call('expire', key, window + 60)
            return {1, limit - count - 1}  -- allowed, remaining
        else
            return {0, 0}  -- not allowed, remaining
        end
        """
        
        # Register script
        self.sliding_window_sha = None
    
    async def _ensure_scripts_loaded(self):
        """Ensure Lua scripts are loaded in Redis"""
        if not self.sliding_window_sha:
            self.sliding_window_sha = await self.redis.script_load(
                self.sliding_window_script
            )
    
    async def _check_sliding_window_atomic(
        self,
        key: str,
        rule: RateLimitRule
    ) -> Tuple[bool, int, datetime]:
        """Atomic sliding window check using Lua script"""
        
        await self._ensure_scripts_loaded()
        
        now = time.time()
        
        try:
            result = await self.redis.evalsha(
                self.sliding_window_sha,
                1,  # number of keys
                key,  # KEYS[1]
                now,  # ARGV[1]
                rule.window_seconds,  # ARGV[2]
                rule.limit  # ARGV[3]
            )
            
            is_allowed = bool(result[0])
            remaining = result[1]
            
            # Calculate reset time
            reset_at = datetime.utcnow() + timedelta(seconds=rule.window_seconds)
            
            return is_allowed, remaining, reset_at
            
        except redis.NoScriptError:
            # Script not in cache, reload and retry
            self.sliding_window_sha = None
            return await self._check_sliding_window(key, rule)