# NET-010: Reverse Proxy with Timeout, Retry, and Circuit Breaker - Baseline Implementation

**Language / 言語**
- [English](#net-010-reverse-proxy-with-timeout-retry-and-circuit-breaker---baseline-implementation)
- [日本語](#net-010-タイムアウトリトライサーキットブレーカー機能付きリバースプロキシ---ベースライン実装)

## Overview

This baseline implementation provides a production-grade reverse proxy with resilience patterns including circuit breakers, exponential backoff retry, rate limiting, and health checks. It maintains SLO even when backend services are unstable or experiencing failures.

## Features Implemented

### Core Features (MUST)
- ✅ HTTP/HTTPS request forwarding to backend services
- ✅ Configurable timeouts for backend requests
- ✅ Exponential backoff retry logic
- ✅ Circuit breaker pattern implementation
- ✅ Health checks for backend services
- ✅ Rate limiting per client
- ✅ Preserve original client headers (X-Forwarded-*)
- ✅ Maintain SLO with unstable backends

### Additional Features (SHOULD)
- ✅ WebSocket connection support
- ✅ Request/response caching (configurable)

## Architecture

```
┌─────────────────────────────────────────────┐
│              Client Requests                │
└──────────────────┬──────────────────────────┘
                   │
           ┌───────▼────────┐
           │  Rate Limiter  │
           └───────┬────────┘
                   │
        ┌──────────▼──────────┐
        │   Reverse Proxy     │
        │  - Load Balancing   │
        │  - Retry Logic      │
        └──────────┬──────────┘
                   │
         ┌─────────▼─────────┐
         │  Circuit Breaker  │
         └─────────┬─────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼───┐    ┌────▼────┐    ┌────▼───┐
│Backend│    │Backend 2│    │Backend 3│
└───────┘    └─────────┘    └─────────┘
```

## Resilience Patterns

### Circuit Breaker
- **Closed State**: Normal operation, requests forwarded
- **Open State**: Backend failing, requests rejected immediately
- **Half-Open State**: Testing recovery with limited requests
- **Thresholds**: Configurable failure/success counts
- **Timeout**: Automatic transition to half-open after timeout

### Retry Logic
- **Exponential Backoff**: Delays increase exponentially
- **Max Attempts**: Configurable retry limit
- **Jitter**: Randomization to prevent thundering herd
- **Retry Conditions**: Only on retryable errors (network, timeout)

### Rate Limiting
- **Token Bucket**: Smooth rate limiting with burst capacity
- **Sliding Window**: Alternative algorithm for strict limits
- **Per-Client**: Individual client rate limits
- **Global**: Overall proxy rate limit

### Health Checks
- **Periodic Checks**: Regular backend health verification
- **Failure Threshold**: Mark unhealthy after N failures
- **Recovery Detection**: Automatic re-enable when healthy

## Load Balancing Algorithms

1. **Round Robin**: Equal distribution in order
2. **Random**: Random backend selection
3. **Weighted**: Distribution based on backend weights
4. **Least Connections**: Route to least busy backend

## API Endpoints

### Proxy Endpoints
- `*` - All requests proxied to backends

### Management Endpoints
- `GET /health` - Proxy health status
- `GET /metrics` - Prometheus metrics
- `GET /backends/health` - Backend health status

## Performance Characteristics

- **P95 Latency**: < 50ms overhead
- **P99 Latency**: < 200ms overhead
- **Throughput**: 10,000+ RPS
- **Connection Pool**: 1000 connections
- **CPU Usage**: < 2 cores at peak

## Configuration

### Backend Configuration
```yaml
backends:
  - id: backend1
    url: http://localhost:8001
    weight: 1
    health_check_enabled: true
```

### Circuit Breaker Settings
```yaml
circuit_breaker:
  failure_threshold: 5
  success_threshold: 2
  timeout: 30
```

### Rate Limiting
```yaml
rate_limit:
  requests_per_second: 100
  burst: 200
  per_client:
    requests_per_second: 10
```

## Running the Proxy

### Docker
```bash
docker build -t net-010-proxy .
docker run -p 8080:8080 net-010-proxy
```

### Local Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run proxy
python -m src.main --config config/proxy.yaml
```

## Testing

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Performance Tests
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8080
```

### Chaos Tests
```bash
# Simulate backend failures
pytest tests/chaos/ -v
```

## Monitoring

### Prometheus Metrics
- `proxy_requests_total` - Total requests by status
- `proxy_request_duration_seconds` - Request latency
- `backend_health` - Backend health status
- `circuit_breaker_state` - Circuit breaker states
- `rate_limit_rejected_total` - Rate limited requests

### Health Check Response
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "backends": {
    "healthy": 2,
    "total": 3
  },
  "features": {
    "circuit_breaker": true,
    "rate_limiting": true,
    "health_checks": true
  }
}
```

## Handling Failures

### Backend Failure Scenarios
1. **Connection Timeout**: Retry with exponential backoff
2. **5xx Errors**: Circuit breaker opens after threshold
3. **Network Errors**: Automatic retry with different backend
4. **All Backends Down**: Return 503 Service Unavailable

### Recovery Mechanisms
1. **Automatic Health Checks**: Detect backend recovery
2. **Circuit Breaker Reset**: Gradual traffic restoration
3. **Connection Pool Recovery**: Automatic reconnection
4. **Rate Limit Reset**: Sliding window cleanup

## Security Considerations

1. **Header Filtering**: Remove sensitive headers
2. **Request Size Limits**: Prevent DoS attacks
3. **Rate Limiting**: Protect against abuse
4. **TLS Support**: Encrypted backend connections
5. **Access Logging**: Audit trail for requests

## Production Deployment

### Recommendations
1. Deploy multiple proxy instances for HA
2. Use external load balancer for proxy instances
3. Configure appropriate timeouts for your backends
4. Monitor circuit breaker states
5. Set rate limits based on capacity planning
6. Enable access logging for debugging

### Scaling
- Horizontal: Add more proxy instances
- Vertical: Increase connection pool and resources
- Backend: Add more backend servers

## License

MIT

---

# NET-010: タイムアウト、リトライ、サーキットブレーカー機能付きリバースプロキシ - ベースライン実装

## 概要

このベースライン実装では、サーキットブレーカー、指数バックオフリトライ、レート制限、ヘルスチェックなどの回復性パターンを備えた本格的なリバースプロキシを提供します。バックエンドサービスが不安定または障害が発生している場合でも、SLOを維持します。

## 実装済み機能

### コア機能（MUST）
- ✅ バックエンドサービスへのHTTP/HTTPSリクエスト転送
- ✅ バックエンドリクエストの設定可能なタイムアウト
- ✅ 指数バックオフリトライロジック
- ✅ サーキットブレーカーパターン実装
- ✅ バックエンドサービスのヘルスチェック
- ✅ クライアント別レート制限
- ✅ 元のクライアントヘッダーの保持（X-Forwarded-*）
- ✅ 不安定なバックエンドでのSLO維持

### 追加機能（SHOULD）
- ✅ WebSocket接続サポート
- ✅ リクエスト/レスポンスキャッシュ（設定可能）

## アーキテクチャ

```
┌─────────────────────────────────────────────┐
│              Client Requests                │
└──────────────────┬──────────────────────────┘
                   │
           ┌───────▼────────┐
           │  Rate Limiter  │
           └───────┬────────┘
                   │
        ┌──────────▼──────────┐
        │   Reverse Proxy     │
        │  - Load Balancing   │
        │  - Retry Logic      │
        └──────────┬──────────┘
                   │
         ┌─────────▼─────────┐
         │  Circuit Breaker  │
         └─────────┬─────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼───┐    ┌────▼────┐    ┌────▼───┐
│Backend│    │Backend 2│    │Backend 3│
└───────┘    └─────────┘    └─────────┘
```

## 回復性パターン

### サーキットブレーカー
- **クローズ状態**: 通常動作、リクエストを転送
- **オープン状態**: バックエンド障害、リクエストを即座に拒否
- **ハーフオープン状態**: 限定的なリクエストで回復をテスト
- **しきい値**: 設定可能な失敗/成功カウント
- **タイムアウト**: タイムアウト後に自動的にハーフオープンに遷移

### リトライロジック
- **指数バックオフ**: 遅延が指数関数的に増加
- **最大試行回数**: 設定可能なリトライ制限
- **ジッター**: サンダリングハードを防ぐランダム化
- **リトライ条件**: リトライ可能なエラーのみ（ネットワーク、タイムアウト）

### レート制限
- **トークンバケット**: バースト容量を持つスムーズなレート制限
- **スライディングウィンドウ**: 厳格な制限のための代替アルゴリズム
- **クライアント別**: 個別のクライアントレート制限
- **グローバル**: プロキシ全体のレート制限

### ヘルスチェック
- **定期的チェック**: 定期的なバックエンドヘルス確認
- **失敗しきい値**: N回失敗後に不健全とマーク
- **回復検出**: 健全になったときに自動再有効化

## ロードバランシングアルゴリズム

1. **ラウンドロビン**: 順次等分散分散
2. **ランダム**: ランダムなバックエンド選択
3. **重み付き**: バックエンドの重みに基づく分散
4. **最小接続**: 最も忙しくないバックエンドにルーティング

## APIエンドポイント

### プロキシエンドポイント
- `*` - すべてのリクエストをバックエンドにプロキシ

### 管理エンドポイント
- `GET /health` - プロキシヘルスステータス
- `GET /metrics` - Prometheusメトリクス
- `GET /backends/health` - バックエンドヘルスステータス

## パフォーマンス特性

- **P95レイテンシ**: < 50msオーバーヘッド
- **P99レイテンシ**: < 200msオーバーヘッド
- **スループット**: 10,000+ RPS
- **コネクションプール**: 1000接続
- **CPU使用率**: ピーク時< 2コア

## 設定

### バックエンド設定
```yaml
backends:
  - id: backend1
    url: http://localhost:8001
    weight: 1
    health_check_enabled: true
```

### サーキットブレーカー設定
```yaml
circuit_breaker:
  failure_threshold: 5
  success_threshold: 2
  timeout: 30
```

### レート制限
```yaml
rate_limit:
  requests_per_second: 100
  burst: 200
  per_client:
    requests_per_second: 10
```

## プロキシの実行

### Docker
```bash
docker build -t net-010-proxy .
docker run -p 8080:8080 net-010-proxy
```

### ローカルインストール
```bash
# 依存関係のインストール
pip install -r requirements.txt

# プロキシの実行
python -m src.main --config config/proxy.yaml
```

## テスト

### ユニットテスト
```bash
pytest tests/unit/ -v
```

### 統合テスト
```bash
pytest tests/integration/ -v
```

### パフォーマンステスト
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8080
```

### カオステスト
```bash
# バックエンド障害のシミュレート
pytest tests/chaos/ -v
```

## 監視

### Prometheusメトリクス
- `proxy_requests_total` - ステータス別総リクエスト数
- `proxy_request_duration_seconds` - リクエストレイテンシ
- `backend_health` - バックエンドヘルスステータス
- `circuit_breaker_state` - サーキットブレーカーの状態
- `rate_limit_rejected_total` - レート制限されたリクエスト数

### ヘルスチェックレスポンス
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "backends": {
    "healthy": 2,
    "total": 3
  },
  "features": {
    "circuit_breaker": true,
    "rate_limiting": true,
    "health_checks": true
  }
}
```

## 障害処理

### バックエンド障害シナリオ
1. **接続タイムアウト**: 指数バックオフでリトライ
2. **5xxエラー**: しきい値後にサーキットブレーカーが開く
3. **ネットワークエラー**: 異なるバックエンドで自動リトライ
4. **全バックエンドダウン**: 503 Service Unavailableを返す

### 回復メカニズム
1. **自動ヘルスチェック**: バックエンドの回復を検出
2. **サーキットブレーカーリセット**: 段階的なトラフィック回復
3. **コネクションプール回復**: 自動再接続
4. **レート制限リセット**: スライディングウィンドウクリーンアップ

## セキュリティ考慮事項

1. **ヘッダーフィルタリング**: 機密ヘッダーの除去
2. **リクエストサイズ制限**: DoS攻撃の防止
3. **レート制限**: 悪用からの保護
4. **TLSサポート**: 暗号化されたバックエンド接続
5. **アクセスログ**: リクエストの監査証跡

## 本番デプロイ

### 推奨事項
1. HAのために複数のプロキシインスタンスをデプロイ
2. プロキシインスタンス用の外部ロードバランサーを使用
3. バックエンドに適切なタイムアウトを設定
4. サーキットブレーカーの状態を監視
5. キャパシティプランニングに基づいてレート制限を設定
6. デバッグのためにアクセスログを有効化

### スケーリング
- 水平: より多くのプロキシインスタンスを追加
- 垂直: コネクションプールとリソースを増加
- バックエンド: より多くのバックエンドサーバーを追加

## ライセンス

MIT