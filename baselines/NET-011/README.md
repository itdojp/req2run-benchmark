# NET-011: gRPC Service Mesh with Load Balancing and Health Checks

## Overview

A production-grade gRPC service mesh implementation featuring client-side load balancing, health checking with grpc.health.v1, mTLS authentication, distributed tracing, and advanced retry policies. The system supports all gRPC communication patterns (unary, server streaming, client streaming, and bidirectional streaming).

## Key Features

### Service Discovery & Load Balancing
- **Dynamic Service Discovery**: Automatic endpoint discovery and registration
- **Client-Side Load Balancing**: Multiple algorithms (Round Robin, Least Connections, Weighted, Random, Consistent Hash)
- **Health Checking**: Standard grpc.health.v1 implementation
- **Outlier Detection**: Automatic unhealthy instance removal

### Communication Patterns
- **Unary RPC**: Request-response pattern
- **Server Streaming**: Server sends multiple responses
- **Client Streaming**: Client sends multiple requests
- **Bidirectional Streaming**: Full-duplex communication

### Resilience Features
- **Retry Policies**: Configurable retry with exponential backoff
- **Request Hedging**: Parallel requests for lower latency
- **Circuit Breaker**: Prevents cascading failures
- **Deadlines & Timeouts**: Request deadline propagation

### Security
- **mTLS**: Mutual TLS authentication between services
- **Certificate Management**: Automatic cert rotation support
- **Secure Channels**: Encrypted communication

### Observability
- **Distributed Tracing**: OpenTelemetry integration
- **Metrics Collection**: Prometheus-compatible metrics
- **Health Dashboard**: Real-time service health monitoring
- **Request Logging**: Structured logging with trace context

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Service Mesh                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐     Load Balancer      ┌──────────┐      │
│  │          │  ◄─────────────────────►│          │      │
│  │ Client 1 │                         │ Server 1 │      │
│  │          │  ┌─────────────────┐   │          │      │
│  └──────────┘  │                 │   └──────────┘      │
│                │   Round Robin    │                     │
│  ┌──────────┐  │  Least Conn     │   ┌──────────┐      │
│  │          │  │  Weighted RR     │   │          │      │
│  │ Client 2 │──│  Random          │───│ Server 2 │      │
│  │          │  │  Consistent Hash │   │          │      │
│  └──────────┘  └─────────────────┘   └──────────┘      │
│                                                          │
│  ┌──────────┐    Health Checks       ┌──────────┐      │
│  │          │  ◄─────────────────────►│          │      │
│  │ Client N │     grpc.health.v1     │ Server N │      │
│  │          │                         │          │      │
│  └──────────┘                         └──────────┘      │
│                                                          │
│              ▼ Tracing  ▼ Metrics  ▼ Logs               │
│         ┌────────────────────────────────┐              │
│         │   Observability Platform       │              │
│         │  (Jaeger, Prometheus, ELK)     │              │
│         └────────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t grpc-service-mesh .

# Run the service mesh
docker run -p 50051-50053:50051-50053 \
  -p 8080:8080 -p 9090:9090 \
  grpc-service-mesh

# Health check
grpc_health_probe -addr=localhost:50051
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Generate certificates for mTLS:**
```bash
# Create CA certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout certs/ca.key -out certs/ca.crt \
  -days 365 -subj "/CN=mesh-ca"

# Create server certificate
openssl req -newkey rsa:4096 -nodes \
  -keyout certs/server.key -out certs/server.csr \
  -subj "/CN=mesh-server"
openssl x509 -req -in certs/server.csr \
  -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial \
  -out certs/server.crt -days 365

# Create client certificate
openssl req -newkey rsa:4096 -nodes \
  -keyout certs/client.key -out certs/client.csr \
  -subj "/CN=mesh-client"
openssl x509 -req -in certs/client.csr \
  -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial \
  -out certs/client.crt -days 365
```

3. **Generate proto code:**
```bash
python -m grpc_tools.protoc \
  -I./proto \
  --python_out=./src \
  --grpc_python_out=./src \
  ./proto/service.proto
```

4. **Run the service mesh:**
```bash
python src/main.py
```

## Configuration

### Service Mesh Configuration (`config/mesh.yaml`)

```yaml
services:
  - name: mesh-service-1
    port: 50051
    replicas: 3
    use_tls: true

load_balancer:
  algorithm: round_robin
  health_check_interval: 30

retry_policy:
  max_attempts: 3
  initial_backoff: 1.0

mtls:
  enabled: true
  cert_dir: certs
```

### Load Balancer Algorithms

#### Round Robin
Distributes requests evenly across all healthy endpoints.

#### Least Connections
Routes to the endpoint with the fewest active connections.

#### Weighted Round Robin
Distributes requests based on endpoint weights.

#### Random
Randomly selects a healthy endpoint.

#### Consistent Hash
Routes based on request hash for session affinity.

## API Examples

### Unary RPC
```python
# Client
request = ProcessRequest(
    request_id="req-123",
    data="test data"
)
response = await client.Process(request)
```

### Server Streaming
```python
# Client
request = StreamRequest(
    stream_id="stream-123",
    event_types=["event1", "event2"]
)
async for event in client.StreamEvents(request):
    print(f"Received: {event}")
```

### Client Streaming
```python
# Client
async def generate_metrics():
    for i in range(10):
        yield Metric(
            metric_name="cpu_usage",
            value=random.random()
        )

response = await client.CollectMetrics(generate_metrics())
```

### Bidirectional Streaming
```python
# Client
async def chat_messages():
    for i in range(5):
        yield ChatMessage(
            user_id="user-123",
            message=f"Message {i}"
        )

async for response in client.Chat(chat_messages()):
    print(f"Server: {response.message}")
```

## Retry Policies

### Configuration
```yaml
retry_policy:
  max_attempts: 3
  initial_backoff: 1.0
  max_backoff: 60.0
  backoff_multiplier: 2.0
  retryable_status_codes:
    - UNAVAILABLE
    - DEADLINE_EXCEEDED
    - RESOURCE_EXHAUSTED
```

### Usage
```python
client = GrpcClient(
    service_name="mesh.v1.MeshService",
    retry_policy=RetryPolicy(max_attempts=3)
)

response = await client.call_with_retry("Process", request)
```

## Request Hedging

Reduce tail latency by sending parallel requests:

```python
# Send hedged requests with 100ms delay
response = await client.call_with_hedging(
    "Process",
    request,
    hedge_delay=0.1,
    max_hedges=2
)
```

## Health Checking

### Standard grpc.health.v1 Implementation
```python
# Health check
health_stub = Health.Stub(channel)
response = await health_stub.Check(
    HealthCheckRequest(service="mesh.v1.MeshService")
)

if response.status == HealthCheckResponse.SERVING:
    print("Service is healthy")
```

### Health Monitoring
```bash
# Using grpc_health_probe
grpc_health_probe -addr=localhost:50051 -service=mesh.v1.MeshService

# Watch health status
grpc_health_probe -addr=localhost:50051 -service=mesh.v1.MeshService -watch
```

## mTLS Configuration

### Server Configuration
```python
server_credentials = grpc.ssl_server_credentials(
    [(server_key, server_cert)],
    root_certificates=ca_cert,
    require_client_auth=True  # Enable mTLS
)
```

### Client Configuration
```python
channel_credentials = grpc.ssl_channel_credentials(
    root_certificates=ca_cert,
    private_key=client_key,
    certificate_chain=client_cert
)
```

## Distributed Tracing

### OpenTelemetry Integration
```python
from opentelemetry import trace
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient

# Instrument gRPC client
GrpcInstrumentorClient().instrument()

# Create span
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("process_request"):
    response = await client.Process(request)
```

### Trace Context Propagation
```python
trace_context = DistributedTracing()
metadata = trace_context.to_metadata()

response = await stub.Process(
    request,
    metadata=metadata
)
```

## Metrics

### Prometheus Metrics
- `grpc_requests_total`: Total number of requests
- `grpc_request_duration_seconds`: Request latency histogram
- `grpc_active_connections`: Active connection gauge
- `grpc_endpoint_health`: Endpoint health status

### Accessing Metrics
```bash
# Prometheus endpoint
curl http://localhost:9090/metrics
```

## Performance Optimization

### Connection Pooling
```yaml
connection_pool:
  max_connections: 1000
  max_connections_per_endpoint: 100
  idle_timeout: 300
```

### Keep-Alive Settings
```python
options = [
    ('grpc.keepalive_time_ms', 10000),
    ('grpc.keepalive_timeout_ms', 5000),
    ('grpc.keepalive_permit_without_calls', True),
]
```

### Message Size Limits
```python
options = [
    ('grpc.max_send_message_length', 100 * 1024 * 1024),
    ('grpc.max_receive_message_length', 100 * 1024 * 1024),
]
```

## Monitoring Dashboard

Access the monitoring dashboard at `http://localhost:8080/dashboard`

Features:
- Real-time service health
- Request metrics
- Load distribution
- Error rates
- Latency percentiles

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/performance/

# Test with grpcurl
grpcurl -plaintext localhost:50051 list
grpcurl -plaintext localhost:50051 describe mesh.v1.MeshService
```

## Production Deployment

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grpc-mesh
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: grpc-service
        image: grpc-service-mesh
        ports:
        - containerPort: 50051
          name: grpc
        - containerPort: 9090
          name: metrics
        livenessProbe:
          grpc:
            port: 50051
            service: grpc.health.v1.Health
        readinessProbe:
          grpc:
            port: 50051
            service: mesh.v1.MeshService
```

### Service Definition
```yaml
apiVersion: v1
kind: Service
metadata:
  name: grpc-mesh
spec:
  type: LoadBalancer
  ports:
  - port: 50051
    targetPort: 50051
    name: grpc
  selector:
    app: grpc-mesh
```

## Best Practices

1. **Health Checks**: Always implement grpc.health.v1 for all services
2. **Timeouts**: Set appropriate deadlines for all RPCs
3. **Retries**: Configure retry policies for transient failures
4. **Load Balancing**: Use appropriate algorithm for your use case
5. **Monitoring**: Track metrics and set up alerts
6. **Security**: Always use mTLS in production
7. **Versioning**: Support multiple protocol versions

## Troubleshooting

### Connection Issues
```bash
# Test connectivity
grpc_health_probe -addr=localhost:50051

# Check certificates
openssl s_client -connect localhost:50051 -cert client.crt -key client.key
```

### Performance Issues
```bash
# Profile with pprof
go tool pprof http://localhost:6060/debug/pprof/profile

# Check metrics
curl http://localhost:9090/metrics | grep grpc_
```

### Debugging
```bash
# Enable debug logging
export GRPC_VERBOSITY=DEBUG
export GRPC_TRACE=all

# Use grpcurl for testing
grpcurl -plaintext -d '{"request_id":"test"}' \
  localhost:50051 mesh.v1.MeshService/Process
```

## License

MIT