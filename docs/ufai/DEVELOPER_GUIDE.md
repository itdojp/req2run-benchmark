# UFAI Developer Guide / UFAI開発者ガイド

## Table of Contents / 目次

1. [Overview / 概要](#overview--概要)
2. [Architecture Deep Dive / アーキテクチャ詳細](#architecture-deep-dive--アーキテクチャ詳細)
3. [Creating Framework Adapters / フレームワークアダプタの作成](#creating-framework-adapters--フレームワークアダプタの作成)
4. [Advanced Configuration / 高度な設定](#advanced-configuration--高度な設定)
5. [Custom Metrics / カスタムメトリクス](#custom-metrics--カスタムメトリクス)
6. [Extending UFAI / UFAIの拡張](#extending-ufai--ufaiの拡張)
7. [Troubleshooting / トラブルシューティング](#troubleshooting--トラブルシューティング)

## Overview / 概要

The Universal Framework Adapter Interface (UFAI) is designed to enable any web framework to participate in standardized benchmarking. As a developer, you can integrate your framework, contribute improvements, or build custom extensions.

UFAI（Universal Framework Adapter Interface）は、あらゆるWebフレームワークが標準化されたベンチマークに参加できるように設計されています。開発者として、フレームワークの統合、改善の貢献、カスタム拡張の構築が可能です。

## Architecture Deep Dive / アーキテクチャ詳細

### Core Components

```
UFAI System
├── bench CLI                 # Command-line interface
│   ├── BenchmarkRunner      # Main execution engine
│   ├── ConfigLoader         # YAML configuration parser
│   └── ResultsGenerator     # Output formatting
├── Validation Layer
│   ├── SchemaValidator      # JSON Schema validation
│   ├── CommandValidator     # Security checks
│   └── ComplianceChecker    # Level verification
├── Execution Engine
│   ├── StageRunner          # Individual stage execution
│   ├── MetricsCollector     # Performance data gathering
│   └── ErrorHandler         # Failure recovery
└── Reporting System
    ├── JSONExporter         # results.json generation
    ├── HTMLGenerator        # Visual reports
    └── MetricsAggregator    # Statistical analysis
```

### Data Flow

```python
# 1. Configuration Loading
config = load_bench_yaml("bench.yaml")
validate_against_schema(config, "bench-schema.json")

# 2. Stage Execution
for stage in ["build", "test", "performance", "security"]:
    if stage in config["commands"]:
        result = execute_stage(config["commands"][stage])
        collect_metrics(result)

# 3. Results Generation
results = {
    "framework": config["framework"],
    "stages": stage_results,
    "overall": calculate_score(stage_results)
}
save_results(results, "results.json")
```

## Creating Framework Adapters / フレームワークアダプタの作成

### Step 1: Framework Analysis

Before creating an adapter, analyze your framework's characteristics:

```python
# framework_analyzer.py
import os
import subprocess
import json

class FrameworkAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path
        
    def detect_language(self):
        """Detect primary programming language."""
        files = {
            "package.json": "javascript",
            "requirements.txt": "python",
            "go.mod": "go",
            "pom.xml": "java",
            "Gemfile": "ruby",
            "composer.json": "php"
        }
        
        for file, language in files.items():
            if os.path.exists(os.path.join(self.project_path, file)):
                return language
        return "other"
    
    def detect_test_framework(self):
        """Detect testing framework."""
        # Implementation specific to each language
        pass
    
    def detect_build_system(self):
        """Detect build system."""
        # Implementation specific to each language
        pass
```

### Step 2: Custom Adapter Implementation

Create a custom adapter class that interfaces with UFAI:

```python
# custom_adapter.py
from typing import Dict, Any, Optional
import os
import subprocess
import json
import time

class CustomFrameworkAdapter:
    """Custom adapter for specific framework requirements."""
    
    def __init__(self, config_path: str = "bench.yaml"):
        self.config = self.load_config(config_path)
        self.metrics = {}
        
    def prepare_environment(self):
        """Set up environment before benchmarking."""
        # Install dependencies
        self.run_command("pip install -r requirements.txt")
        
        # Set environment variables
        os.environ.update(self.config.get("environment", {}).get("variables", {}))
        
        # Start required services
        self.start_services()
    
    def start_services(self):
        """Start any required background services."""
        services = self.config.get("environment", {}).get("services", [])
        for service in services:
            # Docker example
            subprocess.run(f"docker run -d {service}", shell=True)
    
    def run_build(self) -> Dict[str, Any]:
        """Execute build stage with custom logic."""
        start_time = time.time()
        
        # Pre-build hooks
        self.execute_hooks("pre_build")
        
        # Main build
        result = self.run_command(self.config["commands"]["build"])
        
        # Post-build hooks
        self.execute_hooks("post_build")
        
        # Collect metrics
        duration = time.time() - start_time
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "duration": duration,
            "metrics": self.collect_build_metrics()
        }
    
    def collect_build_metrics(self) -> Dict[str, Any]:
        """Collect build-specific metrics."""
        metrics = {}
        
        # Artifact size
        if os.path.exists("dist"):
            metrics["artifact_size_mb"] = self.get_directory_size("dist") / (1024 * 1024)
        
        # Dependency count
        if os.path.exists("package-lock.json"):
            with open("package-lock.json") as f:
                data = json.load(f)
                metrics["dependencies"] = len(data.get("dependencies", {}))
        
        return metrics
    
    def run_performance(self) -> Dict[str, Any]:
        """Execute performance tests with custom profiling."""
        # Start application
        app_process = self.start_application()
        
        # Warm-up phase
        self.warmup_application()
        
        # Run performance tests
        results = self.execute_performance_tests()
        
        # Collect system metrics
        results["system_metrics"] = self.collect_system_metrics()
        
        # Stop application
        self.stop_application(app_process)
        
        return results
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics during performance testing."""
        import psutil
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_mb": psutil.virtual_memory().used / (1024 * 1024),
            "disk_io": self.get_disk_io_stats(),
            "network_io": self.get_network_stats()
        }
    
    def execute_hooks(self, hook_type: str):
        """Execute custom hooks at various stages."""
        hooks = self.config.get("hooks", {}).get(hook_type, [])
        for hook in hooks:
            subprocess.run(hook, shell=True)
```

### Step 3: Advanced Metrics Collection

Implement sophisticated metrics collection:

```python
# metrics_collector.py
import time
import threading
import queue
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class MetricPoint:
    timestamp: float
    name: str
    value: float
    tags: Dict[str, str]

class MetricsCollector:
    """Advanced metrics collection system."""
    
    def __init__(self):
        self.metrics_queue = queue.Queue()
        self.collectors = []
        self.running = False
        
    def register_collector(self, collector):
        """Register a custom metric collector."""
        self.collectors.append(collector)
    
    def start(self):
        """Start metrics collection."""
        self.running = True
        for collector in self.collectors:
            thread = threading.Thread(target=self._run_collector, args=(collector,))
            thread.daemon = True
            thread.start()
    
    def _run_collector(self, collector):
        """Run a single collector in a thread."""
        while self.running:
            try:
                metric = collector.collect()
                if metric:
                    self.metrics_queue.put(metric)
            except Exception as e:
                print(f"Collector error: {e}")
            time.sleep(collector.interval)
    
    def stop(self):
        """Stop metrics collection."""
        self.running = False
    
    def get_metrics(self) -> List[MetricPoint]:
        """Get all collected metrics."""
        metrics = []
        while not self.metrics_queue.empty():
            metrics.append(self.metrics_queue.get())
        return metrics

# Custom collectors
class CPUCollector:
    interval = 1.0
    
    def collect(self) -> MetricPoint:
        import psutil
        return MetricPoint(
            timestamp=time.time(),
            name="cpu_usage",
            value=psutil.cpu_percent(),
            tags={"type": "system"}
        )

class ResponseTimeCollector:
    interval = 0.1
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
    
    def collect(self) -> MetricPoint:
        import requests
        start = time.time()
        try:
            response = requests.get(self.endpoint)
            latency = (time.time() - start) * 1000  # ms
            return MetricPoint(
                timestamp=start,
                name="response_time",
                value=latency,
                tags={"endpoint": self.endpoint, "status": str(response.status_code)}
            )
        except:
            return None
```

## Advanced Configuration / 高度な設定

### Dynamic Configuration

Create dynamic configurations based on environment:

```yaml
# bench.dynamic.yaml
version: "1.0"
framework:
  name: "MyFramework"
  version: "${FRAMEWORK_VERSION:-1.0.0}"

commands:
  build:
    script: |
      {% if ENV == 'production' %}
      npm run build:prod
      {% else %}
      npm run build:dev
      {% endif %}
    
  performance:
    script: "npm run perf"
    endpoint: "${BENCHMARK_ENDPOINT:-http://localhost:3000}"
    concurrency: "${BENCHMARK_CONCURRENCY:-100}"
    duration: "${BENCHMARK_DURATION:-60}"

profiles:
  development:
    environment:
      NODE_ENV: "development"
      DEBUG: "true"
  
  production:
    environment:
      NODE_ENV: "production"
      DEBUG: "false"
    commands:
      build:
        script: "npm run build:prod --optimize"
```

### Configuration Processor

```python
# config_processor.py
import os
import re
import yaml
from jinja2 import Template

class ConfigProcessor:
    """Process dynamic configuration files."""
    
    def __init__(self, config_file: str, profile: str = None):
        self.config_file = config_file
        self.profile = profile
        
    def load(self) -> Dict[str, Any]:
        """Load and process configuration."""
        with open(self.config_file) as f:
            content = f.read()
        
        # Process environment variables
        content = self.process_env_vars(content)
        
        # Process Jinja2 templates
        content = self.process_templates(content)
        
        # Load YAML
        config = yaml.safe_load(content)
        
        # Apply profile
        if self.profile and "profiles" in config:
            config = self.apply_profile(config, self.profile)
        
        return config
    
    def process_env_vars(self, content: str) -> str:
        """Replace environment variables."""
        pattern = r'\$\{(\w+)(?::([^}]*))?\}'
        
        def replacer(match):
            var_name = match.group(1)
            default = match.group(2) or ""
            return os.environ.get(var_name, default)
        
        return re.sub(pattern, replacer, content)
    
    def process_templates(self, content: str) -> str:
        """Process Jinja2 templates."""
        template = Template(content)
        return template.render(**os.environ)
    
    def apply_profile(self, config: Dict, profile: str) -> Dict:
        """Apply configuration profile."""
        if profile in config.get("profiles", {}):
            profile_config = config["profiles"][profile]
            # Merge profile into main config
            config = self.deep_merge(config, profile_config)
        return config
    
    def deep_merge(self, base: Dict, overlay: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.deep_merge(result[key], value)
            else:
                result[key] = value
        return result
```

## Custom Metrics / カスタムメトリクス

### Creating Custom Metric Providers

```python
# custom_metrics.py
from abc import ABC, abstractmethod
from typing import Dict, Any
import os
import subprocess
import json

class MetricProvider(ABC):
    """Base class for custom metric providers."""
    
    @abstractmethod
    def name(self) -> str:
        """Return metric provider name."""
        pass
    
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Collect metrics."""
        pass

class CodeQualityMetrics(MetricProvider):
    """Collect code quality metrics."""
    
    def name(self) -> str:
        return "code_quality"
    
    def collect(self) -> Dict[str, Any]:
        metrics = {}
        
        # Cyclomatic complexity
        result = subprocess.run(
            "radon cc . -j", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            metrics["avg_complexity"] = self.calculate_avg_complexity(data)
        
        # Code coverage
        result = subprocess.run(
            "coverage report --format=json",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            metrics["coverage_percent"] = data.get("totals", {}).get("percent_covered", 0)
        
        # Technical debt (using SonarQube API if available)
        metrics["technical_debt_hours"] = self.get_technical_debt()
        
        return metrics
    
    def calculate_avg_complexity(self, data: Dict) -> float:
        """Calculate average cyclomatic complexity."""
        total = 0
        count = 0
        for file_data in data.values():
            for func in file_data:
                total += func.get("complexity", 0)
                count += 1
        return total / count if count > 0 else 0
    
    def get_technical_debt(self) -> float:
        """Get technical debt from SonarQube or similar."""
        # Implementation depends on your setup
        return 0.0

class DependencyMetrics(MetricProvider):
    """Analyze dependency metrics."""
    
    def name(self) -> str:
        return "dependencies"
    
    def collect(self) -> Dict[str, Any]:
        metrics = {}
        
        # For Node.js projects
        if os.path.exists("package.json"):
            metrics.update(self.analyze_npm_dependencies())
        
        # For Python projects
        if os.path.exists("requirements.txt"):
            metrics.update(self.analyze_pip_dependencies())
        
        return metrics
    
    def analyze_npm_dependencies(self) -> Dict[str, Any]:
        """Analyze npm dependencies."""
        result = subprocess.run(
            "npm audit --json",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "npm_vulnerabilities": data.get("metadata", {}).get("vulnerabilities", {}),
                "npm_dependencies_count": data.get("metadata", {}).get("dependencies", 0)
            }
        return {}
    
    def analyze_pip_dependencies(self) -> Dict[str, Any]:
        """Analyze pip dependencies."""
        result = subprocess.run(
            "pip-audit --format json",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "pip_vulnerabilities": len(data.get("vulnerabilities", [])),
                "pip_dependencies_count": len(data.get("dependencies", []))
            }
        return {}
```

### Integrating Custom Metrics

```python
# bench_extended.py
#!/usr/bin/env python3
"""Extended bench CLI with custom metrics."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from bench import BenchmarkRunner
from custom_metrics import CodeQualityMetrics, DependencyMetrics

class ExtendedBenchmarkRunner(BenchmarkRunner):
    """Extended runner with custom metrics."""
    
    def __init__(self, config_path: str = "bench.yaml"):
        super().__init__(config_path)
        self.metric_providers = [
            CodeQualityMetrics(),
            DependencyMetrics()
        ]
    
    def run_all(self) -> bool:
        """Run all stages with custom metrics."""
        # Run standard stages
        success = super().run_all()
        
        # Collect custom metrics
        custom_metrics = {}
        for provider in self.metric_providers:
            try:
                metrics = provider.collect()
                custom_metrics[provider.name()] = metrics
            except Exception as e:
                print(f"Error collecting {provider.name()} metrics: {e}")
        
        # Add to results
        self.results["custom_metrics"] = custom_metrics
        
        return success

if __name__ == "__main__":
    runner = ExtendedBenchmarkRunner()
    runner.run_all()
    runner.save_results()
    runner.generate_report()
```

## Extending UFAI / UFAIの拡張

### Creating Plugins

Develop plugins to extend UFAI functionality:

```python
# ufai_plugin.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import importlib
import os

class UFAIPlugin(ABC):
    """Base class for UFAI plugins."""
    
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    def on_init(self, runner):
        """Called when runner is initialized."""
        pass
    
    def on_stage_start(self, stage: str):
        """Called before a stage starts."""
        pass
    
    def on_stage_complete(self, stage: str, result: Dict[str, Any]):
        """Called after a stage completes."""
        pass
    
    def on_complete(self, results: Dict[str, Any]):
        """Called when all stages complete."""
        pass

class GitHubIntegrationPlugin(UFAIPlugin):
    """Plugin to integrate with GitHub."""
    
    def name(self) -> str:
        return "github_integration"
    
    def version(self) -> str:
        return "1.0.0"
    
    def on_complete(self, results: Dict[str, Any]):
        """Post results to GitHub."""
        import requests
        
        # Create GitHub comment
        if os.environ.get("GITHUB_TOKEN"):
            self.post_github_comment(results)
        
        # Update GitHub status
        if os.environ.get("GITHUB_SHA"):
            self.update_github_status(results)
    
    def post_github_comment(self, results: Dict[str, Any]):
        """Post benchmark results as PR comment."""
        token = os.environ["GITHUB_TOKEN"]
        repo = os.environ.get("GITHUB_REPOSITORY")
        pr_number = os.environ.get("GITHUB_PR_NUMBER")
        
        if not (repo and pr_number):
            return
        
        comment = self.format_results_comment(results)
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        response = requests.post(url, headers=headers, json={"body": comment})
    
    def format_results_comment(self, results: Dict[str, Any]) -> str:
        """Format results as Markdown comment."""
        return f"""## Benchmark Results

**Framework**: {results['framework']['name']} v{results['framework'].get('version', 'unknown')}
**Overall Score**: {results['overall']['score']}% ({results['overall']['grade']})

### Stage Results
| Stage | Status | Duration | Score |
|-------|--------|----------|-------|
{self.format_stage_table(results['stages'])}

### Performance Metrics
- Throughput: {results['stages'].get('performance', {}).get('metrics', {}).get('requests_per_second', 'N/A')} req/s
- Latency P95: {results['stages'].get('performance', {}).get('metrics', {}).get('latency_p95', 'N/A')} ms

Generated by UFAI v{results.get('version', '1.0')}
"""

class PluginManager:
    """Manage UFAI plugins."""
    
    def __init__(self):
        self.plugins: List[UFAIPlugin] = []
    
    def load_plugin(self, plugin_path: str):
        """Load a plugin from file."""
        spec = importlib.util.spec_from_file_location("plugin", plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin classes
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, UFAIPlugin) and obj != UFAIPlugin:
                plugin = obj()
                self.plugins.append(plugin)
                print(f"Loaded plugin: {plugin.name()} v{plugin.version()}")
    
    def load_plugins_from_directory(self, directory: str):
        """Load all plugins from a directory."""
        if not os.path.exists(directory):
            return
        
        for filename in os.listdir(directory):
            if filename.endswith("_plugin.py"):
                self.load_plugin(os.path.join(directory, filename))
    
    def trigger_event(self, event: str, *args, **kwargs):
        """Trigger an event on all plugins."""
        for plugin in self.plugins:
            method = getattr(plugin, event, None)
            if method:
                try:
                    method(*args, **kwargs)
                except Exception as e:
                    print(f"Plugin {plugin.name()} error in {event}: {e}")
```

## Troubleshooting / トラブルシューティング

### Common Issues and Solutions

#### 1. Schema Validation Failures

```python
# schema_debugger.py
import json
import yaml
import jsonschema
from jsonschema import Draft7Validator

def debug_schema_validation(config_file: str, schema_file: str):
    """Debug schema validation issues."""
    
    # Load files
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    with open(schema_file) as f:
        schema = json.load(f)
    
    # Create validator
    validator = Draft7Validator(schema)
    
    # Check for errors
    errors = sorted(validator.iter_errors(config), key=lambda e: e.path)
    
    if errors:
        print("Validation Errors Found:")
        for error in errors:
            print(f"\nPath: {' -> '.join(str(p) for p in error.path)}")
            print(f"Message: {error.message}")
            print(f"Schema Path: {' -> '.join(str(p) for p in error.schema_path)}")
            
            # Suggest fix
            suggest_fix(error)
    else:
        print("Configuration is valid!")

def suggest_fix(error):
    """Suggest fixes for common validation errors."""
    if "enum" in error.schema:
        print(f"Suggestion: Value must be one of: {error.schema['enum']}")
    elif "type" in error.schema:
        print(f"Suggestion: Value must be of type: {error.schema['type']}")
    elif "required" in error.message:
        print(f"Suggestion: Add the missing required field")
```

#### 2. Performance Testing Issues

```python
# performance_debugger.py
import time
import requests
from typing import Dict, Any

class PerformanceDebugger:
    """Debug performance testing issues."""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
    
    def check_endpoint_health(self) -> Dict[str, Any]:
        """Check if endpoint is responding correctly."""
        results = {
            "endpoint": self.endpoint,
            "checks": []
        }
        
        # Basic connectivity
        try:
            response = requests.get(self.endpoint, timeout=5)
            results["checks"].append({
                "name": "connectivity",
                "status": "pass",
                "response_code": response.status_code
            })
        except requests.RequestException as e:
            results["checks"].append({
                "name": "connectivity",
                "status": "fail",
                "error": str(e)
            })
            return results
        
        # Response time
        start = time.time()
        response = requests.get(self.endpoint)
        latency = (time.time() - start) * 1000
        
        results["checks"].append({
            "name": "response_time",
            "status": "pass" if latency < 1000 else "warning",
            "latency_ms": latency
        })
        
        # Concurrent requests
        results["checks"].append(self.check_concurrent_requests())
        
        return results
    
    def check_concurrent_requests(self) -> Dict[str, Any]:
        """Test concurrent request handling."""
        import concurrent.futures
        
        def make_request():
            try:
                response = requests.get(self.endpoint, timeout=5)
                return response.status_code == 200
            except:
                return False
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]
        
        success_rate = sum(results) / len(results) * 100
        
        return {
            "name": "concurrent_requests",
            "status": "pass" if success_rate >= 90 else "fail",
            "success_rate": success_rate
        }
```

#### 3. Docker Container Issues

```bash
#!/bin/bash
# docker_debugger.sh

echo "UFAI Docker Debugging Script"
echo "============================"

# Check Docker daemon
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running"
    exit 1
fi

# Check image exists
IMAGE="ufai/bench:latest"
if ! docker image inspect $IMAGE > /dev/null 2>&1; then
    echo "ERROR: Docker image $IMAGE not found"
    echo "Run: docker build -t $IMAGE adapters/universal/"
    exit 1
fi

# Test container
echo "Testing container..."
docker run --rm $IMAGE version

# Check port availability
check_port() {
    local port=$1
    if nc -z localhost $port 2>/dev/null; then
        echo "WARNING: Port $port is already in use"
        return 1
    fi
    return 0
}

echo "Checking required ports..."
for port in 8000 5514 514; do
    if check_port $port; then
        echo "  Port $port: Available"
    else
        echo "  Port $port: In use"
    fi
done

# Test with sample config
echo "Testing with sample configuration..."
cat > test-bench.yaml << EOF
version: "1.0"
framework:
  name: "TestFramework"
  language: "python"
commands:
  build: "echo 'Building...'"
  test: "echo 'Testing...'"
EOF

docker run --rm -v $(pwd):/app $IMAGE validate
```

### Debug Mode

Enable debug mode for detailed output:

```python
# bench_debug.py
import os
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bench_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class DebugBenchmarkRunner(BenchmarkRunner):
    """Benchmark runner with debug capabilities."""
    
    def run_command(self, cmd_config: Any, stage: str) -> Dict[str, Any]:
        """Run command with detailed logging."""
        logging.debug(f"Starting stage: {stage}")
        logging.debug(f"Command config: {cmd_config}")
        
        # Log environment
        logging.debug(f"Environment variables: {os.environ}")
        
        # Run command
        result = super().run_command(cmd_config, stage)
        
        # Log result
        logging.debug(f"Stage {stage} result: {result}")
        
        # Save debug information
        self.save_debug_info(stage, result)
        
        return result
    
    def save_debug_info(self, stage: str, result: Dict[str, Any]):
        """Save detailed debug information."""
        debug_dir = "bench_debug"
        os.makedirs(debug_dir, exist_ok=True)
        
        # Save stage output
        with open(f"{debug_dir}/{stage}_output.json", 'w') as f:
            json.dump(result, f, indent=2)
        
        # Save stdout/stderr
        if "stdout" in result:
            with open(f"{debug_dir}/{stage}_stdout.txt", 'w') as f:
                f.write(result["stdout"])
        
        if "stderr" in result:
            with open(f"{debug_dir}/{stage}_stderr.txt", 'w') as f:
                f.write(result["stderr"])
```

## Best Practices / ベストプラクティス

### 1. Configuration Management

- Use version control for `bench.yaml`
- Separate environment-specific settings
- Document all custom configurations
- Validate configurations in CI/CD

### 2. Performance Optimization

- Warm up applications before testing
- Use consistent test data
- Monitor system resources
- Run multiple iterations for accuracy

### 3. Security Considerations

- Never commit secrets in `bench.yaml`
- Use environment variables for sensitive data
- Validate all command inputs
- Run benchmarks in isolated environments

### 4. Continuous Integration

```yaml
# .github/workflows/benchmark.yml
name: UFAI Benchmark

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker
        uses: docker/setup-buildx-action@v3
      
      - name: Run UFAI Benchmark
        run: |
          docker run --rm \
            -v ${{ github.workspace }}:/app \
            -e GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }} \
            -e GITHUB_REPOSITORY=${{ github.repository }} \
            -e GITHUB_PR_NUMBER=${{ github.event.pull_request.number }} \
            ufai/bench:latest all
      
      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: results.json
      
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('results.json', 'utf8'));
            
            const comment = `## Benchmark Results
            Score: ${results.overall.score}%
            Grade: ${results.overall.grade}`;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

## Contributing to UFAI / UFAIへの貢献

### Development Setup

```bash
# Clone repository
git clone https://github.com/itdojp/req2run-benchmark.git
cd req2run-benchmark

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting
black adapters/universal/
flake8 adapters/universal/
mypy adapters/universal/
```

### Submitting Improvements

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style Guidelines

- Follow PEP 8 for Python code
- Use type hints where possible
- Document all public functions
- Include docstring examples
- Write comprehensive tests

## Support Resources / サポートリソース

- **GitHub Issues**: https://github.com/itdojp/req2run-benchmark/issues
- **Documentation**: https://github.com/itdojp/req2run-benchmark/tree/main/docs/ufai
- **Examples**: https://github.com/itdojp/req2run-benchmark/tree/main/adapters/examples
- **Community Discord**: (Coming soon)

---

*This guide is maintained by the Req2Run team. For questions or contributions, please open an issue on GitHub.*