# UFAI User Guide / UFAI利用者ガイド

## Table of Contents / 目次

1. [Getting Started / はじめに](#getting-started--はじめに)
2. [Running Benchmarks / ベンチマークの実行](#running-benchmarks--ベンチマークの実行)
3. [Understanding Results / 結果の理解](#understanding-results--結果の理解)
4. [Comparing Frameworks / フレームワークの比較](#comparing-frameworks--フレームワークの比較)
5. [CI/CD Integration / CI/CD統合](#cicd-integration--cicd統合)
6. [Common Use Cases / 一般的な使用例](#common-use-cases--一般的な使用例)

## Getting Started / はじめに

### What is UFAI?

The Universal Framework Adapter Interface (UFAI) allows you to benchmark any web framework using a standardized approach. Whether you're evaluating frameworks for a new project or optimizing an existing one, UFAI provides consistent, comparable metrics.

UFAI（Universal Framework Adapter Interface）は、標準化されたアプローチを使用して任意のWebフレームワークをベンチマークできます。新しいプロジェクトのためのフレームワーク評価でも、既存のフレームワークの最適化でも、UFAIは一貫性のある比較可能なメトリクスを提供します。

### Installation Options

#### Option 1: Docker (Recommended)

```bash
# Pull the official UFAI image
docker pull ufai/bench:latest

# Verify installation
docker run --rm ufai/bench:latest version
```

#### Option 2: Local Installation

```bash
# Download bench CLI
curl -sSL https://github.com/itdojp/req2run-benchmark/releases/latest/download/bench -o bench
chmod +x bench

# Or use Python directly
git clone https://github.com/itdojp/req2run-benchmark.git
cd req2run-benchmark/adapters/universal
pip install -r requirements.txt
```

#### Option 3: NPM Package (Coming Soon)

```bash
npm install -g @ufai/bench
bench version
```

### Quick Start Example

```bash
# 1. Navigate to your project
cd my-framework-project

# 2. Initialize UFAI configuration
docker run --rm -v $(pwd):/app ufai/bench:latest init

# 3. Run benchmark
docker run --rm -v $(pwd):/app ufai/bench:latest all

# 4. View results
cat results.json
```

## Running Benchmarks / ベンチマークの実行

### Basic Commands

#### Initialize Configuration
```bash
bench init
```
This creates a basic `bench.yaml` file:

```yaml
version: "1.0"
framework:
  name: "MyFramework"
  language: "python"
  version: "1.0.0"
commands:
  build:
    script: "pip install -r requirements.txt"
  test:
    script: "pytest tests/"
```

#### Validate Configuration
```bash
bench validate
```
Checks if your `bench.yaml` is valid and complete.

#### Run Individual Stages

```bash
# Build stage
bench build

# Test stage
bench test

# Performance stage
bench perf

# Security stage
bench security

# All stages
bench all
```

### Docker Usage

#### Basic Docker Commands

```bash
# Run with current directory mounted
docker run --rm -v $(pwd):/app ufai/bench:latest all

# Run with custom config file
docker run --rm -v $(pwd):/app -e BENCH_CONFIG=custom.yaml ufai/bench:latest all

# Run with environment variables
docker run --rm \
  -v $(pwd):/app \
  -e NODE_ENV=production \
  -e API_KEY=test123 \
  ufai/bench:latest all
```

#### Docker Compose Integration

```yaml
# docker-compose.bench.yml
version: '3.8'

services:
  benchmark:
    image: ufai/bench:latest
    volumes:
      - .:/app
    environment:
      - BENCH_CONFIG=bench.yaml
      - DATABASE_URL=postgres://db:5432/test
    depends_on:
      - database
      - redis
    
  database:
    image: postgres:15
    environment:
      POSTGRES_DB: test
      POSTGRES_PASSWORD: test
    
  redis:
    image: redis:7
```

Run with:
```bash
docker-compose -f docker-compose.bench.yml run benchmark all
```

### Advanced Configuration

#### Multi-Environment Setup

```yaml
# bench.yaml
version: "1.0"
framework:
  name: "MyAPI"
  language: "nodejs"

# Base commands
commands:
  build:
    script: "npm install && npm run build"
  test:
    script: "npm test"
  
# Environment-specific overrides
environments:
  development:
    commands:
      build:
        script: "npm install && npm run build:dev"
    environment:
      NODE_ENV: "development"
      DEBUG: "true"
  
  production:
    commands:
      build:
        script: "npm install && npm run build:prod"
      performance:
        script: "npm run bench"
        endpoint: "https://api.example.com"
    environment:
      NODE_ENV: "production"
      DEBUG: "false"
```

Use specific environment:
```bash
bench all --env production
```

#### Custom Metrics Collection

```yaml
# bench.yaml with custom metrics
version: "1.0"
framework:
  name: "CustomFramework"

commands:
  build:
    script: "make build"
    
  # Custom test with coverage
  test:
    script: |
      pytest tests/ --cov=src --cov-report=json
      echo "##METRIC:coverage:$(jq .totals.percent_covered coverage.json)"
    
  # Custom performance with multiple metrics
  performance:
    script: |
      # Run load test
      k6 run load-test.js --out json=metrics.json
      
      # Extract metrics
      echo "##METRIC:p95_latency:$(jq .metrics.http_req_duration.p95 metrics.json)"
      echo "##METRIC:rps:$(jq .metrics.http_reqs.rate metrics.json)"
      echo "##METRIC:error_rate:$(jq .metrics.http_req_failed.rate metrics.json)"
```

## Understanding Results / 結果の理解

### Results Structure

The `results.json` file contains comprehensive benchmark data:

```json
{
  "version": "1.0",
  "timestamp": "2024-01-30T10:00:00Z",
  "framework": {
    "name": "FastAPI",
    "version": "0.100.0",
    "language": "python"
  },
  "compliance": {
    "level": "L3",
    "score": 85
  },
  "stages": {
    "build": {
      "status": "success",
      "duration": 45.2,
      "metrics": {
        "dependencies": 42,
        "artifact_size_mb": 125
      }
    },
    "test": {
      "status": "success",
      "duration": 120.5,
      "metrics": {
        "total": 250,
        "passed": 248,
        "failed": 2,
        "coverage": 92.5
      }
    },
    "performance": {
      "status": "success",
      "duration": 60.0,
      "metrics": {
        "requests_per_second": 5420,
        "latency_p50": 15,
        "latency_p95": 45,
        "latency_p99": 120,
        "error_rate": 0.01
      }
    }
  },
  "overall": {
    "score": 87.5,
    "grade": "B+"
  }
}
```

### Interpreting Metrics

#### Performance Metrics

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Requests/sec | >5000 | 1000-5000 | <1000 |
| Latency P50 | <20ms | 20-50ms | >50ms |
| Latency P95 | <100ms | 100-500ms | >500ms |
| Latency P99 | <500ms | 500-1000ms | >1000ms |
| Error Rate | <0.1% | 0.1-1% | >1% |

#### Compliance Levels

| Level | Badge | Meaning | Requirements |
|-------|-------|---------|--------------|
| L0 | 🔵 | Basic | Build works |
| L1 | 🟢 | Tested | Tests pass (>80%) |
| L2 | 🟡 | Measured | Performance metrics available |
| L3 | 🟠 | Secure | Security scanning implemented |
| L4 | 🔴 | Observable | Coverage & monitoring ready |
| L5 | 🌟 | Complete | All features, >90% scores |

### Viewing Results

#### Command Line

```bash
# View summary
bench report

# View detailed JSON
cat results.json | jq '.'

# View specific metrics
cat results.json | jq '.stages.performance.metrics'

# Generate HTML report
bench report --format html --output report.html
```

#### Web Dashboard (Coming Soon)

```bash
# Start local dashboard
bench dashboard

# Open browser to http://localhost:3000
```

## Comparing Frameworks / フレームワークの比較

### Side-by-Side Comparison

```bash
# Compare two frameworks
bench compare framework1/results.json framework2/results.json

# Output:
# ┌─────────────┬────────────┬────────────┐
# │ Metric      │ Framework1 │ Framework2 │
# ├─────────────┼────────────┼────────────┤
# │ Score       │ 85%        │ 92%        │
# │ Grade       │ B          │ A          │
# │ RPS         │ 4,500      │ 6,200      │
# │ Latency P95 │ 45ms       │ 32ms       │
# │ Coverage    │ 78%        │ 85%        │
# └─────────────┴────────────┴────────────┘
```

### Batch Benchmarking

Create a comparison script:

```bash
#!/bin/bash
# benchmark_all.sh

FRAMEWORKS=("fastapi" "express" "gin" "spring-boot")
RESULTS_DIR="benchmark-results"

mkdir -p $RESULTS_DIR

for framework in "${FRAMEWORKS[@]}"; do
  echo "Benchmarking $framework..."
  cd examples/$framework
  
  docker run --rm -v $(pwd):/app ufai/bench:latest all
  
  cp results.json ../../$RESULTS_DIR/$framework-results.json
  cd ../..
done

# Generate comparison report
bench compare $RESULTS_DIR/*.json --output comparison.html
```

### Framework Ranking

```python
#!/usr/bin/env python3
# rank_frameworks.py

import json
import glob
from typing import List, Dict, Any

def load_results(pattern: str) -> List[Dict[str, Any]]:
    """Load all result files."""
    results = []
    for file in glob.glob(pattern):
        with open(file) as f:
            data = json.load(f)
            data['file'] = file
            results.append(data)
    return results

def rank_by_metric(results: List[Dict], metric_path: str) -> List[tuple]:
    """Rank frameworks by specific metric."""
    ranked = []
    
    for result in results:
        # Navigate to metric value
        value = result
        for key in metric_path.split('.'):
            value = value.get(key, {})
        
        if value:
            ranked.append((
                result['framework']['name'],
                value,
                result['file']
            ))
    
    return sorted(ranked, key=lambda x: x[1], reverse=True)

# Load all results
results = load_results("*/results.json")

# Rank by overall score
print("Overall Score Ranking:")
for name, score, _ in rank_by_metric(results, "overall.score"):
    print(f"  {name}: {score}%")

# Rank by performance
print("\nPerformance Ranking (RPS):")
for name, rps, _ in rank_by_metric(results, "stages.performance.metrics.requests_per_second"):
    print(f"  {name}: {rps:,.0f} req/s")

# Rank by latency
print("\nLatency Ranking (P95):")
ranked = rank_by_metric(results, "stages.performance.metrics.latency_p95")
for name, latency, _ in sorted(ranked, key=lambda x: x[1]):  # Lower is better
    print(f"  {name}: {latency}ms")
```

## CI/CD Integration / CI/CD統合

### GitHub Actions

```yaml
# .github/workflows/benchmark.yml
name: Benchmark

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  benchmark:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Run UFAI Benchmark
        uses: docker://ufai/bench:latest
        with:
          args: all
      
      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: results.json
      
      - name: Check Performance Regression
        run: |
          # Compare with baseline
          if [ -f baseline.json ]; then
            docker run --rm -v $(pwd):/app ufai/bench:latest \
              compare baseline.json results.json --threshold 5
          fi
      
      - name: Update Baseline (main branch only)
        if: github.ref == 'refs/heads/main'
        run: cp results.json baseline.json
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - benchmark

benchmark:
  stage: benchmark
  image: ufai/bench:latest
  script:
    - bench all
    - bench report --format html --output public/benchmark.html
  artifacts:
    paths:
      - results.json
      - public/
    reports:
      performance: results.json
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    stages {
        stage('Benchmark') {
            steps {
                script {
                    docker.image('ufai/bench:latest').inside {
                        sh 'bench all'
                        
                        // Parse results
                        def results = readJSON file: 'results.json'
                        
                        // Set build status based on score
                        if (results.overall.score < 70) {
                            currentBuild.result = 'UNSTABLE'
                        }
                        
                        // Add summary to build
                        currentBuild.description = "Score: ${results.overall.score}%"
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'results.json'
            publishHTML([
                reportDir: '.',
                reportFiles: 'results.json',
                reportName: 'Benchmark Results'
            ])
        }
    }
}
```

## Common Use Cases / 一般的な使用例

### Use Case 1: Framework Selection

**Scenario**: Choosing a framework for a new microservice

```bash
# 1. Create test implementations in each framework
for framework in fastapi express gin; do
  cd $framework-example
  bench all
  cd ..
done

# 2. Compare results
bench compare */results.json --criteria "performance,security,test_coverage"

# 3. Generate decision matrix
bench analyze */results.json --output decision-matrix.html
```

### Use Case 2: Performance Optimization

**Scenario**: Optimizing an existing application

```bash
# 1. Establish baseline
bench all
cp results.json baseline.json

# 2. Make optimization
# ... code changes ...

# 3. Measure improvement
bench all
bench compare baseline.json results.json

# 4. Track over time
bench track --add results.json --tag "v2.0-optimized"
bench history --chart performance-trend.png
```

### Use Case 3: Continuous Monitoring

**Scenario**: Monitor framework performance over releases

```bash
# Run nightly benchmarks
0 2 * * * cd /project && bench all --quiet >> /var/log/bench.log 2>&1

# Weekly report
0 9 * * 1 bench report --period 7d --email team@example.com

# Alert on regression
bench monitor --baseline baseline.json --threshold 10 --alert slack
```

### Use Case 4: Security Compliance

**Scenario**: Ensure framework meets security standards

```yaml
# bench-security.yaml
version: "1.0"
framework:
  name: "SecureAPI"

commands:
  security:
    script: |
      # Dependency scanning
      npm audit --audit-level=high
      
      # SAST scanning
      semgrep --config=auto --json -o semgrep.json .
      
      # Container scanning
      trivy image myapp:latest
      
      # Compliance check
      inspec exec compliance-profile
    
    # Fail if any critical vulnerabilities
    success_criteria:
      max_critical_vulnerabilities: 0
      max_high_vulnerabilities: 5
      compliance_score: 90
```

### Use Case 5: Multi-Region Testing

**Scenario**: Test framework performance across regions

```bash
#!/bin/bash
# multi-region-benchmark.sh

REGIONS=("us-east-1" "eu-west-1" "ap-southeast-1")

for region in "${REGIONS[@]}"; do
  echo "Testing in $region..."
  
  # Deploy to region
  aws deploy --region $region
  
  # Run benchmark
  ENDPOINT="https://api-$region.example.com" \
    bench performance --output results-$region.json
done

# Compare regional performance
bench compare results-*.json --group-by region
```

## Tips and Best Practices / ヒントとベストプラクティス

### 1. Consistent Environment

- Always use the same hardware/VM specs
- Control for network conditions
- Use dedicated benchmark environments
- Avoid running on shared/noisy neighbors

### 2. Warm-Up Period

```yaml
commands:
  performance:
    script: |
      # Warm up the application
      for i in {1..100}; do
        curl -s http://localhost:8000/health > /dev/null
      done
      
      # Run actual benchmark
      wrk -t12 -c400 -d60s http://localhost:8000/
```

### 3. Multiple Runs

```bash
# Run benchmark multiple times and average
for i in {1..5}; do
  bench all --output results-$i.json
done

bench aggregate results-*.json --output final-results.json
```

### 4. Resource Monitoring

```yaml
commands:
  performance:
    script: |
      # Start resource monitoring
      docker stats --format json > resource-usage.json &
      STATS_PID=$!
      
      # Run benchmark
      npm run benchmark
      
      # Stop monitoring
      kill $STATS_PID
      
      # Include resource metrics
      echo "##METRIC:avg_cpu:$(jq -s 'add/length | .cpu_usage' resource-usage.json)"
      echo "##METRIC:avg_memory:$(jq -s 'add/length | .memory_usage' resource-usage.json)"
```

### 5. Version Tracking

```bash
# Tag results with version
bench all --tag "$(git describe --tags)"

# Include in results
jq '.metadata.version = "'$(git describe --tags)'"' results.json > results-versioned.json
```

## Troubleshooting / トラブルシューティング

### Common Issues

#### Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
BENCH_PORT=8080 bench all
```

#### Docker Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Or run with sudo
sudo docker run --rm -v $(pwd):/app ufai/bench:latest all
```

#### Out of Memory
```yaml
# Increase Docker memory limit
commands:
  build:
    script: "npm run build"
    resources:
      memory: "4G"
      cpu: "2"
```

#### Timeout Issues
```yaml
# Increase timeout
commands:
  test:
    script: "npm test"
    timeout: 1800  # 30 minutes
```

## Getting Help / サポート

- **Documentation**: https://github.com/itdojp/req2run-benchmark/docs/ufai
- **Examples**: https://github.com/itdojp/req2run-benchmark/adapters/examples
- **Issues**: https://github.com/itdojp/req2run-benchmark/issues
- **Community**: GitHub Discussions

---

*This guide is maintained by the Req2Run team. For the latest updates, visit our GitHub repository.*