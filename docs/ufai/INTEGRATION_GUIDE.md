# UFAI Integration Guide for Framework Authors
# フレームワーク作者向けUFAI統合ガイド

## Quick Start / クイックスタート

### Step 1: Add bench.yaml to Your Project

Create a `bench.yaml` file in your project root:

```bash
# Interactive initialization
curl -sSL https://bench.req2run.io/init | bash

# Or manual creation
cat > bench.yaml << 'EOF'
version: "1.0"
framework:
  name: "YourFramework"
  language: "python"  # or javascript, go, java, etc.
commands:
  build: "pip install -r requirements.txt"
  test: "pytest tests/"
EOF
```

### Step 2: Validate Your Configuration

```bash
# Download bench CLI
wget https://bench.req2run.io/cli/bench
chmod +x bench

# Validate configuration
./bench validate
```

### Step 3: Run Local Benchmark

```bash
# Run all stages
./bench all

# View results
cat results.json
```

## Detailed Integration Steps / 詳細な統合手順

### 1. Framework Metadata

Define your framework's metadata in `bench.yaml`:

```yaml
framework:
  name: "YourFramework"          # Required: Framework name
  version: "1.0.0"               # Optional: Current version
  language: "python"             # Required: Primary language
  description: "Brief description of your framework"
  repository: "https://github.com/yourorg/yourframework"
  homepage: "https://yourframework.org"
```

### 2. Build Configuration

The build command should prepare your framework for testing:

```yaml
commands:
  build:
    script: |
      # Install dependencies
      pip install -r requirements.txt
      
      # Build artifacts
      python setup.py build
      
      # Any other setup
      ./scripts/prepare.sh
    timeout: 300  # 5 minutes timeout
    workdir: "."  # Working directory
```

**Best Practices:**
- ✅ Use deterministic dependency versions
- ✅ Include all necessary build steps
- ✅ Clean previous builds if needed
- ❌ Don't include interactive prompts

### 3. Test Configuration

Configure your test suite:

```yaml
commands:
  test:
    script: "pytest tests/ --json-report --json-report-file=test-results.json"
    timeout: 600
    env:
      TEST_ENV: "benchmark"
```

**Output Formats Supported:**
- JSON (preferred)
- JUnit XML
- TAP (Test Anything Protocol)
- Plain text with parseable patterns

### 4. Performance Testing

Set up performance benchmarks:

```yaml
commands:
  performance:
    script: |
      # Start your application
      python app.py &
      APP_PID=$!
      sleep 5
      
      # Run performance tests
      locust -f perf_test.py --headless --users 100 --spawn-rate 10 -t 60s
      
      # Stop application
      kill $APP_PID
    endpoint: "http://localhost:8000"
    duration: 60
    concurrency: 100
    tool: "locust"  # or wrk, ab, jmeter, gatling
```

**Supported Tools:**
- **Python**: Locust, pytest-benchmark
- **JavaScript**: Autocannon, Artillery
- **Go**: Vegeta, hey
- **Java**: JMeter, Gatling
- **Universal**: wrk, Apache Bench (ab)

### 5. Security Scanning

Configure security checks:

```yaml
commands:
  security:
    script: |
      # Static analysis
      bandit -r src/ -f json -o security.json
      
      # Dependency scanning
      safety check --json
    scan_type: "static"  # or dynamic, dependency
    severity: "medium"   # minimum severity to report
```

**Security Tools by Language:**
- **Python**: Bandit, Safety, Semgrep
- **JavaScript**: ESLint-security, npm audit, Snyk
- **Go**: Gosec, Nancy
- **Java**: SpotBugs, OWASP Dependency Check
- **Ruby**: Brakeman, Bundler Audit

### 6. Coverage Reporting

Enable code coverage:

```yaml
commands:
  coverage:
    script: "pytest --cov=src --cov-report=html --cov-report=json"
    
artifacts:
  coverage: "htmlcov/index.html"  # HTML report location
```

## Compliance Levels / コンプライアンスレベル

### Progressive Enhancement Path

Start with L0 and gradually add features:

```yaml
# L0: Minimal (Build only)
compliance:
  level: "L0"
  features: ["build"]

# L1: Add testing
compliance:
  level: "L1"
  features: ["build", "test"]

# L2: Add performance
compliance:
  level: "L2"
  features: ["build", "test", "performance"]

# Continue adding features...
```

### Compliance Requirements

| Level | Required Features | Min Score |
|-------|------------------|-----------|
| L0 | build | - |
| L1 | build, test | 50% |
| L2 | build, test, performance | 60% |
| L3 | build, test, performance, security | 70% |
| L4 | build, test, performance, security, coverage | 80% |
| L5 | All features | 90% |

## Environment Configuration / 環境設定

### Environment Variables

```yaml
environment:
  variables:
    NODE_ENV: "production"
    DATABASE_URL: "postgres://localhost/test"
    API_KEY: "${BENCH_API_KEY}"  # Use env var substitution
```

### Service Dependencies

```yaml
environment:
  services:
    - postgres:15     # PostgreSQL database
    - redis:7        # Redis cache
    - mongo:7        # MongoDB
    
  ports:
    - 8000           # Application port
    - 5432           # PostgreSQL
    - 6379           # Redis
```

### Resource Requirements

```yaml
requirements:
  cpu: "2 cores"     # CPU requirement
  memory: "4GB"      # Memory requirement
  disk: "10GB"       # Disk space
  gpu: false         # GPU needed?
```

## Output and Artifacts / 出力とアーティファクト

### Standard Output Locations

```yaml
artifacts:
  # Test results
  test_results: "test-results.json"
  
  # Coverage reports
  coverage: "coverage/index.html"
  
  # Performance data
  performance: "perf-results.json"
  
  # Security reports
  security: "security-report.json"
  
  # Logs
  logs: "logs/"
  
  # Custom artifacts
  custom:
    api_docs: "docs/api.html"
    metrics: "metrics.json"
```

## Testing Your Integration / 統合のテスト

### Local Testing

```bash
# 1. Validate configuration
bench validate

# 2. Run individual stages
bench build
bench test
bench perf
bench security

# 3. Run all stages
bench all

# 4. Generate report
bench report --format html
```

### Docker Testing

```dockerfile
# Use UFAI base image
FROM ufai/bench:latest

# Copy your project
COPY . /app
WORKDIR /app

# Run benchmark
RUN bench all
```

### CI/CD Integration

#### GitHub Actions

```yaml
name: UFAI Benchmark
on: [push, pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run UFAI Benchmark
        uses: ufai/benchmark-action@v1
        with:
          config: bench.yaml
          
      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: results.json
```

#### GitLab CI

```yaml
benchmark:
  image: ufai/bench:latest
  script:
    - bench all
  artifacts:
    reports:
      junit: test-results.xml
    paths:
      - results.json
```

## Common Patterns / 共通パターン

### Pattern 1: Web API Framework

```yaml
version: "1.0"
framework:
  name: "MyAPIFramework"
  language: "python"

commands:
  build: "pip install -e ."
  
  test: "pytest tests/"
  
  performance:
    script: |
      uvicorn app:app &
      sleep 5
      locust -f tests/perf.py --headless -u 100 -t 60s
      
  security: "bandit -r src/"

environment:
  ports: [8000]
```

### Pattern 2: CLI Tool

```yaml
version: "1.0"
framework:
  name: "MyCLITool"
  language: "go"

commands:
  build: "go build -o bin/cli"
  
  test: "go test ./..."
  
  performance: "go test -bench=. -benchtime=60s"
  
  security: "gosec ./..."
```

### Pattern 3: Full-Stack Framework

```yaml
version: "1.0"
framework:
  name: "MyFullStack"
  language: "javascript"

commands:
  build: |
    npm install
    npm run build
    
  test: "npm test"
  
  performance:
    script: |
      npm start &
      sleep 5
      npm run test:perf
      
  security: "npm audit"

environment:
  services:
    - postgres:15
    - redis:7
```

## Troubleshooting / トラブルシューティング

### Common Issues

#### 1. Build Failures

```yaml
# Problem: Dependencies not found
commands:
  build:
    script: |
      # Ensure package manager cache is fresh
      pip install --upgrade pip
      pip cache purge
      pip install -r requirements.txt
```

#### 2. Test Discovery

```yaml
# Problem: Tests not found
commands:
  test:
    script: |
      # Explicitly specify test directory
      pytest tests/ -v
      
      # Or use discovery patterns
      python -m pytest --collect-only
```

#### 3. Performance Testing Port Conflicts

```yaml
# Problem: Port already in use
commands:
  performance:
    script: |
      # Kill any existing process on port
      lsof -ti:8000 | xargs kill -9 || true
      
      # Start application
      python app.py &
```

#### 4. Security Tool Not Found

```yaml
# Problem: Security tool not installed
commands:
  security:
    script: |
      # Install tool if not present
      which bandit || pip install bandit
      bandit -r src/
```

### Debug Mode

Enable debug output:

```bash
# Verbose output
bench all --verbose

# Debug logging
BENCH_LOG_LEVEL=DEBUG bench all

# Dry run (no execution)
bench all --dry-run
```

## Best Practices / ベストプラクティス

### ✅ DO

1. **Version Lock Dependencies**
   ```yaml
   build: "pip install -r requirements.lock.txt"
   ```

2. **Use Explicit Paths**
   ```yaml
   test: "pytest ./tests"  # Not just "pytest"
   ```

3. **Handle Cleanup**
   ```yaml
   performance:
     script: |
       trap 'kill $APP_PID' EXIT
       python app.py &
       APP_PID=$!
   ```

4. **Provide Meaningful Output**
   ```yaml
   test: "pytest --tb=short --verbose"
   ```

5. **Set Appropriate Timeouts**
   ```yaml
   build:
     script: "npm install"
     timeout: 300  # 5 minutes
   ```

### ❌ DON'T

1. **Don't Use Interactive Commands**
   ```yaml
   # Bad
   build: "npm init"  # Requires user input
   
   # Good
   build: "npm ci"    # Non-interactive
   ```

2. **Don't Hardcode Absolute Paths**
   ```yaml
   # Bad
   test: "/home/user/project/run-tests.sh"
   
   # Good
   test: "./run-tests.sh"
   ```

3. **Don't Ignore Errors**
   ```yaml
   # Bad
   build: "make || true"  # Hides failures
   
   # Good
   build: "make"          # Fails appropriately
   ```

## Support and Resources / サポートとリソース

### Documentation
- **Official Docs**: https://bench.req2run.io/docs
- **API Reference**: https://bench.req2run.io/api
- **Examples**: https://github.com/req2run/examples

### Community
- **Discord**: https://discord.gg/req2run
- **Forum**: https://forum.req2run.io
- **Stack Overflow**: Tag with `ufai-benchmark`

### Getting Help
- **Email**: support@req2run.io
- **GitHub Issues**: https://github.com/req2run/ufai/issues
- **Office Hours**: Thursdays 2-3 PM UTC

## Certification / 認証

Once your framework achieves compliance:

1. **Submit for Verification**
   ```bash
   bench submit --registry https://bench.req2run.io
   ```

2. **Receive Certification**
   - Digital badge for your README
   - Listing in the official registry
   - Performance comparison reports

3. **Maintain Compliance**
   - Automatic daily testing
   - Alert on regression
   - Quarterly compliance review

## Example Success Story

> "After integrating UFAI, our framework saw a 40% improvement in performance 
> and identified 3 critical security vulnerabilities we had missed. The 
> standardized benchmarking helped us compare against similar frameworks 
> and make data-driven improvements."
> 
> — FastAPI Team

## Next Steps / 次のステップ

1. ✅ Create your `bench.yaml`
2. ✅ Run local validation
3. ✅ Fix any issues
4. ✅ Submit for certification
5. ✅ Add badge to README
6. ✅ Monitor performance trends

---

*Last Updated: January 2024*  
*Version: 1.0.0*  
*Contact: support@req2run.io*