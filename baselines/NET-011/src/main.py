"""
Main application for gRPC Service Mesh

Orchestrates multiple gRPC services with load balancing and health checks.
"""

import asyncio
import os
import logging
import signal
import sys
from typing import List, Dict, Any
import yaml
import json
from datetime import datetime

from server import GrpcServer
from client import GrpcClient, LoadBalancer, LoadBalanceAlgorithm, RetryPolicy, ServiceEndpoint


class ServiceMesh:
    """Service mesh orchestrator"""
    
    def __init__(self, config_path: str = "config/mesh.yaml"):
        self.config = self._load_config(config_path)
        self.servers: List[GrpcServer] = []
        self.clients: Dict[str, GrpcClient] = {}
        self.logger = logging.getLogger(__name__)
        self.running = False
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load mesh configuration"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            "services": [
                {
                    "name": "mesh-service-1",
                    "port": 50051,
                    "replicas": 1,
                    "use_tls": True
                },
                {
                    "name": "mesh-service-2",
                    "port": 50052,
                    "replicas": 1,
                    "use_tls": True
                },
                {
                    "name": "mesh-service-3",
                    "port": 50053,
                    "replicas": 1,
                    "use_tls": True
                }
            ],
            "load_balancer": {
                "algorithm": "round_robin",
                "health_check_interval": 30,
                "unhealthy_threshold": 3
            },
            "retry_policy": {
                "max_attempts": 3,
                "initial_backoff": 1.0,
                "max_backoff": 60.0,
                "backoff_multiplier": 2.0
            },
            "tracing": {
                "enabled": True,
                "sample_rate": 1.0,
                "exporter": "jaeger"
            },
            "mtls": {
                "enabled": True,
                "cert_dir": "certs"
            }
        }
    
    async def start(self):
        """Start the service mesh"""
        self.running = True
        self.logger.info("Starting service mesh...")
        
        # Start servers
        for service_config in self.config["services"]:
            for replica in range(service_config.get("replicas", 1)):
                port = service_config["port"] + replica
                server = GrpcServer(
                    port=port,
                    use_tls=service_config.get("use_tls", True)
                )
                await server.start()
                self.servers.append(server)
                self.logger.info(f"Started server on port {port}")
        
        # Initialize clients with load balancing
        await self._initialize_clients()
        
        # Start monitoring
        asyncio.create_task(self._monitor_services())
        
        # Start demo workload
        asyncio.create_task(self._demo_workload())
        
        self.logger.info("Service mesh started successfully")
    
    async def stop(self):
        """Stop the service mesh"""
        self.running = False
        self.logger.info("Stopping service mesh...")
        
        # Stop servers
        for server in self.servers:
            await server.stop()
        
        # Close client connections
        for client in self.clients.values():
            await client.close()
        
        self.logger.info("Service mesh stopped")
    
    async def _initialize_clients(self):
        """Initialize clients with service discovery"""
        # Create load balancer
        algorithm = LoadBalanceAlgorithm(
            self.config["load_balancer"].get("algorithm", "round_robin")
        )
        load_balancer = LoadBalancer(algorithm)
        
        # Add service endpoints
        for service_config in self.config["services"]:
            for replica in range(service_config.get("replicas", 1)):
                port = service_config["port"] + replica
                endpoint = ServiceEndpoint(
                    service_id=f"{service_config['name']}-{replica}",
                    address="localhost",
                    port=port,
                    weight=100,
                    healthy=True
                )
                load_balancer.add_endpoint(endpoint)
        
        # Create retry policy
        retry_config = self.config.get("retry_policy", {})
        retry_policy = RetryPolicy(
            max_attempts=retry_config.get("max_attempts", 3),
            initial_backoff=retry_config.get("initial_backoff", 1.0),
            max_backoff=retry_config.get("max_backoff", 60.0),
            backoff_multiplier=retry_config.get("backoff_multiplier", 2.0)
        )
        
        # Create client
        use_tls = self.config.get("mtls", {}).get("enabled", True)
        client = GrpcClient(
            service_name="mesh.v1.MeshService",
            load_balancer=load_balancer,
            retry_policy=retry_policy,
            use_tls=use_tls
        )
        
        self.clients["mesh_service"] = client
    
    async def _monitor_services(self):
        """Monitor service health"""
        interval = self.config["load_balancer"].get("health_check_interval", 30)
        
        while self.running:
            try:
                # Check health of all services
                for client in self.clients.values():
                    for endpoint in client.load_balancer.endpoints:
                        # Perform health check
                        health_status = await self._check_endpoint_health(endpoint)
                        
                        if health_status:
                            client.load_balancer.mark_healthy(endpoint.service_id)
                        else:
                            client.load_balancer.mark_unhealthy(endpoint.service_id)
                
                # Log status
                healthy_count = sum(
                    1 for client in self.clients.values()
                    for endpoint in client.load_balancer.endpoints
                    if endpoint.healthy
                )
                total_count = sum(
                    len(client.load_balancer.endpoints)
                    for client in self.clients.values()
                )
                
                self.logger.info(f"Service health: {healthy_count}/{total_count} healthy")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)
    
    async def _check_endpoint_health(self, endpoint: ServiceEndpoint) -> bool:
        """Check health of a specific endpoint"""
        try:
            # In real implementation, make actual health check call
            # For now, simulate with success probability
            import random
            return random.random() > 0.1  # 90% healthy
        except Exception:
            return False
    
    async def _demo_workload(self):
        """Generate demo workload to test the mesh"""
        await asyncio.sleep(5)  # Wait for services to initialize
        
        client = self.clients.get("mesh_service")
        if not client:
            return
        
        self.logger.info("Starting demo workload...")
        
        while self.running:
            try:
                # Test unary RPC with retry
                request = {
                    "request_id": f"req-{datetime.now().timestamp()}",
                    "data": "test data",
                    "metadata": {"client": "demo"}
                }
                
                response = await client.call_with_retry("Process", request)
                self.logger.info(f"Unary RPC response: {response}")
                
                # Test streaming RPC
                stream_request = {
                    "stream_id": f"stream-{datetime.now().timestamp()}",
                    "event_types": ["demo", "test"]
                }
                
                event_count = 0
                async for event in client.stream_with_retry("StreamEvents", stream_request):
                    event_count += 1
                    if event_count >= 3:
                        break
                
                self.logger.info(f"Received {event_count} events from stream")
                
                # Test request hedging
                hedged_response = await client.call_with_hedging("Process", request)
                self.logger.info(f"Hedged RPC response: {hedged_response}")
                
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Demo workload error: {e}")
                await asyncio.sleep(30)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get service mesh metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "services": [],
            "load_balancer": {},
            "health": {}
        }
        
        # Collect service metrics
        for i, server in enumerate(self.servers):
            metrics["services"].append({
                "server_id": server.service_servicer.server_id,
                "port": server.port,
                "request_count": server.service_servicer.request_count,
                "active_streams": len(server.service_servicer.active_streams)
            })
        
        # Collect load balancer metrics
        for name, client in self.clients.items():
            endpoints_status = []
            for endpoint in client.load_balancer.endpoints:
                endpoints_status.append({
                    "service_id": endpoint.service_id,
                    "healthy": endpoint.healthy,
                    "active_connections": endpoint.active_connections,
                    "consecutive_failures": endpoint.consecutive_failures
                })
            
            metrics["load_balancer"][name] = {
                "algorithm": client.load_balancer.algorithm.value,
                "endpoints": endpoints_status
            }
        
        # Calculate overall health
        total_endpoints = sum(
            len(client.load_balancer.endpoints)
            for client in self.clients.values()
        )
        healthy_endpoints = sum(
            1 for client in self.clients.values()
            for endpoint in client.load_balancer.endpoints
            if endpoint.healthy
        )
        
        metrics["health"] = {
            "total_endpoints": total_endpoints,
            "healthy_endpoints": healthy_endpoints,
            "health_percentage": (healthy_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
        }
        
        return metrics


async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create service mesh
    config_path = os.getenv("MESH_CONFIG", "config/mesh.yaml")
    mesh = ServiceMesh(config_path)
    
    # Handle shutdown signals
    async def shutdown(sig):
        logging.info(f"Received signal {sig.name}")
        await mesh.stop()
        asyncio.get_event_loop().stop()
    
    # Register signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(shutdown(s))
        )
    
    # Start mesh
    await mesh.start()
    
    # Keep running
    try:
        while mesh.running:
            # Print metrics periodically
            metrics = await mesh.get_metrics()
            logging.info(f"Metrics: {json.dumps(metrics, indent=2)}")
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        await mesh.stop()


if __name__ == "__main__":
    asyncio.run(main())