# Req2Run Benchmark Problem Catalog

## Overview

This document provides a comprehensive catalog of all problems currently available in the Req2Run benchmark suite. Problems are organized by difficulty level and cover various technical domains to evaluate AI code generation capabilities.

## Problem Statistics

- **Total Problems**: 34
- **Basic**: 1
- **Intermediate**: 8
- **Advanced**: 17
- **Expert**: 8

## Problem Categories

| Category | Count | Description |
|----------|-------|-------------|
| `web_api` | 7 | RESTful APIs, GraphQL, WebSockets, file uploads |
| `cli_tool` | 3 | Command-line utilities, TUI dashboards, job orchestrators |
| `network_protocol` | 3 | TCP/UDP protocols, reverse proxy, gRPC service mesh |
| `cryptography` | 3 | Encryption, zero-knowledge proofs, homomorphic encryption |
| `data_processing` | 3 | Stream processing, ETL pipelines, CDC |
| `database` | 4 | In-memory, time-series, event sourcing, money transfers |
| `authentication` | 2 | OAuth 2.1/OIDC, RBAC/ABAC authorization |
| `observability` | 1 | OpenTelemetry tracing |
| `language_processor` | 1 | SQL query interpreter |
| `machine_learning` | 1 | ML pipeline with model serving |
| `blockchain` | 1 | Smart contract platform |
| `orchestration` | 1 | Container orchestration |
| `api_gateway` | 1 | GraphQL federation gateway |
| `runtime_platform` | 1 | Serverless function runtime |
| `service_mesh` | 1 | Service mesh control plane |

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

### Intermediate Level (8 problems)

#### WEB-001: RESTful API with Authentication
- **Category**: `web_api`
- **Languages**: Python, JavaScript, TypeScript, Go, Java
- **Time Limit**: 10 minutes generation, 10 minutes execution
- **Key Requirements**:
  - JWT-based authentication
  - CRUD operations with pagination
  - Rate limiting (100 requests/minute)
- **Location**: `problems/intermediate/WEB-001.yaml`
- **Baseline**: `baselines/WEB-001/`

#### CRYPTO-001: AES Encryption Tool
- **Category**: `cryptography`
- **Languages**: Python, JavaScript, Go, Rust
- **Time Limit**: 10 minutes generation, 5 minutes execution
- **Key Requirements**:
  - AES-256-GCM encryption/decryption
  - Key derivation with PBKDF2
  - File and stream encryption support
- **Location**: `problems/intermediate/CRYPTO-001.yaml`
- **Baseline**: `baselines/CRYPTO-001/`

#### NET-001: TCP Chat Server
- **Category**: `network_protocol`
- **Languages**: Python, Go, Rust, Java
- **Time Limit**: 15 minutes generation, 10 minutes execution
- **Key Requirements**:
  - Custom protocol implementation
  - Multi-room support
  - Message broadcasting
- **Location**: `problems/intermediate/NET-001.yaml`
- **Baseline**: `baselines/NET-001/`

#### DATA-001: Stream Processing Pipeline
- **Category**: `data_processing`
- **Languages**: Python, Java, Go
- **Time Limit**: 15 minutes generation, 10 minutes execution
- **Key Requirements**:
  - Kafka integration
  - Real-time aggregations
  - Exactly-once processing
- **Location**: `problems/intermediate/DATA-001.yaml`
- **Baseline**: `baselines/DATA-001/`

#### WEB-010: Search + CRUD with Paging, Sort, and Filter
- **Category**: `web_api`
- **Languages**: Python, JavaScript, TypeScript, Go, Java
- **Time Limit**: 20 minutes generation, 10 minutes execution
- **Key Requirements**:
  - Full-text search across all fields
  - Cursor-based pagination
  - Multi-field sorting and complex filtering
- **Location**: `problems/intermediate/WEB-010.yaml`

#### WEB-011: Secure File Upload with Presigned URLs
- **Category**: `web_api`
- **Languages**: Python, JavaScript, TypeScript, Go, Java
- **Time Limit**: 25 minutes generation, 15 minutes execution
- **Key Requirements**:
  - Generate presigned URLs for secure uploads
  - Malware scanning
  - Multipart uploads for large files
- **Location**: `problems/intermediate/WEB-011.yaml`

#### CLI-010: Interactive TUI Dashboard with Real-Time Updates
- **Category**: `cli_tool`
- **Languages**: Python, Go, Rust, JavaScript, Java
- **Time Limit**: 25 minutes generation, 15 minutes execution
- **Key Requirements**:
  - Multiple widgets with real-time data
  - Keyboard and mouse navigation
  - Responsive layout for terminal resize
- **Location**: `problems/intermediate/CLI-010.yaml`

#### OBS-010: OpenTelemetry Comprehensive Tracing Coverage
- **Category**: `observability`
- **Languages**: Python, Go, Java, JavaScript, Rust
- **Time Limit**: 30 minutes generation, 15 minutes execution
- **Key Requirements**:
  - Distributed tracing with context propagation
  - Custom spans and attributes
  - Multiple exporter support
- **Location**: `problems/intermediate/OBS-010.yaml`

---

### Advanced Level (17 problems)

#### ML-001: ML Pipeline with Model Serving
- **Category**: `machine_learning`
- **Languages**: Python
- **Time Limit**: 40 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Time series prediction
  - Hyperparameter optimization
  - A/B testing framework
  - Model drift detection
- **Location**: `problems/advanced/ML-001.yaml`

#### GQL-001: GraphQL Federation Gateway
- **Category**: `api_gateway`
- **Languages**: JavaScript, TypeScript, Go
- **Time Limit**: 35 minutes generation, 15 minutes execution
- **Key Requirements**:
  - Apollo Federation support
  - Query planning and optimization
  - DataLoader integration
  - Multi-layer caching
- **Location**: `problems/advanced/GQL-001.yaml`

#### FN-001: Serverless Function Runtime
- **Category**: `runtime_platform`
- **Languages**: Go, Rust, Node.js
- **Time Limit**: 35 minutes generation, 15 minutes execution
- **Key Requirements**:
  - Multi-language support
  - Cold start optimization (<50ms)
  - Resource limits enforcement
  - Distributed tracing
- **Location**: `problems/advanced/FN-001.yaml`

#### TS-001: Time-Series Database
- **Category**: `database`
- **Languages**: Go, Rust, C++
- **Time Limit**: 40 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Gorilla compression
  - Downsampling and aggregations
  - Continuous queries
  - InfluxQL compatibility
- **Location**: `problems/advanced/TS-001.yaml`

#### WEB-012: Rate Limiting with Idempotency Keys
- **Category**: `web_api`
- **Languages**: Python, Go, JavaScript, TypeScript, Java
- **Time Limit**: 30 minutes generation, 15 minutes execution
- **Key Requirements**:
  - Token bucket and sliding window algorithms
  - Distributed rate limiting with Redis
  - Idempotency key handling
- **Location**: `problems/advanced/WEB-012.yaml`

#### WEB-013: GraphQL API with N+1 Query Prevention
- **Category**: `web_api`
- **Languages**: Python, JavaScript, TypeScript, Go, Java
- **Time Limit**: 40 minutes generation, 20 minutes execution
- **Key Requirements**:
  - DataLoader for N+1 prevention
  - Query depth and complexity limiting
  - Subscriptions for real-time updates
- **Location**: `problems/advanced/WEB-013.yaml`

#### WEB-014: Event-Driven Webhook System with Retry and DLQ
- **Category**: `web_api`
- **Languages**: Python, JavaScript, TypeScript, Go, Java
- **Time Limit**: 40 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Exponential backoff retry logic
  - Dead Letter Queue implementation
  - HMAC-SHA256 payload signing
- **Location**: `problems/advanced/WEB-014.yaml`

#### AUTH-010: OAuth 2.1/OIDC with PKCE
- **Category**: `authentication`
- **Languages**: Python, Go, Java, TypeScript, Rust
- **Time Limit**: 40 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Authorization code flow with PKCE
  - Token introspection and revocation
  - Dynamic client registration
- **Location**: `problems/advanced/AUTH-010.yaml`

#### AUTH-011: RBAC/ABAC Hybrid Authorization System
- **Category**: `authentication`
- **Languages**: Python, Go, Java, TypeScript, Rust
- **Time Limit**: 45 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Role-Based and Attribute-Based Access Control
  - Policy inheritance and composition
  - Constant-time policy evaluation
- **Location**: `problems/advanced/AUTH-011.yaml`

#### DB-010: Two-Phase Money Transfer with SERIALIZABLE Isolation
- **Category**: `database`
- **Languages**: Python, Go, Java, TypeScript, Rust
- **Time Limit**: 35 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Two-phase commit protocol
  - SERIALIZABLE isolation level
  - Idempotent transfers
- **Location**: `problems/advanced/DB-010.yaml`

#### DB-011: Event Sourcing with CQRS and Projections
- **Category**: `database`
- **Languages**: Python, Go, Java, TypeScript, Rust
- **Time Limit**: 45 minutes generation, 25 minutes execution
- **Key Requirements**:
  - Immutable event store
  - CQRS pattern implementation
  - Multiple projections from events
- **Location**: `problems/advanced/DB-011.yaml`

#### DATA-010: Real-Time Stream Processing with Windowing and State
- **Category**: `data_processing`
- **Languages**: Python, Java, Go, Scala, Rust
- **Time Limit**: 45 minutes generation, 30 minutes execution
- **Key Requirements**:
  - Tumbling, sliding, and session windows
  - Stateful computations with fault tolerance
  - Exactly-once processing semantics
- **Location**: `problems/advanced/DATA-010.yaml`

#### DATA-011: ETL Pipeline with Change Data Capture (CDC)
- **Category**: `data_processing`
- **Languages**: Python, Java, Go, Scala, Rust
- **Time Limit**: 45 minutes generation, 30 minutes execution
- **Key Requirements**:
  - Real-time CDC with Debezium
  - Schema evolution handling
  - Data lineage tracking
- **Location**: `problems/advanced/DATA-011.yaml`

#### NET-010: Reverse Proxy with Circuit Breaker
- **Category**: `network_protocol`
- **Languages**: Go, Rust, Python, Java, TypeScript
- **Time Limit**: 35 minutes generation, 20 minutes execution
- **Key Requirements**:
  - Load balancing algorithms
  - Circuit breaker pattern
  - Health checks and failover
- **Location**: `problems/advanced/NET-010.yaml`

#### NET-011: gRPC Service Mesh with Load Balancing and Health Checks
- **Category**: `network_protocol`
- **Languages**: Go, Java, Python, Rust, TypeScript
- **Time Limit**: 45 minutes generation, 25 minutes execution
- **Key Requirements**:
  - Service discovery
  - Client-side load balancing
  - mTLS for service communication
- **Location**: `problems/advanced/NET-011.yaml`

#### CLI-011: Parallel Job Orchestrator with DAG Execution
- **Category**: `cli_tool`
- **Languages**: Python, Go, Rust, JavaScript, Java
- **Time Limit**: 40 minutes generation, 20 minutes execution
- **Key Requirements**:
  - DAG-based job dependencies
  - Parallel execution of independent jobs
  - Resource pooling and limits
- **Location**: `problems/advanced/CLI-011.yaml`

---

### Expert Level (8 problems)

#### LANG-001: SQL Query Language Interpreter
- **Category**: `language_processor`
- **Languages**: Python, Go, Rust, Java
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - SELECT, INSERT, UPDATE, DELETE operations
  - JOIN operations (INNER, LEFT, RIGHT)
  - B+Tree indexing
  - ACID transaction support
- **Location**: `problems/expert/LANG-001.yaml`

#### CHAIN-001: Blockchain Smart Contract Platform
- **Category**: `blockchain`
- **Languages**: Go, Rust, TypeScript
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - EVM compatibility
  - Gas calculation
  - Merkle Patricia Trie
  - PoA consensus
- **Location**: `problems/expert/CHAIN-001.yaml`

#### DB-001: In-Memory Database Engine
- **Category**: `database`
- **Languages**: Go, Rust, C++
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - Redis protocol compatibility
  - Master-slave replication
  - AOF and RDB persistence
  - Lua scripting support
- **Location**: `problems/expert/DB-001.yaml`

#### ORCH-001: Container Orchestration Controller
- **Category**: `orchestration`
- **Languages**: Go, Rust
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - Kubernetes-like scheduling
  - Auto-scaling
  - Rolling updates
  - Health checks
- **Location**: `problems/expert/ORCH-001.yaml`

#### MESH-001: Service Mesh Control Plane
- **Category**: `service_mesh`
- **Languages**: Go, Rust
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - mTLS certificate management
  - Traffic routing policies
  - Circuit breaker configuration
  - xDS API implementation
- **Location**: `problems/expert/MESH-001.yaml`

#### CRYPTO-010: Zero-Knowledge Proof Authentication System
- **Category**: `cryptography`
- **Languages**: Rust, Go, Python, Java, TypeScript
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - Schnorr identification protocol
  - Zero-knowledge proof generation and verification
  - Commitment schemes
- **Location**: `problems/expert/CRYPTO-010.yaml`

#### CRYPTO-011: Homomorphic Encryption for Privacy-Preserving Computation
- **Category**: `cryptography`
- **Languages**: Rust, Go, Python, Java, C++
- **Time Limit**: 60 minutes generation, 45 minutes execution
- **Key Requirements**:
  - Partially homomorphic encryption (PHE)
  - Operations on encrypted data
  - Noise management
- **Location**: `problems/expert/CRYPTO-011.yaml`

#### RTC-001: WebRTC Video Conferencing Server with SFU
- **Category**: `real_time_communication`
- **Languages**: JavaScript, TypeScript, Go, Rust, Python
- **Time Limit**: 60 minutes generation, 30 minutes execution
- **Key Requirements**:
  - Selective Forwarding Unit (SFU) architecture
  - Adaptive bitrate streaming and simulcast
  - Support for 1000 concurrent rooms
  - Screen sharing and recording capabilities
- **Location**: `problems/expert/RTC-001.yaml`

---

## Evaluation Metrics

All problems are evaluated based on:

1. **Functional Correctness** (40-50% weight)
   - Must pass all mandatory requirements
   - API compatibility and protocol compliance

2. **Performance** (15-30% weight)
   - Latency requirements (P95, P99)
   - Throughput targets
   - Resource efficiency

3. **Code Quality** (10-15% weight)
   - Test coverage
   - Documentation
   - Code complexity metrics

4. **Security** (5-15% weight)
   - Vulnerability scanning
   - Security best practices
   - Authentication/authorization correctness

## Pass Criteria

- **Gold**: ≥90% total score
- **Silver**: 80-89% total score
- **Bronze**: 70-79% total score
- **Fail**: <70% total score

Mandatory requirement: 100% functional correctness for all "MUST" requirements.

## Contributing

To add new problems to the benchmark:

1. Create a YAML specification following the schema in `problems/schema/problem-schema.yaml`
2. Place the file in the appropriate difficulty directory
3. Include comprehensive test cases and evaluation criteria
4. Update this catalog with the new problem information

For detailed contribution guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md).