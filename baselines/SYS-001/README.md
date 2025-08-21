# SYS-001: Distributed Lock Coordinator Service - Baseline Implementation

## Overview

This baseline implementation provides a distributed lock coordination service using the Raft consensus algorithm. It implements distributed mutual exclusion, leader election, and linearizable consistency guarantees.

## Architecture

```
┌─────────────────────────────────────────────┐
│              Client Applications            │
└─────────────┬───────────────────────────────┘
              │ Lock/Unlock Requests
              ▼
┌─────────────────────────────────────────────┐
│            gRPC/HTTP API Layer              │
├─────────────────────────────────────────────┤
│           Lock Manager Service              │
│  - Distributed Locks                        │
│  - Semaphores                               │
│  - Read-Write Locks                         │
├─────────────────────────────────────────────┤
│         Consensus Layer (Raft)              │
│  - Leader Election                          │
│  - Log Replication                          │
│  - Linearizable Reads                       │
├─────────────────────────────────────────────┤
│           State Machine                     │
│  - Lock Registry                            │
│  - Client Sessions                          │
│  - Lease Management                         │
└─────────────────────────────────────────────┘
```

## Features

### Core Features (MUST)
- ✅ Distributed mutual exclusion locks
- ✅ Lock acquisition with timeout
- ✅ Leader election using Raft consensus
- ✅ Network partition handling
- ✅ Linearizable consistency
- ✅ Distributed semaphores
- ✅ Automatic lock release on client failure

### Additional Features (SHOULD/MAY)
- ✅ Read-write locks
- ✅ Lock wait queue visibility
- ⚠️ Distributed barriers (partial)

## API Endpoints

### Lock Operations
- `POST /locks/{name}/acquire` - Acquire a lock
- `POST /locks/{name}/release` - Release a lock
- `GET /locks/{name}/status` - Get lock status
- `POST /locks/{name}/renew` - Renew lock lease

### Semaphore Operations
- `POST /semaphores/{name}/acquire` - Acquire semaphore permit
- `POST /semaphores/{name}/release` - Release semaphore permit
- `GET /semaphores/{name}/status` - Get semaphore status

### Leader Election
- `POST /election/{name}/campaign` - Start leader campaign
- `POST /election/{name}/resign` - Resign leadership
- `GET /election/{name}/leader` - Get current leader

### Health & Monitoring
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /cluster/status` - Cluster status

## Performance Characteristics

- **Lock Acquisition**: P95 < 10ms, P99 < 50ms
- **Throughput**: 10,000+ operations/second
- **Leader Election**: < 1 second
- **Network Partition Recovery**: < 5 seconds

## Building and Running

### Prerequisites
- Go 1.21+ (for Go implementation)
- Docker 24.0+
- Make

### Build
```bash
make build
```

### Run Single Node (Development)
```bash
./distributed-lock --config config/single.yaml
```

### Run Cluster (Production)
```bash
# Node 1
./distributed-lock --config config/node1.yaml

# Node 2
./distributed-lock --config config/node2.yaml

# Node 3
./distributed-lock --config config/node3.yaml
```

### Docker
```bash
docker build -t distributed-lock .
docker run -p 8080:8080 -p 9090:9090 distributed-lock
```

## Testing

### Unit Tests
```bash
make test-unit
```

### Integration Tests
```bash
make test-integration
```

### Chaos Tests
```bash
make test-chaos
```

### Performance Tests
```bash
make test-performance
```

## Configuration

See `config/cluster.yaml` for cluster configuration options:

```yaml
cluster:
  node_id: "node-1"
  peers:
    - "node-2:9090"
    - "node-3:9090"
  
consensus:
  algorithm: "raft"
  election_timeout_ms: 300
  heartbeat_interval_ms: 100
  
locks:
  default_ttl_seconds: 30
  max_wait_time_seconds: 60
  cleanup_interval_seconds: 10
```

## Monitoring

The service exposes Prometheus metrics on port 9090:

- `lock_acquisitions_total` - Total lock acquisitions
- `lock_acquisition_duration_seconds` - Lock acquisition latency
- `active_locks_gauge` - Currently held locks
- `leader_elections_total` - Leader election count
- `consensus_commit_latency_seconds` - Consensus commit latency

## Security

- TLS encryption for all network communication
- Client authentication via mTLS or API keys
- Access control lists for lock namespaces
- Audit logging for all operations

## Limitations

- Maximum 100,000 concurrent locks
- Maximum cluster size: 7 nodes (for optimal performance)
- Lock names limited to 256 characters
- Client session timeout: 30 seconds

## License

MIT