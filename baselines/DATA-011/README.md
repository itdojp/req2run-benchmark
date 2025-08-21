# DATA-011: ETL Pipeline with Change Data Capture (CDC)

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

A comprehensive ETL pipeline system with real-time Change Data Capture (CDC), configurable transformations, data lineage tracking, and schema evolution support. The system captures database changes in real-time, transforms data according to rules, and maintains complete data lineage throughout the pipeline.

## Key Features

### Change Data Capture (CDC)
- **Real-time Capture**: Monitor database changes in real-time
- **Multiple Sources**: Support for PostgreSQL, MySQL, MongoDB
- **Event Types**: INSERT, UPDATE, DELETE, TRUNCATE, DDL
- **Deduplication**: Automatic event deduplication
- **Position Tracking**: Resume from last position after restart

### Data Transformation
- **Configurable Rules**: Map, filter, aggregate, join transformations
- **Jinja2 Templates**: Flexible expression-based transformations
- **Custom Functions**: Extensible with custom transformation logic
- **Idempotent Operations**: Ensure exactly-once processing
- **Batch Processing**: Efficient batch transformations

### Data Lineage
- **Complete Tracking**: Track data flow from source to sink
- **Impact Analysis**: Analyze downstream impact of changes
- **Visualization**: Generate data flow diagrams
- **Audit Trail**: Complete audit log of all operations

### Schema Evolution
- **Version Management**: Track schema versions
- **Compatibility Checking**: Backward/forward compatibility
- **Auto-migration**: Automatic data migration between versions

### Data Quality
- **Quality Rules**: Configurable data quality checks
- **Validation**: Type, range, pattern validation
- **Monitoring**: Real-time quality metrics

## Architecture

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│   Sources  │────▶│    CDC     │────▶│ Transform  │────▶│   Sinks    │
│            │     │   Engine   │     │   Engine   │     │            │
└────────────┘     └────────────┘     └────────────┘     └────────────┘
                           │                  │                  │
                           ▼                  ▼                  ▼
                    ┌────────────┐     ┌────────────┐     ┌────────────┐
                    │   Buffer   │     │  Quality   │     │  Lineage   │
                    │            │     │  Checker   │     │  Tracker   │
                    └────────────┘     └────────────┘     └────────────┘
```

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t etl-cdc-pipeline .

# Run the container
docker run -p 8000:8000 \
  -v ./config:/app/config \
  -v ./data:/data \
  etl-cdc-pipeline

# Health check
curl http://localhost:8000/health
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure sources and transformations:**
```bash
# Edit configuration files
vi config/cdc.yaml
vi config/transformations.yaml
vi config/connectors.yaml
```

3. **Run the application:**
```bash
cd src
python main.py
```

## API Endpoints

### Pipeline Control
- `POST /api/v1/pipeline/start` - Start the ETL pipeline
- `POST /api/v1/pipeline/stop` - Stop the ETL pipeline
- `GET /api/v1/pipeline/status` - Get pipeline status

### Source Management
- `POST /api/v1/sources/connect` - Connect a data source
- `POST /api/v1/sources/{source_id}/start` - Start CDC for source
- `POST /api/v1/sources/{source_id}/stop` - Stop CDC for source

### Transformations
- `POST /api/v1/transformations` - Add transformation rule
- `GET /api/v1/transformations` - List transformation rules

### Data Lineage
- `GET /api/v1/lineage/asset/{asset_id}/downstream` - Get downstream lineage
- `GET /api/v1/lineage/asset/{asset_id}/upstream` - Get upstream lineage
- `GET /api/v1/lineage/impact/{asset_id}` - Impact analysis
- `GET /api/v1/lineage/flow` - Data flow diagram

### Schema Management
- `POST /api/v1/schema/register` - Register schema version
- `POST /api/v1/schema/check-compatibility` - Check compatibility

### Data Quality
- `POST /api/v1/quality/add-rule` - Add quality rule
- `POST /api/v1/quality/check` - Check data quality

## Usage Examples

### Connect PostgreSQL Source

```bash
curl -X POST http://localhost:8000/api/v1/sources/connect \
  -H "Content-Type: application/json" \
  -d '{
    "id": "postgres_main",
    "type": "postgresql",
    "connection_string": "postgresql://user:pass@localhost/db",
    "config": {
      "poll_interval": 1,
      "tables": ["users", "orders"]
    }
  }'
```

### Start CDC

```bash
curl -X POST http://localhost:8000/api/v1/sources/postgres_main/start \
  -H "Content-Type: application/json" \
  -d '["users", "orders"]'
```

### Add Transformation Rule

```bash
curl -X POST http://localhost:8000/api/v1/transformations \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": "mask_email",
    "name": "Mask Email Addresses",
    "rule_type": "map",
    "source_fields": ["email"],
    "target_field": "masked_email",
    "expression": "{{ email.split(\"@\")[0][:3] }}***@{{ email.split(\"@\")[1] }}"
  }'
```

### Get Data Lineage

```bash
curl http://localhost:8000/api/v1/lineage/asset/postgres_main_users/downstream?max_depth=3
```

### Check Impact Analysis

```bash
curl http://localhost:8000/api/v1/lineage/impact/postgres_main_users
```

## Configuration

### CDC Configuration (`config/cdc.yaml`)

```yaml
sources:
  - id: postgres_source
    type: postgresql
    connection_string: postgresql://user:pass@localhost/db
    poll_interval: 1
    tables:
      - users
      - orders
```

### Transformation Rules (`config/transformations.yaml`)

```yaml
rules:
  - rule_id: mask_pii
    name: Mask PII Data
    rule_type: map
    source_fields: [email, phone]
    target_field: masked_data
    expression: |
      {
        "email": "***@{{ email.split('@')[1] }}",
        "phone": "***-***-{{ phone[-4:] }}"
      }
```

## Supported Transformations

### Map Transformation
Transform field values using expressions:
```yaml
rule_type: map
source_fields: [price, tax]
target_field: total
expression: "{{ price + tax }}"
```

### Filter Transformation
Filter records based on conditions:
```yaml
rule_type: filter
source_fields: [status]
expression: "{{ status == 'active' }}"
```

### Aggregate Transformation
Aggregate multiple fields:
```yaml
rule_type: aggregate
source_fields: [amount1, amount2]
target_field: total
parameters:
  type: sum  # sum, avg, min, max, count
```

## Data Lineage Features

### Lineage Tracking
- Automatic tracking of all data transformations
- Source-to-sink visibility
- Operation history

### Impact Analysis
- Identify affected downstream assets
- Critical path analysis
- Change impact assessment

### Visualization
- Data flow diagrams
- Dependency graphs
- Export to DOT format

## Schema Evolution

### Compatibility Modes
- **BACKWARD**: New schema can read old data
- **FORWARD**: Old schema can read new data
- **FULL**: Both backward and forward compatible
- **NONE**: No compatibility checking

### Version Management
- Register schema versions
- Automatic migration between versions
- Compatibility validation

## Performance Optimization

### CDC Optimization
- Batch reading for efficiency
- Position checkpointing
- Parallel source processing

### Transformation Optimization
- Batch transformations
- Caching of compiled expressions
- Parallel rule execution

### Sink Optimization
- Batch writes
- Connection pooling
- Async I/O operations

## Monitoring

### Metrics
- Events processed per second
- Transformation success/failure rates
- CDC lag monitoring
- Data quality scores

### Health Checks
- Source connectivity
- Transformation engine status
- Sink availability
- Memory and CPU usage

## Production Deployment

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost/db
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
LOG_LEVEL=INFO
BUFFER_SIZE=10000
```

### Docker Compose
```yaml
version: '3.8'
services:
  etl-pipeline:
    image: etl-cdc-pipeline
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
      - ./data:/data
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: etl-pipeline
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: etl-pipeline
        image: etl-cdc-pipeline
        ports:
        - containerPort: 8000
```

## License

MIT

---

<a id="japanese"></a>
## 日本語

# DATA-011: 変更データキャプチャ（CDC）付きETLパイプライン

## 概要

リアルタイム変更データキャプチャ（CDC）、設定可能な変換、データリネージ追跡、スキーマ進化サポートを備えた包括的なETLパイプラインシステム。システムはデータベースの変更をリアルタイムでキャプチャし、ルールに従ってデータを変換し、パイプライン全体で完全なデータリネージを維持します。

## 主要機能

### 変更データキャプチャ（CDC）
- **リアルタイムキャプチャ**: データベースの変更をリアルタイムで監視
- **複数ソース**: PostgreSQL、MySQL、MongoDBをサポート
- **イベントタイプ**: INSERT、UPDATE、DELETE、TRUNCATE、DDL
- **重複除去**: 自動イベント重複除去
- **位置追跡**: 再起動後に最後の位置から再開

### データ変換
- **設定可能なルール**: マップ、フィルター、集約、結合変換
- **Jinja2テンプレート**: 柔軟な式ベースの変換
- **カスタム関数**: カスタム変換ロジックで拡張可能
- **冪等操作**: 厳密な一度限りの処理を保証
- **バッチ処理**: 効率的なバッチ変換

### データリネージ
- **完全な追跡**: ソースからシンクまでのデータフローを追跡
- **影響分析**: 変更の下流への影響を分析
- **可視化**: データフロー図の生成
- **監査証跡**: すべての操作の完全な監査ログ

### スキーマ進化
- **バージョン管理**: スキーマバージョンの追跡
- **互換性チェック**: 後方/前方互換性
- **自動移行**: バージョン間の自動データ移行

### データ品質
- **品質ルール**: 設定可能なデータ品質チェック
- **検証**: タイプ、範囲、パターン検証
- **監視**: リアルタイム品質メトリクス

## アーキテクチャ

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│   ソース    │────▶│    CDC     │────▶│   変換      │────▶│   シンク    │
│            │     │  エンジン   │     │  エンジン   │     │            │
└────────────┘     └────────────┘     └────────────┘     └────────────┘
                           │                  │                  │
                           ▼                  ▼                  ▼
                    ┌────────────┐     ┌────────────┐     ┌────────────┐
                    │  バッファ   │     │   品質      │     │  リネージ   │
                    │            │     │  チェッカー  │     │  トラッカー  │
                    └────────────┘     └────────────┘     └────────────┘
```

## クイックスタート

### Dockerを使用

```bash
# イメージをビルド
docker build -t etl-cdc-pipeline .

# コンテナを実行
docker run -p 8000:8000 \
  -v ./config:/app/config \
  -v ./data:/data \
  etl-cdc-pipeline

# ヘルスチェック
curl http://localhost:8000/health
```

### 手動セットアップ

1. **依存関係のインストール:**
```bash
pip install -r requirements.txt
```

2. **ソースと変換の設定:**
```bash
# 設定ファイルの編集
vi config/cdc.yaml
vi config/transformations.yaml
vi config/connectors.yaml
```

3. **アプリケーションの実行:**
```bash
cd src
python main.py
```

## APIエンドポイント

### パイプライン制御
- `POST /api/v1/pipeline/start` - ETLパイプラインを開始
- `POST /api/v1/pipeline/stop` - ETLパイプラインを停止
- `GET /api/v1/pipeline/status` - パイプラインステータスを取得

### ソース管理
- `POST /api/v1/sources/connect` - データソースを接続
- `POST /api/v1/sources/{source_id}/start` - ソースのCDCを開始
- `POST /api/v1/sources/{source_id}/stop` - ソースのCDCを停止

### 変換
- `POST /api/v1/transformations` - 変換ルールを追加
- `GET /api/v1/transformations` - 変換ルールをリスト

### データリネージ
- `GET /api/v1/lineage/asset/{asset_id}/downstream` - 下流リネージを取得
- `GET /api/v1/lineage/asset/{asset_id}/upstream` - 上流リネージを取得
- `GET /api/v1/lineage/impact/{asset_id}` - 影響分析
- `GET /api/v1/lineage/flow` - データフロー図

### スキーマ管理
- `POST /api/v1/schema/register` - スキーマバージョンを登録
- `POST /api/v1/schema/check-compatibility` - 互換性をチェック

### データ品質
- `POST /api/v1/quality/add-rule` - 品質ルールを追加
- `POST /api/v1/quality/check` - データ品質をチェック

## 使用例

### PostgreSQLソースの接続

```bash
curl -X POST http://localhost:8000/api/v1/sources/connect \
  -H "Content-Type: application/json" \
  -d '{
    "id": "postgres_main",
    "type": "postgresql",
    "connection_string": "postgresql://user:pass@localhost/db",
    "config": {
      "poll_interval": 1,
      "tables": ["users", "orders"]
    }
  }'
```

### CDCの開始

```bash
curl -X POST http://localhost:8000/api/v1/sources/postgres_main/start \
  -H "Content-Type: application/json" \
  -d '["users", "orders"]'
```

### 変換ルールの追加

```bash
curl -X POST http://localhost:8000/api/v1/transformations \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": "mask_email",
    "name": "メールアドレスのマスク",
    "rule_type": "map",
    "source_fields": ["email"],
    "target_field": "masked_email",
    "expression": "{{ email.split(\"@\")[0][:3] }}***@{{ email.split(\"@\")[1] }}"
  }'
```

### データリネージの取得

```bash
curl http://localhost:8000/api/v1/lineage/asset/postgres_main_users/downstream?max_depth=3
```

### 影響分析のチェック

```bash
curl http://localhost:8000/api/v1/lineage/impact/postgres_main_users
```

## 設定

### CDC設定 (`config/cdc.yaml`)

```yaml
sources:
  - id: postgres_source
    type: postgresql
    connection_string: postgresql://user:pass@localhost/db
    poll_interval: 1
    tables:
      - users
      - orders
```

### 変換ルール (`config/transformations.yaml`)

```yaml
rules:
  - rule_id: mask_pii
    name: PIIデータのマスク
    rule_type: map
    source_fields: [email, phone]
    target_field: masked_data
    expression: |
      {
        "email": "***@{{ email.split('@')[1] }}",
        "phone": "***-***-{{ phone[-4:] }}"
      }
```

## サポートされる変換

### マップ変換
式を使用してフィールド値を変換:
```yaml
rule_type: map
source_fields: [price, tax]
target_field: total
expression: "{{ price + tax }}"
```

### フィルター変換
条件に基づいてレコードをフィルター:
```yaml
rule_type: filter
source_fields: [status]
expression: "{{ status == 'active' }}"
```

### 集約変換
複数のフィールドを集約:
```yaml
rule_type: aggregate
source_fields: [amount1, amount2]
target_field: total
parameters:
  type: sum  # sum, avg, min, max, count
```

## データリネージ機能

### リネージ追跡
- すべてのデータ変換の自動追跡
- ソースからシンクまでの可視性
- 操作履歴

### 影響分析
- 影響を受ける下流資産の特定
- クリティカルパス分析
- 変更影響評価

### 可視化
- データフロー図
- 依存関係グラフ
- DOT形式へのエクスポート

## スキーマ進化

### 互換性モード
- **BACKWARD**: 新しいスキーマは古いデータを読み取り可能
- **FORWARD**: 古いスキーマは新しいデータを読み取り可能
- **FULL**: 後方および前方互換
- **NONE**: 互換性チェックなし

### バージョン管理
- スキーマバージョンの登録
- バージョン間の自動移行
- 互換性検証

## パフォーマンス最適化

### CDC最適化
- 効率のためのバッチ読み取り
- 位置チェックポイント
- 並列ソース処理

### 変換最適化
- バッチ変換
- コンパイル済み式のキャッシュ
- 並列ルール実行

### シンク最適化
- バッチ書き込み
- 接続プーリング
- 非同期I/O操作

## 監視

### メトリクス
- 毎秒処理されるイベント数
- 変換成功/失敗率
- CDCラグ監視
- データ品質スコア

### ヘルスチェック
- ソース接続性
- 変換エンジンステータス
- シンク可用性
- メモリとCPU使用率

## 本番環境デプロイメント

### 環境変数
```bash
DATABASE_URL=postgresql://user:pass@localhost/db
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
LOG_LEVEL=INFO
BUFFER_SIZE=10000
```

### Docker Compose
```yaml
version: '3.8'
services:
  etl-pipeline:
    image: etl-cdc-pipeline
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
      - ./data:/data
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: etl-pipeline
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: etl-pipeline
        image: etl-cdc-pipeline
        ports:
        - containerPort: 8000
```

## ライセンス

MIT