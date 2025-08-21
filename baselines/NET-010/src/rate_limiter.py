"""Rate limiting implementation"""
import asyncio
import logging
import time
from typing import Dict, Optional
from collections import defaultdict, deque

from .config import ProxyConfig

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket rate limiter"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens"""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


class SlidingWindowCounter:
    """Sliding window counter for rate limiting"""
    
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # in seconds
        self.max_requests = max_requests
        self.requests = deque()
    
    def allow_request(self) -> bool:
        """Check if request is allowed"""
        now = time.time()
        
        # Remove old requests outside the window
        while self.requests and self.requests[0] < now - self.window_size:
            self.requests.popleft()
        
        # Check if we're at the limit
        if len(self.requests) >= self.max_requests:
            return False
        
        # Add current request
        self.requests.append(now)
        return True


class RateLimiter:
    """Rate limiter for client requests"""
    
    def __init__(self, config: ProxyConfig):
        self.config = config
        self.algorithm = config.rate_limit_algorithm
        
        # Storage for per-client limiters
        self.client_limiters: Dict[str, any] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Global rate limiter
        if self.algorithm == "token_bucket":
            self.global_limiter = TokenBucket(
                capacity=config.rate_limit_burst,
                refill_rate=config.rate_limit_requests_per_second
            )
        else:
            self.global_limiter = SlidingWindowCounter(
                window_size=config.rate_limit_window,
                max_requests=config.rate_limit_requests_per_second * config.rate_limit_window
            )
    
    async def start(self):
        """Start rate limiter"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"Rate limiter started with {self.algorithm} algorithm")
    
    async def stop(self):
        """Stop rate limiter"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Rate limiter stopped")
    
    async def allow_request(self, client_id: str) -> bool:
        """Check if request from client is allowed"""
        # Check global rate limit
        if not self._check_global_limit():
            logger.debug(f"Global rate limit exceeded")
            return False
        
        # Check per-client rate limit
        if not self._check_client_limit(client_id):
            logger.debug(f"Client {client_id} rate limit exceeded")
            return False
        
        return True
    
    def _check_global_limit(self) -> bool:
        """Check global rate limit"""
        if self.algorithm == "token_bucket":
            return self.global_limiter.consume()
        else:
            return self.global_limiter.allow_request()
    
    def _check_client_limit(self, client_id: str) -> bool:
        """Check per-client rate limit"""
        if not self.config.rate_limit_per_client:
            return True
        
        # Get or create client limiter
        if client_id not in self.client_limiters:
            if self.algorithm == "token_bucket":
                self.client_limiters[client_id] = TokenBucket(
                    capacity=self.config.rate_limit_per_client_burst,
                    refill_rate=self.config.rate_limit_per_client_requests
                )
            else:
                self.client_limiters[client_id] = SlidingWindowCounter(
                    window_size=self.config.rate_limit_window,
                    max_requests=self.config.rate_limit_per_client_requests * self.config.rate_limit_window
                )
        
        limiter = self.client_limiters[client_id]
        
        if self.algorithm == "token_bucket":
            return limiter.consume()
        else:
            return limiter.allow_request()
    
    async def _cleanup_loop(self):
        """Periodic cleanup of old client limiters"""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
                # Remove old client limiters that haven't been used
                # This is a simple implementation; in production, track last access time
                if len(self.client_limiters) > 10000:
                    # Clear half of the limiters if we have too many
                    to_remove = list(self.client_limiters.keys())[:5000]
                    for client_id in to_remove:
                        del self.client_limiters[client_id]
                    
                    logger.info(f"Cleaned up {len(to_remove)} client rate limiters")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def get_status(self) -> Dict:
        """Get rate limiter status"""
        return {
            "algorithm": self.algorithm,
            "active_clients": len(self.client_limiters),
            "global_limit": {
                "requests_per_second": self.config.rate_limit_requests_per_second,
                "burst": self.config.rate_limit_burst
            },
            "per_client_limit": {
                "enabled": self.config.rate_limit_per_client,
                "requests_per_second": self.config.rate_limit_per_client_requests,
                "burst": self.config.rate_limit_per_client_burst
            } if self.config.rate_limit_per_client else None
        }