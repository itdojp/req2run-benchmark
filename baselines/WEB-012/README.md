# WEB-012: Rate Limiting and Retry Design with Idempotency Keys

**Language:** [English](#english) | [日本語](#japanese)

---

## English

## Overview

Production-grade payment processing API implementing comprehensive rate limiting, retry mechanisms, and idempotency key handling. This system ensures reliable payment processing with protection against duplicate charges, rate limit abuse, and concurrent request conflicts.

## Key Features

### Rate Limiting
- **Multiple Strategies**: Sliding window and token bucket algorithms
- **Distributed Rate Limiting**: Redis-backed with Lua scripts for atomicity
- **Flexible Scopes**: Global, per-user, per-IP, per-endpoint limits
- **Burst Handling**: Token bucket algorithm for handling burst traffic
- **Real-time Headers**: X-RateLimit-* headers on all responses

### Idempotency Support
- **Duplicate Prevention**: Prevents duplicate payment processing
- **Request Validation**: Ensures identical requests with same idempotency key
- **Concurrent Handling**: Distributed locking for concurrent requests
- **Response Caching**: Returns cached responses for replayed requests
- **TTL Management**: Automatic cleanup of expired keys

### Retry Mechanisms
- **Client Configuration**: Recommended retry strategies with exponential backoff
- **Jitter Support**: Prevents thundering herd problem
- **Smart Headers**: Retry-After headers for rate-limited requests
- **Circuit Breaking**: Automatic failure detection and recovery

### Audit & Monitoring
- **Comprehensive Logging**: Structured logging with contextual information
- **Audit Trail**: Complete audit log of all payment attempts
- **Metrics Export**: Prometheus metrics for monitoring
- **Health Checks**: Liveness and readiness endpoints

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  Rate       │────▶│  Idempotency│
│             │     │  Limiter    │     │  Manager    │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Redis    │     │  PostgreSQL │
                    │   (Cache)   │     │  (Database) │
                    └─────────────┘     └─────────────┘
```

## API Endpoints

### Payment Processing
- `POST /api/v1/payments` - Process payment with idempotency key
- `GET /api/v1/payments/{transaction_id}` - Get payment status

### Configuration & Monitoring
- `GET /api/v1/retry-config` - Get recommended retry configuration
- `GET /api/v1/rate-limits` - Get current rate limit status
- `GET /api/v1/audit-logs` - Get audit logs for user
- `GET /health` - Health check endpoint

### Testing
- `POST /api/v1/simulate-concurrent` - Test concurrent request handling

## Quick Start

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f app
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/payments
export REDIS_URL=redis://localhost:6379
export API_KEY=your-secret-key
```

3. **Run application:**
```bash
cd src
python main.py
```

## Usage Examples

### Process Payment with Idempotency

```bash
# Generate unique idempotency key
IDEMPOTENCY_KEY=$(uuidgen)

# Process payment
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d '{
    "amount": 99.99,
    "currency": "USD",
    "description": "Premium subscription",
    "payment_method": "credit_card",
    "metadata": {
      "customer_id": "cust_123",
      "order_id": "ord_456"
    }
  }'
```

### Retry Same Request (Idempotent)

```bash
# Retry with same idempotency key - returns cached response
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d '{
    "amount": 99.99,
    "currency": "USD",
    "description": "Premium subscription",
    "payment_method": "credit_card"
  }'
```

### Check Rate Limits

```bash
curl -X GET http://localhost:8000/api/v1/rate-limits \
  -H "Authorization: Bearer test-api-key"
```

### Get Retry Configuration

```bash
curl -X GET http://localhost:8000/api/v1/retry-config
```

### Test Concurrent Requests

```bash
# Simulate 10 concurrent requests with same idempotency key
curl -X POST http://localhost:8000/api/v1/simulate-concurrent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -H "Idempotency-Key: test-concurrent-key" \
  -d '{
    "amount": 50.00,
    "currency": "USD",
    "payment_method": "credit_card"
  }' \
  --data-urlencode "concurrent_count=10"
```

## Rate Limiting Rules

Default rate limits (configurable):

| Scope | Limit | Window | Algorithm |
|-------|-------|--------|-----------|
| Global | 1000 req | 60s | Sliding Window |
| Per User | 100 req | 60s | Sliding Window |
| Payment Endpoint | 10 req | 60s | Sliding Window |
| Burst | 20 req/s | 1s | Token Bucket (50 burst) |

## Idempotency Key Requirements

- **Format**: 16-255 characters, alphanumeric + hyphens/underscores
- **TTL**: 24 hours by default
- **Scope**: Per-user (different users can use same key)
- **Validation**: Request body must match for same key

## Client Best Practices

### Retry Strategy

```python
import time
import random
import httpx

def retry_with_backoff(func, max_retries=3):
    """Exponential backoff with jitter"""
    for attempt in range(max_retries):
        try:
            return func()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limited - use Retry-After header
                retry_after = int(e.response.headers.get('Retry-After', 1))
                time.sleep(retry_after)
            elif e.response.status_code >= 500:
                # Server error - exponential backoff
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(min(delay, 30))
            else:
                raise
    raise Exception("Max retries exceeded")
```

### Idempotency Key Generation

```python
import uuid
import hashlib

def generate_idempotency_key(user_id, operation, params):
    """Generate deterministic idempotency key"""
    data = f"{user_id}:{operation}:{sorted(params.items())}"
    return hashlib.sha256(data.encode()).hexdigest()

# Or use random UUID
idempotency_key = str(uuid.uuid4())
```

## Monitoring

### Prometheus Metrics

Available at `http://localhost:8000/metrics`:

- `payment_requests_total` - Total payment requests
- `payment_success_rate` - Success rate percentage
- `rate_limit_exceeded_total` - Rate limit violations
- `idempotent_replays_total` - Cached response replays
- `concurrent_conflicts_total` - Concurrent request conflicts

### Health Checks

```bash
# Liveness probe
curl http://localhost:8000/health

# Check specific service
curl http://localhost:8000/health | jq '.services'
```

## Testing

### Unit Tests

```bash
pytest tests/ -v --cov=src
```

### Load Testing

```bash
# Using locust
locust -f tests/load_test.py --host=http://localhost:8000
```

### Concurrent Testing

```bash
# Test idempotency with parallel requests
python tests/test_concurrent.py
```

## Security Considerations

1. **API Keys**: Always use secure, rotated API keys
2. **HTTPS**: Deploy with TLS termination in production
3. **Database**: Use encrypted connections and strong passwords
4. **Redis**: Configure with authentication in production
5. **Secrets**: Use environment variables or secret management systems

## Performance Tuning

### Database Optimization
- Indexed columns: user_id, idempotency_key, created_at
- Connection pooling: 20 connections default
- Async operations for non-blocking I/O

### Redis Optimization
- Lua scripts for atomic operations
- Pipeline operations for batch processing
- Appropriate TTLs to prevent memory bloat

### Application Optimization
- Async/await throughout for concurrency
- Background task for cleanup operations
- Efficient request hashing and caching

## Troubleshooting

### Common Issues

1. **"Idempotency key already in use"**
   - Different request body with same key
   - Solution: Use new key or ensure identical request

2. **"Rate limit exceeded"**
   - Too many requests in time window
   - Solution: Implement retry with backoff

3. **"Lock acquisition timeout"**
   - Concurrent requests taking too long
   - Solution: Increase timeout or retry later

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python src/main.py
```

## License

MIT

---

## Japanese

# WEB-012: 冪等性キーを使用したレート制限とリトライ設計

## 概要

包括的なレート制限、リトライメカニズム、冪等性キー処理を実装した本格的な決済処理API。このシステムは、重複課金、レート制限の悪用、同時リクエストの競合から保護し、信頼性の高い決済処理を保証します。

## 主要機能

### レート制限
- **複数戦略**: スライディングウィンドウとトークンバケットアルゴリズム
- **分散レート制限**: 原子性を保証するLuaスクリプトを使用したRedisベース
- **柔軟なスコープ**: グローバル、ユーザー単位、IP単位、エンドポイント単位の制限
- **バースト処理**: バーストトラフィック処理のためのトークンバケットアルゴリズム
- **リアルタイムヘッダー**: すべてのレスポンスにX-RateLimit-*ヘッダー

### 冪等性サポート
- **重複防止**: 重複決済処理の防止
- **リクエスト検証**: 同じ冪等性キーでの同一リクエストの保証
- **同時処理**: 同時リクエスト用の分散ロック
- **レスポンスキャッシュ**: 再実行リクエストのキャッシュレスポンス返却
- **TTL管理**: 期限切れキーの自動クリーンアップ

### リトライメカニズム
- **クライアント設定**: 指数バックオフ付き推奨リトライ戦略
- **ジッター対応**: サンダリングハード問題の防止
- **スマートヘッダー**: レート制限されたリクエスト用のRetry-Afterヘッダー
- **サーキットブレーキング**: 自動障害検出と回復

### 監査・監視
- **包括的ログ**: コンテキスト情報付き構造化ログ
- **監査証跡**: すべての決済試行の完全な監査ログ
- **メトリクス出力**: 監視用Prometheusメトリクス
- **ヘルスチェック**: 生存性と準備性エンドポイント

## アーキテクチャ

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  Rate       │────▶│  Idempotency│
│             │     │  Limiter    │     │  Manager    │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Redis    │     │  PostgreSQL │
                    │   (Cache)   │     │  (Database) │
                    └─────────────┘     └─────────────┘
```

## APIエンドポイント

### 決済処理
- `POST /api/v1/payments` - 冪等性キー付き決済処理
- `GET /api/v1/payments/{transaction_id}` - 決済ステータス取得

### 設定・監視
- `GET /api/v1/retry-config` - 推奨リトライ設定取得
- `GET /api/v1/rate-limits` - 現在のレート制限ステータス取得
- `GET /api/v1/audit-logs` - ユーザーの監査ログ取得
- `GET /health` - ヘルスチェックエンドポイント

### テスト
- `POST /api/v1/simulate-concurrent` - 同時リクエスト処理テスト

## クイックスタート

### Docker Composeの使用

```bash
# すべてのサービス開始
docker-compose up -d

# サービスヘルス確認
docker-compose ps

# ログ表示
docker-compose logs -f app
```

### 手動セットアップ

1. **依存関係インストール:**
```bash
pip install -r requirements.txt
```

2. **環境設定:**
```bash
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/payments
export REDIS_URL=redis://localhost:6379
export API_KEY=your-secret-key
```

3. **アプリケーション実行:**
```bash
cd src
python main.py
```

## 使用例

### 冪等性付き決済処理

```bash
# 一意の冪等性キー生成
IDEMPOTENCY_KEY=$(uuidgen)

# 決済処理
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -d '{
    "amount": 99.99,
    "currency": "USD",
    "description": "プレミアムサブスクリプション",
    "payment_method": "credit_card",
    "metadata": {
      "customer_id": "cust_123",
      "order_id": "ord_456"
    }
  }'
```

### レート制限確認

```bash
curl -X GET http://localhost:8000/api/v1/rate-limits \
  -H "Authorization: Bearer test-api-key"
```

### リトライ設定取得

```bash
curl -X GET http://localhost:8000/api/v1/retry-config
```

## レート制限ルール

デフォルトレート制限（設定可能）：

| スコープ | 制限 | ウィンドウ | アルゴリズム |
|-------|-------|--------|--------|
| グローバル | 1000 req | 60s | スライディングウィンドウ |
| ユーザー単位 | 100 req | 60s | スライディングウィンドウ |
| 決済エンドポイント | 10 req | 60s | スライディングウィンドウ |
| バースト | 20 req/s | 1s | トークンバケット（50バースト） |

## 冪等性キー要件

- **形式**: 16-255文字、英数字+ハイフン/アンダースコア
- **TTL**: デフォルト24時間
- **スコープ**: ユーザー単位（異なるユーザーは同じキー使用可能）
- **検証**: 同じキーでリクエストボディが一致する必要

## クライアントベストプラクティス

### リトライ戦略

```python
import time
import random
import httpx

def retry_with_backoff(func, max_retries=3):
    """指数バックオフとジッター"""
    for attempt in range(max_retries):
        try:
            return func()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # レート制限 - Retry-Afterヘッダー使用
                retry_after = int(e.response.headers.get('Retry-After', 1))
                time.sleep(retry_after)
            elif e.response.status_code >= 500:
                # サーバーエラー - 指数バックオフ
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(min(delay, 30))
            else:
                raise
    raise Exception("最大リトライ回数を超過")
```

### 冪等性キー生成

```python
import uuid
import hashlib

def generate_idempotency_key(user_id, operation, params):
    """決定論的冪等性キー生成"""
    data = f"{user_id}:{operation}:{sorted(params.items())}"
    return hashlib.sha256(data.encode()).hexdigest()

# またはランダムUUID使用
idempotency_key = str(uuid.uuid4())
```

## 監視

### Prometheusメトリクス

`http://localhost:8000/metrics`で利用可能：

- `payment_requests_total` - 決済リクエスト総数
- `payment_success_rate` - 成功率パーセンテージ
- `rate_limit_exceeded_total` - レート制限違反数
- `idempotent_replays_total` - キャッシュレスポンス再生数
- `concurrent_conflicts_total` - 同時リクエスト競合数

### ヘルスチェック

```bash
# 生存性プローブ
curl http://localhost:8000/health

# 特定サービス確認
curl http://localhost:8000/health | jq '.services'
```

## テスト

### ユニットテスト

```bash
pytest tests/ -v --cov=src
```

### 負荷テスト

```bash
# locustの使用
locust -f tests/load_test.py --host=http://localhost:8000
```

### 同時テスト

```bash
# 並列リクエストでの冪等性テスト
python tests/test_concurrent.py
```

## セキュリティ考慮事項

1. **APIキー**: 常にセキュアでローテーションされたAPIキーを使用
2. **HTTPS**: 本番環境でTLS終端をデプロイ
3. **データベース**: 暗号化接続と強力なパスワードを使用
4. **Redis**: 本番環境で認証を設定
5. **シークレット**: 環境変数またはシークレット管理システムを使用

## パフォーマンスチューニング

### データベース最適化
- インデックス付きカラム：user_id、idempotency_key、created_at
- 接続プール：デフォルト20接続
- ノンブロッキングI/O用非同期操作

### Redis最適化
- 原子操作用Luaスクリプト
- バッチ処理用パイプライン操作
- メモリ膨張防止のための適切なTTL

### アプリケーション最適化
- 同時性のための全体的なasync/await
- クリーンアップ操作用バックグラウンドタスク
- 効率的なリクエストハッシュとキャッシュ

## トラブルシューティング

### 一般的な問題

1. **「冪等性キーは既に使用中」**
   - 同じキーで異なるリクエストボディ
   - 解決策：新しいキーを使用するか同一リクエストを保証

2. **「レート制限を超過」**
   - 時間ウィンドウ内のリクエスト数過多
   - 解決策：バックオフ付きリトライを実装

3. **「ロック取得タイムアウト」**
   - 同時リクエストの処理時間が長すぎる
   - 解決策：タイムアウトを増加または後でリトライ

### デバッグモード

```bash
# デバッグログ有効化
export LOG_LEVEL=DEBUG
python src/main.py
```

## ライセンス

MIT