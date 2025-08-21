"""Backend service manager with health checks and load balancing"""
import asyncio
import logging
import random
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .config import ProxyConfig, BackendConfig

logger = logging.getLogger(__name__)


@dataclass
class Backend:
    """Backend server representation"""
    id: str
    url: str
    weight: int = 1
    healthy: bool = True
    last_health_check: datetime = field(default_factory=datetime.utcnow)
    consecutive_failures: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return (self.total_requests - self.failed_requests) / self.total_requests


class BackendManager:
    """Manages backend servers with health checks and load balancing"""
    
    def __init__(self, config: ProxyConfig):
        self.config = config
        self.backends: Dict[str, Backend] = {}
        self.load_balancing_algorithm = config.load_balancing_algorithm
        self._health_check_task: Optional[asyncio.Task] = None
        self._round_robin_index = 0
        
        # Initialize backends
        for backend_config in config.backends:
            backend = Backend(
                id=backend_config.id,
                url=backend_config.url,
                weight=backend_config.weight
            )
            self.backends[backend.id] = backend
    
    async def start(self):
        """Start backend manager"""
        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info(f"Backend manager started with {len(self.backends)} backends")
    
    async def stop(self):
        """Stop backend manager"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Backend manager stopped")
    
    async def select_backend(self, exclude: Optional[List[str]] = None) -> Optional[Backend]:
        """Select a backend based on load balancing algorithm"""
        # Get healthy backends
        available_backends = [
            b for b in self.backends.values()
            if b.healthy and (not exclude or b.id not in exclude)
        ]
        
        if not available_backends:
            return None
        
        if self.load_balancing_algorithm == "round_robin":
            return self._round_robin_select(available_backends)
        elif self.load_balancing_algorithm == "random":
            return random.choice(available_backends)
        elif self.load_balancing_algorithm == "weighted":
            return self._weighted_select(available_backends)
        elif self.load_balancing_algorithm == "least_connections":
            return self._least_connections_select(available_backends)
        else:
            # Default to round robin
            return self._round_robin_select(available_backends)
    
    def _round_robin_select(self, backends: List[Backend]) -> Backend:
        """Round-robin selection"""
        backend = backends[self._round_robin_index % len(backends)]
        self._round_robin_index += 1
        backend.total_requests += 1
        return backend
    
    def _weighted_select(self, backends: List[Backend]) -> Backend:
        """Weighted random selection"""
        weights = [b.weight for b in backends]
        backend = random.choices(backends, weights=weights)[0]
        backend.total_requests += 1
        return backend
    
    def _least_connections_select(self, backends: List[Backend]) -> Backend:
        """Select backend with least active connections (approximated by recent requests)"""
        # Sort by total requests (as proxy for connections)
        backend = min(backends, key=lambda b: b.total_requests)
        backend.total_requests += 1
        return backend
    
    async def _health_check_loop(self):
        """Periodic health check loop"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._check_all_backends()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _check_all_backends(self):
        """Check health of all backends"""
        tasks = [
            self._check_backend_health(backend)
            for backend in self.backends.values()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_backend_health(self, backend: Backend):
        """Check health of a single backend"""
        try:
            # Simple HTTP health check
            import aiohttp
            
            health_url = f"{backend.url}{self.config.health_check_path}"
            timeout = aiohttp.ClientTimeout(total=self.config.health_check_timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(health_url) as response:
                    if response.status == 200:
                        # Backend is healthy
                        if not backend.healthy:
                            logger.info(f"Backend {backend.id} is now healthy")
                        backend.healthy = True
                        backend.consecutive_failures = 0
                    else:
                        # Backend returned non-200 status
                        self._mark_backend_unhealthy(backend, f"Status {response.status}")
                        
        except Exception as e:
            # Health check failed
            self._mark_backend_unhealthy(backend, str(e))
        
        backend.last_health_check = datetime.utcnow()
    
    def _mark_backend_unhealthy(self, backend: Backend, reason: str):
        """Mark backend as unhealthy"""
        backend.consecutive_failures += 1
        
        if backend.consecutive_failures >= self.config.health_check_threshold:
            if backend.healthy:
                logger.warning(f"Backend {backend.id} marked unhealthy: {reason}")
            backend.healthy = False
    
    def get_backend_status(self) -> Dict[str, Any]:
        """Get status of all backends"""
        return {
            backend_id: {
                "url": backend.url,
                "healthy": backend.healthy,
                "weight": backend.weight,
                "last_health_check": backend.last_health_check.isoformat(),
                "consecutive_failures": backend.consecutive_failures,
                "total_requests": backend.total_requests,
                "failed_requests": backend.failed_requests,
                "success_rate": backend.success_rate
            }
            for backend_id, backend in self.backends.items()
        }
    
    def mark_request_failed(self, backend_id: str):
        """Mark a request as failed for a backend"""
        if backend_id in self.backends:
            self.backends[backend_id].failed_requests += 1