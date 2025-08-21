# WEB-012: Rate Limiting and Retry Design with Idempotency Keys

## Overview

Production-grade payment processing API implementing comprehensive rate limiting, retry mechanisms, and idempotency key handling. This system ensures reliable payment processing with protection against duplicate charges, rate limit abuse, and concurrent request conflicts.

## Key Features

### Rate Limiting
- **Multiple Strategies**: Sliding window and token bucket algorithms
- **Distributed Rate Limiting**: Redis-backed with Lua scripts for atomicity
- **Flexible Scopes**: Global, per-user, per-IP, per-endpoint limits
- **Burst Handling**: Token bucket algorithm for handling burst traffic
- **Real-time Headers**: X-RateLimit-* headers on all responses

### Idempotency Support
- **Duplicate Prevention**: Prevents duplicate payment processing
- **Request Validation**: Ensures identical requests with same idempotency key
- **Concurrent Handling**: Distributed locking for concurrent requests
- **Response Caching**: Returns cached responses for replayed requests
- **TTL Management**: Automatic cleanup of expired keys

### Retry Mechanisms
- **Client Configuration**: Recommended retry strategies with exponential backoff
- **Jitter Support**: Prevents thundering herd problem
- **Smart Headers**: Retry-After headers for rate-limited requests
- **Circuit Breaking**: Automatic failure detection and recovery

### Audit & Monitoring
- **Comprehensive Logging**: Structured logging with contextual information
- **Audit Trail**: Complete audit log of all payment attempts
- **Metrics Export**: Prometheus metrics for monitoring
- **Health Checks**: Liveness and readiness endpoints

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  Rate       │────▶│  Idempotency│
│             │     │  Limiter    │     │  Manager    │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Redis    │     │  PostgreSQL │
                    │   (Cache)   │     │  (Database) │
                    └─────────────┘     └─────────────┘
```

## API Endpoints

### Payment Processing
- `POST /api/v1/payments` - Process payment with idempotency key
- `GET /api/v1/payments/{transaction_id}` - Get payment status

### Configuration & Monitoring
- `GET /api/v1/retry-config` - Get recommended retry configuration
- `GET /api/v1/rate-limits` - Get current rate limit status
- `GET /api/v1/audit-logs` - Get audit logs for user
- `GET /health` - Health check endpoint

### Testing
- `POST /api/v1/simulate-concurrent` - Test concurrent request handling

## Quick Start

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f app
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/payments
export REDIS_URL=redis://localhost:6379
export API_KEY=your-secret-key
```

3. **Run application:**
```bash
cd src
python main.py
```

## Usage Examples

### Process Payment with Idempotency

```bash
# Generate unique idempotency key
IDEMPOTENCY_KEY=$(uuidgen)

# Process payment
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d '{
    "amount": 99.99,
    "currency": "USD",
    "description": "Premium subscription",
    "payment_method": "credit_card",
    "metadata": {
      "customer_id": "cust_123",
      "order_id": "ord_456"
    }
  }'
```

### Retry Same Request (Idempotent)

```bash
# Retry with same idempotency key - returns cached response
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d '{
    "amount": 99.99,
    "currency": "USD",
    "description": "Premium subscription",
    "payment_method": "credit_card"
  }'
```

### Check Rate Limits

```bash
curl -X GET http://localhost:8000/api/v1/rate-limits \
  -H "Authorization: Bearer test-api-key"
```

### Get Retry Configuration

```bash
curl -X GET http://localhost:8000/api/v1/retry-config
```

### Test Concurrent Requests

```bash
# Simulate 10 concurrent requests with same idempotency key
curl -X POST http://localhost:8000/api/v1/simulate-concurrent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -H "Idempotency-Key: test-concurrent-key" \
  -d '{
    "amount": 50.00,
    "currency": "USD",
    "payment_method": "credit_card"
  }' \
  --data-urlencode "concurrent_count=10"
```

## Rate Limiting Rules

Default rate limits (configurable):

| Scope | Limit | Window | Algorithm |
|-------|-------|--------|-----------|
| Global | 1000 req | 60s | Sliding Window |
| Per User | 100 req | 60s | Sliding Window |
| Payment Endpoint | 10 req | 60s | Sliding Window |
| Burst | 20 req/s | 1s | Token Bucket (50 burst) |

## Idempotency Key Requirements

- **Format**: 16-255 characters, alphanumeric + hyphens/underscores
- **TTL**: 24 hours by default
- **Scope**: Per-user (different users can use same key)
- **Validation**: Request body must match for same key

## Client Best Practices

### Retry Strategy

```python
import time
import random
import httpx

def retry_with_backoff(func, max_retries=3):
    """Exponential backoff with jitter"""
    for attempt in range(max_retries):
        try:
            return func()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limited - use Retry-After header
                retry_after = int(e.response.headers.get('Retry-After', 1))
                time.sleep(retry_after)
            elif e.response.status_code >= 500:
                # Server error - exponential backoff
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(min(delay, 30))
            else:
                raise
    raise Exception("Max retries exceeded")
```

### Idempotency Key Generation

```python
import uuid
import hashlib

def generate_idempotency_key(user_id, operation, params):
    """Generate deterministic idempotency key"""
    data = f"{user_id}:{operation}:{sorted(params.items())}"
    return hashlib.sha256(data.encode()).hexdigest()

# Or use random UUID
idempotency_key = str(uuid.uuid4())
```

## Monitoring

### Prometheus Metrics

Available at `http://localhost:8000/metrics`:

- `payment_requests_total` - Total payment requests
- `payment_success_rate` - Success rate percentage
- `rate_limit_exceeded_total` - Rate limit violations
- `idempotent_replays_total` - Cached response replays
- `concurrent_conflicts_total` - Concurrent request conflicts

### Health Checks

```bash
# Liveness probe
curl http://localhost:8000/health

# Check specific service
curl http://localhost:8000/health | jq '.services'
```

## Testing

### Unit Tests

```bash
pytest tests/ -v --cov=src
```

### Load Testing

```bash
# Using locust
locust -f tests/load_test.py --host=http://localhost:8000
```

### Concurrent Testing

```bash
# Test idempotency with parallel requests
python tests/test_concurrent.py
```

## Security Considerations

1. **API Keys**: Always use secure, rotated API keys
2. **HTTPS**: Deploy with TLS termination in production
3. **Database**: Use encrypted connections and strong passwords
4. **Redis**: Configure with authentication in production
5. **Secrets**: Use environment variables or secret management systems

## Performance Tuning

### Database Optimization
- Indexed columns: user_id, idempotency_key, created_at
- Connection pooling: 20 connections default
- Async operations for non-blocking I/O

### Redis Optimization
- Lua scripts for atomic operations
- Pipeline operations for batch processing
- Appropriate TTLs to prevent memory bloat

### Application Optimization
- Async/await throughout for concurrency
- Background task for cleanup operations
- Efficient request hashing and caching

## Troubleshooting

### Common Issues

1. **"Idempotency key already in use"**
   - Different request body with same key
   - Solution: Use new key or ensure identical request

2. **"Rate limit exceeded"**
   - Too many requests in time window
   - Solution: Implement retry with backoff

3. **"Lock acquisition timeout"**
   - Concurrent requests taking too long
   - Solution: Increase timeout or retry later

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python src/main.py
```

## License

MIT