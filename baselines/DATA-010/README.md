# DATA-010: Stream Processing with Windowing and State

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

A production-grade stream processing system implementing windowing operations, state management, watermark tracking, and exactly-once processing semantics.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Event Sources │───▶│ Stream Processor │───▶│  Event Sinks    │
│                 │    │                  │    │                 │
│ • Mock Events   │    │ • Windowing      │    │ • Console       │
│ • File Sources  │    │ • State Store    │    │ • File Output   │
│ • Kafka (TODO)  │    │ • Watermarks     │    │ • Metrics       │
└─────────────────┘    │ • Pipelines      │    └─────────────────┘
                       └──────────────────┘
                               │
                               ▼
                       ┌──────────────────┐
                       │   API Server     │
                       │ • REST API       │
                       │ • Metrics        │
                       │ • Monitoring     │
                       └──────────────────┘
```

## Key Features

### 🔄 Stream Processing
- **Exactly-once processing semantics** with offset tracking
- **Backpressure handling** with configurable queue sizes
- **Pipeline-based architecture** for multiple processing workflows
- **Asynchronous processing** with configurable parallelism

### 🪟 Windowing Operations
- **Tumbling Windows**: Fixed-size, non-overlapping time windows
- **Sliding Windows**: Fixed-size windows with configurable slide intervals
- **Session Windows**: Dynamic windows based on activity gaps
- **Late data handling** with configurable allowed lateness

### 💾 State Management
- **Persistent state storage** using RocksDB (with DiskCache fallback)
- **Checkpointing** for fault tolerance and recovery
- **State scanning** with prefix-based queries
- **Automatic cleanup** of expired state

### 🌊 Watermark Tracking
- **Event-time processing** with watermark-based progress tracking
- **Per-partition watermarks** for parallel processing
- **Late event detection** and handling
- **Configurable watermark delays** for late data tolerance

### 📊 Monitoring & Metrics
- **Prometheus metrics** (when available) with comprehensive counters and gauges
- **REST API** for real-time monitoring and control
- **Performance tracking** with latency and throughput metrics
- **Pipeline statistics** and health checks

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create configuration directory
mkdir -p config

# Copy default configuration
cp config/stream.yaml.example config/stream.yaml
```

### Running the Application

```bash
# Start with default configuration
python src/main.py

# Start with custom configuration
python src/main.py --config config/custom.yaml

# Run in Docker
docker build -t data-010-stream-processor .
docker run -p 8080:8080 -p 9090:9090 data-010-stream-processor
```

### Testing the System

```bash
# Check system health
curl http://localhost:8080/health

# View current status
curl http://localhost:8080/status

# List active pipelines
curl http://localhost:8080/pipelines

# Monitor metrics (Prometheus format)
curl http://localhost:9090/metrics
```

## Configuration

### Basic Configuration

```yaml
# config/stream.yaml
app_name: "My Stream Processor"
debug: false

processing:
  parallelism: 4
  queue_size: 10000
  checkpoint_interval: 30.0

windowing:
  windows:
    - type: "tumbling"
      size_ms: 60000  # 1 minute
      allowed_lateness_ms: 5000
```

### Window Types

#### Tumbling Windows
```yaml
- type: "tumbling"
  size_ms: 60000        # Window size: 1 minute
  allowed_lateness_ms: 5000  # Late data tolerance: 5 seconds
```

#### Sliding Windows
```yaml
- type: "sliding"
  size_ms: 300000       # Window size: 5 minutes
  slide_ms: 30000       # Slide interval: 30 seconds
  allowed_lateness_ms: 10000
```

#### Session Windows
```yaml
- type: "session"
  gap_ms: 30000         # Inactivity gap: 30 seconds
  allowed_lateness_ms: 15000
```

## API Reference

### Health & Status

- `GET /health` - System health check
- `GET /status` - Detailed system status and statistics

### Pipeline Management

- `GET /pipelines` - List all pipelines
- `POST /pipelines/{id}/start` - Start a specific pipeline
- `POST /pipelines/{id}/stop` - Stop a specific pipeline
- `GET /pipelines/{id}/stats` - Get pipeline statistics

### Monitoring

- `GET /watermarks` - Current watermark information
- `GET /state` - State store information
- `GET /windows` - Active windows information
- `POST /checkpoint` - Create a system checkpoint

### Metrics (Prometheus)

Available at `http://localhost:9090/metrics`:

- `stream_events_processed_total` - Total events processed
- `stream_processing_duration_seconds` - Processing latency histogram
- `stream_active_windows` - Current active window count
- `stream_watermark_lag_seconds` - Watermark lag by partition

## Processing Model

### Event Flow

1. **Ingestion**: Events are read from sources (mock, file, Kafka)
2. **Routing**: Events are routed to appropriate pipelines
3. **Windowing**: Events are assigned to time-based windows
4. **Processing**: Window functions aggregate or transform data
5. **Output**: Results are written to configured sinks

### Exactly-Once Processing

The system implements exactly-once semantics through:

- **Offset tracking**: Each event has a unique source/partition/offset
- **Deduplication**: Processed events are tracked to prevent reprocessing
- **Checkpointing**: State is periodically saved for recovery
- **Atomic commits**: State updates and output are coordinated

### Fault Tolerance

- **Graceful shutdown**: Clean resource cleanup on termination
- **Error handling**: Comprehensive error handling with retries
- **State recovery**: Restore from checkpoints after failures
- **Circuit breaking**: Prevent cascade failures

## Performance Tuning

### Configuration Parameters

```yaml
processing:
  parallelism: 8          # Increase for higher throughput
  queue_size: 50000       # Larger queues for burst handling
  checkpoint_interval: 60 # Less frequent checkpoints for performance

watermarks:
  delay_seconds: 2.0      # Reduce for lower latency
```

### Resource Requirements

- **CPU**: 1-4 cores depending on parallelism
- **Memory**: 2-8GB depending on state size and window configuration
- **Storage**: SSD recommended for state storage
- **Network**: 1Gbps for high-throughput scenarios

## Development

### Project Structure

```
src/
├── main.py              # Application entry point
├── stream_processor.py  # Core processing engine
├── models.py           # Data models and types
├── windowing.py        # Window implementations
├── state_store.py      # Persistent state management
├── watermark_tracker.py # Watermark tracking
├── sources.py          # Event sources
├── sinks.py            # Event sinks
├── api_server.py       # REST API server
├── metrics.py          # Metrics collection
└── config.py           # Configuration management
```

### Adding Custom Sources

```python
from src.sources import EventSource
from src.models import StreamEvent

class CustomSource(EventSource):
    async def read_batch(self, max_events: int = 100) -> List[StreamEvent]:
        # Implement custom event reading logic
        pass
    
    async def close(self):
        # Cleanup resources
        pass
```

### Adding Custom Sinks

```python
from src.sinks import EventSink
from src.models import ProcessingResult

class CustomSink(EventSink):
    async def write(self, result: ProcessingResult):
        # Implement custom output logic
        pass
    
    async def close(self):
        # Cleanup resources
        pass
```

## Testing

```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Run performance tests
python tests/performance/throughput_test.py
```

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY config/ config/

EXPOSE 8080 9090

CMD ["python", "src/main.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stream-processor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: stream-processor
  template:
    metadata:
      labels:
        app: stream-processor
    spec:
      containers:
      - name: stream-processor
        image: data-010-stream-processor:latest
        ports:
        - containerPort: 8080
        - containerPort: 9090
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

## License

This implementation is part of the Req2Run benchmark suite.

---

<a id="japanese"></a>
## 日本語

# DATA-010: ウィンドウイングと状態管理を備えたストリーム処理

ウィンドウ処理、状態管理、ウォーターマーク追跡、および厳密な一度限りの処理セマンティクスを実装した本番環境向けストリーム処理システム。

## アーキテクチャ概要

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  イベントソース   │───▶│ ストリームプロセッサ │───▶│  イベントシンク   │
│                 │    │                  │    │                 │
│ • モックイベント  │    │ • ウィンドウ処理   │    │ • コンソール     │
│ • ファイルソース  │    │ • 状態ストア      │    │ • ファイル出力    │
│ • Kafka (TODO)  │    │ • ウォーターマーク  │    │ • メトリクス     │
└─────────────────┘    │ • パイプライン     │    └─────────────────┘
                       └──────────────────┘
                               │
                               ▼
                       ┌──────────────────┐
                       │   APIサーバー     │
                       │ • REST API       │
                       │ • メトリクス      │
                       │ • モニタリング     │
                       └──────────────────┘
```

## 主要機能

### 🔄 ストリーム処理
- オフセット追跡による**厳密な一度限りの処理セマンティクス**
- 設定可能なキューサイズによる**バックプレッシャー処理**
- 複数の処理ワークフローのための**パイプラインベースアーキテクチャ**
- 設定可能な並列性による**非同期処理**

### 🪟 ウィンドウ処理
- **タンブリングウィンドウ**: 固定サイズ、非重複の時間ウィンドウ
- **スライディングウィンドウ**: 設定可能なスライド間隔を持つ固定サイズウィンドウ
- **セッションウィンドウ**: アクティビティギャップに基づく動的ウィンドウ
- 設定可能な許容遅延による**遅延データ処理**

### 💾 状態管理
- RocksDB（DiskCacheフォールバック付き）を使用した**永続的な状態ストレージ**
- フォールトトレランスとリカバリのための**チェックポイント**
- プレフィックスベースのクエリによる**状態スキャン**
- 期限切れ状態の**自動クリーンアップ**

### 🌊 ウォーターマーク追跡
- ウォーターマークベースの進捗追跡による**イベント時間処理**
- 並列処理のための**パーティションごとのウォーターマーク**
- **遅延イベントの検出**と処理
- 遅延データ許容のための**設定可能なウォーターマーク遅延**

### 📊 モニタリング＆メトリクス
- 包括的なカウンターとゲージを備えた**Prometheusメトリクス**（利用可能な場合）
- リアルタイムモニタリングと制御のための**REST API**
- レイテンシとスループットメトリクスによる**パフォーマンス追跡**
- **パイプライン統計**とヘルスチェック

## クイックスタート

### 前提条件

- Python 3.11+
- Docker（オプション）

### インストール

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 設定ディレクトリの作成
mkdir -p config

# デフォルト設定のコピー
cp config/stream.yaml.example config/stream.yaml
```

### アプリケーションの実行

```bash
# デフォルト設定で開始
python src/main.py

# カスタム設定で開始
python src/main.py --config config/custom.yaml

# Dockerで実行
docker build -t data-010-stream-processor .
docker run -p 8080:8080 -p 9090:9090 data-010-stream-processor
```

### システムのテスト

```bash
# システムヘルスチェック
curl http://localhost:8080/health

# 現在のステータスを表示
curl http://localhost:8080/status

# アクティブなパイプラインをリスト
curl http://localhost:8080/pipelines

# メトリクスを監視（Prometheus形式）
curl http://localhost:9090/metrics
```

## 設定

### 基本設定

```yaml
# config/stream.yaml
app_name: "My Stream Processor"
debug: false

processing:
  parallelism: 4
  queue_size: 10000
  checkpoint_interval: 30.0

windowing:
  windows:
    - type: "tumbling"
      size_ms: 60000  # 1分
      allowed_lateness_ms: 5000
```

### ウィンドウタイプ

#### タンブリングウィンドウ
```yaml
- type: "tumbling"
  size_ms: 60000        # ウィンドウサイズ: 1分
  allowed_lateness_ms: 5000  # 遅延データ許容: 5秒
```

#### スライディングウィンドウ
```yaml
- type: "sliding"
  size_ms: 300000       # ウィンドウサイズ: 5分
  slide_ms: 30000       # スライド間隔: 30秒
  allowed_lateness_ms: 10000
```

#### セッションウィンドウ
```yaml
- type: "session"
  gap_ms: 30000         # 非アクティブギャップ: 30秒
  allowed_lateness_ms: 15000
```

## APIリファレンス

### ヘルス＆ステータス

- `GET /health` - システムヘルスチェック
- `GET /status` - 詳細なシステムステータスと統計

### パイプライン管理

- `GET /pipelines` - すべてのパイプラインをリスト
- `POST /pipelines/{id}/start` - 特定のパイプラインを開始
- `POST /pipelines/{id}/stop` - 特定のパイプラインを停止
- `GET /pipelines/{id}/stats` - パイプライン統計を取得

### モニタリング

- `GET /watermarks` - 現在のウォーターマーク情報
- `GET /state` - 状態ストア情報
- `GET /windows` - アクティブウィンドウ情報
- `POST /checkpoint` - システムチェックポイントを作成

### メトリクス（Prometheus）

`http://localhost:9090/metrics`で利用可能:

- `stream_events_processed_total` - 処理されたイベント総数
- `stream_processing_duration_seconds` - 処理レイテンシヒストグラム
- `stream_active_windows` - 現在のアクティブウィンドウ数
- `stream_watermark_lag_seconds` - パーティション別ウォーターマーク遅延

## 処理モデル

### イベントフロー

1. **取り込み**: イベントはソース（モック、ファイル、Kafka）から読み取られる
2. **ルーティング**: イベントは適切なパイプラインにルーティングされる
3. **ウィンドウイング**: イベントは時間ベースのウィンドウに割り当てられる
4. **処理**: ウィンドウ関数がデータを集約または変換
5. **出力**: 結果は設定されたシンクに書き込まれる

### 厳密な一度限りの処理

システムは以下により厳密な一度限りのセマンティクスを実装:

- **オフセット追跡**: 各イベントは一意のソース/パーティション/オフセットを持つ
- **重複除去**: 処理済みイベントは再処理を防ぐために追跡される
- **チェックポイント**: 状態はリカバリのために定期的に保存される
- **アトミックコミット**: 状態更新と出力が調整される

### フォールトトレランス

- **グレースフルシャットダウン**: 終了時のクリーンなリソースクリーンアップ
- **エラー処理**: リトライを含む包括的なエラー処理
- **状態リカバリ**: 障害後のチェックポイントからの復元
- **サーキットブレーカー**: カスケード障害の防止

## パフォーマンスチューニング

### 設定パラメータ

```yaml
processing:
  parallelism: 8          # スループット向上のために増加
  queue_size: 50000       # バースト処理用の大きなキュー
  checkpoint_interval: 60 # パフォーマンスのためにチェックポイント頻度を減少

watermarks:
  delay_seconds: 2.0      # レイテンシ低減のために減少
```

### リソース要件

- **CPU**: 並列性に応じて1-4コア
- **メモリ**: 状態サイズとウィンドウ設定に応じて2-8GB
- **ストレージ**: 状態ストレージにはSSD推奨
- **ネットワーク**: 高スループットシナリオでは1Gbps

## 開発

### プロジェクト構造

```
src/
├── main.py              # アプリケーションエントリポイント
├── stream_processor.py  # コア処理エンジン
├── models.py           # データモデルと型
├── windowing.py        # ウィンドウ実装
├── state_store.py      # 永続的な状態管理
├── watermark_tracker.py # ウォーターマーク追跡
├── sources.py          # イベントソース
├── sinks.py            # イベントシンク
├── api_server.py       # REST APIサーバー
├── metrics.py          # メトリクス収集
└── config.py           # 設定管理
```

### カスタムソースの追加

```python
from src.sources import EventSource
from src.models import StreamEvent

class CustomSource(EventSource):
    async def read_batch(self, max_events: int = 100) -> List[StreamEvent]:
        # カスタムイベント読み取りロジックを実装
        pass
    
    async def close(self):
        # リソースのクリーンアップ
        pass
```

### カスタムシンクの追加

```python
from src.sinks import EventSink
from src.models import ProcessingResult

class CustomSink(EventSink):
    async def write(self, result: ProcessingResult):
        # カスタム出力ロジックを実装
        pass
    
    async def close(self):
        # リソースのクリーンアップ
        pass
```

## テスト

```bash
# ユニットテストの実行
python -m pytest tests/

# 統合テストの実行
python -m pytest tests/integration/

# パフォーマンステストの実行
python tests/performance/throughput_test.py
```

## 本番環境デプロイメント

### Dockerデプロイメント

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY config/ config/

EXPOSE 8080 9090

CMD ["python", "src/main.py"]
```

### Kubernetesデプロイメント

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stream-processor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: stream-processor
  template:
    metadata:
      labels:
        app: stream-processor
    spec:
      containers:
      - name: stream-processor
        image: data-010-stream-processor:latest
        ports:
        - containerPort: 8080
        - containerPort: 9090
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

## ライセンス

この実装はReq2Runベンチマークスイートの一部です。