# MESH-001: Service Mesh Control Plane

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

Production-grade service mesh control plane implementing mTLS, traffic management, observability, and policy enforcement for microservices.

## Architecture

### Core Components

1. **Control Plane**
   - Configuration management
   - Service registry
   - Certificate authority
   - Policy engine
   - Telemetry collection

2. **Data Plane Proxy**
   - Sidecar injection
   - mTLS termination
   - Load balancing
   - Circuit breaking
   - Request routing

3. **Certificate Management**
   - SPIFFE identity
   - Certificate rotation
   - mTLS enforcement
   - Trust domain management

4. **Traffic Management**
   - Canary deployments
   - A/B testing
   - Blue-green deployments
   - Fault injection
   - Retry policies

5. **Observability Stack**
   - Distributed tracing
   - Metrics aggregation
   - Access logging
   - Service topology

## Features

### Security
- Automatic mTLS between services
- SPIFFE-based service identity
- Policy-based access control
- Certificate rotation
- Encryption at rest

### Traffic Control
- Intelligent load balancing
- Circuit breaking
- Retry with backoff
- Timeout management
- Rate limiting

### Observability
- Distributed tracing (OpenTelemetry)
- Golden metrics (RED/USE)
- Service dependency graph
- Real-time dashboards
- Alert management

### Policy Management
```yaml
apiVersion: security.mesh.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: frontend-policy
spec:
  selector:
    matchLabels:
      app: frontend
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/default/sa/backend"]
    to:
    - operation:
        methods: ["GET", "POST"]
```

## Testing

- mTLS validation tests
- Traffic routing scenarios
- Circuit breaker behavior
- Policy enforcement
- Multi-cluster federation
- Performance benchmarks

## Deployment

```bash
# Install control plane
meshctl install --set profile=production

# Deploy sample application
kubectl apply -f examples/bookinfo.yaml

# Configure traffic management
kubectl apply -f config/traffic-rules.yaml

# View service graph
meshctl dashboard
```

## Monitoring

- Request rate, error rate, duration (RED)
- Utilization, saturation, errors (USE)
- Certificate expiration
- Policy violations
- Circuit breaker trips
- Retry exhaustion

## Dependencies

### Go Implementation
- `envoyproxy/go-control-plane`: Envoy xDS APIs
- `spiffe/go-spiffe`: SPIFFE library
- `grpc-go`: RPC framework
- `opentelemetry-go`: Observability
- `prometheus/client_golang`: Metrics
- `hashicorp/consul`: Service discovery

---

<a id="japanese"></a>
## 日本語

# MESH-001: サービスメッシュ コントロールプレーン

## 概要

マイクロサービスのmTLS、トラフィック管理、可観測性、ポリシー適用を実装するプロダクショングレードのサービスメッシュ コントロールプレーンです。

## アーキテクチャ

### コア コンポーネント

1. **コントロールプレーン**
   - 設定管理
   - サービスレジストリ
   - 証明書局
   - ポリシーエンジン
   - テレメトリ収集

2. **データプレーン プロキシ**
   - サイドカーインジェクション
   - mTLS終端処理
   - ロードバランシング
   - サーキットブレーカー
   - リクエストルーティング

3. **証明書管理**
   - SPIFFEアイデンティティ
   - 証明書ローテーション
   - mTLS適用
   - 信頼ドメイン管理

4. **トラフィック管理**
   - カナリアデプロイメント
   - A/Bテスト
   - ブルーグリーンデプロイメント
   - 障害インジェクション
   - 再試行ポリシー

5. **可観測性スタック**
   - 分散トレーシング
   - メトリクス集約
   - アクセスログ
   - サービストポロジー

## 機能

### セキュリティ
- サービス間の自動mTLS
- SPIFFEベースのサービスアイデンティティ
- ポリシーベースのアクセス制御
- 証明書ローテーション
- 保存時の暗号化

### トラフィック制御
- インテリジェントロードバランシング
- サーキットブレーカー
- バックオフ付き再試行
- タイムアウト管理
- レート制限

### 可観測性
- 分散トレーシング（OpenTelemetry）
- ゴールデンメトリクス（RED/USE）
- サービス依存グラフ
- リアルタイムダッシュボード
- アラート管理

### ポリシー管理
```yaml
apiVersion: security.mesh.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: frontend-policy
spec:
  selector:
    matchLabels:
      app: frontend
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/default/sa/backend"]
    to:
    - operation:
        methods: ["GET", "POST"]
```

## テスト

- mTLS検証テスト
- トラフィックルーティングシナリオ
- サーキットブレーカー動作
- ポリシー適用
- マルチクラスター連搭
- パフォーマンスベンチマーク

## デプロイメント

```bash
# コントロールプレーンインストール
meshctl install --set profile=production

# サンプルアプリケーションデプロイ
 kubectl apply -f examples/bookinfo.yaml

# トラフィック管理設定
kubectl apply -f config/traffic-rules.yaml

# サービスグラフ表示
meshctl dashboard
```

## 監視

- リクエスト率、エラー率、持続時間（RED）
- 使用率、飽和率、エラー（USE）
- 証明書有効期限
- ポリシー違反
- サーキットブレーカー作動
- 再試行不足

## 依存関係

### Go実装
- `envoyproxy/go-control-plane`: Envoy xDS API
- `spiffe/go-spiffe`: SPIFFEライブラリ
- `grpc-go`: RPCフレームワーク
- `opentelemetry-go`: 可観測性
- `prometheus/client_golang`: メトリクス
- `hashicorp/consul`: サービスディスカバリ