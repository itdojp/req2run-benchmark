# UFAI Compliance Levels Specification
# UFAIコンプライアンスレベル仕様

## Overview / 概要

The UFAI Compliance Levels provide a progressive framework for frameworks to achieve benchmarking capabilities. Each level builds upon the previous one, allowing frameworks to start simple and gradually add more sophisticated features.

UFAIコンプライアンスレベルは、フレームワークがベンチマーク機能を段階的に達成するためのフレームワークを提供します。各レベルは前のレベルの上に構築され、フレームワークはシンプルに始めて徐々により洗練された機能を追加できます。

## Level Definitions / レベル定義

### Level 0 (L0): Basic / 基本
**Badge**: 🔵 Blue  
**Requirements**:
- ✅ Valid `bench.yaml` file exists
- ✅ Build command executes successfully
- ✅ Framework metadata is complete

**Validation Criteria**:
```yaml
# Minimum bench.yaml for L0
version: "1.0"
framework:
  name: "MyFramework"
  language: "python"
commands:
  build: "pip install -r requirements.txt"
```

**Benefits**:
- Listed in the framework registry
- Basic badge on leaderboard
- Eligible for automated testing

### Level 1 (L1): Testable / テスト可能
**Badge**: 🟢 Green  
**Requirements**:
- ✅ All L0 requirements
- ✅ Test command implemented
- ✅ Tests execute and pass (≥80% pass rate)
- ✅ Test output is parseable

**Validation Criteria**:
```yaml
commands:
  build: "..."
  test:
    script: "pytest tests/"
    timeout: 600
```

**Metrics Required**:
- Total tests count
- Passed/failed breakdown
- Execution time

### Level 2 (L2): Measured / 測定済み
**Badge**: 🟡 Yellow  
**Requirements**:
- ✅ All L1 requirements
- ✅ Performance testing implemented
- ✅ Metrics collection configured
- ✅ Resource usage tracked

**Validation Criteria**:
```yaml
commands:
  # ... previous commands
  performance:
    script: "locust -f perf_test.py"
    endpoint: "http://localhost:8000"
    duration: 60
    concurrency: 100
```

**Metrics Required**:
- Requests per second
- Latency percentiles (p50, p90, p95, p99)
- Error rate
- Resource usage (CPU, memory)

### Level 3 (L3): Secure / セキュア
**Badge**: 🟠 Orange  
**Requirements**:
- ✅ All L2 requirements
- ✅ Security scanning implemented
- ✅ Vulnerability reporting configured
- ✅ Dependency checking enabled

**Validation Criteria**:
```yaml
commands:
  # ... previous commands
  security:
    script: "bandit -r src/"
    scan_type: "static"
    severity: "medium"
```

**Metrics Required**:
- Vulnerability count by severity
- Compliance score
- Security tool coverage

### Level 4 (L4): Observable / 観測可能
**Badge**: 🔴 Red  
**Requirements**:
- ✅ All L3 requirements
- ✅ Code coverage reporting (≥70%)
- ✅ Logging standardized
- ✅ Metrics exportable
- ✅ Tracing implemented (optional)

**Validation Criteria**:
```yaml
commands:
  # ... previous commands
  coverage:
    script: "pytest --cov=src --cov-report=html"
    threshold: 70
artifacts:
  coverage: "htmlcov/index.html"
  logs: "logs/"
  metrics: "metrics.json"
```

**Metrics Required**:
- Line coverage percentage
- Branch coverage percentage
- Function coverage percentage
- Log format compliance

### Level 5 (L5): Complete / 完全
**Badge**: 🌟 Gold Star  
**Requirements**:
- ✅ All L4 requirements
- ✅ All benchmark stages score ≥90%
- ✅ Documentation complete
- ✅ CI/CD integration demonstrated
- ✅ Production readiness validated
- ✅ Scalability testing passed

**Validation Criteria**:
```yaml
compliance:
  level: "L5"
  features:
    - build
    - test
    - performance
    - security
    - coverage
    - docs
    - deploy
    - scale
```

**Additional Requirements**:
- Comprehensive API documentation
- Deployment manifests (Docker, Kubernetes)
- Performance under load (10x baseline)
- Zero critical vulnerabilities
- Automated release process

## Compliance Matrix / コンプライアンスマトリックス

| Feature | L0 | L1 | L2 | L3 | L4 | L5 |
|---------|----|----|----|----|----|----|
| Build | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Test | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Performance | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Security | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Coverage | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Documentation | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Production Ready | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

## Scoring Algorithm / スコアリングアルゴリズム

### Base Score Calculation

```python
def calculate_compliance_score(results):
    weights = {
        'build': 0.10,      # L0
        'test': 0.20,       # L1
        'performance': 0.25, # L2
        'security': 0.20,   # L3
        'coverage': 0.15,   # L4
        'docs': 0.10        # L5
    }
    
    score = 0
    for stage, weight in weights.items():
        if stage in results['stages']:
            stage_score = calculate_stage_score(results['stages'][stage])
            score += stage_score * weight
    
    return score
```

### Level Determination

```python
def determine_compliance_level(results):
    score = results['overall']['score']
    features = results['compliance']['features']
    
    if score >= 90 and all_features_present(features):
        return 'L5'
    elif 'coverage' in features and score >= 80:
        return 'L4'
    elif 'security' in features and score >= 70:
        return 'L3'
    elif 'performance' in features and score >= 60:
        return 'L2'
    elif 'test' in features and score >= 50:
        return 'L1'
    elif 'build' in features:
        return 'L0'
    else:
        return None  # Not compliant
```

## Progressive Enhancement Guide / 段階的強化ガイド

### Starting at L0

1. Create minimal `bench.yaml`:
```bash
bench init --level L0
```

2. Verify build works:
```bash
bench build
```

3. Submit for validation:
```bash
bench validate --submit
```

### Upgrading to L1

1. Add test configuration:
```yaml
commands:
  test:
    script: "npm test"
```

2. Ensure tests pass:
```bash
bench test
# Must achieve ≥80% pass rate
```

### Upgrading to L2

1. Add performance testing:
```yaml
commands:
  performance:
    script: "wrk -t12 -c400 -d30s http://localhost:8080/"
    endpoint: "http://localhost:8080"
```

2. Verify metrics collection:
```bash
bench perf
# Check results.json for metrics
```

### Upgrading to L3

1. Add security scanning:
```yaml
commands:
  security:
    script: "npm audit && snyk test"
    scan_type: "dependency"
```

2. Fix critical vulnerabilities:
```bash
bench security
# Address any critical/high findings
```

### Upgrading to L4

1. Add coverage reporting:
```yaml
commands:
  coverage:
    script: "jest --coverage"
artifacts:
  coverage: "coverage/lcov-report/index.html"
```

2. Achieve coverage threshold:
```bash
bench coverage
# Must achieve ≥70% coverage
```

### Achieving L5

1. Complete all features:
```yaml
compliance:
  level: "L5"
  features: [build, test, performance, security, coverage, docs, deploy]
```

2. Score ≥90% on all stages:
```bash
bench all --strict
# All stages must score ≥90%
```

## Compliance Badges / コンプライアンスバッジ

### Markdown Badges

```markdown
![UFAI L0](https://bench.req2run.io/badge/L0)
![UFAI L1](https://bench.req2run.io/badge/L1)
![UFAI L2](https://bench.req2run.io/badge/L2)
![UFAI L3](https://bench.req2run.io/badge/L3)
![UFAI L4](https://bench.req2run.io/badge/L4)
![UFAI L5](https://bench.req2run.io/badge/L5)
```

### HTML Badges

```html
<img src="https://bench.req2run.io/badge/L5" alt="UFAI Level 5 Compliant">
```

### Dynamic Badge

```markdown
![UFAI Compliance](https://bench.req2run.io/badge/dynamic/myframework)
```

## Verification Process / 検証プロセス

### Automated Verification

1. **Daily Runs**: Frameworks are tested daily
2. **Version Tracking**: Each framework version is tested separately
3. **Historical Data**: Performance trends tracked over time
4. **Regression Detection**: Automatic alerts on score drops

### Manual Verification

For L4 and L5 compliance:
1. Code review of implementation
2. Production deployment verification
3. Scalability testing validation
4. Documentation quality check

## Benefits by Level / レベル別のメリット

| Level | Benefits |
|-------|----------|
| **L0** | • Registry listing<br>• Basic visibility<br>• Community recognition |
| **L1** | • "Tested" badge<br>• Quality assurance<br>• CI/CD ready |
| **L2** | • Performance metrics<br>• Benchmark comparisons<br>• "Fast" badge eligibility |
| **L3** | • Security badge<br>• Vulnerability tracking<br>• Enterprise ready |
| **L4** | • "Production Ready" status<br>• Observability proven<br>• Premium listing |
| **L5** | • "Gold Standard" recognition<br>• Featured framework<br>• Reference implementation |

## FAQ / よくある質問

### Q: Can I skip levels?
**A**: No, each level builds on the previous one. You must achieve L0 before L1, etc.

### Q: How often is compliance verified?
**A**: Daily for L0-L3, weekly for L4-L5.

### Q: What if my framework fails a level?
**A**: You retain your highest achieved level for 30 days to fix issues.

### Q: Can I use custom tools?
**A**: Yes, as long as they produce parseable output in expected formats.

### Q: Is L5 required for production use?
**A**: No, L3 is typically sufficient for production. L5 represents excellence.

## Support / サポート

- **Documentation**: https://bench.req2run.io/docs
- **Examples**: https://github.com/req2run/examples
- **Community**: https://discord.gg/req2run
- **Email**: support@req2run.io