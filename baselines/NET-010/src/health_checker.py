"""Health check service for proxy and backends"""
import asyncio
import logging
from typing import Dict, Any

from .config import ProxyConfig
from .backend_manager import BackendManager

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health checker for proxy system"""
    
    def __init__(self, config: ProxyConfig, backend_manager: BackendManager):
        self.config = config
        self.backend_manager = backend_manager
        self.proxy_healthy = True
        self.start_time = asyncio.get_event_loop().time()
    
    async def start(self):
        """Start health checker"""
        logger.info("Health checker started")
    
    async def stop(self):
        """Stop health checker"""
        logger.info("Health checker stopped")
    
    async def check_health(self) -> Dict[str, Any]:
        """Check overall proxy health"""
        backends_status = self.backend_manager.get_backend_status()
        healthy_backends = sum(
            1 for backend in backends_status.values()
            if backend["healthy"]
        )
        total_backends = len(backends_status)
        
        # Proxy is healthy if at least one backend is healthy
        is_healthy = healthy_backends > 0
        
        uptime = asyncio.get_event_loop().time() - self.start_time
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "uptime_seconds": uptime,
            "backends": {
                "healthy": healthy_backends,
                "total": total_backends
            },
            "features": {
                "circuit_breaker": self.config.circuit_breaker_enabled,
                "rate_limiting": self.config.rate_limit_enabled,
                "health_checks": self.config.health_check_enabled
            }
        }
    
    async def get_backends_status(self) -> Dict[str, Any]:
        """Get detailed backend status"""
        return self.backend_manager.get_backend_status()