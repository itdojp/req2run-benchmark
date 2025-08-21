# NET-010: Reverse Proxy with Timeout, Retry, and Circuit Breaker - Baseline Implementation

## Overview

This baseline implementation provides a production-grade reverse proxy with resilience patterns including circuit breakers, exponential backoff retry, rate limiting, and health checks. It maintains SLO even when backend services are unstable or experiencing failures.

## Features Implemented

### Core Features (MUST)
- ✅ HTTP/HTTPS request forwarding to backend services
- ✅ Configurable timeouts for backend requests
- ✅ Exponential backoff retry logic
- ✅ Circuit breaker pattern implementation
- ✅ Health checks for backend services
- ✅ Rate limiting per client
- ✅ Preserve original client headers (X-Forwarded-*)
- ✅ Maintain SLO with unstable backends

### Additional Features (SHOULD)
- ✅ WebSocket connection support
- ✅ Request/response caching (configurable)

## Architecture

```
┌─────────────────────────────────────────────┐
│              Client Requests                │
└──────────────────┬──────────────────────────┘
                   │
           ┌───────▼────────┐
           │  Rate Limiter  │
           └───────┬────────┘
                   │
        ┌──────────▼──────────┐
        │   Reverse Proxy     │
        │  - Load Balancing   │
        │  - Retry Logic      │
        └──────────┬──────────┘
                   │
         ┌─────────▼─────────┐
         │  Circuit Breaker  │
         └─────────┬─────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼───┐    ┌────▼────┐    ┌────▼───┐
│Backend│    │Backend 2│    │Backend 3│
└───────┘    └─────────┘    └─────────┘
```

## Resilience Patterns

### Circuit Breaker
- **Closed State**: Normal operation, requests forwarded
- **Open State**: Backend failing, requests rejected immediately
- **Half-Open State**: Testing recovery with limited requests
- **Thresholds**: Configurable failure/success counts
- **Timeout**: Automatic transition to half-open after timeout

### Retry Logic
- **Exponential Backoff**: Delays increase exponentially
- **Max Attempts**: Configurable retry limit
- **Jitter**: Randomization to prevent thundering herd
- **Retry Conditions**: Only on retryable errors (network, timeout)

### Rate Limiting
- **Token Bucket**: Smooth rate limiting with burst capacity
- **Sliding Window**: Alternative algorithm for strict limits
- **Per-Client**: Individual client rate limits
- **Global**: Overall proxy rate limit

### Health Checks
- **Periodic Checks**: Regular backend health verification
- **Failure Threshold**: Mark unhealthy after N failures
- **Recovery Detection**: Automatic re-enable when healthy

## Load Balancing Algorithms

1. **Round Robin**: Equal distribution in order
2. **Random**: Random backend selection
3. **Weighted**: Distribution based on backend weights
4. **Least Connections**: Route to least busy backend

## API Endpoints

### Proxy Endpoints
- `*` - All requests proxied to backends

### Management Endpoints
- `GET /health` - Proxy health status
- `GET /metrics` - Prometheus metrics
- `GET /backends/health` - Backend health status

## Performance Characteristics

- **P95 Latency**: < 50ms overhead
- **P99 Latency**: < 200ms overhead
- **Throughput**: 10,000+ RPS
- **Connection Pool**: 1000 connections
- **CPU Usage**: < 2 cores at peak

## Configuration

### Backend Configuration
```yaml
backends:
  - id: backend1
    url: http://localhost:8001
    weight: 1
    health_check_enabled: true
```

### Circuit Breaker Settings
```yaml
circuit_breaker:
  failure_threshold: 5
  success_threshold: 2
  timeout: 30
```

### Rate Limiting
```yaml
rate_limit:
  requests_per_second: 100
  burst: 200
  per_client:
    requests_per_second: 10
```

## Running the Proxy

### Docker
```bash
docker build -t net-010-proxy .
docker run -p 8080:8080 net-010-proxy
```

### Local Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run proxy
python -m src.main --config config/proxy.yaml
```

## Testing

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Performance Tests
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8080
```

### Chaos Tests
```bash
# Simulate backend failures
pytest tests/chaos/ -v
```

## Monitoring

### Prometheus Metrics
- `proxy_requests_total` - Total requests by status
- `proxy_request_duration_seconds` - Request latency
- `backend_health` - Backend health status
- `circuit_breaker_state` - Circuit breaker states
- `rate_limit_rejected_total` - Rate limited requests

### Health Check Response
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "backends": {
    "healthy": 2,
    "total": 3
  },
  "features": {
    "circuit_breaker": true,
    "rate_limiting": true,
    "health_checks": true
  }
}
```

## Handling Failures

### Backend Failure Scenarios
1. **Connection Timeout**: Retry with exponential backoff
2. **5xx Errors**: Circuit breaker opens after threshold
3. **Network Errors**: Automatic retry with different backend
4. **All Backends Down**: Return 503 Service Unavailable

### Recovery Mechanisms
1. **Automatic Health Checks**: Detect backend recovery
2. **Circuit Breaker Reset**: Gradual traffic restoration
3. **Connection Pool Recovery**: Automatic reconnection
4. **Rate Limit Reset**: Sliding window cleanup

## Security Considerations

1. **Header Filtering**: Remove sensitive headers
2. **Request Size Limits**: Prevent DoS attacks
3. **Rate Limiting**: Protect against abuse
4. **TLS Support**: Encrypted backend connections
5. **Access Logging**: Audit trail for requests

## Production Deployment

### Recommendations
1. Deploy multiple proxy instances for HA
2. Use external load balancer for proxy instances
3. Configure appropriate timeouts for your backends
4. Monitor circuit breaker states
5. Set rate limits based on capacity planning
6. Enable access logging for debugging

### Scaling
- Horizontal: Add more proxy instances
- Vertical: Increase connection pool and resources
- Backend: Add more backend servers

## License

MIT