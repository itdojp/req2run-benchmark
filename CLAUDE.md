# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains the Req2Run benchmark specification - a comprehensive evaluation framework for AI code generation systems. The benchmark tests AI systems' ability to generate working implementations from detailed requirement specifications across various technical domains.

## Architecture and Structure

### Core Components

1. **Benchmark Specification** (`req2run-benchmark-spec.md`)
   - Defines problem format using YAML structures
   - Contains 5 core benchmark problems covering: web APIs, cryptography, network protocols, data processing, and distributed systems
   - Each problem includes functional/non-functional requirements, test cases, and evaluation criteria

2. **Evaluation Framework** (`req2run-evaluation-framework.md`)
   - Establishes evaluation principles and execution environment standards
   - Defines resource constraints, time limits, and fairness guarantees
   - Specifies automated evaluation pipeline and scoring mechanisms
   - Details infrastructure requirements (Kubernetes, Docker, cloud platforms)

3. **Additional Problems** (`req2run-additional-problems.md`)
   - Contains 10 additional expert-level problems
   - Covers domains like language processors, ML pipelines, WebRTC, blockchain, databases, orchestration, and service mesh

### Problem Categories

- **web_api**: RESTful APIs with authentication and rate limiting
- **cli_tool**: Command-line utilities
- **network_protocol**: Custom TCP/UDP protocol implementations  
- **cryptography**: Encryption and security tools
- **data_processing**: Stream processing and data pipelines
- **system_utility**: Distributed systems and infrastructure
- **language_processor**: DSL interpreters and compilers
- **machine_learning**: ML training and serving pipelines
- **real_time_communication**: WebRTC and video conferencing
- **blockchain**: Smart contract platforms
- **database**: In-memory and time-series databases
- **orchestration**: Container schedulers
- **api_gateway**: GraphQL federation
- **runtime_platform**: Serverless execution environments
- **service_mesh**: mTLS and traffic management

## Key Technical Details

### Evaluation Environment
- **Infrastructure**: AWS/GCP/Azure with standardized instance types
- **Container Runtime**: Kubernetes v1.28 with containerd 1.7
- **Supported Languages**: Python 3.11, Node.js 20 LTS, Go 1.21, Java 17 LTS, Rust 1.75
- **Databases**: PostgreSQL 15, MySQL 8.0, MongoDB 7.0, Redis 7.2

### Resource Constraints
- **Generation Time**: 5-60 minutes depending on problem difficulty
- **Execution Resources**: 4 CPU cores, 16GB RAM max
- **Storage**: 10GB build artifacts, 50GB runtime data

### Scoring System
- Problems are evaluated on multiple weighted metrics
- Pass threshold: 70% total score with mandatory 100% functional correctness
- Categories: Gold (≥90%), Silver (80-89%), Bronze (70-79%), Fail (<70%)

## Working with This Repository

When implementing solutions for Req2Run problems:

1. Parse the YAML problem specification to extract all requirements
2. Generate code that strictly adheres to the functional requirements (marked as "must")
3. Ensure the solution can be deployed in the specified environment (Docker/Kubernetes)
4. Implement all required API endpoints, protocols, or interfaces exactly as specified
5. Include proper error handling and meet non-functional requirements (performance, security)
6. Structure code to pass all defined test cases

The evaluation is fully automated with no human intervention allowed during generation or execution phases. All generated code must be production-ready and handle edge cases appropriately.