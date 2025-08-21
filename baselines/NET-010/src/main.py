"""
NET-010: Reverse Proxy with Timeout, Retry, and Circuit Breaker
Main application entry point
"""
import asyncio
import logging
import signal
from typing import Optional

from aiohttp import web
import aiohttp_cors

from .proxy import ReverseProxy
from .config import ProxyConfig
from .health_checker import HealthChecker
from .metrics import setup_metrics, metrics_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProxyApplication:
    """Main proxy application"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = ProxyConfig.load(config_path)
        self.app = web.Application(
            middlewares=[],
            client_max_size=self.config.max_request_size
        )
        self.proxy = ReverseProxy(self.config)
        self.health_checker = HealthChecker(self.config, self.proxy.backend_manager)
        self.setup_routes()
        self.setup_cors()
        self.setup_metrics()
        
    def setup_routes(self):
        """Setup HTTP routes"""
        # Health and metrics endpoints
        self.app.router.add_get('/health', self.health_handler)
        self.app.router.add_get('/metrics', metrics_handler)
        self.app.router.add_get('/backends/health', self.backends_health_handler)
        
        # Proxy all other requests
        self.app.router.add_route('*', '/{path:.*}', self.proxy.handle_request)
        
    def setup_cors(self):
        """Setup CORS if enabled"""
        if self.config.cors_enabled:
            cors = aiohttp_cors.setup(self.app, defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*"
                )
            })
            
            for route in list(self.app.router.routes()):
                cors.add(route)
    
    def setup_metrics(self):
        """Setup Prometheus metrics"""
        setup_metrics(self.app)
    
    async def health_handler(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        health_status = await self.health_checker.check_health()
        
        if health_status['status'] == 'healthy':
            return web.json_response(health_status, status=200)
        else:
            return web.json_response(health_status, status=503)
    
    async def backends_health_handler(self, request: web.Request) -> web.Response:
        """Backend health status endpoint"""
        backends_status = await self.health_checker.get_backends_status()
        return web.json_response(backends_status)
    
    async def startup(self, app: web.Application):
        """Application startup handler"""
        logger.info("Starting reverse proxy...")
        
        # Start proxy components
        await self.proxy.start()
        
        # Start health checker
        await self.health_checker.start()
        
        logger.info(f"Proxy started on port {self.config.port}")
    
    async def cleanup(self, app: web.Application):
        """Application cleanup handler"""
        logger.info("Shutting down reverse proxy...")
        
        # Stop health checker
        await self.health_checker.stop()
        
        # Stop proxy components
        await self.proxy.stop()
        
        logger.info("Proxy shutdown complete")
    
    def run(self):
        """Run the proxy application"""
        self.app.on_startup.append(self.startup)
        self.app.on_cleanup.append(self.cleanup)
        
        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.shutdown())
            )
        
        # Run the application
        web.run_app(
            self.app,
            host=self.config.host,
            port=self.config.port,
            access_log=logger if self.config.access_log else None
        )
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Received shutdown signal")
        await self.app.shutdown()
        await self.app.cleanup()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reverse Proxy with Resilience Patterns")
    parser.add_argument(
        "--config",
        default="config/proxy.yaml",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Create and run application
    app = ProxyApplication(config_path=args.config)
    app.run()


if __name__ == "__main__":
    main()