"""Monitoring and metrics for transaction system"""
from prometheus_client import Counter, Histogram, Gauge

# Transaction metrics
transaction_counter = Counter(
    'transactions_total',
    'Total number of transactions',
    ['status', 'type']
)

transaction_latency = Histogram(
    'transaction_duration_seconds',
    'Transaction processing duration',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

failed_transactions = Counter(
    'failed_transactions_total',
    'Total number of failed transactions',
    ['reason']
)

# Balance metrics
balance_gauge = Gauge(
    'account_balance',
    'Current account balance',
    ['account_id']
)

# Database metrics
db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

db_connection_pool_free = Gauge(
    'db_connection_pool_free',
    'Free connections in pool'
)

# Idempotency metrics
idempotency_cache_hits = Counter(
    'idempotency_cache_hits_total',
    'Number of idempotency cache hits'
)

idempotency_cache_misses = Counter(
    'idempotency_cache_misses_total',
    'Number of idempotency cache misses'
)