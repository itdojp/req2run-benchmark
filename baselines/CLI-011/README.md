# CLI-011: Parallel Job Orchestrator with DAG Execution

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

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

---

<a id="japanese"></a>
## 日本語

DAG（有向非巡回グラフ）依存関係を持つ並列ジョブ実行をオーケストレートするための洗練されたコマンドラインツール。リソース管理、リトライロジック、リアルタイム監視機能を備えています。

## アーキテクチャ概要

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ ワークフローファイル │───▶│   DAGアナライザー   │───▶│  ジョブエグゼキュータ  │
│  (YAML/JSON)    │    │                  │    │                 │
│                 │    │ • 検証           │    │ • リソース管理    │
└─────────────────┘    │ • サイクル検出     │    │ • リトライロジック │
                       │ • レベル計画      │    │ • プロセス管理    │
                       └──────────────────┘    └─────────────────┘
                               │                         │
                               ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  オーケストレーター  │◄───│  ライブモニター    │
                       │                  │    │                 │
                       │ • 並列実行        │    │ • リアルタイムUI  │
                       │ • ステータス追跡   │    │ • 進行状況バー    │
                       │ • イベント処理     │    │ • リソース統計    │
                       └──────────────────┘    └─────────────────┘
```

## 主要機能

### 🏗️ DAGベース実行
- **依存関係解決**: ジョブ依存関係の自動トポロジカルソート
- **サイクル検出**: 明確なエラーメッセージで循環依存を防止
- **並列実行**: リソース限界まで独立ジョブを同時実行
- **クリティカルパス分析**: 最適化のための最長実行パスを特定

### 🔄 高度なジョブ管理
- **複数のジョブタイプ**: コマンド、スクリプト、Pythonコード、HTTPリクエスト
- **リトライロジック**: 設定可能な最大試行回数での指数バックオフ
- **条件付き実行**: 依存関係の失敗に基づいてジョブをスキップ
- **リソース制限**: CPU、メモリ、実行時間の制約

### 📊 リアルタイム監視
- **ライブ進行状況表示**: 進行状況バーとステータス付きリッチターミナルUI
- **リソース追跡**: すべての実行中ジョブのCPU、メモリ使用量を監視
- **イベント履歴**: すべてのジョブ状態変更の完全な監査証跡
- **ステータスコールバック**: カスタム監視用の拡張可能なイベントシステム

### ⚙️ リソース管理
- **同時ジョブ制限**: 設定可能な最大並列ジョブ実行
- **メモリ管理**: ジョブごとのメモリ使用量の追跡と制限
- **プロセスライフサイクル**: 適切なクリーンアップとシグナル処理
- **グレースフルシャットダウン**: 実行中ジョブのクリーンアップでクリーン終了

## クイックスタート

### 前提条件

- Python 3.11+
- 依存関係: `pip install -r requirements.txt`

### インストール

```bash
# クローンとセットアップ
cd baselines/CLI-011
pip install -r requirements.txt

# インストール確認
python src/main.py --help
```

### 基本的な使用法

```bash
# サンプルワークフローを作成
python src/main.py create --name "My Pipeline" --output workflow.yaml

# ワークフロー構造を分析
python src/main.py analyze workflow.yaml

# ライブ監視でワークフローを実行
python src/main.py run workflow.yaml --max-concurrent 4

# 実行せずに検証するドライラン
python src/main.py run workflow.yaml --dry-run
```

### Docker使用法

```bash
# コンテナをビルド
docker build -t job-orchestrator .

# マウントされたワークフローで実行
docker run -v $(pwd)/workflows:/app/workflows job-orchestrator run /app/workflows/sample.yaml

# インタラクティブモード
docker run -it job-orchestrator bash
```

## ワークフロー定義

### YAML形式

```yaml
name: "CI/CDパイプライン"
version: "1.0.0"
description: "ビルドとデプロイメントパイプライン"

global_config:
  max_retries: 3
  timeout: 3600

jobs:
  - id: "build"
    name: "アプリケーションビルド"
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
    name: "テスト実行"
    job_type: "script"
    script_path: "./scripts/test.sh"
    dependencies: ["build"]
    timeout: 600

  - id: "deploy"
    name: "アプリケーションデプロイ"
    job_type: "command"
    command: "kubectl apply -f deployment.yaml"
    dependencies: ["test"]
    timeout: 900
```

### ジョブタイプ

#### コマンドジョブ
```yaml
job_type: "command"
command: "echo 'Hello World' && ls -la"
working_directory: "/app"
environment:
  PATH: "/usr/local/bin:$PATH"
```

#### スクリプトジョブ
```yaml
job_type: "script"
script_path: "./scripts/deploy.sh"
working_directory: "/app"
```

#### Pythonジョブ
```yaml
job_type: "python"
command: |
  import os
  print(f"現在のディレクトリ: {os.getcwd()}")
  # Pythonコードはここに
```

#### HTTPジョブ
```yaml
job_type: "http"
command: "https://api.example.com/health"
timeout: 30
```

## CLIコマンド

### `run` - ワークフロー実行

```bash
python src/main.py run workflow.yaml [OPTIONS]

オプション:
  -c, --max-concurrent INTEGER  最大同時ジョブ数 [デフォルト: 4]
  --dry-run                    実行せずにワークフローを検証
  -o, --output PATH            結果をJSONファイルに出力
  --live / --no-live          ライブ進行状況表示を表示 [デフォルト: True]
```

### `analyze` - DAG構造分析

```bash
python src/main.py analyze workflow.yaml [OPTIONS]

オプション:
  -o, --output PATH  分析をJSONファイルに出力
```

出力例:
```
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ プロパティ           ┃ 値                  ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ ワークフロー名        │ サンプルCI/CD        │
│ 総ジョブ数           │ 14                  │
│ 有効なDAG           │ ✓                   │
│ サイクル有無         │ ✓                   │
│ 実行レベル           │ 8                   │
│ クリティカルパス     │ 7                   │
│ 最大並列度           │ 3                   │
└─────────────────────┴─────────────────────┘

実行順序:
  レベル 0: setup
  レベル 1: install_deps
  レベル 2: lint, build_frontend, build_backend
  レベル 3: test_unit_frontend, test_unit_backend, security_scan
  ...
```

### `create` - サンプルワークフロー生成

```bash
python src/main.py create --name "パイプライン名" --output workflow.yaml
```

## 設定

### リトライ設定

```yaml
retry_config:
  max_attempts: 3        # 最大リトライ試行回数
  initial_delay: 1.0     # 初期遅延（秒）
  max_delay: 60.0        # リトライ間の最大遅延
  backoff_factor: 2.0    # 指数バックオフ乗数
```

### リソース制限

```yaml
resource_limits:
  max_memory_mb: 1024         # ジョブごとの最大メモリ
  max_cpu_percent: 100.0      # CPU使用制限
  max_execution_time: 3600    # タイムアウト（秒）
  max_concurrent_jobs: 4      # グローバル同時実行制限
```

### 環境変数

```yaml
environment:
  NODE_ENV: "production"
  API_URL: "https://api.example.com"
  DEBUG: "false"
```

## 監視とステータス

### ライブ表示

オーケストレーターは以下を示すリッチターミナルインターフェースを提供:

- **リアルタイムジョブステータス** と進行状況バー
- **リソース使用量** (CPU、メモリ、アクティブジョブ)
- **実行タイムライン** 開始/完了時刻付き
- **エラーメッセージ** とリトライ試行

### ステータスコールバック

```python
def status_callback(event_type: str, data: dict):
    if event_type == "job_started":
        print(f"ジョブ {data['job_id']} 開始")
    elif event_type == "job_completed":
        print(f"ジョブ {data['job_id']} 完了")

orchestrator.add_status_callback(status_callback)
```

### イベントタイプ

- `job_started` - ジョブ実行開始
- `job_completed` - ジョブ正常完了
- `job_failed` - すべてのリトライ後にジョブ失敗
- `job_cancelled` - ユーザーによりジョブキャンセル
- `job_retrying` - ジョブ失敗、リトライ中
- `job_skipped` - 依存関係の失敗によりジョブスキップ

## 高度な機能

### 条件付き実行

条件に基づいてジョブをスキップ可能:

```yaml
conditions:
  skip_if_failed: ["build"]  # ビルドジョブが失敗した場合スキップ
  only_if_branch: "main"     # mainブランチでのみ実行
```

### ジョブタグとフィルタリング

```yaml
tags: ["build", "frontend", "critical"]
```

選択的実行または監視にタグを使用。

### DAG視覚化

実行計画とクリティカルパス分析を生成:

```bash
python src/main.py analyze workflow.yaml --output analysis.json
```

### カスタムジョブタイプ

カスタムジョブタイプでシステムを拡張:

```python
from executor import JobExecutor

class CustomJobExecutor(JobExecutor):
    async def _execute_custom(self, job_execution):
        # カスタム実行ロジック
        pass
```

## エラー処理

### 一般的な問題

1. **循環依存**
   ```
   エラー: 循環依存が検出されました: job1 -> job2 -> job1
   ```
   解決策: 依存関係チェーンを確認し、サイクルを削除

2. **依存関係の欠落**
   ```
   エラー: ジョブ 'deploy' が存在しないジョブ 'missing' に依存
   ```
   解決策: すべての参照されるジョブIDが存在することを確認

3. **リソース枯渇**
   ```
   エラー: ジョブを開始するための不十分なリソース
   ```
   解決策: 制限を増やすか同時ジョブを削減

4. **ジョブタイムアウト**
   ```
   エラー: 300秒後にジョブがタイムアウト
   ```
   解決策: タイムアウトを増やすかジョブを最適化

### デバッグ

デバッグログを有効化:

```bash
export LOG_LEVEL=DEBUG
python src/main.py run workflow.yaml
```

詳細な実行履歴を表示:

```bash
python src/main.py run workflow.yaml --output results.json
cat results.json | jq '.jobs[] | select(.status == "failed")'
```

## パフォーマンスチューニング

### 同時実行設定

```yaml
# CPUバウンドジョブ用に最適化
max_concurrent_jobs: $(nproc)

# I/Oバウンドジョブ用に最適化
max_concurrent_jobs: $(($(nproc) * 2))
```

### リソース割り当て

```yaml
resource_limits:
  max_memory_mb: 512      # 多くの小さなジョブ用に削減
  max_execution_time: 300  # 現実的なタイムアウトを設定
```

### DAG最適化

- **クリティカルパスの最小化**: 独立した操作を並列化
- **レベルのバランス**: 単一レベルに多すぎるジョブを避ける
- **リソース認識**: メモリ/CPU要件を考慮

## テスト

含まれるテストスイートを実行:

```bash
# ユニットテスト
python -m pytest tests/unit/

# 統合テスト
python -m pytest tests/integration/

# 完全なテストスイート
python -m pytest tests/ -v --cov=src
```

### テストワークフロー

```bash
# サンプルワークフローでテスト
python src/main.py run config/sample_workflow.yaml

# テストワークフローを作成
python src/main.py create --name "Test" --output test.yaml
python src/main.py run test.yaml --dry-run
```

## 本番デプロイメント

### Kubernetesデプロイメント

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

### セキュリティ考慮事項

- **サンドボックス化**: 分離されたコンテナでジョブを実行
- **リソース制限**: リソース枯渇攻撃を防止
- **入力検証**: ワークフロー定義をサニタイズ
- **アクセス制御**: ワークフロー変更機能を制限

## ライセンス

この実装はReq2Runベンチマークスイートの一部です。