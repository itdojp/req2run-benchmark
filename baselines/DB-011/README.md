# DB-011: Event Sourcing with CQRS and Projections

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

A comprehensive implementation of Event Sourcing with Command Query Responsibility Segregation (CQRS) pattern, featuring multiple projections, event replay, temporal queries, saga orchestration, and event stream branching. The system stores all state changes as immutable events and maintains separate read and write models for optimal performance.

## Key Features

### Event Sourcing
- **Immutable Event Store**: All state changes stored as events
- **Event Ordering**: Guaranteed ordering within aggregates
- **Event Versioning**: Support for schema evolution
- **Tamper Detection**: Checksum validation for events
- **Event Replay**: Rebuild state from events

### CQRS Implementation
- **Command Bus**: Routes commands to handlers
- **Query Bus**: Routes queries to read models
- **Separate Models**: Optimized read and write models
- **Middleware Support**: Logging, validation, authorization

### Projections
- **Multiple Projections**: Account balance, orders, inventory, user activity
- **Async Updates**: Non-blocking projection updates
- **Rebuild Capability**: Reconstruct projections from events
- **Custom Projections**: Extensible projection framework

### Advanced Features
- **Snapshots**: Optimize replay performance
- **Temporal Queries**: Query state at any point in time
- **Saga Orchestration**: Long-running transaction support
- **Event Stream Branching**: Alternative timeline exploration

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Commands   │────▶│  Command Bus │────▶│   Aggregates │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────────┐     ┌──────────────┐
                     │ Event Store  │◀────│    Events    │
                     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Projections  │
                     └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Read Model 1 │   │ Read Model 2 │   │ Read Model N │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Queries    │   │   Queries    │   │   Queries    │
└──────────────┘   └──────────────┘   └──────────────┘
```

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t event-sourcing-cqrs .

# Run with PostgreSQL and Redis
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@postgres/eventstore \
  -e REDIS_URL=redis://redis:6379 \
  event-sourcing-cqrs

# Health check
curl http://localhost:8000/health
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start PostgreSQL and Redis:**
```bash
# PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  postgres:15

# Redis
docker run -d -p 6379:6379 redis:7
```

3. **Run the application:**
```bash
python src/main.py
```

## API Endpoints

### Commands
- `POST /api/v1/commands` - Send command to command bus

### Queries
- `POST /api/v1/queries` - Send query to query bus

### Events
- `POST /api/v1/events` - Append event to store
- `GET /api/v1/events/{aggregate_id}` - Get events for aggregate

### Replay & Temporal
- `POST /api/v1/replay` - Replay events to rebuild state
- `POST /api/v1/temporal-query` - Query events by time range

### Projections
- `POST /api/v1/projections/{name}/rebuild` - Rebuild projection

### Sagas
- `POST /api/v1/sagas` - Start new saga

### Branching
- `POST /api/v1/branches` - Create event stream branch

## Usage Examples

### Create Account
```bash
curl -X POST http://localhost:8000/api/v1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "CreateAccount",
    "aggregate_id": "acc-123",
    "data": {
      "account_id": "acc-123",
      "owner": "John Doe",
      "initial_balance": 1000
    }
  }'
```

### Deposit Money
```bash
curl -X POST http://localhost:8000/api/v1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "DepositMoney",
    "aggregate_id": "acc-123",
    "data": {
      "account_id": "acc-123",
      "amount": 500
    }
  }'
```

### Query Account Balance
```bash
curl -X POST http://localhost:8000/api/v1/queries \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "GetAccountBalance",
    "filters": {
      "account_id": "acc-123"
    },
    "projection": "account_balance"
  }'
```

### Get Events
```bash
curl http://localhost:8000/api/v1/events/acc-123
```

### Replay Events
```bash
curl -X POST http://localhost:8000/api/v1/replay \
  -H "Content-Type: application/json" \
  -d '{
    "aggregate_id": "acc-123",
    "from_sequence": 0,
    "use_snapshot": true
  }'
```

### Temporal Query
```bash
curl -X POST http://localhost:8000/api/v1/temporal-query \
  -H "Content-Type: application/json" \
  -d '{
    "aggregate_id": "acc-123",
    "from_time": "2024-01-01T00:00:00Z",
    "to_time": "2024-01-31T23:59:59Z"
  }'
```

## Projections

### Account Balance Projection
Tracks account balances and transaction history:
- Current balance
- Transaction history
- Transfer tracking

### Order Summary Projection
Maintains order summaries and statistics:
- Order details and status
- Customer order history
- Product order tracking
- Daily statistics

### Inventory Projection
Manages inventory levels and movements:
- Stock on hand
- Reserved quantities
- Stock movements
- Low stock alerts

### User Activity Projection
Tracks user activity timeline:
- User registration
- Login sessions
- User actions
- Activity timeline

## Event Versioning

The system supports event schema evolution:

```python
# Register migration
migration.register_migration(
    event_type="AccountCreated",
    from_version=1,
    to_version=2,
    migration_func=migrate_account_v1_to_v2
)
```

## Saga Example

Long-running transaction orchestration:

```python
class TransferSaga(Saga):
    async def start(self, command_bus):
        # Withdraw from source
        await command_bus.send(Command(
            command_type="WithdrawMoney",
            aggregate_id=self.data["from_account"],
            data={"amount": self.data["amount"]}
        ))
    
    async def handle_event(self, event, command_bus):
        if event.event_type == "MoneyWithdrawn":
            # Deposit to target
            await command_bus.send(Command(
                command_type="DepositMoney",
                aggregate_id=self.data["to_account"],
                data={"amount": self.data["amount"]}
            ))
```

## Performance Optimization

### Snapshots
- Created every 100 events by default
- Significantly speeds up replay
- Configurable frequency per aggregate

### Caching
- Query results cached for 60 seconds
- Redis-based distributed cache
- Invalidation on write

### Batch Processing
- Events processed in batches
- Configurable batch size
- Async projection updates

## Configuration

### Event Store (`config/event_store.yaml`)
- Database connections
- Snapshot settings
- Security options

### Projections (`config/projections.yaml`)
- Projection definitions
- Read model storage
- Consistency settings

### CQRS (`config/cqrs.yaml`)
- Command and query handlers
- Aggregate configuration
- Saga definitions

## Monitoring

### Metrics
- Events per second
- Command/query latency
- Projection lag
- Saga completion rate

### Health Checks
- Event store connectivity
- Projection status
- Redis availability
- Database health

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/performance/

# Generate coverage report
pytest --cov=src tests/
```

## Production Deployment

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@db/eventstore
REDIS_URL=redis://redis:6379
LOG_LEVEL=INFO
SNAPSHOT_FREQUENCY=100
```

### Docker Compose
```yaml
version: '3.8'
services:
  app:
    image: event-sourcing-cqrs
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/eventstore
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=eventstore
  
  redis:
    image: redis:7
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-sourcing
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: event-sourcing-cqrs
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## Best Practices

1. **Event Design**: Make events fine-grained and domain-specific
2. **Idempotency**: Ensure command handlers are idempotent
3. **Versioning**: Always version events for future compatibility
4. **Snapshots**: Use snapshots for aggregates with many events
5. **Projections**: Keep projections simple and focused
6. **Testing**: Test event replay and projection rebuilds

## License

MIT

---

<a id="japanese"></a>
## 日本語

# DB-011: CQRSとプロジェクションを備えたイベントソーシング

## 概要

コマンドクエリ責任分離（CQRS）パターンによるイベントソーシングの包括的な実装。複数のプロジェクション、イベントリプレイ、時間的クエリ、サーガオーケストレーション、イベントストリーム分岐機能を備えています。システムはすべての状態変更を不変のイベントとして保存し、最適なパフォーマンスのために読み取りモデルと書き込みモデルを分離して維持します。

## 主要機能

### イベントソーシング
- **不変イベントストア**: すべての状態変更をイベントとして保存
- **イベント順序**: 集約内での順序を保証
- **イベントバージョニング**: スキーマ進化のサポート
- **改ざん検出**: イベントのチェックサム検証
- **イベントリプレイ**: イベントから状態を再構築

### CQRS実装
- **コマンドバス**: コマンドをハンドラーにルーティング
- **クエリバス**: クエリを読み取りモデルにルーティング
- **分離モデル**: 最適化された読み取りおよび書き込みモデル
- **ミドルウェアサポート**: ログ、検証、認可

### プロジェクション
- **複数のプロジェクション**: アカウント残高、注文、在庫、ユーザーアクティビティ
- **非同期更新**: ノンブロッキングプロジェクション更新
- **再構築機能**: イベントからプロジェクションを再構築
- **カスタムプロジェクション**: 拡張可能なプロジェクションフレームワーク

### 高度な機能
- **スナップショット**: リプレイパフォーマンスの最適化
- **時間的クエリ**: 任意の時点での状態をクエリ
- **サーガオーケストレーション**: 長時間実行トランザクションのサポート
- **イベントストリーム分岐**: 代替タイムラインの探索

## アーキテクチャ

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  コマンド    │────▶│ コマンドバス  │────▶│   集約       │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────────┐     ┌──────────────┐
                     │イベントストア │◀────│  イベント    │
                     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │プロジェクション│
                     └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│読取モデル 1  │   │読取モデル 2  │   │読取モデル N  │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   クエリ     │   │   クエリ     │   │   クエリ     │
└──────────────┘   └──────────────┘   └──────────────┘
```

## クイックスタート

### Dockerを使用

```bash
# イメージをビルド
docker build -t event-sourcing-cqrs .

# PostgreSQLとRedisで実行
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@postgres/eventstore \
  -e REDIS_URL=redis://redis:6379 \
  event-sourcing-cqrs

# ヘルスチェック
curl http://localhost:8000/health
```

### 手動セットアップ

1. **依存関係のインストール:**
```bash
pip install -r requirements.txt
```

2. **PostgreSQLとRedisの起動:**
```bash
# PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  postgres:15

# Redis
docker run -d -p 6379:6379 redis:7
```

3. **アプリケーションの実行:**
```bash
python src/main.py
```

## APIエンドポイント

### コマンド
- `POST /api/v1/commands` - コマンドバスにコマンドを送信

### クエリ
- `POST /api/v1/queries` - クエリバスにクエリを送信

### イベント
- `POST /api/v1/events` - ストアにイベントを追加
- `GET /api/v1/events/{aggregate_id}` - 集約のイベントを取得

### リプレイと時間的クエリ
- `POST /api/v1/replay` - イベントをリプレイして状態を再構築
- `POST /api/v1/temporal-query` - 時間範囲でイベントをクエリ

### プロジェクション
- `POST /api/v1/projections/{name}/rebuild` - プロジェクションを再構築

### サーガ
- `POST /api/v1/sagas` - 新しいサーガを開始

### 分岐
- `POST /api/v1/branches` - イベントストリーム分岐を作成

## 使用例

### アカウント作成
```bash
curl -X POST http://localhost:8000/api/v1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "CreateAccount",
    "aggregate_id": "acc-123",
    "data": {
      "account_id": "acc-123",
      "owner": "John Doe",
      "initial_balance": 1000
    }
  }'
```

### 入金
```bash
curl -X POST http://localhost:8000/api/v1/commands \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "DepositMoney",
    "aggregate_id": "acc-123",
    "data": {
      "account_id": "acc-123",
      "amount": 500
    }
  }'
```

### アカウント残高のクエリ
```bash
curl -X POST http://localhost:8000/api/v1/queries \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "GetAccountBalance",
    "filters": {
      "account_id": "acc-123"
    },
    "projection": "account_balance"
  }'
```

### イベントの取得
```bash
curl http://localhost:8000/api/v1/events/acc-123
```

### イベントリプレイ
```bash
curl -X POST http://localhost:8000/api/v1/replay \
  -H "Content-Type: application/json" \
  -d '{
    "aggregate_id": "acc-123",
    "from_sequence": 0,
    "use_snapshot": true
  }'
```

### 時間的クエリ
```bash
curl -X POST http://localhost:8000/api/v1/temporal-query \
  -H "Content-Type: application/json" \
  -d '{
    "aggregate_id": "acc-123",
    "from_time": "2024-01-01T00:00:00Z",
    "to_time": "2024-01-31T23:59:59Z"
  }'
```

## プロジェクション

### アカウント残高プロジェクション
アカウント残高とトランザクション履歴を追跡:
- 現在残高
- トランザクション履歴
- 送金追跡

### 注文サマリープロジェクション
注文サマリーと統計を維持:
- 注文詳細とステータス
- 顧客注文履歴
- 製品注文追跡
- 日次統計

### 在庫プロジェクション
在庫レベルと移動を管理:
- 手持ち在庫
- 予約数量
- 在庫移動
- 低在庫アラート

### ユーザーアクティビティプロジェクション
ユーザーアクティビティタイムラインを追跡:
- ユーザー登録
- ログインセッション
- ユーザーアクション
- アクティビティタイムライン

## イベントバージョニング

システムはイベントスキーマの進化をサポート:

```python
# マイグレーションの登録
migration.register_migration(
    event_type="AccountCreated",
    from_version=1,
    to_version=2,
    migration_func=migrate_account_v1_to_v2
)
```

## サーガの例

長時間実行トランザクションのオーケストレーション:

```python
class TransferSaga(Saga):
    async def start(self, command_bus):
        # ソースから引き出し
        await command_bus.send(Command(
            command_type="WithdrawMoney",
            aggregate_id=self.data["from_account"],
            data={"amount": self.data["amount"]}
        ))
    
    async def handle_event(self, event, command_bus):
        if event.event_type == "MoneyWithdrawn":
            # ターゲットに入金
            await command_bus.send(Command(
                command_type="DepositMoney",
                aggregate_id=self.data["to_account"],
                data={"amount": self.data["amount"]}
            ))
```

## パフォーマンス最適化

### スナップショット
- デフォルトで100イベントごとに作成
- リプレイを大幅に高速化
- 集約ごとに設定可能な頻度

### キャッシング
- クエリ結果は60秒間キャッシュ
- Redisベースの分散キャッシュ
- 書き込み時の無効化

### バッチ処理
- イベントをバッチで処理
- 設定可能なバッチサイズ
- 非同期プロジェクション更新

## 設定

### イベントストア (`config/event_store.yaml`)
- データベース接続
- スナップショット設定
- セキュリティオプション

### プロジェクション (`config/projections.yaml`)
- プロジェクション定義
- 読み取りモデルストレージ
- 一貫性設定

### CQRS (`config/cqrs.yaml`)
- コマンドおよびクエリハンドラー
- 集約設定
- サーガ定義

## 監視

### メトリクス
- 毎秒のイベント数
- コマンド/クエリレイテンシ
- プロジェクションラグ
- サーガ完了率

### ヘルスチェック
- イベントストア接続性
- プロジェクションステータス
- Redis可用性
- データベースヘルス

## テスト

```bash
# ユニットテストの実行
pytest tests/unit/

# 統合テストの実行
pytest tests/integration/

# パフォーマンステストの実行
pytest tests/performance/

# カバレッジレポートの生成
pytest --cov=src tests/
```

## 本番環境デプロイメント

### 環境変数
```bash
DATABASE_URL=postgresql://user:pass@db/eventstore
REDIS_URL=redis://redis:6379
LOG_LEVEL=INFO
SNAPSHOT_FREQUENCY=100
```

### Docker Compose
```yaml
version: '3.8'
services:
  app:
    image: event-sourcing-cqrs
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/eventstore
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=eventstore
  
  redis:
    image: redis:7
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-sourcing
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: event-sourcing-cqrs
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## ベストプラクティス

1. **イベント設計**: イベントを細かく、ドメイン固有にする
2. **冪等性**: コマンドハンドラーが冪等であることを確認
3. **バージョニング**: 将来の互換性のために常にイベントをバージョン管理
4. **スナップショット**: 多くのイベントを持つ集約にはスナップショットを使用
5. **プロジェクション**: プロジェクションをシンプルで焦点を絞ったものに保つ
6. **テスト**: イベントリプレイとプロジェクション再構築をテスト

## ライセンス

MIT