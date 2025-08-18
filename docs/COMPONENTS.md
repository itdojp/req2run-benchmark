# Component Functionality Documentation
# コンポーネント機能説明書

## Core Components / コアコンポーネント

### 1. Evaluator (評価エンジン)

**Location**: `req2run/core.py`

**Purpose**: Central orchestration engine that manages the entire evaluation workflow.

**Key Responsibilities**:
- Parse and validate problem specifications
- Coordinate execution across different runners
- Collect and aggregate metrics
- Generate evaluation reports

**Main Methods**:

```python
class Evaluator:
    def __init__(self, problem_spec: dict, config: EvaluationConfig)
        """Initialize evaluator with problem specification and configuration."""
    
    def evaluate(self, submission_path: Path) -> EvaluationResult
        """Execute complete evaluation pipeline."""
    
    def validate_requirements(self) -> ValidationResult
        """Check if submission meets all requirements."""
    
    def run_tests(self) -> TestResults
        """Execute test suites against submission."""
```

**Configuration Options**:
```yaml
evaluator:
  timeout: 300  # seconds
  max_retries: 3
  runner_type: docker  # docker|kubernetes|local
  enable_sandbox: true
  collect_metrics: true
```

### 2. Runner System (実行システム)

**Location**: `req2run/runner.py`

**Purpose**: Provides abstraction layer for executing code in different environments.

#### 2.1 DockerRunner

**Features**:
- Containerized execution
- Resource isolation
- Network sandboxing
- Volume mounting for data/code

**Usage Example**:
```python
runner = DockerRunner(
    image="python:3.11-slim",
    resources={"cpu": "2", "memory": "512m"},
    network_mode="none"
)
result = runner.execute(command="python main.py")
```

#### 2.2 KubernetesRunner

**Features**:
- Pod-based execution
- Namespace isolation
- ConfigMap/Secret support
- Service mesh integration

**Usage Example**:
```python
runner = KubernetesRunner(
    namespace="evaluation",
    service_account="evaluator",
    node_selector={"workload": "evaluation"}
)
result = runner.execute(manifest="deployment.yaml")
```

#### 2.3 LocalRunner

**Features**:
- Virtual environment isolation
- Process sandboxing
- Resource limiting via cgroups
- Suitable for development

**Usage Example**:
```python
runner = LocalRunner(
    venv_path="/tmp/venv",
    env_vars={"PYTHONPATH": "/app"},
    working_dir="/tmp/workspace"
)
result = runner.execute(script="test.py")
```

### 3. Metrics Calculator (メトリクス計算機)

**Location**: `req2run/metrics.py`

**Purpose**: Calculate comprehensive metrics for evaluation scoring.

**Metric Categories**:

#### 3.1 Functional Metrics
- Test pass rate
- Requirement coverage
- Edge case handling
- Error recovery

#### 3.2 Performance Metrics
- Response time (p50, p95, p99)
- Throughput (requests/second)
- Resource utilization
- Scalability factor

#### 3.3 Security Metrics
- Vulnerability count (Critical/High/Medium/Low)
- OWASP compliance
- Dependency vulnerabilities
- Security headers

#### 3.4 Code Quality Metrics
- Cyclomatic complexity
- Code coverage
- Linting score
- Documentation coverage

**Calculation Formula**:
```python
def calculate_total_score(metrics: Dict[str, float]) -> float:
    weights = {
        "functional": 0.35,
        "test_pass": 0.25,
        "performance": 0.15,
        "quality": 0.15,
        "security": 0.10
    }
    
    total = sum(metrics[key] * weight 
                for key, weight in weights.items())
    return min(100, max(0, total))
```

### 4. Reporter (レポート生成器)

**Location**: `req2run/reporter.py`

**Purpose**: Generate comprehensive evaluation reports in multiple formats.

**Output Formats**:

#### 4.1 HTML Report
- Interactive dashboard
- Charts and visualizations
- Detailed breakdowns
- Code snippets with syntax highlighting

#### 4.2 JSON Report
- Machine-readable format
- Complete metrics data
- Structured results
- API-friendly

#### 4.3 Markdown Report
- Human-readable text
- GitHub-compatible
- Tables and lists
- Embedded diagrams

**Report Sections**:
1. Executive Summary
2. Functional Test Results
3. Performance Analysis
4. Security Assessment
5. Code Quality Review
6. Recommendations
7. Detailed Logs

## Security Components / セキュリティコンポーネント

### 5. Security Sandbox (セキュリティサンドボックス)

**Location**: `infrastructure/security/sandbox.py`

**Purpose**: Provide secure execution environment for untrusted code.

**Features**:

#### 5.1 nsjail Backend
```bash
nsjail_config = {
    "mode": "ONCE",
    "hostname": "sandbox",
    "max_cpus": 2,
    "time_limit": 300,
    "rlimit_as": 512,  # MB
    "rlimit_cpu": 300,  # seconds
    "rlimit_fsize": 100,  # MB
    "disable_clone_newnet": True
}
```

#### 5.2 firejail Backend
```bash
firejail_config = {
    "profile": "evaluation.profile",
    "net": "none",
    "cpu": 2,
    "memory": "512m",
    "timeout": "5m",
    "overlay": True,
    "quiet": True
}
```

#### 5.3 Seccomp Filters
- System call filtering
- Prevents privilege escalation
- Blocks dangerous operations
- Customizable per problem

### 6. Vulnerability Scanner (脆弱性スキャナー)

**Location**: `infrastructure/security/scanner.py`

**Tools Integration**:

#### 6.1 Static Analysis
- **Bandit** (Python): AST-based security linting
- **Semgrep**: Pattern-based code analysis
- **CodeQL**: Semantic code analysis

#### 6.2 Dependency Scanning
- **Safety**: Python package vulnerabilities
- **Trivy**: Container image scanning
- **Snyk**: Comprehensive dependency analysis

#### 6.3 Runtime Protection
- System call monitoring
- Network traffic analysis
- File system access control
- Resource usage tracking

## Infrastructure Components / インフラコンポーネント

### 7. Container Management (コンテナ管理)

**Location**: `infrastructure/docker/`

**Components**:

#### 7.1 Base Images
- Minimal attack surface
- Security updates applied
- Non-root user by default
- Read-only filesystems

#### 7.2 Build Pipeline
```dockerfile
# Multi-stage build for security and size
FROM python:3.11-slim AS builder
# Build dependencies

FROM python:3.11-slim AS runtime
# Minimal runtime
USER nonroot
```

#### 7.3 Registry Management
- Vulnerability scanning on push
- Image signing with Cosign
- SBOM generation
- Retention policies

### 8. Kubernetes Integration (Kubernetes統合)

**Location**: `infrastructure/kubernetes/`

**Resources**:

#### 8.1 Custom Resources
```yaml
apiVersion: req2run.io/v1
kind: Evaluation
metadata:
  name: web-001-eval
spec:
  problemId: WEB-001
  submissionPath: /submissions/abc123
  runner: kubernetes
  timeout: 300
```

#### 8.2 Security Policies
- NetworkPolicies for isolation
- PodSecurityPolicies enforcement
- RBAC with least privilege
- Admission webhooks for validation

#### 8.3 Monitoring Stack
- Prometheus metrics collection
- Grafana dashboards
- Alert manager integration
- Log aggregation with Fluentd

## Data Management / データ管理

### 9. Database Layer (データベース層)

**Location**: `req2run/database/`

**Schema Design**:

```sql
-- Core tables
CREATE TABLE evaluations (
    id UUID PRIMARY KEY,
    problem_id VARCHAR(50),
    submission_id VARCHAR(100),
    status VARCHAR(20),
    score DECIMAL(5,2),
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE metrics (
    evaluation_id UUID REFERENCES evaluations(id),
    metric_type VARCHAR(50),
    metric_name VARCHAR(100),
    value DECIMAL(10,4),
    unit VARCHAR(20)
);

CREATE TABLE test_results (
    evaluation_id UUID REFERENCES evaluations(id),
    test_name VARCHAR(200),
    status VARCHAR(20),
    duration_ms INTEGER,
    error_message TEXT
);
```

### 10. Storage Management (ストレージ管理)

**Location**: `infrastructure/storage/`

**Storage Types**:

#### 10.1 Object Storage (S3)
- Evaluation artifacts
- Generated reports
- Test data sets
- Submission archives

#### 10.2 Block Storage
- Database volumes
- Temporary build space
- Cache directories

#### 10.3 File Storage (NFS)
- Shared configuration
- Problem specifications
- Baseline implementations

## API Components / APIコンポーネント

### 11. REST API Server (REST APIサーバー)

**Location**: `api/server.py`

**Endpoints**:

```python
# Evaluation endpoints
POST   /api/v1/evaluations          # Submit new evaluation
GET    /api/v1/evaluations/{id}     # Get evaluation status
GET    /api/v1/evaluations/{id}/report  # Download report

# Problem endpoints
GET    /api/v1/problems             # List all problems
GET    /api/v1/problems/{id}        # Get problem details
GET    /api/v1/problems/{id}/baseline  # Get baseline code

# Metrics endpoints
GET    /api/v1/metrics/{eval_id}    # Get evaluation metrics
GET    /api/v1/leaderboard/{problem_id}  # Get leaderboard

# Health endpoints
GET    /health                      # Health check
GET    /metrics                     # Prometheus metrics
```

### 12. Authentication & Authorization (認証・認可)

**Location**: `api/auth.py`

**Features**:
- JWT token authentication
- API key management
- Rate limiting per user/IP
- Role-based access control

```python
@app.post("/api/v1/auth/token")
async def login(credentials: OAuth2PasswordRequestForm):
    user = authenticate_user(credentials.username, credentials.password)
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

## Testing Components / テストコンポーネント

### 13. Test Framework (テストフレームワーク)

**Location**: `tests/`

**Test Categories**:

#### 13.1 Unit Tests
- Component isolation
- Mock external dependencies
- Fast execution
- High coverage target (>80%)

#### 13.2 Integration Tests
- Component interaction
- Real dependencies
- Database transactions
- API endpoint testing

#### 13.3 End-to-End Tests
- Complete workflow
- Real problem submissions
- Performance validation
- Security scanning

#### 13.4 Property-Based Tests
```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=100))
def test_score_bounds(score):
    result = normalize_score(score)
    assert 0 <= result <= 100
```

### 14. Performance Testing (性能テスト)

**Location**: `tests/performance/`

**Tools**:

#### 14.1 Locust
```python
class EvaluationUser(HttpUser):
    @task
    def submit_evaluation(self):
        self.client.post("/api/v1/evaluations", 
                        json={"problem_id": "WEB-001"})
```

#### 14.2 Apache Bench
```bash
ab -n 10000 -c 100 http://localhost:8000/api/v1/health
```

#### 14.3 wrk
```lua
-- Custom script for complex scenarios
wrk.method = "POST"
wrk.body = '{"problem_id": "WEB-001"}'
wrk.headers["Content-Type"] = "application/json"
```

## Monitoring Components / 監視コンポーネント

### 15. Metrics Collection (メトリクス収集)

**Location**: `monitoring/`

**Metrics Types**:

#### 15.1 Application Metrics
- Request count and latency
- Error rates
- Queue depths
- Cache hit rates

#### 15.2 System Metrics
- CPU/Memory usage
- Disk I/O
- Network traffic
- Container stats

#### 15.3 Business Metrics
- Evaluations per day
- Success/failure rates
- Average scores
- User activity

### 16. Alerting System (アラートシステム)

**Location**: `monitoring/alerts/`

**Alert Rules**:
```yaml
groups:
  - name: evaluation
    rules:
      - alert: HighErrorRate
        expr: rate(evaluation_errors[5m]) > 0.1
        annotations:
          summary: "High error rate detected"
      
      - alert: LongEvaluationTime
        expr: evaluation_duration_seconds > 300
        annotations:
          summary: "Evaluation taking too long"
```

## Development Tools / 開発ツール

### 17. CLI Interface (CLIインターフェース)

**Location**: `cli/`

**Commands**:
```bash
# Evaluation commands
req2run evaluate <problem-id> <submission-path>
req2run status <evaluation-id>
req2run report <evaluation-id> --format html

# Problem management
req2run problem list
req2run problem show <problem-id>
req2run problem validate <spec-file>

# Development commands
req2run dev server --port 8000
req2run dev test <problem-id>
req2run dev benchmark <submission>
```

### 18. SDK and Client Libraries (SDK・クライアントライブラリ)

**Location**: `sdk/`

**Python SDK**:
```python
from req2run import Client

client = Client(api_key="your-api-key")
result = client.evaluate(
    problem_id="WEB-001",
    submission_path="./my-solution"
)
print(f"Score: {result.score}")
```

**JavaScript SDK**:
```javascript
import { Req2RunClient } from '@req2run/client';

const client = new Req2RunClient({ apiKey: 'your-api-key' });
const result = await client.evaluate({
  problemId: 'WEB-001',
  submissionPath: './my-solution'
});
console.log(`Score: ${result.score}`);
```

## Version History / バージョン履歴

- **v1.0.0** (2024-01-15): Initial component architecture
- **v1.1.0** (2024-01-20): Added Kubernetes runner
- **v1.2.0** (2024-01-25): Enhanced security sandbox
- **v1.3.0** (2024-01-30): Multi-language support framework