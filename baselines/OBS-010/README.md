# OBS-010: OpenTelemetry Comprehensive Tracing Coverage

**Language / 言語**
- [English](#obs-010-opentelemetry-comprehensive-tracing-coverage)
- [日本語](#obs-010-opentelemetry包括的トレーシングカバレッジ)

A comprehensive OpenTelemetry tracing implementation that instruments build operations, application startup, test execution, and performance benchmarks with detailed observability coverage.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Build Process │───▶│  OpenTelemetry   │───▶│    Exporters    │
│                 │    │                  │    │                 │
│ • Dependencies  │    │ • Trace Context  │    │ • Jaeger        │
│ • Compilation   │    │ • Span Hierarchy │    │ • OTLP          │
│ • Linting       │    │ • Attributes     │    │ • Zipkin        │
│ • Artifacts     │    │ • Events         │    │ • Console       │
└─────────────────┘    │ • Error Capture  │    └─────────────────┘
                       └──────────────────┘
┌─────────────────┐                │                ┌─────────────────┐
│ App Startup     │────────────────┼───────────────▶│ Observability   │
│                 │                │                │                 │
│ • Config Load   │                │                │ • Distributed   │
│ • Dependencies  │                │                │   Tracing       │
│ • Health Checks │                │                │ • Performance   │
│ • Resources     │    ┌───────────▼──────────┐     │   Monitoring    │
└─────────────────┘    │                      │     │ • Error         │
                       │   Instrumented       │     │   Tracking      │
┌─────────────────┐    │     FastAPI          │     │ • Context       │
│ Test Execution  │───▶│     Application      │────▶│   Propagation   │
│                 │    │                      │     └─────────────────┘
│ • Unit Tests    │    │ • HTTP Endpoints     │
│ • Integration   │    │ • Middleware         │
│ • Benchmarks    │    │ • Request Tracing    │
│ • Coverage      │    │ • Error Handling     │
└─────────────────┘    └──────────────────────┘
```

## Key Features

### 🔍 Comprehensive Instrumentation
- **Build Process Tracing**: Complete build pipeline instrumentation
- **Startup Process Monitoring**: Application initialization tracking
- **Test Execution Coverage**: Unit, integration, and performance tests
- **HTTP Request Tracing**: Automatic API endpoint instrumentation

### 📊 Advanced Observability
- **Distributed Tracing**: Full trace context propagation
- **Span Attributes**: Rich metadata and tagging
- **Error Capture**: Complete stack traces and error details
- **Performance Metrics**: Latency, throughput, and resource usage

### 🚀 Multiple Export Formats
- **Jaeger**: Industry-standard distributed tracing
- **OTLP (OpenTelemetry Protocol)**: Vendor-neutral format
- **Zipkin**: Distributed tracing system
- **Console Output**: Development and debugging

### ⚡ Production-Ready Features
- **Context Propagation**: Across service boundaries
- **Sampling Configuration**: Configurable trace sampling
- **Resource Attribution**: Service metadata and versioning
- **Health Monitoring**: Application health and readiness

## Quick Start

### Prerequisites

- Python 3.11+
- OpenTelemetry collectors (Jaeger, OTLP, etc.) - optional

### Installation

```bash
# Clone and setup
cd baselines/OBS-010
pip install -r requirements.txt

# Copy configuration
cp config/tracing.yaml config/local.yaml
# Edit config/local.yaml with your exporter endpoints
```

### Basic Usage

```bash
# Start the instrumented web server
python src/main.py serve --config config/tracing.yaml

# Run build process with tracing
python src/main.py build

# Execute tests with tracing
python src/main.py test --coverage

# Run performance benchmarks
python src/main.py benchmark --iterations 100

# Trace application startup
python src/main.py startup
```

### Docker Deployment

```bash
# Build container
docker build -t obs-010-tracer .

# Run with Jaeger (requires Jaeger running)
docker run -p 8000:8000 \
  -e JAEGER_ENDPOINT=http://jaeger:14268 \
  obs-010-tracer

# Run with console output
docker run -p 8000:8000 obs-010-tracer
```

## Configuration

### Basic Configuration

```yaml
# config/tracing.yaml
tracing:
  service_name: "obs-010-service"
  service_version: "1.0.0"
  console_exporter: true
  
  # Configure exporters
  jaeger_endpoint: "http://localhost:14268"
  otlp_endpoint: "http://localhost:4317"
  zipkin_endpoint: "http://localhost:9411/api/v2/spans"
  
  # Sampling (adjust for production)
  sampling:
    type: "probabilistic"
    rate: 1.0  # 100% sampling

app:
  name: "My Traced Application"
  version: "1.0.0"
  environment: "production"
```

### Exporter Setup

#### Jaeger
```bash
# Start Jaeger all-in-one
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14268:14268 \
  jaegertracing/all-in-one:latest

# Configure endpoint
JAEGER_ENDPOINT=http://localhost:14268
```

#### OTLP Collector
```bash
# Start OTEL collector
docker run -p 4317:4317 -p 8889:8889 \
  otel/opentelemetry-collector:latest

# Configure endpoint  
OTLP_ENDPOINT=http://localhost:4317
```

#### Zipkin
```bash
# Start Zipkin
docker run -d -p 9411:9411 openzipkin/zipkin

# Configure endpoint
ZIPKIN_ENDPOINT=http://localhost:9411/api/v2/spans
```

## API Endpoints

### Core Endpoints

#### Health Check
```http
GET /health

Response:
{
  "status": "healthy",
  "timestamp": 1640995200.0,
  "service": "obs-010-service"
}
```

#### Trigger Build
```http
POST /build
Content-Type: application/json

{
  "steps": [
    {
      "name": "install_deps",
      "type": "python",
      "module": "pip",
      "args": ["install", "-r", "requirements.txt"]
    },
    {
      "name": "lint",
      "type": "command", 
      "command": "flake8 src/"
    }
  ]
}
```

#### Execute Tests
```http
POST /test
Content-Type: application/json

{
  "framework": "pytest",
  "coverage": true,
  "parallel": false,
  "verbose": true
}
```

#### Run Benchmarks
```http
POST /benchmark
Content-Type: application/json

{
  "iterations": 100,
  "warmup": 10
}
```

#### Get Trace Context
```http
GET /trace-context

Response:
{
  "trace_id": "1234567890abcdef1234567890abcdef",
  "span_id": "abcdef1234567890",
  "trace_flags": 1,
  "trace_context": {
    "traceparent": "00-1234567890abcdef1234567890abcdef-abcdef1234567890-01"
  }
}
```

## Trace Instrumentation

### Build Process Tracing

The build tracer instruments various build operations:

```python
from build_tracer import BuildTracer

tracer = BuildTracer()

build_steps = [
    {
        "name": "install_dependencies",
        "type": "python", 
        "module": "pip",
        "args": ["install", "-r", "requirements.txt"]
    },
    {
        "name": "run_tests",
        "type": "command",
        "command": "pytest tests/ -v"
    }
]

result = tracer.execute_build(build_steps)
```

**Generated Spans:**
- `build.execute` - Overall build process
- `build.step.install_dependencies` - Individual build step
- `build.dependency_analysis` - Dependency analysis
- `build.artifact_collection` - Artifact collection

### Startup Process Tracing

The startup tracer captures application initialization:

```python
from startup_tracer import StartupTracer

tracer = StartupTracer("my-app")
startup_info = tracer.trace_startup(config)
```

**Generated Spans:**
- `startup.initialize` - Complete startup process
- `startup.config.load` - Configuration loading
- `startup.dependencies.load` - Dependency loading
- `startup.resources.initialize` - Resource initialization
- `startup.health_checks` - Health check execution

### Test Execution Tracing

The test tracer instruments test runs:

```python
from test_tracer import TestTracer

tracer = TestTracer(framework="pytest")

test_config = {
    "coverage": True,
    "parallel": False,
    "verbose": True
}

result = tracer.execute_test_suite(test_config)
```

**Generated Spans:**
- `test.suite.execute` - Complete test suite
- `test.file.test_example` - Individual test file
- `test.case.test_function` - Individual test case
- `benchmark.performance_test` - Performance benchmarks

### Custom Instrumentation

Add custom tracing to your code:

```python
from tracing import trace_operation, trace_span, add_span_attribute

@trace_operation("custom.operation")
def my_function(param1, param2):
    add_span_attribute("custom.param1", param1)
    
    with trace_span("custom.processing") as span:
        span.set_attribute("processing.type", "data_transformation")
        
        # Your code here
        result = process_data(param1, param2)
        
        span.set_attribute("processing.result_size", len(result))
        
    return result
```

## Span Attributes and Events

### Standard Attributes

All spans include standard OpenTelemetry semantic conventions:

```
service.name = "obs-010-service"
service.version = "1.0.0"
deployment.environment = "production"
telemetry.sdk.language = "python"
telemetry.sdk.name = "opentelemetry"
```

### Build Spans

```
build.project_path = "/app"
build.steps_count = 4
build.step.name = "install_dependencies"
build.step.type = "python"
build.step.command = "pip install -r requirements.txt"
build.step.duration = 45.2
build.step.exit_code = 0
build.success = true
```

### Test Spans

```
test.framework = "pytest"
test.suite.total = 25
test.suite.passed = 23
test.suite.failed = 2
test.suite.duration = 12.5
test.case.name = "test_user_authentication"
test.case.result = "passed"
test.coverage.percentage = 85.0
```

### HTTP Spans

```
http.method = "POST"
http.url = "/api/build"
http.status_code = 200
http.user_agent = "curl/7.68.0"
http.request_content_length = 1024
```

## Monitoring and Observability

### Trace Visualization

#### Jaeger UI
Access Jaeger at `http://localhost:16686` to visualize traces:

- **Service Map**: Understand service interactions
- **Trace Timeline**: See complete request flow
- **Span Details**: Examine individual operations
- **Error Analysis**: Identify failure points

#### Metrics and Analytics

Use trace data for:

- **Performance Analysis**: P95/P99 latency tracking
- **Error Rate Monitoring**: Failure pattern detection
- **Resource Utilization**: CPU/memory usage correlation
- **Dependency Mapping**: Service relationship visualization

### Custom Dashboards

Create custom dashboards using trace data:

```yaml
# dashboard.yaml
dashboards:
  - name: "Build Performance"
    panels:
      - title: "Build Duration"
        query: "histogram_quantile(0.95, rate(build_duration_bucket[5m]))"
      
      - title: "Build Success Rate"
        query: "rate(build_success_total[5m]) / rate(build_total[5m])"
  
  - name: "Test Metrics" 
    panels:
      - title: "Test Coverage"
        query: "avg(test_coverage_percentage)"
      
      - title: "Failed Tests"
        query: "sum(test_failed_total)"
```

## Performance Considerations

### Sampling Configuration

For production environments, configure appropriate sampling:

```yaml
tracing:
  sampling:
    type: "probabilistic"
    rate: 0.1  # Sample 10% of traces
    
    # Or use adaptive sampling
    type: "adaptive"
    max_traces_per_second: 100
```

### Resource Usage

Typical resource overhead:
- **CPU**: 1-3% additional overhead
- **Memory**: 50-100MB for trace buffers
- **Network**: ~1KB per span exported

### Batch Export Configuration

Optimize export performance:

```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor

processor = BatchSpanProcessor(
    exporter,
    max_queue_size=2048,
    schedule_delay_millis=5000,
    max_export_batch_size=512
)
```

## Testing

### Unit Tests

```bash
# Run tests with tracing
python src/main.py test --framework pytest --coverage

# Run specific test categories
pytest tests/test_build_tracer.py -v
pytest tests/test_startup_tracer.py -v
pytest tests/test_tracing.py -v
```

### Integration Tests

```bash
# Test with real exporters
JAEGER_ENDPOINT=http://localhost:14268 python src/main.py test

# Test trace propagation
curl -H "traceparent: 00-1234567890abcdef1234567890abcdef-abcdef1234567890-01" \
     http://localhost:8000/health
```

### Load Testing

```bash
# Generate trace load
for i in {1..100}; do
  curl -X POST http://localhost:8000/build &
done
wait

# Monitor trace ingestion in Jaeger UI
```

## Troubleshooting

### Common Issues

#### No Traces Appearing

1. **Check Exporter Configuration**:
   ```bash
   # Test connectivity
   curl http://localhost:14268/api/traces
   ```

2. **Verify Sampling**:
   ```yaml
   tracing:
     sampling:
       rate: 1.0  # 100% sampling for testing
   ```

3. **Check Console Output**:
   ```yaml
   tracing:
     console_exporter: true
   ```

#### High Resource Usage

1. **Reduce Sampling Rate**:
   ```yaml
   tracing:
     sampling:
       rate: 0.01  # 1% sampling
   ```

2. **Optimize Batch Export**:
   ```python
   processor = BatchSpanProcessor(
       exporter,
       max_queue_size=512,  # Reduce queue size
       schedule_delay_millis=1000  # Export more frequently
   )
   ```

#### Context Propagation Issues

1. **Check Headers**:
   ```bash
   curl -H "traceparent: 00-trace-id-span-id-01" /api/endpoint
   ```

2. **Verify Middleware**:
   ```python
   app.add_middleware(TracingMiddleware)
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
```

Or set environment variable:
```bash
export OTEL_LOG_LEVEL=debug
```

## Production Deployment

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: obs-010-tracer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: obs-010-tracer
  template:
    metadata:
      labels:
        app: obs-010-tracer
    spec:
      containers:
      - name: tracer
        image: obs-010-tracer:latest
        ports:
        - containerPort: 8000
        env:
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector:4317"
        - name: OTEL_SERVICE_NAME
          value: "obs-010-service"
        - name: OTEL_RESOURCE_ATTRIBUTES
          value: "service.name=obs-010-service,deployment.environment=production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
```

### OpenTelemetry Collector

```yaml
# otel-collector.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  
  otlp/datadog:
    endpoint: "https://api.datadoghq.com"
    headers:
      "DD-API-KEY": "${DD_API_KEY}"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger, otlp/datadog]
```

### Security Considerations

- **Sensitive Data**: Never include secrets in span attributes
- **PII Protection**: Sanitize personally identifiable information  
- **Access Control**: Secure exporter endpoints
- **Network Security**: Use TLS for trace export

### Monitoring the Monitor

Monitor your observability infrastructure:

- **Trace Export Success Rate**: Monitor export failures
- **Collector Health**: Check collector resource usage
- **Storage Utilization**: Monitor trace storage growth
- **Query Performance**: Track query response times

## License

This implementation is part of the Req2Run benchmark suite.

---

# OBS-010: OpenTelemetry包括的トレーシングカバレッジ

ビルド操作、アプリケーション起動、テスト実行、パフォーマンスベンチマークをインストルメントし、詳細な可観測性カバレッジを提供する包括的なOpenTelemetryトレーシング実装。

## アーキテクチャ概要

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Build Process │───►│  OpenTelemetry   │───►│    Exporters    │
│                 │    │                  │    │                 │
│ • Dependencies  │    │ • Trace Context  │    │ • Jaeger        │
│ • Compilation   │    │ • Span Hierarchy │    │ • OTLP          │
│ • Linting       │    │ • Attributes     │    │ • Zipkin        │
│ • Artifacts     │    │ • Events         │    │ • Console       │
└─────────────────┘    │ • Error Capture  │    └─────────────────┘
                       └──────────────────┘
┌─────────────────┐                │                ┌─────────────────┐
│ App Startup     │────────────────┼───────────────►│ Observability   │
│                 │                │                │                 │
│ • Config Load   │                │                │ • Distributed   │
│ • Dependencies  │                │                │   Tracing       │
│ • Health Checks │                │                │ • Performance   │
│ • Resources     │    ┌───────────▼──────────┐     │   Monitoring    │
└─────────────────┘    │                      │     │ • Error         │
                       │   Instrumented       │     │   Tracking      │
┌─────────────────┐    │     FastAPI          │────►│ • Context       │
│ Test Execution  │───►│     Application      │     │   Propagation   │
│                 │    │                      │     └─────────────────┘
│ • Unit Tests    │    │ • HTTP Endpoints     │
│ • Integration   │    │ • Middleware         │
│ • Benchmarks    │    │ • Request Tracing    │
│ • Coverage      │    │ • Error Handling     │
└─────────────────┘    └──────────────────────┘
```

## 主要機能

### 🔍 包括的インストルメンテーション
- **ビルドプロセストレーシング**: 完全なビルドパイプラインのインストルメンテーション
- **スタートアッププロセス監視**: アプリケーション初期化の追跡
- **テスト実行カバレッジ**: ユニット、統合、パフォーマンステスト
- **HTTPリクエストトレーシング**: 自動APIエンドポイントインストルメンテーション

### 📊 高度な可観測性
- **分散トレーシング**: 完全なトレースコンテキスト伝播
- **スパン属性**: 豊富なメタデータとタグ付け
- **エラーキャプチャ**: 完全なスタックトレースとエラー詳細
- **パフォーマンスメトリクス**: レイテンシ、スループット、リソース使用量

### 🚀 複数のエクスポート形式
- **Jaeger**: 業界標準の分散トレーシング
- **OTLP（OpenTelemetry Protocol）**: ベンダーニュートラルな形式
- **Zipkin**: 分散トレーシングシステム
- **コンソール出力**: 開発およびデバッグ用

### ⚡ 本番環境対応機能
- **コンテキスト伝播**: サービス境界を越えた伝播
- **サンプリング設定**: 設定可能なトレースサンプリング
- **リソース属性**: サービスメタデータとバージョン管理
- **ヘルス監視**: アプリケーションのヘルスと準備状態

## クイックスタート

### 前提条件

- Python 3.11+
- OpenTelemetryコレクター（Jaeger、OTLP等） - オプション

### インストール

```bash
# クローンとセットアップ
cd baselines/OBS-010
pip install -r requirements.txt

# 設定のコピー
cp config/tracing.yaml config/local.yaml
# config/local.yamlをエクスポーターエンドポイントで編集
```

### 基本的な使用方法

```bash
# インストルメンテーションされたWebサーバーの開始
python src/main.py serve --config config/tracing.yaml

# トレーシング付きビルドプロセスの実行
python src/main.py build

# トレーシング付きテストの実行
python src/main.py test --coverage

# パフォーマンスベンチマークの実行
python src/main.py benchmark --iterations 100

# アプリケーション起動のトレーシング
python src/main.py startup
```

### Dockerデプロイ

```bash
# コンテナのビルド
docker build -t obs-010-tracer .

# Jaegerとともに実行（Jaegerが実行中であることが必要）
docker run -p 8000:8000 \
  -e JAEGER_ENDPOINT=http://jaeger:14268 \
  obs-010-tracer

# コンソール出力で実行
docker run -p 8000:8000 obs-010-tracer
```

## 設定

### 基本設定

```yaml
# config/tracing.yaml
tracing:
  service_name: "obs-010-service"
  service_version: "1.0.0"
  console_exporter: true
  
  # エクスポーターの設定
  jaeger_endpoint: "http://localhost:14268"
  otlp_endpoint: "http://localhost:4317"
  zipkin_endpoint: "http://localhost:9411/api/v2/spans"
  
  # サンプリング（本番環境で調整）
  sampling:
    type: "probabilistic"
    rate: 1.0  # 100%サンプリング

app:
  name: "My Traced Application"
  version: "1.0.0"
  environment: "production"
```

### エクスポーターセットアップ

#### Jaeger
```bash
# Jaeger all-in-oneの開始
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14268:14268 \
  jaegertracing/all-in-one:latest

# エンドポイントの設定
JAEGER_ENDPOINT=http://localhost:14268
```

#### OTLPコレクター
```bash
# OTELコレクターの開始
docker run -p 4317:4317 -p 8889:8889 \
  otel/opentelemetry-collector:latest

# エンドポイントの設定  
OTLP_ENDPOINT=http://localhost:4317
```

#### Zipkin
```bash
# Zipkinの開始
docker run -d -p 9411:9411 openzipkin/zipkin

# エンドポイントの設定
ZIPKIN_ENDPOINT=http://localhost:9411/api/v2/spans
```

## APIエンドポイント

### コアエンドポイント

#### ヘルスチェック
```http
GET /health

Response:
{
  "status": "healthy",
  "timestamp": 1640995200.0,
  "service": "obs-010-service"
}
```

#### ビルドトリガー
```http
POST /build
Content-Type: application/json

{
  "steps": [
    {
      "name": "install_deps",
      "type": "python",
      "module": "pip",
      "args": ["install", "-r", "requirements.txt"]
    },
    {
      "name": "lint",
      "type": "command", 
      "command": "flake8 src/"
    }
  ]
}
```

#### テスト実行
```http
POST /test
Content-Type: application/json

{
  "framework": "pytest",
  "coverage": true,
  "parallel": false,
  "verbose": true
}
```

#### ベンチマーク実行
```http
POST /benchmark
Content-Type: application/json

{
  "iterations": 100,
  "warmup": 10
}
```

#### トレースコンテキスト取得
```http
GET /trace-context

Response:
{
  "trace_id": "1234567890abcdef1234567890abcdef",
  "span_id": "abcdef1234567890",
  "trace_flags": 1,
  "trace_context": {
    "traceparent": "00-1234567890abcdef1234567890abcdef-abcdef1234567890-01"
  }
}
```

## トレースインストルメンテーション

### ビルドプロセストレーシング

ビルドトレーサーは様々なビルド操作をインストルメントします:

```python
from build_tracer import BuildTracer

tracer = BuildTracer()

build_steps = [
    {
        "name": "install_dependencies",
        "type": "python", 
        "module": "pip",
        "args": ["install", "-r", "requirements.txt"]
    },
    {
        "name": "run_tests",
        "type": "command",
        "command": "pytest tests/ -v"
    }
]

result = tracer.execute_build(build_steps)
```

**生成されるスパン:**
- `build.execute` - 全体のビルドプロセス
- `build.step.install_dependencies` - 個別のビルドステップ
- `build.dependency_analysis` - 依存関係分析
- `build.artifact_collection` - アーティファクト収集

### スタートアッププロセストレーシング

スタートアップトレーサーはアプリケーションの初期化をキャプチャします:

```python
from startup_tracer import StartupTracer

tracer = StartupTracer("my-app")
startup_info = tracer.trace_startup(config)
```

**生成されるスパン:**
- `startup.initialize` - 完全なスタートアッププロセス
- `startup.config.load` - 設定の読み込み
- `startup.dependencies.load` - 依存関係の読み込み
- `startup.resources.initialize` - リソースの初期化
- `startup.health_checks` - ヘルスチェックの実行

### テスト実行トレーシング

テストトレーサーはテスト実行をインストルメントします:

```python
from test_tracer import TestTracer

tracer = TestTracer(framework="pytest")

test_config = {
    "coverage": True,
    "parallel": False,
    "verbose": True
}

result = tracer.execute_test_suite(test_config)
```

**生成されるスパン:**
- `test.suite.execute` - 完全なテストスイート
- `test.file.test_example` - 個別のテストファイル
- `test.case.test_function` - 個別のテストケース
- `benchmark.performance_test` - パフォーマンスベンチマーク

### カスタムインストルメンテーション

コードにカスタムトレーシングを追加:

```python
from tracing import trace_operation, trace_span, add_span_attribute

@trace_operation("custom.operation")
def my_function(param1, param2):
    add_span_attribute("custom.param1", param1)
    
    with trace_span("custom.processing") as span:
        span.set_attribute("processing.type", "data_transformation")
        
        # ここにコード
        result = process_data(param1, param2)
        
        span.set_attribute("processing.result_size", len(result))
        
    return result
```

## スパン属性とイベント

### 標準属性

すべてのスパンにはOpenTelemetryセマンティック規約が含まれます:

```
service.name = "obs-010-service"
service.version = "1.0.0"
deployment.environment = "production"
telemetry.sdk.language = "python"
telemetry.sdk.name = "opentelemetry"
```

### ビルドスパン

```
build.project_path = "/app"
build.steps_count = 4
build.step.name = "install_dependencies"
build.step.type = "python"
build.step.command = "pip install -r requirements.txt"
build.step.duration = 45.2
build.step.exit_code = 0
build.success = true
```

### テストスパン

```
test.framework = "pytest"
test.suite.total = 25
test.suite.passed = 23
test.suite.failed = 2
test.suite.duration = 12.5
test.case.name = "test_user_authentication"
test.case.result = "passed"
test.coverage.percentage = 85.0
```

### HTTPスパン

```
http.method = "POST"
http.url = "/api/build"
http.status_code = 200
http.user_agent = "curl/7.68.0"
http.request_content_length = 1024
```

## 監視と可観測性

### トレース可視化

#### Jaeger UI
`http://localhost:16686`でJaegerにアクセスしてトレースを可視化:

- **サービスマップ**: サービスの相互作用を理解
- **トレースタイムライン**: 完全なリクエストフローを見る
- **スパン詳細**: 個別の操作を調査
- **エラー分析**: 障害ポイントを特定

#### メトリクスと分析

トレースデータを以下の用途で使用:

- **パフォーマンス分析**: P95/P99レイテンシの追跡
- **エラー率監視**: 障害パターンの検出
- **リソース使用率**: CPU/メモリ使用量の相関
- **依存関係マッピング**: サービス関係の可視化

### カスタムダッシュボード

トレースデータを使用したカスタムダッシュボードの作成:

```yaml
# dashboard.yaml
dashboards:
  - name: "ビルドパフォーマンス"
    panels:
      - title: "ビルド時間"
        query: "histogram_quantile(0.95, rate(build_duration_bucket[5m]))"
      
      - title: "ビルド成功率"
        query: "rate(build_success_total[5m]) / rate(build_total[5m])"
  
  - name: "テストメトリクス" 
    panels:
      - title: "テストカバレッジ"
        query: "avg(test_coverage_percentage)"
      
      - title: "失敗テスト"
        query: "sum(test_failed_total)"
```

## パフォーマンス考慮事項

### サンプリング設定

本番環境では適切なサンプリングを設定:

```yaml
tracing:
  sampling:
    type: "probabilistic"
    rate: 0.1  # 10%のトレースをサンプリング
    
    # または適応サンプリングを使用
    type: "adaptive"
    max_traces_per_second: 100
```

### リソース使用量

一般的なリソースオーバーヘッド:
- **CPU**: 1-3%の追加オーバーヘッド
- **メモリ**: トレースバッファ用に50-100MB
- **ネットワーク**: エクスポートされるスパンあたり約1KB

### バッチエクスポート設定

エクスポートパフォーマンスの最適化:

```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor

processor = BatchSpanProcessor(
    exporter,
    max_queue_size=2048,
    schedule_delay_millis=5000,
    max_export_batch_size=512
)
```

## テスト

### ユニットテスト

```bash
# トレーシング付きテストの実行
python src/main.py test --framework pytest --coverage

# 特定のテストカテゴリの実行
pytest tests/test_build_tracer.py -v
pytest tests/test_startup_tracer.py -v
pytest tests/test_tracing.py -v
```

### 統合テスト

```bash
# 実際のエクスポーターでのテスト
JAEGER_ENDPOINT=http://localhost:14268 python src/main.py test

# トレース伝播のテスト
curl -H "traceparent: 00-1234567890abcdef1234567890abcdef-abcdef1234567890-01" \
     http://localhost:8000/health
```

### 負荷テスト

```bash
# トレース負荷の生成
for i in {1..100}; do
  curl -X POST http://localhost:8000/build &
done
wait

# Jaeger UIでトレース取り込みを監視
```

## トラブルシューティング

### 一般的な問題

#### トレースが表示されない

1. **エクスポーター設定の確認**:
   ```bash
   # 接続性のテスト
   curl http://localhost:14268/api/traces
   ```

2. **サンプリングの確認**:
   ```yaml
   tracing:
     sampling:
       rate: 1.0  # テスト用に100%サンプリング
   ```

3. **コンソール出力の確認**:
   ```yaml
   tracing:
     console_exporter: true
   ```

#### 高リソース使用量

1. **サンプリング率の削減**:
   ```yaml
   tracing:
     sampling:
       rate: 0.01  # 1%サンプリング
   ```

2. **バッチエクスポートの最適化**:
   ```python
   processor = BatchSpanProcessor(
       exporter,
       max_queue_size=512,  # キューサイズの削減
       schedule_delay_millis=1000  # より頻繁なエクスポート
   )
   ```

#### コンテキスト伝播問題

1. **ヘッダーの確認**:
   ```bash
   curl -H "traceparent: 00-trace-id-span-id-01" /api/endpoint
   ```

2. **ミドルウェアの確認**:
   ```python
   app.add_middleware(TracingMiddleware)
   ```

### デバッグモード

デバッグログの有効化:

```python
import logging
logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
```

または環境変数の設定:
```bash
export OTEL_LOG_LEVEL=debug
```

## 本番デプロイ

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: obs-010-tracer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: obs-010-tracer
  template:
    metadata:
      labels:
        app: obs-010-tracer
    spec:
      containers:
      - name: tracer
        image: obs-010-tracer:latest
        ports:
        - containerPort: 8000
        env:
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector:4317"
        - name: OTEL_SERVICE_NAME
          value: "obs-010-service"
        - name: OTEL_RESOURCE_ATTRIBUTES
          value: "service.name=obs-010-service,deployment.environment=production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
```

### OpenTelemetryコレクター

```yaml
# otel-collector.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  
  otlp/datadog:
    endpoint: "https://api.datadoghq.com"
    headers:
      "DD-API-KEY": "${DD_API_KEY}"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger, otlp/datadog]
```

### セキュリティ考慮事項

- **機密情報**: スパン属性に秘密情報を含めない
- **PII保護**: 個人識別情報をサニタイズ  
- **アクセス制御**: エクスポーターエンドポイントを保護
- **ネットワークセキュリティ**: トレースエクスポートにTLSを使用

### 監視の監視

可観測性インフラを監視:

- **トレースエクスポート成功率**: エクスポート失敗を監視
- **コレクターヘルス**: コレクターのリソース使用量を確認
- **ストレージ使用率**: トレースストレージの成長を監視
- **クエリパフォーマンス**: クエリレスポンス時間を追跡

## ライセンス

この実装はReq2Runベンチマークスイートの一部です。