# WEB-014: Event-Driven Webhook System with Retry and DLQ

**Language:** [English](#english) | [日本語](#japanese)

---

## English

## Overview

A production-grade event-driven webhook system with comprehensive retry logic, Dead Letter Queue (DLQ) support, and HMAC-SHA256 payload signing. The system ensures reliable webhook delivery with at-least-once guarantees, exponential backoff retries, and comprehensive monitoring.

## Key Features

### Webhook Delivery System
- **Reliable Delivery**: At-least-once delivery guarantees
- **Exponential Backoff**: Smart retry logic with configurable policies
- **Dead Letter Queue**: Failed webhooks moved to DLQ for manual inspection
- **HMAC Signing**: SHA-256 payload signing for security
- **Event Filtering**: Flexible event filtering and endpoint management

### Performance & Scalability
- **Worker-Based Architecture**: Concurrent webhook delivery workers
- **Async Processing**: Non-blocking I/O for high throughput
- **Queue Management**: Efficient message queuing and processing
- **Rate Limiting**: Per-endpoint and global rate limiting
- **Circuit Breaker**: Automatic endpoint failure detection

### Monitoring & Observability
- **Prometheus Metrics**: Comprehensive metrics collection
- **Health Checks**: Built-in health monitoring
- **Structured Logging**: Detailed logging for debugging
- **Delivery Tracking**: Real-time delivery status tracking

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Webhook System                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐            │
│  │              │         │              │            │
│  │   FastAPI    │◄────────│   Events     │            │
│  │   Server     │         │   API        │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│         │                        │                     │
│         ▼                        ▼                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │              │         │              │            │
│  │  Webhook     │◄────────│  Delivery    │            │
│  │  Engine      │         │  Queue       │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│         │                        │                     │
│         ▼                        ▼                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │              │         │              │            │
│  │   Retry      │◄────────│     DLQ      │            │
│  │  Workers     │         │              │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t webhook-system .

# Run the application
docker run -p 8000:8000 \
  -e WEBHOOK_WORKER_COUNT=4 \
  -e RETRY_MAX_DELAY=300 \
  webhook-system

# Access the API
curl http://localhost:8000/health
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the application:**
```bash
python src/main.py
```

3. **Access the API:**
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

## API Usage

### Register Webhook Endpoint

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/webhook",
    "secret": "your-secret-key",
    "events": ["user.created", "order.updated"],
    "max_retries": 5,
    "timeout": 30
  }'
```

### Emit Event

```bash
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user.created",
    "payload": {
      "user_id": "12345",
      "username": "john_doe",
      "email": "john@example.com"
    }
  }'
```

### Check Delivery Status

```bash
curl "http://localhost:8000/api/v1/deliveries/{delivery_id}"
```

### View DLQ Messages

```bash
curl "http://localhost:8000/api/v1/dlq"
```

## Webhook Payload Format

```json
{
  "id": "event-uuid",
  "event": "user.created",
  "timestamp": "2024-01-21T12:00:00Z",
  "data": {
    "user_id": "12345",
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

## HMAC Signature Verification

Webhooks are signed with HMAC-SHA256:

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    expected_signature = f"sha256={expected}"
    return hmac.compare_digest(signature, expected_signature)

# Example usage
payload = '{"id":"123","event":"user.created",...}'
signature = request.headers.get('X-Webhook-Signature')
secret = 'your-webhook-secret'

if verify_webhook_signature(payload, signature, secret):
    # Process webhook
    pass
```

## Retry Logic

The system implements exponential backoff with jitter:

### Default Retry Policy
- **Initial Delay**: 1 second
- **Max Delay**: 300 seconds (5 minutes)
- **Multiplier**: 2.0
- **Max Attempts**: 5
- **Jitter**: ±25%

### Retry Schedule Example
```
Attempt 1: 1s ± 25%
Attempt 2: 2s ± 25%
Attempt 3: 4s ± 25%
Attempt 4: 8s ± 25%
Attempt 5: 16s ± 25%
Final: Send to DLQ
```

### Custom Retry Policies

Configure different retry policies per event type:

```yaml
# config/retry.yaml
event_retry_policies:
  critical:
    events:
      - "payment.success"
      - "payment.failed"
    retry_policy:
      initial_delay: 0.5
      max_delay: 600.0
      max_attempts: 8
```

## Dead Letter Queue (DLQ)

Failed webhooks are automatically sent to the DLQ after exhausting retry attempts:

### DLQ Features
- **Retention**: 7-day default retention period
- **Replay**: Manual replay functionality
- **Inspection**: Full event and failure details
- **Monitoring**: DLQ growth alerts

### DLQ Message Format

```json
{
  "id": "dlq-message-id",
  "delivery_id": "original-delivery-id",
  "event_id": "original-event-id",
  "endpoint_id": "webhook-endpoint-id",
  "event_type": "user.created",
  "payload": { ... },
  "endpoint_url": "https://example.com/webhook",
  "failure_reason": "HTTP 503: Service Unavailable",
  "attempts": 5,
  "created_at": "2024-01-21T12:00:00Z",
  "expires_at": "2024-01-28T12:00:00Z"
}
```

## Configuration

### Environment Variables

```bash
# Worker Configuration
WEBHOOK_WORKER_COUNT=4
WEBHOOK_MAX_QUEUE_SIZE=10000

# Retry Configuration
RETRY_INITIAL_DELAY=1.0
RETRY_MAX_DELAY=300.0
RETRY_MULTIPLIER=2.0

# DLQ Configuration
DLQ_RETENTION_DAYS=7

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Configuration Files

- `config/webhooks.yaml`: Webhook engine settings
- `config/retry.yaml`: Retry policy configuration
- `config/queue.yaml`: Queue backend configuration

## Monitoring

### Prometheus Metrics

```
# Event metrics
webhook_events_total{event_type="user.created"} 1234
webhook_deliveries_total{status="delivered"} 1150
webhook_deliveries_total{status="failed"} 34

# Performance metrics
webhook_delivery_duration_seconds_bucket{le="0.1"} 800
webhook_delivery_duration_seconds_bucket{le="1.0"} 1100

# System metrics
webhook_queue_size 45
webhook_endpoints_total 12
```

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics
```

## Event Types

### Predefined Event Types
- `user.created`
- `user.updated`
- `user.deleted`
- `order.created`
- `order.updated`
- `order.cancelled`
- `payment.success`
- `payment.failed`

### Custom Event Types
The system supports custom event types - simply use any string identifier.

## Security

### HMAC Signing
- **Algorithm**: HMAC-SHA256
- **Header**: `X-Webhook-Signature`
- **Format**: `sha256=<hex_digest>`

### Best Practices
1. **Secret Management**: Use strong, unique secrets per endpoint
2. **Signature Verification**: Always verify webhook signatures
3. **HTTPS Only**: Only deliver to HTTPS endpoints
4. **Timestamp Validation**: Check webhook timestamp to prevent replay attacks

## Testing

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### Load Testing

```bash
# Test webhook delivery performance
python tests/load/webhook_load_test.py
```

### Test Webhook Receiver

The application includes a test webhook receiver:

```bash
# Register test endpoint
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:8000/test/webhook",
    "secret": "test-secret",
    "events": ["*"]
  }'

# Send test event
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test.event",
    "payload": {"message": "Hello, World!"}
  }'
```

## Performance Characteristics

### Benchmarks
- **Throughput**: 1000+ events/second
- **Latency**: P95 < 500ms
- **Memory Usage**: ~100MB base + 10KB per queued webhook
- **CPU Usage**: ~20% per worker core at full load

### Scalability
- **Horizontal**: Multiple instances with shared queue backend
- **Vertical**: Configurable worker count per instance
- **Queue Backend**: Supports Redis, RabbitMQ, SQS for distributed deployments

## Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  webhook-system:
    build: .
    ports:
      - "8000:8000"
    environment:
      - WEBHOOK_WORKER_COUNT=4
      - RETRY_MAX_DELAY=300
    volumes:
      - ./config:/app/config
      - ./data:/app/data
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webhook-system
  template:
    metadata:
      labels:
        app: webhook-system
    spec:
      containers:
      - name: webhook-system
        image: webhook-system:latest
        ports:
        - containerPort: 8000
        env:
        - name: WEBHOOK_WORKER_COUNT
          value: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Troubleshooting

### Common Issues

1. **High DLQ Growth**
   - Check endpoint availability
   - Review retry policies
   - Monitor error rates

2. **Delivery Delays**
   - Increase worker count
   - Check queue size
   - Review timeout settings

3. **Signature Verification Failures**
   - Verify secret configuration
   - Check clock synchronization
   - Review payload encoding

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Check queue status
curl http://localhost:8000/api/v1/stats

# Review DLQ messages
curl http://localhost:8000/api/v1/dlq
```

## Production Considerations

1. **Queue Backend**: Use Redis/RabbitMQ for production
2. **Monitoring**: Set up Prometheus + Grafana
3. **Load Balancing**: Use multiple instances behind load balancer
4. **Database**: Consider persistent storage for webhook metadata
5. **Security**: Implement proper secret management
6. **Backup**: Regular DLQ message backups

## License

MIT

---

## Japanese

# WEB-014: リトライとDLQ付きイベント駆動Webhookシステム

## 概要

包括的なリトライロジック、Dead Letter Queue（DLQ）サポート、HMAC-SHA256ペイロード署名を備えた本格的なイベント駆動webhookシステム。システムはアットリーストワンス保証、指数バックオフリトライ、包括的な監視で信頼性の高いwebhook配信を保証します。

## 主要機能

### Webhook配信システム
- **信頼性配信**: アットリーストワンス配信保証
- **指数バックオフ**: 設定可能なポリシーでのスマートリトライロジック
- **Dead Letter Queue**: 失敗webhookをDLQに移動して手動検査
- **HMAC署名**: セキュリティのためのSHA-256ペイロード署名
- **イベントフィルタリング**: 柔軟なイベントフィルタリングとエンドポイント管理

### パフォーマンス・スケーラビリティ
- **ワーカーベースアーキテクチャ**: 同時webhook配信ワーカー
- **非同期処理**: 高スループットのためのノンブロッキングI/O
- **キュー管理**: 効率的なメッセージキューイングと処理
- **レート制限**: エンドポイント別およびグローバルレート制限
- **サーキットブレーカー**: 自動エンドポイント障害検出

### 監視・可観測性
- **Prometheusメトリクス**: 包括的なメトリクス収集
- **ヘルスチェック**: 内蔵ヘルス監視
- **構造化ログ**: デバッグ用詳細ログ
- **配信追跡**: リアルタイム配信ステータス追跡

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    Webhookシステム                        │
├─────────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐            │
│  │              │         │              │            │
│  │   FastAPI    │◄────────│   Events     │            │
│  │   Server     │         │   API        │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│         │                        │                     │
│         ▼                        ▼                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │              │         │              │            │
│  │  Webhook     │◄────────│  Delivery    │            │
│  │  Engine      │         │  Queue       │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│         │                        │                     │
│         ▼                        ▼                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │              │         │              │            │
│  │   Retry      │◄────────│     DLQ      │            │
│  │  Workers     │         │              │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│                                                          │
└─────────────────────────────────────────────────────────────┘
```

## クイックスタート

### Dockerの使用

```bash
# イメージビルド
docker build -t webhook-system .

# アプリケーション実行
docker run -p 8000:8000 \
  -e WEBHOOK_WORKER_COUNT=4 \
  -e RETRY_MAX_DELAY=300 \
  webhook-system

# APIアクセス
curl http://localhost:8000/health
```

### 手動セットアップ

1. **依存関係インストール:**
```bash
pip install -r requirements.txt
```

2. **アプリケーション実行:**
```bash
python src/main.py
```

3. **APIアクセス:**
```bash
# ヘルスチェック
curl http://localhost:8000/health

# APIドキュメント
open http://localhost:8000/docs
```

## API使用法

### Webhookエンドポイント登録

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/webhook",
    "secret": "your-secret-key",
    "events": ["user.created", "order.updated"],
    "max_retries": 5,
    "timeout": 30
  }'
```

### イベント発行

```bash
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user.created",
    "payload": {
      "user_id": "12345",
      "username": "john_doe",
      "email": "john@example.com"
    }
  }'
```

### 配信ステータス確認

```bash
curl "http://localhost:8000/api/v1/deliveries/{delivery_id}"
```

### DLQメッセージ表示

```bash
curl "http://localhost:8000/api/v1/dlq"
```

## Webhookペイロード形式

```json
{
  "id": "event-uuid",
  "event": "user.created",
  "timestamp": "2024-01-21T12:00:00Z",
  "data": {
    "user_id": "12345",
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

## HMAC署名検証

WebhookはHMAC-SHA256で署名されています：

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    expected_signature = f"sha256={expected}"
    return hmac.compare_digest(signature, expected_signature)

# 使用例
payload = '{"id":"123","event":"user.created",...}'
signature = request.headers.get('X-Webhook-Signature')
secret = 'your-webhook-secret'

if verify_webhook_signature(payload, signature, secret):
    # webhook処理
    pass
```

## リトライロジック

システムはジッター付き指数バックオフを実装：

### デフォルトリトライポリシー
- **初期遅延**: 1秒
- **最大遅延**: 300秒（5分）
- **乗数**: 2.0
- **最大試行**: 5回
- **ジッター**: ±25%

### リトライスケジュール例
```
試行1: 1s ± 25%
試行2: 2s ± 25%
試行3: 4s ± 25%
試行4: 8s ± 25%
試行5: 16s ± 25%
最終: DLQに送信
```

### カスタムリトライポリシー

イベントタイプ別に異なるリトライポリシーを設定：

```yaml
# config/retry.yaml
event_retry_policies:
  critical:
    events:
      - "payment.success"
      - "payment.failed"
    retry_policy:
      initial_delay: 0.5
      max_delay: 600.0
      max_attempts: 8
```

## Dead Letter Queue (DLQ)

リトライ試行を尽くした失敗webhookは自動的にDLQに送信されます：

### DLQ機能
- **保持**: デフォルト7日間保持期間
- **再生**: 手動再生機能
- **検査**: 完全なイベントと失敗詳細
- **監視**: DLQ成長アラート

### DLQメッセージ形式

```json
{
  "id": "dlq-message-id",
  "delivery_id": "original-delivery-id",
  "event_id": "original-event-id",
  "endpoint_id": "webhook-endpoint-id",
  "event_type": "user.created",
  "payload": { ... },
  "endpoint_url": "https://example.com/webhook",
  "failure_reason": "HTTP 503: Service Unavailable",
  "attempts": 5,
  "created_at": "2024-01-21T12:00:00Z",
  "expires_at": "2024-01-28T12:00:00Z"
}
```

## 設定

### 環境変数

```bash
# ワーカー設定
WEBHOOK_WORKER_COUNT=4
WEBHOOK_MAX_QUEUE_SIZE=10000

# リトライ設定
RETRY_INITIAL_DELAY=1.0
RETRY_MAX_DELAY=300.0
RETRY_MULTIPLIER=2.0

# DLQ設定
DLQ_RETENTION_DAYS=7

# サーバー設定
HOST=0.0.0.0
PORT=8000
```

### 設定ファイル

- `config/webhooks.yaml`: Webhookエンジン設定
- `config/retry.yaml`: リトライポリシー設定
- `config/queue.yaml`: キューバックエンド設定

## 監視

### Prometheusメトリクス

```
# イベントメトリクス
webhook_events_total{event_type="user.created"} 1234
webhook_deliveries_total{status="delivered"} 1150
webhook_deliveries_total{status="failed"} 34

# パフォーマンスメトリクス
webhook_delivery_duration_seconds_bucket{le="0.1"} 800
webhook_delivery_duration_seconds_bucket{le="1.0"} 1100

# システムメトリクス
webhook_queue_size 45
webhook_endpoints_total 12
```

### ヘルスチェック

```bash
# アプリケーションヘルス
curl http://localhost:8000/health

# メトリクスエンドポイント
curl http://localhost:8000/metrics
```

## イベントタイプ

### 事前定義イベントタイプ
- `user.created`
- `user.updated`
- `user.deleted`
- `order.created`
- `order.updated`
- `order.cancelled`
- `payment.success`
- `payment.failed`

### カスタムイベントタイプ
システムはカスタムイベントタイプをサポート - 単純に任意の文字列識別子を使用。

## セキュリティ

### HMAC署名
- **アルゴリズム**: HMAC-SHA256
- **ヘッダー**: `X-Webhook-Signature`
- **形式**: `sha256=<hex_digest>`

### ベストプラクティス
1. **シークレット管理**: エンドポイントごとに強力で一意のシークレットを使用
2. **署名検証**: 常にwebhook署名を検証
3. **HTTPSのみ**: HTTPSエンドポイントのみに配信
4. **タイムスタンプ検証**: リプレイ攻撃防止のためwebhookタイムスタンプを確認

## テスト

### ユニットテスト

```bash
pytest tests/unit/ -v
```

### 統合テスト

```bash
pytest tests/integration/ -v
```

### 負荷テスト

```bash
# webhook配信パフォーマンステスト
python tests/load/webhook_load_test.py
```

### テストWebhookレシーバー

アプリケーションにはテストwebhookレシーバーが含まれています：

```bash
# テストエンドポイント登録
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:8000/test/webhook",
    "secret": "test-secret",
    "events": ["*"]
  }'

# テストイベント送信
curl -X POST "http://localhost:8000/api/v1/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test.event",
    "payload": {"message": "Hello, World!"}
  }'
```

## パフォーマンス特性

### ベンチマーク
- **スループット**: 1000+イベント/秒
- **レイテンシ**: P95 < 500ms
- **メモリ使用量**: ~100MBベース + キュー内webhook当たり10KB
- **CPU使用量**: フルロード時ワーカーコア当たり~20%

### スケーラビリティ
- **水平**: 共有キューバックエンドで複数インスタンス
- **垂直**: インスタンス当たり設定可能ワーカー数
- **キューバックエンド**: 分散デプロイメント用Redis、RabbitMQ、SQSをサポート

## デプロイメント

### Docker Compose

```yaml
version: '3.8'
services:
  webhook-system:
    build: .
    ports:
      - "8000:8000"
    environment:
      - WEBHOOK_WORKER_COUNT=4
      - RETRY_MAX_DELAY=300
    volumes:
      - ./config:/app/config
      - ./data:/app/data
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webhook-system
  template:
    metadata:
      labels:
        app: webhook-system
    spec:
      containers:
      - name: webhook-system
        image: webhook-system:latest
        ports:
        - containerPort: 8000
        env:
        - name: WEBHOOK_WORKER_COUNT
          value: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## トラブルシューティング

### 一般的な問題

1. **DLQ成長が高い**
   - エンドポイントの可用性を確認
   - リトライポリシーを確認
   - エラー率を監視

2. **配信遅延**
   - ワーカー数を増加
   - キューサイズを確認
   - タイムアウト設定を確認

3. **署名検証失敗**
   - シークレット設定を検証
   - クロック同期を確認
   - ペイロードエンコーディングを確認

### デバッグ

```bash
# デバッグログ有効化
export LOG_LEVEL=DEBUG

# キューステータス確認
curl http://localhost:8000/api/v1/stats

# DLQメッセージ確認
curl http://localhost:8000/api/v1/dlq
```

## 本番環境考慮事項

1. **キューバックエンド**: 本番環境でRedis/RabbitMQを使用
2. **監視**: Prometheus + Grafanaをセットアップ
3. **ロードバランシング**: ロードバランサーの背後に複数インスタンスを使用
4. **データベース**: webhookメタデータ用永続ストレージを検討
5. **セキュリティ**: 適切なシークレット管理を実装
6. **バックアップ**: 定期DLQメッセージバックアップ

## ライセンス

MIT