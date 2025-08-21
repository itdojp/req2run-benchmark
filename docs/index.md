# Req2Run Benchmark

Welcome to the Req2Run Benchmark documentation. This benchmark suite is designed to evaluate AI and LLM code generation capabilities across a wide range of programming challenges.

## Overview

Req2Run provides a comprehensive set of benchmark problems spanning multiple difficulty levels and technical domains:

- **25+ Benchmark Problems** across various categories
- **4 Difficulty Levels**: Basic, Intermediate, Advanced, Expert
- **Multiple Languages**: Python, JavaScript, TypeScript, Go, Java, Rust
- **Diverse Domains**: Web APIs, Databases, CLI Tools, Machine Learning, Cryptography, and more

## Quick Links

- [Problem Catalog](PROBLEM_CATALOG.md) - Browse all available benchmark problems
- [Getting Started Guide](getting-started/quickstart.md) - Start using the benchmark
- [Contributing](development/contributing.md) - Add new problems or improvements
- [GitHub Repository](https://github.com/itdojp/req2run-benchmark)

## Features

### Comprehensive Problem Set
- Web API development (REST, GraphQL, WebSocket)
- Database engines and query processors
- Machine learning pipelines
- Cryptographic implementations
- Real-time systems
- Distributed systems

### Rigorous Evaluation
- Functional correctness testing
- Performance benchmarking
- Security validation
- Code quality metrics
- Resource usage monitoring

### Flexible Framework
- Language-agnostic problem definitions
- Docker-based isolation
- Automated evaluation pipeline
- Extensible architecture

## Getting Started

```bash
# Clone the repository
git clone https://github.com/itdojp/req2run-benchmark.git

# Install dependencies
pip install -r requirements.txt

# Run a benchmark
python -m req2run.evaluate --problem WEB-001
```

## Problem Categories

| Category | Count | Description |
|----------|-------|-------------|
| Web API | 7 | RESTful services, GraphQL, WebSockets |
| Database | 4 | SQL engines, time-series, event sourcing |
| CLI Tool | 3 | Terminal UIs, job orchestration |
| Machine Learning | 2 | ML pipelines, model serving |
| Cryptography | 2 | Zero-knowledge proofs, homomorphic encryption |
| Authentication | 2 | OAuth, RBAC/ABAC |
| Network Protocol | 2 | gRPC, reverse proxy |
| Others | 5+ | Blockchain, orchestration, observability |

## Contributing

We welcome contributions! Please see our [Contributing Guide](development/contributing.md) for details on:
- Adding new benchmark problems
- Improving existing problems
- Enhancing the evaluation framework
- Documentation improvements

## License

This project is licensed under the MIT License. See [LICENSE](about/license.md) for details.