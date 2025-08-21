# DB-011: Event Sourcing with CQRS and Projections

## Overview

A comprehensive implementation of Event Sourcing with Command Query Responsibility Segregation (CQRS) pattern, featuring multiple projections, event replay, temporal queries, saga orchestration, and event stream branching. The system stores all state changes as immutable events and maintains separate read and write models for optimal performance.

## Key Features

### Event Sourcing
- **Immutable Event Store**: All state changes stored as events
- **Event Ordering**: Guaranteed ordering within aggregates
- **Event Versioning**: Support for schema evolution
- **Tamper Detection**: Checksum validation for events
- **Event Replay**: Rebuild state from events

### CQRS Implementation
- **Command Bus**: Routes commands to handlers
- **Query Bus**: Routes queries to read models
- **Separate Models**: Optimized read and write models
- **Middleware Support**: Logging, validation, authorization

### Projections
- **Multiple Projections**: Account balance, orders, inventory, user activity
- **Async Updates**: Non-blocking projection updates
- **Rebuild Capability**: Reconstruct projections from events
- **Custom Projections**: Extensible projection framework

### Advanced Features
- **Snapshots**: Optimize replay performance
- **Temporal Queries**: Query state at any point in time
- **Saga Orchestration**: Long-running transaction support
- **Event Stream Branching**: Alternative timeline exploration

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Commands   │────▶│  Command Bus │────▶│   Aggregates │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────────┐     ┌──────────────┐
                     │ Event Store  │◀────│    Events    │
                     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Projections  │
                     └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Read Model 1 │   │ Read Model 2 │   │ Read Model N │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Queries    │   │   Queries    │   │   Queries    │
└──────────────┘   └──────────────┘   └──────────────┘
```

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t event-sourcing-cqrs .

# Run with PostgreSQL and Redis
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@postgres/eventstore \
  -e REDIS_URL=redis://redis:6379 \
  event-sourcing-cqrs

# Health check
curl http://localhost:8000/health
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start PostgreSQL and Redis:**
```bash
# PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  postgres:15

# Redis
docker run -d -p 6379:6379 redis:7
```

3. **Run the application:**
```bash
python src/main.py
```

## API Endpoints

### Commands
- `POST /api/v1/commands` - Send command to command bus

### Queries
- `POST /api/v1/queries` - Send query to query bus

### Events
- `POST /api/v1/events` - Append event to store
- `GET /api/v1/events/{aggregate_id}` - Get events for aggregate

### Replay & Temporal
- `POST /api/v1/replay` - Replay events to rebuild state
- `POST /api/v1/temporal-query` - Query events by time range

### Projections
- `POST /api/v1/projections/{name}/rebuild` - Rebuild projection

### Sagas
- `POST /api/v1/sagas` - Start new saga

### Branching
- `POST /api/v1/branches` - Create event stream branch

## Usage Examples

### Create Account
```bash
curl -X POST http://localhost:8000/api/v1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "CreateAccount",
    "aggregate_id": "acc-123",
    "data": {
      "account_id": "acc-123",
      "owner": "John Doe",
      "initial_balance": 1000
    }
  }'
```

### Deposit Money
```bash
curl -X POST http://localhost:8000/api/v1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "DepositMoney",
    "aggregate_id": "acc-123",
    "data": {
      "account_id": "acc-123",
      "amount": 500
    }
  }'
```

### Query Account Balance
```bash
curl -X POST http://localhost:8000/api/v1/queries \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "GetAccountBalance",
    "filters": {
      "account_id": "acc-123"
    },
    "projection": "account_balance"
  }'
```

### Get Events
```bash
curl http://localhost:8000/api/v1/events/acc-123
```

### Replay Events
```bash
curl -X POST http://localhost:8000/api/v1/replay \
  -H "Content-Type: application/json" \
  -d '{
    "aggregate_id": "acc-123",
    "from_sequence": 0,
    "use_snapshot": true
  }'
```

### Temporal Query
```bash
curl -X POST http://localhost:8000/api/v1/temporal-query \
  -H "Content-Type: application/json" \
  -d '{
    "aggregate_id": "acc-123",
    "from_time": "2024-01-01T00:00:00Z",
    "to_time": "2024-01-31T23:59:59Z"
  }'
```

## Projections

### Account Balance Projection
Tracks account balances and transaction history:
- Current balance
- Transaction history
- Transfer tracking

### Order Summary Projection
Maintains order summaries and statistics:
- Order details and status
- Customer order history
- Product order tracking
- Daily statistics

### Inventory Projection
Manages inventory levels and movements:
- Stock on hand
- Reserved quantities
- Stock movements
- Low stock alerts

### User Activity Projection
Tracks user activity timeline:
- User registration
- Login sessions
- User actions
- Activity timeline

## Event Versioning

The system supports event schema evolution:

```python
# Register migration
migration.register_migration(
    event_type="AccountCreated",
    from_version=1,
    to_version=2,
    migration_func=migrate_account_v1_to_v2
)
```

## Saga Example

Long-running transaction orchestration:

```python
class TransferSaga(Saga):
    async def start(self, command_bus):
        # Withdraw from source
        await command_bus.send(Command(
            command_type="WithdrawMoney",
            aggregate_id=self.data["from_account"],
            data={"amount": self.data["amount"]}
        ))
    
    async def handle_event(self, event, command_bus):
        if event.event_type == "MoneyWithdrawn":
            # Deposit to target
            await command_bus.send(Command(
                command_type="DepositMoney",
                aggregate_id=self.data["to_account"],
                data={"amount": self.data["amount"]}
            ))
```

## Performance Optimization

### Snapshots
- Created every 100 events by default
- Significantly speeds up replay
- Configurable frequency per aggregate

### Caching
- Query results cached for 60 seconds
- Redis-based distributed cache
- Invalidation on write

### Batch Processing
- Events processed in batches
- Configurable batch size
- Async projection updates

## Configuration

### Event Store (`config/event_store.yaml`)
- Database connections
- Snapshot settings
- Security options

### Projections (`config/projections.yaml`)
- Projection definitions
- Read model storage
- Consistency settings

### CQRS (`config/cqrs.yaml`)
- Command and query handlers
- Aggregate configuration
- Saga definitions

## Monitoring

### Metrics
- Events per second
- Command/query latency
- Projection lag
- Saga completion rate

### Health Checks
- Event store connectivity
- Projection status
- Redis availability
- Database health

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/performance/

# Generate coverage report
pytest --cov=src tests/
```

## Production Deployment

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@db/eventstore
REDIS_URL=redis://redis:6379
LOG_LEVEL=INFO
SNAPSHOT_FREQUENCY=100
```

### Docker Compose
```yaml
version: '3.8'
services:
  app:
    image: event-sourcing-cqrs
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/eventstore
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=eventstore
  
  redis:
    image: redis:7
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-sourcing
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: event-sourcing-cqrs
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## Best Practices

1. **Event Design**: Make events fine-grained and domain-specific
2. **Idempotency**: Ensure command handlers are idempotent
3. **Versioning**: Always version events for future compatibility
4. **Snapshots**: Use snapshots for aggregates with many events
5. **Projections**: Keep projections simple and focused
6. **Testing**: Test event replay and projection rebuilds

## License

MIT