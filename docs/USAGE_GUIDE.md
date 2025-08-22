# Req2Run Usage Guide
# Req2Run 使い方ガイド

## Quick Start / クイックスタート

### Installation / インストール

#### Using pip
```bash
# Install from PyPI
pip install req2run

# Install from source
git clone https://github.com/itdojp/req2run-benchmark.git
cd req2run-benchmark
pip install -e .
```

#### Using Docker
```bash
# Pull the official image
docker pull ghcr.io/itdojp/req2run:latest

# Run with Docker
docker run -v $(pwd):/workspace ghcr.io/itdojp/req2run evaluate WEB-001 /workspace/solution
```

#### Using Kubernetes
```bash
# Install with Helm
helm repo add req2run https://itdojp.github.io/req2run-charts
helm install req2run req2run/evaluator
```

### Basic Usage / 基本的な使い方

#### 1. Evaluate a Solution (解決策の評価)

```bash
# Evaluate your solution for a specific problem
req2run evaluate WEB-001 ./my-solution/

# With custom configuration
req2run evaluate WEB-001 ./my-solution/ --config evaluation.yaml

# Using Docker runner
req2run evaluate WEB-001 ./my-solution/ --runner docker

# With timeout
req2run evaluate WEB-001 ./my-solution/ --timeout 600
```

#### 2. Check Evaluation Status (評価ステータスの確認)

```bash
# Get status of an evaluation
req2run status <evaluation-id>

# Watch status in real-time
req2run status <evaluation-id> --watch

# Get detailed logs
req2run status <evaluation-id> --verbose
```

#### 3. Generate Reports (レポート生成)

```bash
# Generate HTML report
req2run report <evaluation-id> --format html --output report.html

# Generate JSON report for processing
req2run report <evaluation-id> --format json --output results.json

# Generate Markdown for GitHub
req2run report <evaluation-id> --format markdown --output RESULTS.md
```

## Problem Solving Workflow / 問題解決ワークフロー

### Step 1: Understanding the Problem (問題の理解)

```bash
# List all available problems
req2run problem list

# Show detailed problem specification
req2run problem show WEB-001

# Export problem spec to file
req2run problem export WEB-001 --output web-001-spec.yaml
```

### Step 2: Reviewing Requirements (要件の確認)

```yaml
# Example problem specification structure
problem_id: WEB-001
title: RESTful API with Authentication
category: web_api
difficulty: intermediate

requirements:
  functional:
    - id: FR-001
      description: "The API SHALL implement CRUD operations"
      priority: MUST  # RFC 2119
    
    - id: FR-002
      description: "WHEN a user authenticates, the API SHALL return a JWT token"
      priority: MUST
  
  non_functional:
    - id: NFR-001
      description: "The API SHOULD handle 100 requests per second"
      priority: SHOULD
      
    - id: NFR-002
      description: "Response time SHALL be under 200ms for 95% of requests"
      priority: MUST
```

### Step 3: Implementing the Solution (解決策の実装)

#### Project Structure (プロジェクト構造)
```
my-solution/
├── Dockerfile           # Required for Docker runner
├── requirements.txt     # Python dependencies
├── src/
│   ├── __init__.py
│   ├── main.py         # Entry point
│   ├── api/            # API endpoints
│   ├── models/         # Data models
│   └── utils/          # Utilities
├── tests/              # Test cases
├── config/             # Configuration
└── README.md           # Documentation
```

#### Example Implementation (実装例)
```python
# src/main.py
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
import uvicorn

app = FastAPI(title="WEB-001 Solution")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/items")
async def create_item(item: dict, token: str = Depends(oauth2_scheme)):
    # Implementation here
    return {"id": "123", "item": item}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 4: Local Testing (ローカルテスト)

```bash
# Run local tests
pytest tests/

# Test with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_api.py::test_authentication

# Performance testing
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Step 5: Pre-evaluation Validation (評価前検証)

```bash
# Validate solution structure
req2run validate ./my-solution/

# Check requirements coverage
req2run check-requirements WEB-001 ./my-solution/

# Dry run (no scoring)
req2run evaluate WEB-001 ./my-solution/ --dry-run
```

### Step 6: Submit for Evaluation (評価の提出)

```bash
# Standard evaluation
req2run evaluate WEB-001 ./my-solution/

# Save evaluation ID
EVAL_ID=$(req2run evaluate WEB-001 ./my-solution/ --json | jq -r '.evaluation_id')

# Monitor progress
req2run status $EVAL_ID --watch
```

## Advanced Usage / 高度な使用方法

### Custom Configuration (カスタム設定)

#### evaluation.yaml
```yaml
# Custom evaluation configuration
evaluator:
  runner: docker  # docker|kubernetes|local
  timeout: 600    # seconds
  retries: 3
  
security:
  sandbox: nsjail  # nsjail|firejail|none
  strict_mode: true
  
metrics:
  collect_all: true
  performance:
    tool: locust  # locust|ab|wrk
    duration: 60
    users: 100
  
reporting:
  formats: [html, json, markdown]
  include_logs: true
  include_artifacts: true
```

### Batch Evaluation (バッチ評価)

```bash
# Evaluate multiple solutions
for dir in solutions/*; do
  req2run evaluate WEB-001 "$dir" --async
done

# Process results
req2run batch-report --format csv --output results.csv
```

### CI/CD Integration (CI/CD統合)

#### GitHub Actions
```yaml
# .github/workflows/evaluate.yml
name: Evaluate Solution

on:
  push:
    branches: [main]
  pull_request:

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Req2Run
        uses: itdojp/setup-req2run@v1
        with:
          version: latest
      
      - name: Run Evaluation
        run: |
          req2run evaluate ${{ env.PROBLEM_ID }} .
        env:
          PROBLEM_ID: WEB-001
      
      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: evaluation-report
          path: report.html
```

#### GitLab CI
```yaml
# .gitlab-ci.yml
evaluate:
  image: ghcr.io/itdojp/req2run:latest
  script:
    - req2run evaluate WEB-001 .
  artifacts:
    reports:
      junit: report.xml
    paths:
      - report.html
```

### Docker Compose Setup (Docker Compose設定)

```yaml
# docker-compose.yml
version: '3.8'

services:
  evaluator:
    image: ghcr.io/itdojp/req2run:latest
    volumes:
      - ./solution:/workspace
      - ./results:/output
    environment:
      - PROBLEM_ID=WEB-001
      - RUNNER=docker
    command: evaluate ${PROBLEM_ID} /workspace
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=testdb
      - POSTGRES_USER=testuser
      - POSTGRES_PASSWORD=testpass
  
  redis:
    image: redis:7-alpine
```

### Kubernetes Deployment (Kubernetesデプロイメント)

```yaml
# evaluation-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: req2run-evaluation
spec:
  template:
    spec:
      containers:
      - name: evaluator
        image: ghcr.io/itdojp/req2run:latest
        args:
          - evaluate
          - WEB-001
          - /workspace/solution
        volumeMounts:
        - name: solution
          mountPath: /workspace/solution
        - name: output
          mountPath: /output
      volumes:
      - name: solution
        configMap:
          name: solution-code
      - name: output
        emptyDir: {}
      restartPolicy: Never
```

## API Usage / API使用方法

### REST API

```python
# Python example
import requests

# Submit evaluation
response = requests.post(
    "https://api.req2run.io/v1/evaluations",
    json={
        "problem_id": "WEB-001",
        "submission_url": "https://github.com/user/solution.git"
    },
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

eval_id = response.json()["evaluation_id"]

# Check status
status = requests.get(
    f"https://api.req2run.io/v1/evaluations/{eval_id}"
).json()

print(f"Status: {status['status']}")
print(f"Score: {status['score']}")
```

### Python SDK

```python
from req2run import Client, EvaluationConfig

# Initialize client
client = Client(
    api_key="YOUR_API_KEY",
    base_url="https://api.req2run.io"
)

# Configure evaluation
config = EvaluationConfig(
    runner="docker",
    timeout=600,
    collect_metrics=True
)

# Submit evaluation
result = client.evaluate(
    problem_id="WEB-001",
    submission_path="./my-solution",
    config=config
)

# Get detailed report
report = client.get_report(
    evaluation_id=result.evaluation_id,
    format="html"
)

with open("report.html", "w") as f:
    f.write(report)
```

### JavaScript/TypeScript SDK

```typescript
import { Req2RunClient, EvaluationConfig } from '@req2run/client';

// Initialize client
const client = new Req2RunClient({
  apiKey: 'YOUR_API_KEY',
  baseUrl: 'https://api.req2run.io'
});

// Configure evaluation
const config: EvaluationConfig = {
  runner: 'docker',
  timeout: 600,
  collectMetrics: true
};

// Submit evaluation
const result = await client.evaluate({
  problemId: 'WEB-001',
  submissionPath: './my-solution',
  config
});

// Stream logs
const logStream = await client.streamLogs(result.evaluationId);
logStream.on('data', (log) => {
  console.log(log.message);
});

// Get final score
const score = await client.getScore(result.evaluationId);
console.log(`Final score: ${score.total}`);
```

## Troubleshooting / トラブルシューティング

### Common Issues (よくある問題)

#### 1. Docker Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### 2. Timeout Errors
```bash
# Increase timeout
req2run evaluate WEB-001 ./solution --timeout 1200

# Or in configuration
echo "evaluator:\n  timeout: 1200" > config.yaml
req2run evaluate WEB-001 ./solution --config config.yaml
```

#### 3. Memory Limit Exceeded
```bash
# Check memory usage
docker stats

# Increase memory limit (if allowed)
req2run evaluate WEB-001 ./solution --memory 1024m
```

#### 4. Network Access Blocked
```python
# Solutions should not make external network calls
# Use mocking for external dependencies

from unittest.mock import patch

@patch('requests.get')
def test_external_api(mock_get):
    mock_get.return_value.json.return_value = {"data": "mocked"}
    # Your test here
```

### Debug Mode (デバッグモード)

```bash
# Enable debug logging
export REQ2RUN_DEBUG=true
req2run evaluate WEB-001 ./solution --verbose

# Save debug logs
req2run evaluate WEB-001 ./solution --debug 2>&1 | tee debug.log

# Interactive debugging
req2run debug WEB-001 ./solution --interactive
```

### Getting Help (ヘルプ)

```bash
# Show help
req2run --help

# Show command help
req2run evaluate --help

# Check version
req2run --version

# Run diagnostics
req2run doctor
```

## Best Practices / ベストプラクティス

### 1. Structure Your Solution Properly
- Follow the expected directory structure
- Include clear documentation
- Add comprehensive tests
- Use dependency management

### 2. Optimize for Evaluation
- Minimize startup time
- Cache dependencies in Docker images
- Use efficient algorithms
- Handle edge cases

### 3. Security Considerations
- Never hardcode secrets
- Validate all inputs
- Use secure dependencies
- Follow OWASP guidelines

### 4. Performance Optimization
- Profile your code
- Use appropriate data structures
- Implement caching where needed
- Optimize database queries

### 5. Testing Strategy
- Write unit tests first
- Add integration tests
- Include performance tests
- Test error scenarios

## Support and Resources / サポートとリソース

### Documentation
- [Official Documentation](https://docs.req2run.io)
- [API Reference](https://api.req2run.io/docs)
- [Problem Specifications](https://github.com/itdojp/req2run-benchmark/tree/main/problems)

### Community
- [GitHub Discussions](https://github.com/itdojp/req2run-benchmark/discussions)
- [Stack Overflow Tag](https://stackoverflow.com/questions/tagged/req2run)

### Contact
- **Organization**: ITdo Inc. Japan
- **Email**: contact@itdo.jp
- **Issues**: [GitHub Issues](https://github.com/itdojp/req2run-benchmark/issues)

## Version History / バージョン履歴

- **v1.0.0** (2024-01-15): Initial release
- **v1.1.0** (2024-01-20): Added Kubernetes support
- **v1.2.0** (2024-01-25): Multi-language support
- **v1.3.0** (2024-01-30): Enhanced security features