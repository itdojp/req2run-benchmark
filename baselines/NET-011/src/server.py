"""
gRPC Server Implementation with Service Mesh Features

Implements gRPC server with health checking, load balancing, and mTLS.
"""

import asyncio
import grpc
from grpc import aio
import logging
import os
import ssl
import time
from concurrent import futures
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime, timedelta
import uuid
import random
import json
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib

# Proto imports (these would be generated from protoc)
# from mesh.api.v1 import service_pb2, service_pb2_grpc

# For now, we'll create mock implementations
class ServiceServicer:
    """Main service implementation"""
    
    def __init__(self, server_id: str = None):
        self.server_id = server_id or f"server-{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger(__name__)
        self.request_count = 0
        self.active_streams = {}
        self.metrics_buffer = []
        
    async def Process(self, request, context):
        """Unary RPC handler"""
        start_time = time.time()
        self.request_count += 1
        
        # Extract tracing context
        trace_id = self._extract_trace_id(context)
        
        # Log request with trace
        self.logger.info(f"Processing request {request.request_id} [trace:{trace_id}]")
        
        # Simulate processing
        await asyncio.sleep(0.01)
        
        # Build response
        processing_time = time.time() - start_time
        
        return {
            "request_id": request.request_id,
            "result": f"Processed: {request.data}",
            "status": {"code": 0, "message": "Success"},
            "processing_time": {"seconds": int(processing_time), "nanos": int((processing_time % 1) * 1e9)},
            "server_id": self.server_id
        }
    
    async def StreamEvents(self, request, context):
        """Server streaming RPC handler"""
        stream_id = request.stream_id
        self.active_streams[stream_id] = True
        
        self.logger.info(f"Starting event stream {stream_id}")
        
        try:
            event_count = 0
            while self.active_streams.get(stream_id, False):
                # Check if client is still connected
                if context.is_active():
                    # Generate event
                    event = {
                        "event_id": str(uuid.uuid4()),
                        "event_type": random.choice(request.event_types or ["default"]),
                        "payload": {"data": f"Event {event_count}"},
                        "timestamp": {"seconds": int(time.time())},
                        "source": self.server_id
                    }
                    
                    yield event
                    event_count += 1
                    
                    # Wait before next event
                    await asyncio.sleep(1)
                else:
                    break
                    
        finally:
            del self.active_streams[stream_id]
            self.logger.info(f"Closed event stream {stream_id}")
    
    async def CollectMetrics(self, request_iterator, context):
        """Client streaming RPC handler"""
        metrics_count = 0
        last_timestamp = None
        
        async for metric in request_iterator:
            self.metrics_buffer.append(metric)
            metrics_count += 1
            last_timestamp = metric.timestamp
            
            # Process metric
            self.logger.debug(f"Received metric: {metric.metric_name} = {metric.value}")
        
        # Clear old metrics from buffer
        if len(self.metrics_buffer) > 10000:
            self.metrics_buffer = self.metrics_buffer[-5000:]
        
        return {
            "metrics_received": metrics_count,
            "warnings": [] if metrics_count > 0 else ["No metrics received"],
            "last_timestamp": last_timestamp
        }
    
    async def Chat(self, request_iterator, context):
        """Bidirectional streaming RPC handler"""
        user_id = None
        
        async for message in request_iterator:
            if not user_id:
                user_id = message.user_id
                self.logger.info(f"Chat session started for user {user_id}")
            
            # Echo message back with server response
            yield message
            
            # Send system message
            if message.type == 0:  # TEXT message
                system_response = {
                    "user_id": "system",
                    "message": f"Server {self.server_id} received: {message.message}",
                    "timestamp": {"seconds": int(time.time())},
                    "type": 1  # SYSTEM
                }
                yield system_response
        
        self.logger.info(f"Chat session ended for user {user_id}")
    
    async def ProcessV2(self, request, context):
        """Versioned endpoint handler"""
        start_time = time.time()
        
        # V2 processing with bytes data
        result = request.data[::-1]  # Reverse bytes as example
        
        processing_time = time.time() - start_time
        
        return {
            "request_id": request.request_id,
            "result": result,
            "status": {"code": 0, "message": "Success V2"},
            "processing_time": {"seconds": int(processing_time), "nanos": int((processing_time % 1) * 1e9)},
            "server_id": self.server_id,
            "version": "2.0.0"
        }
    
    def _extract_trace_id(self, context) -> str:
        """Extract trace ID from metadata"""
        metadata = dict(context.invocation_metadata())
        return metadata.get("trace-id", str(uuid.uuid4()))


class HealthServicer:
    """Health check service implementation (grpc.health.v1)"""
    
    def __init__(self):
        self.services_status = {
            "": 1,  # Overall server health: SERVING
            "mesh.v1.MeshService": 1,
            "mesh.v1.LoadBalancer": 1
        }
        self.logger = logging.getLogger(__name__)
    
    async def Check(self, request, context):
        """Health check handler"""
        service = request.service or ""
        status = self.services_status.get(service, 3)  # SERVICE_UNKNOWN
        
        return {
            "status": status,
            "message": self._get_status_message(status),
            "timestamp": {"seconds": int(time.time())}
        }
    
    async def Watch(self, request, context):
        """Health watch handler - streams health updates"""
        service = request.service or ""
        
        while context.is_active():
            status = self.services_status.get(service, 3)
            
            yield {
                "status": status,
                "message": self._get_status_message(status),
                "timestamp": {"seconds": int(time.time())}
            }
            
            await asyncio.sleep(5)  # Send update every 5 seconds
    
    def set_service_status(self, service: str, status: int):
        """Update service health status"""
        self.services_status[service] = status
        self.logger.info(f"Health status updated: {service} = {self._get_status_message(status)}")
    
    def _get_status_message(self, status: int) -> str:
        """Get human-readable status message"""
        messages = {
            0: "UNKNOWN",
            1: "SERVING",
            2: "NOT_SERVING",
            3: "SERVICE_UNKNOWN"
        }
        return messages.get(status, "UNKNOWN")


class LoadBalancerServicer:
    """Load balancer service for service discovery"""
    
    def __init__(self):
        self.service_registry: Dict[str, Dict[str, Any]] = {}
        self.health_status: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        self.load_balancer_configs = {}
        
    async def RegisterService(self, request, context):
        """Register service instance"""
        service_key = f"{request.service_name}:{request.service_id}"
        
        self.service_registry[service_key] = {
            "service_name": request.service_name,
            "service_id": request.service_id,
            "address": request.address,
            "port": request.port,
            "metadata": dict(request.metadata),
            "tags": list(request.tags),
            "registered_at": time.time()
        }
        
        # Initialize health status
        self.health_status[service_key] = {
            "healthy": True,
            "last_check": time.time(),
            "consecutive_failures": 0
        }
        
        self.logger.info(f"Service registered: {service_key}")
        
        return {
            "success": True,
            "message": f"Service {request.service_id} registered successfully",
            "registered_at": {"seconds": int(time.time())}
        }
    
    async def DeregisterService(self, request, context):
        """Deregister service instance"""
        # Find and remove service
        removed = False
        for key in list(self.service_registry.keys()):
            if request.service_id in key:
                del self.service_registry[key]
                if key in self.health_status:
                    del self.health_status[key]
                removed = True
                break
        
        return {
            "success": removed,
            "message": f"Service {request.service_id} {'deregistered' if removed else 'not found'}"
        }
    
    async def DiscoverServices(self, request, context):
        """Discover available service instances"""
        instances = []
        
        for key, service in self.service_registry.items():
            if service["service_name"] != request.service_name:
                continue
            
            # Filter by tags if specified
            if request.tags:
                if not all(tag in service["tags"] for tag in request.tags):
                    continue
            
            # Filter by health if requested
            health = self.health_status.get(key, {})
            if request.healthy_only and not health.get("healthy", False):
                continue
            
            instances.append({
                "service_id": service["service_id"],
                "address": service["address"],
                "port": service["port"],
                "metadata": service["metadata"],
                "health": health,
                "weight": service.get("weight", 100),
                "version": service.get("version", "1.0.0")
            })
        
        # Get or create load balancer config
        config = self.load_balancer_configs.get(request.service_name, {
            "algorithm": 0,  # ROUND_ROBIN
            "sticky_sessions": False,
            "session_timeout": {"seconds": 300}
        })
        
        return {
            "instances": instances,
            "config": config
        }
    
    async def GetServiceHealth(self, request, context):
        """Get health status of all instances of a service"""
        health_map = {}
        total_instances = 0
        healthy_instances = 0
        
        for key, service in self.service_registry.items():
            if service["service_name"] == request.service_name:
                health = self.health_status.get(key, {})
                health_map[service["service_id"]] = health
                total_instances += 1
                if health.get("healthy", False):
                    healthy_instances += 1
        
        health_percentage = (healthy_instances / total_instances * 100) if total_instances > 0 else 0
        
        return {
            "instances": health_map,
            "overall_health_percentage": health_percentage
        }
    
    async def check_service_health(self, service_key: str):
        """Background task to check service health"""
        if service_key not in self.service_registry:
            return
        
        service = self.service_registry[service_key]
        
        try:
            # Try to connect to service
            channel = grpc.aio.insecure_channel(f"{service['address']}:{service['port']}")
            stub = grpc.health.v1.health_pb2_grpc.HealthStub(channel)
            
            request = grpc.health.v1.health_pb2.HealthCheckRequest(service="")
            response = await stub.Check(request, timeout=5)
            
            # Update health status
            if response.status == grpc.health.v1.health_pb2.HealthCheckResponse.SERVING:
                self.health_status[service_key] = {
                    "healthy": True,
                    "last_check": time.time(),
                    "consecutive_failures": 0
                }
            else:
                self._mark_unhealthy(service_key)
            
            await channel.close()
            
        except Exception as e:
            self.logger.warning(f"Health check failed for {service_key}: {e}")
            self._mark_unhealthy(service_key)
    
    def _mark_unhealthy(self, service_key: str):
        """Mark service as unhealthy"""
        if service_key in self.health_status:
            self.health_status[service_key]["healthy"] = False
            self.health_status[service_key]["consecutive_failures"] += 1
            self.health_status[service_key]["last_check"] = time.time()


class GrpcServer:
    """Main gRPC server with all services"""
    
    def __init__(self, port: int = 50051, use_tls: bool = True):
        self.port = port
        self.use_tls = use_tls
        self.server = None
        self.logger = logging.getLogger(__name__)
        
        # Service instances
        self.service_servicer = ServiceServicer()
        self.health_servicer = HealthServicer()
        self.lb_servicer = LoadBalancerServicer()
        
    async def start(self):
        """Start the gRPC server"""
        self.server = aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),
                ('grpc.keepalive_time_ms', 10000),
                ('grpc.keepalive_timeout_ms', 5000),
                ('grpc.keepalive_permit_without_calls', True),
                ('grpc.http2.max_pings_without_data', 0),
            ]
        )
        
        # Add services
        # In real implementation, these would use generated pb2_grpc modules
        # service_pb2_grpc.add_MeshServiceServicer_to_server(self.service_servicer, self.server)
        # health_pb2_grpc.add_HealthServicer_to_server(self.health_servicer, self.server)
        # service_pb2_grpc.add_LoadBalancerServicer_to_server(self.lb_servicer, self.server)
        
        # Configure TLS if enabled
        if self.use_tls:
            server_credentials = self._load_credentials()
            self.server.add_secure_port(f"[::]:{self.port}", server_credentials)
            self.logger.info(f"Starting secure gRPC server on port {self.port}")
        else:
            self.server.add_insecure_port(f"[::]:{self.port}")
            self.logger.info(f"Starting insecure gRPC server on port {self.port}")
        
        await self.server.start()
        
        # Start background tasks
        asyncio.create_task(self._health_check_loop())
        
        self.logger.info(f"gRPC server started successfully")
    
    async def stop(self):
        """Stop the gRPC server"""
        if self.server:
            await self.server.stop(grace_period=10)
            self.logger.info("gRPC server stopped")
    
    async def wait_for_termination(self):
        """Wait for server termination"""
        if self.server:
            await self.server.wait_for_termination()
    
    def _load_credentials(self):
        """Load TLS credentials for mTLS"""
        cert_dir = os.getenv("CERT_DIR", "certs")
        
        # Read certificates
        with open(f"{cert_dir}/server.crt", "rb") as f:
            server_cert = f.read()
        with open(f"{cert_dir}/server.key", "rb") as f:
            server_key = f.read()
        with open(f"{cert_dir}/ca.crt", "rb") as f:
            ca_cert = f.read()
        
        # Create server credentials
        server_credentials = grpc.ssl_server_credentials(
            [(server_key, server_cert)],
            root_certificates=ca_cert,
            require_client_auth=True  # Enable mTLS
        )
        
        return server_credentials
    
    async def _health_check_loop(self):
        """Background loop for health checking registered services"""
        while True:
            try:
                # Check health of all registered services
                for service_key in list(self.lb_servicer.service_registry.keys()):
                    await self.lb_servicer.check_service_health(service_key)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)


async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    port = int(os.getenv("GRPC_PORT", "50051"))
    use_tls = os.getenv("USE_TLS", "true").lower() == "true"
    
    server = GrpcServer(port=port, use_tls=use_tls)
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())