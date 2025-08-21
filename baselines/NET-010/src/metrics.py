"""Prometheus metrics for proxy monitoring"""
from aiohttp import web
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST
)

# Request metrics
request_counter = Counter(
    'proxy_requests_total',
    'Total number of proxy requests',
    ['method', 'status', 'backend']
)

request_duration = Histogram(
    'proxy_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'backend'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Backend metrics
backend_request_counter = Counter(
    'backend_requests_total',
    'Total requests to backend',
    ['backend', 'method']
)

backend_health_gauge = Gauge(
    'backend_health',
    'Backend health status (1=healthy, 0=unhealthy)',
    ['backend']
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['backend']
)

circuit_breaker_failures = Counter(
    'circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['backend']
)

# Rate limiting metrics
rate_limit_rejected = Counter(
    'rate_limit_rejected_total',
    'Total requests rejected by rate limiter',
    ['reason']
)

# Connection pool metrics
connection_pool_size = Gauge(
    'connection_pool_size',
    'Current connection pool size'
)

connection_pool_in_use = Gauge(
    'connection_pool_in_use',
    'Connections currently in use'
)


def setup_metrics(app: web.Application):
    """Setup metrics collection"""
    # Initialize gauges
    connection_pool_size.set(0)
    connection_pool_in_use.set(0)


async def metrics_handler(request: web.Request) -> web.Response:
    """Prometheus metrics endpoint handler"""
    metrics = generate_latest()
    return web.Response(
        body=metrics,
        content_type=CONTENT_TYPE_LATEST
    )