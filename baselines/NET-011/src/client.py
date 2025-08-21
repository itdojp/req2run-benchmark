"""
gRPC Client with Load Balancing and Retry Policies

Implements client-side load balancing, retries, and distributed tracing.
"""

import asyncio
import grpc
from grpc import aio
import logging
import time
import random
import uuid
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from collections import defaultdict
import os

# Retry and load balancing utilities
class LoadBalanceAlgorithm(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    CONSISTENT_HASH = "consistent_hash"


@dataclass
class ServiceEndpoint:
    """Represents a service endpoint"""
    service_id: str
    address: str
    port: int
    weight: int = 100
    healthy: bool = True
    active_connections: int = 0
    last_used: float = 0
    consecutive_failures: int = 0


@dataclass
class RetryPolicy:
    """Retry policy configuration"""
    max_attempts: int = 3
    initial_backoff: float = 1.0
    max_backoff: float = 60.0
    backoff_multiplier: float = 2.0
    retryable_status_codes: List[int] = None
    timeout: float = 30.0
    
    def __post_init__(self):
        if self.retryable_status_codes is None:
            self.retryable_status_codes = [
                grpc.StatusCode.UNAVAILABLE.value[0],
                grpc.StatusCode.DEADLINE_EXCEEDED.value[0],
                grpc.StatusCode.RESOURCE_EXHAUSTED.value[0],
            ]


class LoadBalancer:
    """Client-side load balancer"""
    
    def __init__(self, algorithm: LoadBalanceAlgorithm = LoadBalanceAlgorithm.ROUND_ROBIN):
        self.algorithm = algorithm
        self.endpoints: List[ServiceEndpoint] = []
        self.current_index = 0
        self.logger = logging.getLogger(__name__)
        self.consistent_hash_ring = {}
        
    def add_endpoint(self, endpoint: ServiceEndpoint):
        """Add service endpoint"""
        self.endpoints.append(endpoint)
        if self.algorithm == LoadBalanceAlgorithm.CONSISTENT_HASH:
            self._update_hash_ring()
    
    def remove_endpoint(self, service_id: str):
        """Remove service endpoint"""
        self.endpoints = [e for e in self.endpoints if e.service_id != service_id]
        if self.algorithm == LoadBalanceAlgorithm.CONSISTENT_HASH:
            self._update_hash_ring()
    
    def get_endpoint(self, request_key: str = None) -> Optional[ServiceEndpoint]:
        """Get next endpoint based on algorithm"""
        healthy_endpoints = [e for e in self.endpoints if e.healthy]
        
        if not healthy_endpoints:
            self.logger.warning("No healthy endpoints available")
            return None
        
        if self.algorithm == LoadBalanceAlgorithm.ROUND_ROBIN:
            endpoint = healthy_endpoints[self.current_index % len(healthy_endpoints)]
            self.current_index += 1
            return endpoint
            
        elif self.algorithm == LoadBalanceAlgorithm.LEAST_CONNECTIONS:
            return min(healthy_endpoints, key=lambda e: e.active_connections)
            
        elif self.algorithm == LoadBalanceAlgorithm.WEIGHTED_ROUND_ROBIN:
            weighted_list = []
            for endpoint in healthy_endpoints:
                weighted_list.extend([endpoint] * (endpoint.weight // 10))
            if weighted_list:
                return random.choice(weighted_list)
            return healthy_endpoints[0]
            
        elif self.algorithm == LoadBalanceAlgorithm.RANDOM:
            return random.choice(healthy_endpoints)
            
        elif self.algorithm == LoadBalanceAlgorithm.CONSISTENT_HASH:
            if request_key:
                return self._get_from_hash_ring(request_key)
            return random.choice(healthy_endpoints)
        
        return healthy_endpoints[0]
    
    def _update_hash_ring(self):
        """Update consistent hash ring"""
        self.consistent_hash_ring = {}
        for endpoint in self.endpoints:
            for i in range(100):  # Virtual nodes
                hash_key = hashlib.md5(f"{endpoint.service_id}:{i}".encode()).hexdigest()
                self.consistent_hash_ring[hash_key] = endpoint
    
    def _get_from_hash_ring(self, request_key: str) -> Optional[ServiceEndpoint]:
        """Get endpoint from consistent hash ring"""
        if not self.consistent_hash_ring:
            return None
        
        request_hash = hashlib.md5(request_key.encode()).hexdigest()
        sorted_keys = sorted(self.consistent_hash_ring.keys())
        
        for key in sorted_keys:
            if key >= request_hash:
                endpoint = self.consistent_hash_ring[key]
                if endpoint.healthy:
                    return endpoint
        
        # Wrap around to first endpoint
        for key in sorted_keys:
            endpoint = self.consistent_hash_ring[key]
            if endpoint.healthy:
                return endpoint
        
        return None
    
    def mark_unhealthy(self, service_id: str):
        """Mark endpoint as unhealthy"""
        for endpoint in self.endpoints:
            if endpoint.service_id == service_id:
                endpoint.healthy = False
                endpoint.consecutive_failures += 1
                self.logger.warning(f"Marked {service_id} as unhealthy")
                break
    
    def mark_healthy(self, service_id: str):
        """Mark endpoint as healthy"""
        for endpoint in self.endpoints:
            if endpoint.service_id == service_id:
                endpoint.healthy = True
                endpoint.consecutive_failures = 0
                self.logger.info(f"Marked {service_id} as healthy")
                break


class DistributedTracing:
    """Distributed tracing context"""
    
    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.span_id = str(uuid.uuid4())
        self.parent_span_id = None
        self.baggage = {}
        self.start_time = time.time()
        
    def create_child_span(self) -> 'DistributedTracing':
        """Create child span"""
        child = DistributedTracing()
        child.trace_id = self.trace_id
        child.parent_span_id = self.span_id
        child.baggage = self.baggage.copy()
        return child
    
    def to_metadata(self) -> List[tuple]:
        """Convert to gRPC metadata"""
        metadata = [
            ("trace-id", self.trace_id),
            ("span-id", self.span_id),
        ]
        if self.parent_span_id:
            metadata.append(("parent-span-id", self.parent_span_id))
        
        for key, value in self.baggage.items():
            metadata.append((f"baggage-{key}", str(value)))
        
        return metadata
    
    def record_duration(self) -> float:
        """Record span duration"""
        return time.time() - self.start_time


class GrpcClient:
    """gRPC client with advanced features"""
    
    def __init__(
        self,
        service_name: str,
        load_balancer: LoadBalancer = None,
        retry_policy: RetryPolicy = None,
        use_tls: bool = True
    ):
        self.service_name = service_name
        self.load_balancer = load_balancer or LoadBalancer()
        self.retry_policy = retry_policy or RetryPolicy()
        self.use_tls = use_tls
        self.logger = logging.getLogger(__name__)
        self.channels: Dict[str, aio.Channel] = {}
        self.stubs: Dict[str, Any] = {}
        
    async def discover_services(self, discovery_endpoint: str):
        """Discover available service instances"""
        try:
            channel = await self._create_channel(discovery_endpoint)
            # In real implementation, use generated stub
            # stub = service_pb2_grpc.LoadBalancerStub(channel)
            
            # Mock discovery
            instances = [
                ServiceEndpoint("server-1", "localhost", 50051),
                ServiceEndpoint("server-2", "localhost", 50052),
                ServiceEndpoint("server-3", "localhost", 50053),
            ]
            
            for instance in instances:
                self.load_balancer.add_endpoint(instance)
            
            self.logger.info(f"Discovered {len(instances)} service instances")
            
        except Exception as e:
            self.logger.error(f"Service discovery failed: {e}")
    
    async def call_with_retry(
        self,
        method_name: str,
        request: Any,
        trace_context: DistributedTracing = None
    ) -> Any:
        """Call RPC with retry logic"""
        if not trace_context:
            trace_context = DistributedTracing()
        
        last_error = None
        backoff = self.retry_policy.initial_backoff
        
        for attempt in range(self.retry_policy.max_attempts):
            try:
                # Get endpoint
                endpoint = self.load_balancer.get_endpoint(str(request))
                if not endpoint:
                    raise grpc.RpcError("No available endpoints")
                
                # Get or create channel
                channel = await self._get_or_create_channel(endpoint)
                
                # Create metadata with tracing
                metadata = trace_context.to_metadata()
                
                # Call RPC
                self.logger.info(f"Attempt {attempt + 1}: Calling {method_name} on {endpoint.service_id}")
                
                endpoint.active_connections += 1
                try:
                    # In real implementation, use actual stub method
                    response = await self._mock_rpc_call(method_name, request, metadata)
                    
                    # Mark endpoint as healthy on success
                    self.load_balancer.mark_healthy(endpoint.service_id)
                    
                    return response
                    
                finally:
                    endpoint.active_connections -= 1
                    endpoint.last_used = time.time()
                
            except grpc.RpcError as e:
                last_error = e
                
                # Check if retryable
                if e.code() not in self.retry_policy.retryable_status_codes:
                    raise
                
                # Mark endpoint as unhealthy
                if endpoint:
                    self.load_balancer.mark_unhealthy(endpoint.service_id)
                
                # Wait with exponential backoff
                if attempt < self.retry_policy.max_attempts - 1:
                    wait_time = min(backoff, self.retry_policy.max_backoff)
                    self.logger.warning(f"RPC failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    backoff *= self.retry_policy.backoff_multiplier
        
        # All retries exhausted
        raise last_error or grpc.RpcError("All retry attempts failed")
    
    async def call_with_hedging(
        self,
        method_name: str,
        request: Any,
        hedge_delay: float = 0.1,
        max_hedges: int = 2
    ) -> Any:
        """Call RPC with request hedging for lower latency"""
        tasks = []
        
        async def hedged_call(endpoint: ServiceEndpoint, delay: float = 0):
            if delay > 0:
                await asyncio.sleep(delay)
            
            channel = await self._get_or_create_channel(endpoint)
            # In real implementation, use actual stub
            return await self._mock_rpc_call(method_name, request, [])
        
        # Start first request
        endpoint1 = self.load_balancer.get_endpoint()
        if endpoint1:
            tasks.append(asyncio.create_task(hedged_call(endpoint1)))
        
        # Start hedged requests
        for i in range(min(max_hedges, len(self.load_balancer.endpoints) - 1)):
            endpoint = self.load_balancer.get_endpoint()
            if endpoint and endpoint != endpoint1:
                tasks.append(asyncio.create_task(
                    hedged_call(endpoint, hedge_delay * (i + 1))
                ))
        
        # Return first successful response
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
        
        # Return first result
        for task in done:
            try:
                return task.result()
            except Exception as e:
                self.logger.warning(f"Hedged request failed: {e}")
        
        raise grpc.RpcError("All hedged requests failed")
    
    async def stream_with_retry(
        self,
        method_name: str,
        request: Any,
        trace_context: DistributedTracing = None
    ) -> AsyncIterator[Any]:
        """Stream RPC with retry logic"""
        if not trace_context:
            trace_context = DistributedTracing()
        
        last_error = None
        
        for attempt in range(self.retry_policy.max_attempts):
            try:
                endpoint = self.load_balancer.get_endpoint()
                if not endpoint:
                    raise grpc.RpcError("No available endpoints")
                
                channel = await self._get_or_create_channel(endpoint)
                metadata = trace_context.to_metadata()
                
                # Stream responses
                async for response in self._mock_stream_call(method_name, request, metadata):
                    yield response
                
                return  # Stream completed successfully
                
            except grpc.RpcError as e:
                last_error = e
                
                if e.code() not in self.retry_policy.retryable_status_codes:
                    raise
                
                if endpoint:
                    self.load_balancer.mark_unhealthy(endpoint.service_id)
                
                if attempt < self.retry_policy.max_attempts - 1:
                    await asyncio.sleep(self.retry_policy.initial_backoff * (2 ** attempt))
        
        raise last_error or grpc.RpcError("Stream retry failed")
    
    async def _get_or_create_channel(self, endpoint: ServiceEndpoint) -> aio.Channel:
        """Get or create gRPC channel"""
        channel_key = f"{endpoint.address}:{endpoint.port}"
        
        if channel_key not in self.channels:
            self.channels[channel_key] = await self._create_channel(channel_key)
        
        return self.channels[channel_key]
    
    async def _create_channel(self, target: str) -> aio.Channel:
        """Create gRPC channel"""
        options = [
            ('grpc.max_send_message_length', 100 * 1024 * 1024),
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', True),
        ]
        
        if self.use_tls:
            credentials = self._load_credentials()
            return aio.secure_channel(target, credentials, options=options)
        else:
            return aio.insecure_channel(target, options=options)
    
    def _load_credentials(self):
        """Load TLS credentials for mTLS"""
        cert_dir = os.getenv("CERT_DIR", "certs")
        
        with open(f"{cert_dir}/client.crt", "rb") as f:
            client_cert = f.read()
        with open(f"{cert_dir}/client.key", "rb") as f:
            client_key = f.read()
        with open(f"{cert_dir}/ca.crt", "rb") as f:
            ca_cert = f.read()
        
        return grpc.ssl_channel_credentials(
            root_certificates=ca_cert,
            private_key=client_key,
            certificate_chain=client_cert
        )
    
    async def _mock_rpc_call(self, method_name: str, request: Any, metadata: List[tuple]) -> Any:
        """Mock RPC call for testing"""
        await asyncio.sleep(0.01)  # Simulate network latency
        
        # Simulate occasional failures
        if random.random() < 0.1:
            raise grpc.RpcError("Simulated failure")
        
        return {
            "request_id": str(uuid.uuid4()),
            "result": f"Mock response for {method_name}",
            "status": {"code": 0, "message": "Success"},
            "server_id": "mock-server"
        }
    
    async def _mock_stream_call(
        self,
        method_name: str,
        request: Any,
        metadata: List[tuple]
    ) -> AsyncIterator[Any]:
        """Mock streaming RPC call"""
        for i in range(5):
            await asyncio.sleep(0.1)
            yield {
                "event_id": str(uuid.uuid4()),
                "event_type": "test",
                "payload": {"index": i},
                "timestamp": {"seconds": int(time.time())}
            }
    
    async def close(self):
        """Close all channels"""
        for channel in self.channels.values():
            await channel.close()
        self.channels.clear()


async def main():
    """Main client example"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create client with load balancing
    load_balancer = LoadBalancer(LoadBalanceAlgorithm.ROUND_ROBIN)
    client = GrpcClient(
        service_name="mesh.v1.MeshService",
        load_balancer=load_balancer,
        retry_policy=RetryPolicy(max_attempts=3),
        use_tls=False  # For testing
    )
    
    # Discover services
    await client.discover_services("localhost:50000")
    
    # Create tracing context
    trace = DistributedTracing()
    
    # Make RPC call with retry
    try:
        request = {"request_id": str(uuid.uuid4()), "data": "test"}
        response = await client.call_with_retry("Process", request, trace)
        logging.info(f"Response: {response}")
    except Exception as e:
        logging.error(f"RPC failed: {e}")
    
    # Stream with retry
    try:
        stream_request = {"stream_id": str(uuid.uuid4()), "event_types": ["test"]}
        async for event in client.stream_with_retry("StreamEvents", stream_request, trace):
            logging.info(f"Received event: {event}")
    except Exception as e:
        logging.error(f"Stream failed: {e}")
    
    # Cleanup
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())