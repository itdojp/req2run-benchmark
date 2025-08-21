# UFAI Quick Start / UFAIクイックスタート

## 5 Minutes to Your First Benchmark / 5分で最初のベンチマーク

### Prerequisites / 前提条件

- Docker installed (recommended) / Dockerインストール済み（推奨）
- OR Python 3.8+ / またはPython 3.8以上
- A web framework project / Webフレームワークプロジェクト

## Step 1: Setup / ステップ1: セットアップ

### Option A: Using Docker (Fastest) / Docker使用（最速）

```bash
# Pull the UFAI image
docker pull ghcr.io/itdojp/ufai-bench:latest

# Verify installation
docker run --rm ghcr.io/itdojp/ufai-bench:latest version
```

### Option B: Local Installation / ローカルインストール

```bash
# Clone the repository
git clone https://github.com/itdojp/req2run-benchmark.git
cd req2run-benchmark/adapters/universal

# Install dependencies
pip install -r requirements.txt

# Make bench executable
chmod +x bench
```

## Step 2: Create Configuration / ステップ2: 設定作成

Navigate to your project directory and create `bench.yaml`:

```bash
cd your-project-directory
```

### For Python/FastAPI Projects

```yaml
# bench.yaml
version: "1.0"
framework:
  name: "MyFastAPI"
  language: "python"
  version: "1.0.0"

commands:
  build:
    script: |
      pip install -r requirements.txt
      # Optional: Build any assets
    timeout: 300

  test:
    script: "pytest tests/"
    timeout: 600

  performance:
    script: |
      # Start server in background
      uvicorn main:app --port 8000 &
      SERVER_PID=$!
      sleep 5
      
      # Run performance test
      wrk -t4 -c100 -d30s http://localhost:8000/
      
      # Stop server
      kill $SERVER_PID
    timeout: 120
```

### For Node.js/Express Projects

```yaml
# bench.yaml
version: "1.0"
framework:
  name: "MyExpress"
  language: "nodejs"
  version: "1.0.0"

commands:
  build:
    script: "npm install && npm run build"
    timeout: 300

  test:
    script: "npm test"
    timeout: 600

  performance:
    script: |
      # Start server
      npm start &
      SERVER_PID=$!
      sleep 3
      
      # Run benchmark
      npx autocannon -c 100 -d 30 http://localhost:3000
      
      # Stop server
      kill $SERVER_PID
    timeout: 120
```

### For Go/Gin Projects

```yaml
# bench.yaml
version: "1.0"
framework:
  name: "MyGin"
  language: "go"
  version: "1.0.0"

commands:
  build:
    script: "go mod download && go build -o server ."
    timeout: 300

  test:
    script: "go test ./..."
    timeout: 600

  performance:
    script: |
      # Start server
      ./server &
      SERVER_PID=$!
      sleep 2
      
      # Run benchmark
      go-wrk -c 100 -d 30 http://localhost:8080
      
      # Stop server
      kill $SERVER_PID
    timeout: 120
```

## Step 3: Run Benchmark / ステップ3: ベンチマーク実行

### Using Docker / Docker使用

```bash
# Validate configuration
docker run --rm -v $(pwd):/app ghcr.io/itdojp/ufai-bench:latest validate

# Run all benchmarks
docker run --rm -v $(pwd):/app ghcr.io/itdojp/ufai-bench:latest all

# Or run specific stages
docker run --rm -v $(pwd):/app ghcr.io/itdojp/ufai-bench:latest build
docker run --rm -v $(pwd):/app ghcr.io/itdojp/ufai-bench:latest test
docker run --rm -v $(pwd):/app ghcr.io/itdojp/ufai-bench:latest perf
```

### Using Local Installation / ローカルインストール使用

```bash
# Validate configuration
./bench validate

# Run all benchmarks
./bench all

# Or run specific stages
./bench build
./bench test
./bench perf
```

## Step 4: View Results / ステップ4: 結果確認

After running, check `results.json`:

```bash
# View summary
cat results.json | jq '.overall'

# Output example:
# {
#   "score": 85,
#   "grade": "B+",
#   "compliance_level": "L2"
# }

# View detailed metrics
cat results.json | jq '.stages.performance.metrics'

# Generate readable report
./bench report
```

## Complete Example: FastAPI Application / 完全な例: FastAPIアプリケーション

### 1. Project Structure / プロジェクト構造

```
my-fastapi-app/
├── main.py
├── requirements.txt
├── tests/
│   └── test_main.py
└── bench.yaml
```

### 2. Sample Application / サンプルアプリケーション

```python
# main.py
from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.post("/items/")
def create_item(item: Item):
    return item

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/slow")
def slow_endpoint():
    time.sleep(0.1)  # Simulate slow operation
    return {"status": "completed"}
```

### 3. Test File / テストファイル

```python
# tests/test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_item():
    response = client.post("/items/", json={"name": "Test", "price": 10.5})
    assert response.status_code == 200
    assert response.json()["name"] == "Test"
```

### 4. Benchmark Configuration / ベンチマーク設定

```yaml
# bench.yaml
version: "1.0"
framework:
  name: "FastAPI Example"
  language: "python"
  version: "0.100.0"

commands:
  build:
    script: |
      pip install -r requirements.txt
      echo "##METRIC:dependencies:$(pip list | wc -l)"
    timeout: 300

  test:
    script: |
      pytest tests/ -v --tb=short
      echo "##METRIC:test_count:$(pytest --collect-only -q | wc -l)"
    timeout: 300

  performance:
    script: |
      # Start server
      uvicorn main:app --port 8000 &
      SERVER_PID=$!
      
      # Wait for server
      for i in {1..10}; do
        curl -s http://localhost:8000/health && break
        sleep 1
      done
      
      # Warm up
      for i in {1..100}; do
        curl -s http://localhost:8000/ > /dev/null
      done
      
      # Benchmark with wrk
      wrk -t4 -c100 -d30s --latency http://localhost:8000/ > perf.txt
      
      # Extract metrics
      RPS=$(grep "Requests/sec" perf.txt | awk '{print $2}')
      P50=$(grep "50%" perf.txt | awk '{print $2}')
      P99=$(grep "99%" perf.txt | awk '{print $2}')
      
      echo "##METRIC:requests_per_second:$RPS"
      echo "##METRIC:latency_p50:$P50"
      echo "##METRIC:latency_p99:$P99"
      
      # Clean up
      kill $SERVER_PID
    timeout: 120

  security:
    script: |
      # Check for known vulnerabilities
      pip-audit --format json > audit.json
      VULNS=$(jq '.vulnerabilities | length' audit.json)
      echo "##METRIC:vulnerabilities:$VULNS"
      
      # Basic security checks
      bandit -r . -f json -o bandit.json
      ISSUES=$(jq '.results | length' bandit.json)
      echo "##METRIC:security_issues:$ISSUES"
    timeout: 300

environment:
  variables:
    PYTHONPATH: "."
    ENV: "test"
```

### 5. Run Complete Benchmark / 完全なベンチマーク実行

```bash
# Using Docker (recommended)
docker run --rm -v $(pwd):/app ghcr.io/itdojp/ufai-bench:latest all

# Or locally
./bench all
```

### 6. Expected Output / 期待される出力

```json
{
  "version": "1.0",
  "timestamp": "2024-01-30T10:00:00Z",
  "framework": {
    "name": "FastAPI Example",
    "language": "python",
    "version": "0.100.0"
  },
  "compliance": {
    "level": "L4",
    "score": 90
  },
  "stages": {
    "build": {
      "status": "success",
      "duration": 45.2,
      "metrics": {
        "dependencies": 42
      }
    },
    "test": {
      "status": "success",
      "duration": 12.5,
      "metrics": {
        "test_count": 3
      }
    },
    "performance": {
      "status": "success",
      "duration": 35.0,
      "metrics": {
        "requests_per_second": 8500,
        "latency_p50": "12ms",
        "latency_p99": "45ms"
      }
    },
    "security": {
      "status": "success",
      "duration": 8.3,
      "metrics": {
        "vulnerabilities": 0,
        "security_issues": 2
      }
    }
  },
  "overall": {
    "score": 88,
    "grade": "B+"
  }
}
```

## Troubleshooting / トラブルシューティング

### Common Issues / よくある問題

#### 1. Docker not found / Dockerが見つからない

```bash
# Install Docker
# macOS/Windows: Download Docker Desktop
# Linux:
curl -fsSL https://get.docker.com | sh
```

#### 2. Permission denied / 権限エラー

```bash
# Add execute permission
chmod +x bench

# Or use Python directly
python3 bench all
```

#### 3. Port already in use / ポート使用中

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port in bench.yaml
```

#### 4. Tests failing / テスト失敗

```bash
# Run tests manually to debug
pytest tests/ -v

# Check test output in results.json
cat results.json | jq '.stages.test'
```

## Next Steps / 次のステップ

Now that you have your first benchmark running:

1. **Optimize Performance** / パフォーマンス最適化
   - Analyze the results / 結果を分析
   - Identify bottlenecks / ボトルネックを特定
   - Improve and re-benchmark / 改善して再ベンチマーク

2. **Add More Metrics** / メトリクス追加
   - Custom performance metrics / カスタムパフォーマンスメトリクス
   - Code quality metrics / コード品質メトリクス
   - Resource usage metrics / リソース使用メトリクス

3. **CI/CD Integration** / CI/CD統合
   - Add to GitHub Actions / GitHub Actionsに追加
   - Set up automated benchmarking / 自動ベンチマーク設定
   - Track performance over time / 時系列でパフォーマンス追跡

4. **Compare Frameworks** / フレームワーク比較
   - Benchmark multiple implementations / 複数実装をベンチマーク
   - Generate comparison reports / 比較レポート生成
   - Make data-driven decisions / データドリブンな意思決定

## Resources / リソース

- **Full Documentation**: [Developer Guide](DEVELOPER_GUIDE.md) | [User Guide](USER_GUIDE.md)
- **Examples**: [/adapters/examples](../../adapters/examples)
- **Support**: [GitHub Issues](https://github.com/itdojp/req2run-benchmark/issues)
- **Community**: Discord (Coming Soon)

---

*Get benchmarking in 5 minutes with UFAI - The Universal Framework Adapter Interface*