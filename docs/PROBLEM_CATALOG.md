# Req2Run Benchmark Problem Catalog

## Overview

This document provides a comprehensive catalog of all problems currently available in the Req2Run benchmark suite. Problems are organized by difficulty level and cover various technical domains to evaluate AI code generation capabilities.

## Problem Statistics

- **Total Problems**: 15
- **Basic**: 1
- **Intermediate**: 4
- **Advanced**: 4
- **Expert**: 6

## Problem Categories

| Category | Count | Description |
|----------|-------|-------------|
| `web_api` | 2 | RESTful APIs with authentication and rate limiting |
| `cli_tool` | 1 | Command-line utilities and tools |
| `network_protocol` | 1 | Custom TCP/UDP protocol implementations |
| `cryptography` | 1 | Encryption and security tools |
| `data_processing` | 1 | Stream processing and data pipelines |
| `database` | 2 | In-memory and time-series databases |
| `language_processor` | 1 | DSL interpreters and compilers |
| `machine_learning` | 1 | ML training and serving pipelines |
| `blockchain` | 1 | Smart contract platforms |
| `orchestration` | 1 | Container schedulers |
| `api_gateway` | 1 | GraphQL federation |
| `runtime_platform` | 1 | Serverless execution environments |
| `service_mesh` | 1 | mTLS and traffic management |

## Problem Directory

### Basic Level (1 problem)

#### CLI-001: File Processing CLI Tool
- **Category**: `cli_tool`
- **Languages**: Python, JavaScript, Go
- **Time Limit**: 5 minutes generation, 5 minutes execution
- **Key Requirements**:
  - Support CSV, JSON, and TXT file formats
  - Provide format conversion capabilities
  - Implement batch processing
- **Location**: `problems/basic/CLI-001.yaml`
- **Baseline**: `baselines/CLI-001/`

---

### Intermediate Level (4 problems)

#### WEB-001: Task Management API
- **Category**: `web_api`
- **Languages**: Python, JavaScript, Go, Java
- **Time Limit**: 15 minutes generation, 10 minutes execution
- **Key Requirements**:
  - RESTful API with CRUD operations
  - JWT authentication
  - Rate limiting
  - Database persistence
- **Location**: `problems/intermediate/WEB-001.yaml`
- **Baseline**: `baselines/WEB-001/`

#### WEB-001-task-api: Enhanced Task Management API
- **Category**: `web_api`
- **Languages**: Python, JavaScript, Go, Java
- **Time Limit**: 15 minutes generation, 10 minutes execution
- **Key Requirements**:
  - Extended version of WEB-001
  - Additional features for task assignment and tracking
- **Location**: `problems/intermediate/WEB-001-task-api.yaml`

#### CRYPTO-001: File Encryption Tool
- **Category**: `cryptography`
- **Languages**: Python, Go, Rust
- **Time Limit**: 20 minutes generation, 10 minutes execution
- **Key Requirements**:
  - AES-256-GCM encryption
  - Key derivation with PBKDF2
  - Secure file handling
  - CLI interface
- **Location**: `problems/intermediate/CRYPTO-001-file-encryption.yaml`
- **Baseline**: `baselines/CRYPTO-001/`

#### NET-001: Custom Network Protocol
- **Category**: `network_protocol`
- **Languages**: Python, Go, Rust, C++
- **Time Limit**: 25 minutes generation, 15 minutes execution
- **Key Requirements**:
  - Binary protocol implementation
  - Client-server architecture
  - Connection multiplexing
  - Error recovery
- **Location**: `problems/intermediate/NET-001.yaml`
- **Baseline**: `baselines/NET-001/`

---

### Advanced Level (4 problems)

#### DATA-001: Stream Processing Pipeline
- **Category**: `data_processing`
- **Languages**: Python, Java, Go
- **Time Limit**: 30 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Real-time data ingestion
  - Stream transformations
  - Windowing and aggregations
  - Fault tolerance
- **Location**: `problems/advanced/DATA-001.yaml`
- **Baseline**: `baselines/DATA-001/`

#### ML-001: ML Pipeline with Model Serving
- **Category**: `machine_learning`
- **Languages**: Python, Go, Java
- **Time Limit**: 45 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Automated ML pipeline
  - Hyperparameter optimization
  - Model versioning and serving
  - A/B testing capabilities
  - Real-time inference
- **Location**: `problems/advanced/ML-001.yaml`
- **Baseline**: `baselines/ML-001/`
- **Added**: 2024-01-20

#### GQL-001: GraphQL Federation Gateway
- **Category**: `api_gateway`
- **Languages**: TypeScript, JavaScript, Python
- **Time Limit**: 45 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Schema stitching across services
  - Federated authentication
  - Query planning and optimization
  - Response caching
  - Real-time subscriptions
- **Location**: `problems/advanced/GQL-001.yaml`
- **Baseline**: `baselines/GQL-001/`
- **Added**: 2024-01-20

#### FN-001: Serverless Function Runtime
- **Category**: `runtime_platform`
- **Languages**: Go, Rust, Node.js
- **Time Limit**: 45 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Cold start optimization (<100ms)
  - Multi-language runtime support
  - Auto-scaling
  - Function versioning
  - Distributed tracing
- **Location**: `problems/advanced/FN-001.yaml`
- **Baseline**: `baselines/FN-001/`
- **Added**: 2024-01-20

#### TS-001: Time-Series Database
- **Category**: `database`
- **Languages**: Rust, Go, C++
- **Time Limit**: 45 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Efficient compression algorithms
  - Downsampling and retention policies
  - Continuous aggregations
  - SQL-like query language
  - 1M+ points/sec ingestion
- **Location**: `problems/advanced/TS-001.yaml`
- **Baseline**: `baselines/TS-001/`
- **Added**: 2024-01-20

---

### Expert Level (6 problems)

#### LANG-001: SQL-like Query Language Interpreter
- **Category**: `language_processor`
- **Languages**: Python, Go, Rust
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - SQL subset implementation
  - B+Tree indexes
  - Query optimization
  - ACID transactions
  - EXPLAIN output
- **Location**: `problems/expert/LANG-001.yaml`
- **Baseline**: `baselines/LANG-001/`
- **Added**: 2024-01-20

#### CHAIN-001: Blockchain Smart Contract Platform
- **Category**: `blockchain`
- **Languages**: Python, Go, Rust
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - Proof of Stake consensus
  - EVM-compatible smart contracts
  - Merkle Patricia Tries
  - JSON-RPC API
  - mTLS between nodes
- **Location**: `problems/expert/CHAIN-001.yaml`
- **Baseline**: `baselines/CHAIN-001/`
- **Added**: 2024-01-20

#### DB-001: In-Memory Database Engine
- **Category**: `database`
- **Languages**: Rust, Go, C++
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - B+Tree indexes
  - MVCC transactions
  - SQL query interface
  - WAL for durability
  - 100k+ RPS throughput
- **Location**: `problems/expert/DB-001.yaml`
- **Baseline**: `baselines/DB-001/`
- **Added**: 2024-01-20

#### ORCH-001: Container Orchestration Controller
- **Category**: `orchestration`
- **Languages**: Go, Rust, Python
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - Pod scheduling with constraints
  - Auto-scaling
  - Service discovery
  - Rolling updates
  - Health checks and self-healing
- **Location**: `problems/expert/ORCH-001.yaml`
- **Baseline**: `baselines/ORCH-001/`
- **Added**: 2024-01-20

#### MESH-001: Service Mesh Control Plane
- **Category**: `service_mesh`
- **Languages**: Go, Rust, C++
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - mTLS between all services
  - Traffic management
  - Distributed tracing
  - Canary deployments
  - Policy enforcement
- **Location**: `problems/expert/MESH-001.yaml`
- **Baseline**: `baselines/MESH-001/`
- **Added**: 2024-01-20

---

## Performance Requirements Summary

### Resource Limits by Difficulty

| Difficulty | Max CPU | Max Memory | Max Disk | Generation Time | Execution Time |
|------------|---------|------------|----------|-----------------|----------------|
| Basic | 2 cores | 4GB | 10GB | 5-10 min | 5 min |
| Intermediate | 4 cores | 8GB | 20GB | 15-25 min | 10-15 min |
| Advanced | 4 cores | 8-16GB | 50GB | 30-45 min | 20 min |
| Expert | 4-8 cores | 8-16GB | 100GB | 60 min | 30 min |

### Common Performance Targets

- **API Response Time**: p95 < 100ms, p99 < 500ms
- **Throughput**: 1000-100000 RPS depending on problem
- **Cold Start** (serverless): < 100ms
- **Query Latency** (databases): < 10ms for point queries
- **Ingestion Rate** (streaming): 10k-1M events/sec

## Evaluation Metrics

All problems are evaluated on the following weighted metrics:

1. **Functional Coverage** (30-40%): Meeting all MUST requirements
2. **Pass Rate** (25-30%): Percentage of test cases passed
3. **Performance** (20-25%): Meeting latency and throughput targets
4. **Code Quality** (10-15%): Complexity, test coverage, documentation
5. **Security** (5-10%): Authentication, encryption, input validation

### Scoring Thresholds

- **Gold**: ≥90% total score
- **Silver**: 80-89% total score
- **Bronze**: 70-79% total score
- **Fail**: <70% total score

## Recent Additions (January 2024)

The following 9 problems were added to expand the benchmark coverage:

1. **LANG-001**: SQL Query Language Interpreter (Expert)
2. **ML-001**: ML Pipeline with Model Serving (Advanced)
3. **CHAIN-001**: Blockchain Smart Contract Platform (Expert)
4. **DB-001**: In-Memory Database Engine (Expert)
5. **ORCH-001**: Container Orchestration Controller (Expert)
6. **GQL-001**: GraphQL Federation Gateway (Advanced)
7. **FN-001**: Serverless Function Runtime (Advanced)
8. **TS-001**: Time-Series Database (Advanced)
9. **MESH-001**: Service Mesh Control Plane (Expert)

These additions significantly expand the benchmark's coverage of modern distributed systems, databases, and cloud-native technologies.

## Usage Guidelines

### For Implementers

1. Start with problems matching your expertise level
2. Read the complete YAML specification before implementation
3. Focus on MUST requirements first, then SHOULD, then MAY
4. Use the baseline implementations as reference (not for copying)
5. Ensure your solution works within the resource constraints

### For Evaluators

1. Use the automated evaluation harness in `evaluation/`
2. Ensure consistent environment setup across evaluations
3. Run each problem multiple times to account for variance
4. Record both functional and non-functional metrics
5. Generate detailed reports using the reporting tools

## Future Additions

Planned problem categories for future releases:

- **Compiler/Interpreter**: Full programming language implementation
- **Distributed Consensus**: Raft/Paxos implementation
- **Search Engine**: Full-text search with ranking
- **Message Queue**: Pub/sub with persistence
- **CDN/Cache**: Content delivery network
- **Monitoring System**: Metrics collection and alerting

## Contributing

To contribute a new problem:

1. Follow the problem schema in `problems/schema/problem-schema.yaml`
2. Provide comprehensive test cases
3. Include a baseline implementation achieving >70% score
4. Document all requirements clearly
5. Submit a PR with problem definition and tests

## Related Documentation

- [Problem Schema Definition](../problems/schema/problem-schema.yaml)
- [Evaluation Framework](../req2run-evaluation-framework.md)
- [Benchmark Specification](../req2run-benchmark-spec.md)
- [Implementation Guide](implementation-guide.md)
- [Testing Guidelines](test-authoring.md)

---

*Last Updated: January 2024*
*Version: 1.1.0*