# DB-010: Two-Phase Money Transfer with SERIALIZABLE Isolation - Baseline Implementation

## Overview

This baseline implementation provides a robust financial transaction system with strong consistency guarantees, implementing two-phase commit protocol with SERIALIZABLE isolation level. It ensures ACID properties, exactly-once processing through idempotency, and comprehensive audit logging.

## Features Implemented

### Core Features (MUST)
- ✅ Atomic money transfers between accounts
- ✅ SERIALIZABLE isolation level for all transactions
- ✅ Exactly-once execution with idempotency keys
- ✅ Balance consistency invariants maintained
- ✅ Prevention of negative balances
- ✅ Optimistic locking with retry logic
- ✅ Complete audit trail for all transactions
- ✅ Deadlock-free concurrent transfers

### Additional Features (SHOULD)
- ✅ Transaction timeouts
- ✅ Transaction status queries

## Architecture

```
┌─────────────────────────────────────────────┐
│              REST API Layer                 │
│         (FastAPI + Pydantic Models)         │
├─────────────────────────────────────────────┤
│          Transaction Manager                │
│    (Two-Phase Commit + Retry Logic)         │
├─────────────────────────────────────────────┤
│         Idempotency Manager                 │
│      (Exactly-Once Processing)              │
├─────────────────────────────────────────────┤
│           Database Layer                    │
│    (PostgreSQL + SERIALIZABLE)              │
└─────────────────────────────────────────────┘
```

## API Endpoints

### Account Management
- `POST /accounts` - Create new account
- `GET /accounts/{account_id}` - Get account details
- `GET /accounts/{account_id}/balance` - Get current balance

### Transfers
- `POST /transfers` - Execute money transfer
- `GET /transfers/{transaction_id}/status` - Get transaction status

### Audit
- `GET /audit-logs` - Query audit logs

### Admin
- `POST /admin/reset` - Reset database (debug mode only)

## Transaction Guarantees

### ACID Properties
- **Atomicity**: All-or-nothing execution
- **Consistency**: Balance invariants always maintained
- **Isolation**: SERIALIZABLE isolation prevents anomalies
- **Durability**: Committed transactions persist

### Consistency Invariants
1. No negative balances allowed
2. Total money in system remains constant
3. Every debit has corresponding credit
4. Audit trail completeness

### Concurrency Control
- Row-level locking with SELECT FOR UPDATE
- Consistent lock ordering to prevent deadlocks
- Automatic retry on serialization failures
- Optimistic locking with version numbers

## Example Usage

### Create Accounts
```bash
curl -X POST http://localhost:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{"initial_balance": 1000.00}'
```

### Transfer Money
```bash
curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "from_account_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "to_account_id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22",
    "amount": 100.00,
    "idempotency_key": "unique_key_123"
  }'
```

### Check Transaction Status
```bash
curl http://localhost:8000/transfers/{transaction_id}/status
```

## Performance Characteristics

- **P95 Latency**: < 150ms
- **P99 Latency**: < 500ms
- **Throughput**: 100+ TPS
- **Concurrent Transactions**: 20 max
- **Retry Strategy**: Exponential backoff

## Database Schema

### Tables
- `accounts` - Account balances and metadata
- `transactions` - Transaction records
- `audit_logs` - Complete audit trail
- `idempotency_records` - Idempotency cache

### Indexes
- Balance lookups
- Account transaction history
- Audit log queries
- Idempotency key lookups

## Running the System

### Prerequisites
- PostgreSQL 13+
- Python 3.11+
- Docker (optional)

### Docker Setup
```bash
# Start PostgreSQL
docker run -d \
  --name postgres-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=transactions \
  -p 5432:5432 \
  postgres:15

# Build and run application
docker build -t db-010-baseline .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/transactions \
  db-010-baseline
```

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/transactions

# Run migrations
python -m src.main --migrate

# Start application
uvicorn src.main:app --host 0.0.0.0 --port 8000
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

### Property Tests
```bash
pytest tests/property/ -v
```

### Performance Tests
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## Configuration

### Environment Variables
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DB_POOL_MIN=10
DB_POOL_MAX=20
TRANSACTION_TIMEOUT=30
IDEMPOTENCY_TTL=86400
MAX_RETRY_ATTEMPTS=3
```

### Configuration Files
- `config/database.yaml` - Database settings
- `config/transaction.yaml` - Transaction parameters

## Monitoring

### Prometheus Metrics
- `transactions_total` - Transaction count by status
- `transaction_duration_seconds` - Processing latency
- `failed_transactions_total` - Failure reasons
- `account_balance` - Current balances

### Health Check
```bash
curl http://localhost:8000/health
```

## Security Considerations

1. **SQL Injection**: Parameterized queries only
2. **Race Conditions**: SERIALIZABLE isolation
3. **Double Spending**: Idempotency protection
4. **Audit Trail**: Immutable log records
5. **Balance Checks**: Database constraints

## Troubleshooting

### Common Issues

1. **Serialization Failures**
   - Automatic retry handles most cases
   - Check for long-running transactions

2. **Deadlocks**
   - Consistent lock ordering prevents most deadlocks
   - Monitor for circular wait conditions

3. **Performance Degradation**
   - Check connection pool exhaustion
   - Review transaction duration metrics
   - Ensure proper indexing

## License

MIT