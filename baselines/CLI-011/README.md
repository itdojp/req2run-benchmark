# CLI-011: Parallel Job Orchestrator with DAG Execution

A sophisticated command-line tool for orchestrating parallel job execution with DAG (Directed Acyclic Graph) dependencies, featuring resource management, retry logic, and real-time monitoring.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Workflow File  │───▶│   DAG Analyzer   │───▶│  Job Executor   │
│  (YAML/JSON)    │    │                  │    │                 │
│                 │    │ • Validation     │    │ • Resource Mgmt │
└─────────────────┘    │ • Cycle Detection│    │ • Retry Logic   │
                       │ • Level Planning │    │ • Process Mgmt  │
                       └──────────────────┘    └─────────────────┘
                               │                         │
                               ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Orchestrator   │◄───│  Live Monitor   │
                       │                  │    │                 │
                       │ • Parallel Exec  │    │ • Real-time UI  │
                       │ • Status Tracking│    │ • Progress Bars │
                       │ • Event Handling │    │ • Resource Stats│
                       └──────────────────┘    └─────────────────┘
```

## Key Features

### 🏗️ DAG-Based Execution
- **Dependency Resolution**: Automatic topological sorting of job dependencies
- **Cycle Detection**: Prevents circular dependencies with clear error messages
- **Parallel Execution**: Runs independent jobs concurrently up to resource limits
- **Critical Path Analysis**: Identifies longest execution path for optimization

### 🔄 Advanced Job Management
- **Multiple Job Types**: Command, script, Python code, and HTTP requests
- **Retry Logic**: Exponential backoff with configurable max attempts
- **Conditional Execution**: Skip jobs based on dependency failures
- **Resource Limits**: CPU, memory, and execution time constraints

### 📊 Real-Time Monitoring
- **Live Progress Display**: Rich terminal UI with progress bars and status
- **Resource Tracking**: Monitor CPU, memory usage across all running jobs
- **Event History**: Complete audit trail of all job state changes
- **Status Callbacks**: Extensible event system for custom monitoring

### ⚙️ Resource Management
- **Concurrent Job Limits**: Configurable maximum parallel job execution
- **Memory Management**: Track and limit memory usage per job
- **Process Lifecycle**: Proper cleanup and signal handling
- **Graceful Shutdown**: Clean termination with running job cleanup

## Quick Start

### Prerequisites

- Python 3.11+
- Dependencies: `pip install -r requirements.txt`

### Installation

```bash
# Clone and setup
cd baselines/CLI-011
pip install -r requirements.txt

# Verify installation
python src/main.py --help
```

### Basic Usage

```bash
# Create a sample workflow
python src/main.py create --name "My Pipeline" --output workflow.yaml

# Analyze workflow structure
python src/main.py analyze workflow.yaml

# Execute workflow with live monitoring
python src/main.py run workflow.yaml --max-concurrent 4

# Dry run to validate without execution
python src/main.py run workflow.yaml --dry-run
```

### Docker Usage

```bash
# Build container
docker build -t job-orchestrator .

# Run with mounted workflow
docker run -v $(pwd)/workflows:/app/workflows job-orchestrator run /app/workflows/sample.yaml

# Interactive mode
docker run -it job-orchestrator bash
```

## Workflow Definition

### YAML Format

```yaml
name: "CI/CD Pipeline"
version: "1.0.0"
description: "Build and deployment pipeline"

global_config:
  max_retries: 3
  timeout: 3600

jobs:
  - id: "build"
    name: "Build Application"
    job_type: "command"
    command: "make build"
    dependencies: []
    timeout: 300
    retry_config:
      max_attempts: 3
      initial_delay: 1.0
      backoff_factor: 2.0
    resource_limits:
      max_memory_mb: 1024
      max_execution_time: 600
    environment:
      NODE_ENV: "production"
    tags: ["build", "compile"]

  - id: "test"
    name: "Run Tests"
    job_type: "script"
    script_path: "./scripts/test.sh"
    dependencies: ["build"]
    timeout: 600

  - id: "deploy"
    name: "Deploy Application"
    job_type: "command"
    command: "kubectl apply -f deployment.yaml"
    dependencies: ["test"]
    timeout: 900
```

### Job Types

#### Command Jobs
```yaml
job_type: "command"
command: "echo 'Hello World' && ls -la"
working_directory: "/app"
environment:
  PATH: "/usr/local/bin:$PATH"
```

#### Script Jobs
```yaml
job_type: "script"
script_path: "./scripts/deploy.sh"
working_directory: "/app"
```

#### Python Jobs
```yaml
job_type: "python"
command: |
  import os
  print(f"Current directory: {os.getcwd()}")
  # Your Python code here
```

#### HTTP Jobs
```yaml
job_type: "http"
command: "https://api.example.com/health"
timeout: 30
```

## CLI Commands

### `run` - Execute Workflow

```bash
python src/main.py run workflow.yaml [OPTIONS]

Options:
  -c, --max-concurrent INTEGER  Maximum concurrent jobs [default: 4]
  --dry-run                    Validate workflow without execution
  -o, --output PATH            Output results to JSON file
  --live / --no-live          Show live progress display [default: True]
```

### `analyze` - Analyze DAG Structure

```bash
python src/main.py analyze workflow.yaml [OPTIONS]

Options:
  -o, --output PATH  Output analysis to JSON file
```

Example output:
```
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Property            ┃ Value               ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ Workflow Name       │ Sample CI/CD        │
│ Total Jobs          │ 14                  │
│ Valid DAG           │ ✓                   │
│ Has Cycles          │ ✓                   │
│ Execution Levels    │ 8                   │
│ Critical Path       │ 7                   │
│ Max Parallelism     │ 3                   │
└─────────────────────┴─────────────────────┘

Execution Order:
  Level 0: setup
  Level 1: install_deps
  Level 2: lint, build_frontend, build_backend
  Level 3: test_unit_frontend, test_unit_backend, security_scan
  ...
```

### `create` - Generate Sample Workflow

```bash
python src/main.py create --name "Pipeline Name" --output workflow.yaml
```

## Configuration

### Retry Configuration

```yaml
retry_config:
  max_attempts: 3        # Maximum retry attempts
  initial_delay: 1.0     # Initial delay in seconds
  max_delay: 60.0        # Maximum delay between retries
  backoff_factor: 2.0    # Exponential backoff multiplier
```

### Resource Limits

```yaml
resource_limits:
  max_memory_mb: 1024         # Maximum memory per job
  max_cpu_percent: 100.0      # CPU usage limit
  max_execution_time: 3600    # Timeout in seconds
  max_concurrent_jobs: 4      # Global concurrency limit
```

### Environment Variables

```yaml
environment:
  NODE_ENV: "production"
  API_URL: "https://api.example.com"
  DEBUG: "false"
```

## Monitoring and Status

### Live Display

The orchestrator provides a rich terminal interface showing:

- **Real-time job status** with progress bars
- **Resource usage** (CPU, memory, active jobs)
- **Execution timeline** with start/completion times
- **Error messages** and retry attempts

### Status Callbacks

```python
def status_callback(event_type: str, data: dict):
    if event_type == "job_started":
        print(f"Job {data['job_id']} started")
    elif event_type == "job_completed":
        print(f"Job {data['job_id']} completed")

orchestrator.add_status_callback(status_callback)
```

### Event Types

- `job_started` - Job execution begins
- `job_completed` - Job completes successfully
- `job_failed` - Job fails after all retries
- `job_cancelled` - Job cancelled by user
- `job_retrying` - Job failed, retrying
- `job_skipped` - Job skipped due to dependency failure

## Advanced Features

### Conditional Execution

Jobs can be skipped based on conditions:

```yaml
conditions:
  skip_if_failed: ["build"]  # Skip if build job failed
  only_if_branch: "main"     # Only run on main branch
```

### Job Tags and Filtering

```yaml
tags: ["build", "frontend", "critical"]
```

Use tags for selective execution or monitoring.

### DAG Visualization

Generate execution plans and critical path analysis:

```bash
python src/main.py analyze workflow.yaml --output analysis.json
```

### Custom Job Types

Extend the system with custom job types:

```python
from executor import JobExecutor

class CustomJobExecutor(JobExecutor):
    async def _execute_custom(self, job_execution):
        # Custom execution logic
        pass
```

## Error Handling

### Common Issues

1. **Circular Dependencies**
   ```
   Error: Circular dependency detected: job1 -> job2 -> job1
   ```
   Solution: Review dependency chain and remove cycles

2. **Missing Dependencies**
   ```
   Error: Job 'deploy' depends on non-existent job 'missing'
   ```
   Solution: Ensure all referenced job IDs exist

3. **Resource Exhaustion**
   ```
   Error: Insufficient resources to start job
   ```
   Solution: Increase limits or reduce concurrent jobs

4. **Job Timeouts**
   ```
   Error: Job timed out after 300 seconds
   ```
   Solution: Increase timeout or optimize job

### Debugging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python src/main.py run workflow.yaml
```

View detailed execution history:

```bash
python src/main.py run workflow.yaml --output results.json
cat results.json | jq '.jobs[] | select(.status == "failed")'
```

## Performance Tuning

### Concurrency Settings

```yaml
# Optimize for CPU-bound jobs
max_concurrent_jobs: $(nproc)

# Optimize for I/O-bound jobs  
max_concurrent_jobs: $(($(nproc) * 2))
```

### Resource Allocation

```yaml
resource_limits:
  max_memory_mb: 512      # Reduce for many small jobs
  max_execution_time: 300  # Set realistic timeouts
```

### DAG Optimization

- **Minimize critical path**: Parallelize independent operations
- **Balance levels**: Avoid too many jobs in single level
- **Resource awareness**: Consider memory/CPU requirements

## Testing

Run the included test suite:

```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# Full test suite
python -m pytest tests/ -v --cov=src
```

### Test Workflows

```bash
# Test with sample workflow
python src/main.py run config/sample_workflow.yaml

# Create test workflow
python src/main.py create --name "Test" --output test.yaml
python src/main.py run test.yaml --dry-run
```

## Production Deployment

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: job-orchestrator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: job-orchestrator
  template:
    metadata:
      labels:
        app: job-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: job-orchestrator:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2"
        volumeMounts:
        - name: workflows
          mountPath: /app/workflows
      volumes:
      - name: workflows
        configMap:
          name: workflow-config
```

### Security Considerations

- **Sandboxing**: Run jobs in isolated containers
- **Resource limits**: Prevent resource exhaustion attacks
- **Input validation**: Sanitize workflow definitions
- **Access control**: Restrict workflow modification capabilities

## License

This implementation is part of the Req2Run benchmark suite.