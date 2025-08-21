"""Core reverse proxy implementation"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional

import aiohttp
from aiohttp import web
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from .backend_manager import BackendManager
from .circuit_breaker import CircuitBreakerManager
from .rate_limiter import RateLimiter
from .config import ProxyConfig
from .metrics import (
    request_counter,
    request_duration,
    backend_request_counter,
    circuit_breaker_state
)

logger = logging.getLogger(__name__)


class ReverseProxy:
    """Reverse proxy with resilience patterns"""
    
    def __init__(self, config: ProxyConfig):
        self.config = config
        self.backend_manager = BackendManager(config)
        self.circuit_breaker = CircuitBreakerManager(config)
        self.rate_limiter = RateLimiter(config)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def start(self):
        """Start proxy components"""
        # Create HTTP client session
        timeout = aiohttp.ClientTimeout(
            total=self.config.request_timeout,
            connect=self.config.connect_timeout,
            sock_read=self.config.read_timeout
        )
        
        connector = aiohttp.TCPConnector(
            limit=self.config.connection_pool_size,
            limit_per_host=self.config.connections_per_host,
            ttl_dns_cache=300
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector
        )
        
        # Start components
        await self.backend_manager.start()
        await self.rate_limiter.start()
        
        logger.info("Proxy components started")
    
    async def stop(self):
        """Stop proxy components"""
        if self.session:
            await self.session.close()
        
        await self.backend_manager.stop()
        await self.rate_limiter.stop()
        
        logger.info("Proxy components stopped")
    
    async def handle_request(self, request: web.Request) -> web.Response:
        """Handle incoming proxy request"""
        start_time = time.time()
        client_ip = request.remote
        
        try:
            # Rate limiting check
            if not await self.rate_limiter.allow_request(client_ip):
                request_counter.labels(
                    method=request.method,
                    status="429",
                    backend="rate_limited"
                ).inc()
                return web.Response(status=429, text="Rate limit exceeded")
            
            # Select backend
            backend = await self.backend_manager.select_backend()
            if not backend:
                request_counter.labels(
                    method=request.method,
                    status="503",
                    backend="no_backend"
                ).inc()
                return web.Response(status=503, text="No healthy backends available")
            
            # Check circuit breaker
            if not self.circuit_breaker.can_request(backend.id):
                # Try another backend
                backend = await self.backend_manager.select_backend(exclude=[backend.id])
                if not backend:
                    request_counter.labels(
                        method=request.method,
                        status="503",
                        backend="all_circuits_open"
                    ).inc()
                    return web.Response(status=503, text="All backends unavailable")
            
            # Forward request with retry
            response = await self._forward_request(request, backend)
            
            # Update metrics
            duration = time.time() - start_time
            request_duration.labels(
                method=request.method,
                backend=backend.id
            ).observe(duration)
            
            request_counter.labels(
                method=request.method,
                status=str(response.status),
                backend=backend.id
            ).inc()
            
            # Update circuit breaker
            if response.status >= 500:
                self.circuit_breaker.record_failure(backend.id)
            else:
                self.circuit_breaker.record_success(backend.id)
            
            return response
            
        except asyncio.TimeoutError:
            request_counter.labels(
                method=request.method,
                status="504",
                backend="timeout"
            ).inc()
            return web.Response(status=504, text="Gateway timeout")
            
        except Exception as e:
            logger.error(f"Proxy error: {e}", exc_info=True)
            request_counter.labels(
                method=request.method,
                status="500",
                backend="error"
            ).inc()
            return web.Response(status=500, text="Internal proxy error")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, max=2),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _forward_request(self, request: web.Request, backend: Any) -> web.Response:
        """Forward request to backend with retry"""
        # Build backend URL
        path = request.match_info.get('path', '')
        query_string = request.query_string
        backend_url = f"{backend.url}/{path}"
        if query_string:
            backend_url += f"?{query_string}"
        
        # Prepare headers
        headers = dict(request.headers)
        headers = self._prepare_headers(headers, request)
        
        # Read request body
        body = await request.read()
        
        # Make backend request
        backend_request_counter.labels(
            backend=backend.id,
            method=request.method
        ).inc()
        
        async with self.session.request(
            method=request.method,
            url=backend_url,
            headers=headers,
            data=body,
            allow_redirects=False,
            ssl=False  # For testing, use proper SSL in production
        ) as backend_response:
            # Read response
            response_body = await backend_response.read()
            
            # Build client response
            response = web.Response(
                status=backend_response.status,
                body=response_body,
                headers=self._prepare_response_headers(backend_response.headers)
            )
            
            return response
    
    def _prepare_headers(self, headers: Dict[str, str], request: web.Request) -> Dict[str, str]:
        """Prepare headers for backend request"""
        # Remove hop-by-hop headers
        hop_by_hop = [
            'connection', 'keep-alive', 'proxy-authenticate',
            'proxy-authorization', 'te', 'trailers', 'transfer-encoding',
            'upgrade'
        ]
        
        for header in hop_by_hop:
            headers.pop(header, None)
        
        # Add X-Forwarded headers
        headers['X-Forwarded-For'] = request.remote
        headers['X-Forwarded-Proto'] = request.scheme
        headers['X-Forwarded-Host'] = request.host
        headers['X-Real-IP'] = request.remote
        
        return headers
    
    def _prepare_response_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Prepare headers for client response"""
        # Remove hop-by-hop headers
        hop_by_hop = [
            'connection', 'keep-alive', 'proxy-authenticate',
            'proxy-authorization', 'te', 'trailers', 'transfer-encoding',
            'upgrade'
        ]
        
        response_headers = {}
        for key, value in headers.items():
            if key.lower() not in hop_by_hop:
                response_headers[key] = value
        
        return response_headers