# TS-001: Time-Series Database

## Overview

High-performance time-series database optimized for metrics storage with compression, downsampling, and continuous aggregations.

## Architecture

### Core Components

1. **Storage Engine**
   - Time-partitioned data files
   - Columnar storage format
   - Compression (Gorilla, Snappy, Zstd)
   - Memory-mapped files

2. **Ingestion Pipeline**
   - Write-ahead log
   - In-memory buffer
   - Batch flushing
   - Out-of-order handling

3. **Query Engine**
   - Time-range optimization
   - Parallel query execution
   - Aggregation pushdown
   - Cache layer

4. **Compaction System**
   - Background compaction
   - Downsampling
   - Retention enforcement
   - Space reclamation

5. **Continuous Aggregations**
   - Materialized views
   - Incremental updates
   - Rollup hierarchies
   - Real-time refresh

## Features

### Data Model
- Multi-dimensional metrics
- Tags and fields
- Nanosecond precision
- Schema-on-write

### Compression
- Delta-of-delta timestamps
- XOR floating point
- Dictionary encoding
- Run-length encoding

### Query Language
```sql
SELECT mean(cpu_usage), max(memory)
FROM system_metrics
WHERE host = 'server-1'
  AND time >= now() - 1h
GROUP BY time(5m)
```

### Performance
- 1M+ points/sec ingestion
- Sub-millisecond queries
- 10x compression ratio
- Efficient range scans

## Testing

- Ingestion benchmarks
- Query performance tests
- Compression ratio validation
- Data integrity checks
- Concurrent load testing

## Deployment

```bash
# Build
cargo build --release

# Run database
./target/release/tsdb --config config/database.yaml

# Write data
curl -X POST http://localhost:8086/write \
  -d "cpu,host=server1 usage=0.64 1465839830100400200"

# Query data
curl -G http://localhost:8086/query \
  --data-urlencode "q=SELECT mean(usage) FROM cpu WHERE time > now() - 1h"
```