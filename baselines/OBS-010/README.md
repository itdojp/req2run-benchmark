# OBS-010: OpenTelemetry Comprehensive Tracing Coverage

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