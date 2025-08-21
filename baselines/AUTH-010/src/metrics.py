"""Prometheus metrics for monitoring"""
from prometheus_client import Counter, Histogram, Gauge

# Request counters
auth_requests_total = Counter(
    'oauth_auth_requests_total',
    'Total number of authorization requests'
)

token_requests_total = Counter(
    'oauth_token_requests_total',
    'Total number of token requests',
    ['grant_type']
)

token_validations_total = Counter(
    'oauth_token_validations_total',
    'Total number of token validations'
)

introspection_requests_total = Counter(
    'oauth_introspection_requests_total',
    'Total number of introspection requests'
)

# Error counters
auth_errors_total = Counter(
    'oauth_auth_errors_total',
    'Total number of authorization errors',
    ['error_type']
)

token_errors_total = Counter(
    'oauth_token_errors_total',
    'Total number of token errors',
    ['error_type']
)

# Latency histograms
auth_latency_histogram = Histogram(
    'oauth_auth_latency_seconds',
    'Authorization request latency'
)

token_latency_histogram = Histogram(
    'oauth_token_latency_seconds',
    'Token request latency'
)

validation_latency_histogram = Histogram(
    'oauth_validation_latency_seconds',
    'Token validation latency'
)

# Gauges
active_sessions_gauge = Gauge(
    'oauth_active_sessions',
    'Number of active sessions'
)

active_tokens_gauge = Gauge(
    'oauth_active_tokens',
    'Number of active tokens',
    ['token_type']
)