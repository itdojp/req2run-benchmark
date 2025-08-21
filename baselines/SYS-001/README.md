# SYS-001: Distributed Lock Coordinator Service - Baseline Implementation

**Languages / 言語:** [English](#english) | [日本語](#japanese)

## English

## Overview

This baseline implementation provides a distributed lock coordination service using the Raft consensus algorithm. It implements distributed mutual exclusion, leader election, and linearizable consistency guarantees.

## Architecture

```
┌─────────────────────────────────────────────┐
│              Client Applications            │
└─────────────┬───────────────────────────────┘
              │ Lock/Unlock Requests
              ▼
┌─────────────────────────────────────────────┐
│            gRPC/HTTP API Layer              │
├─────────────────────────────────────────────┤
│           Lock Manager Service              │
│  - Distributed Locks                        │
│  - Semaphores                               │
│  - Read-Write Locks                         │
├─────────────────────────────────────────────┤
│         Consensus Layer (Raft)              │
│  - Leader Election                          │
│  - Log Replication                          │
│  - Linearizable Reads                       │
├─────────────────────────────────────────────┤
│           State Machine                     │
│  - Lock Registry                            │
│  - Client Sessions                          │
│  - Lease Management                         │
└─────────────────────────────────────────────┘
```

## Features

### Core Features (MUST)
- ✅ Distributed mutual exclusion locks
- ✅ Lock acquisition with timeout
- ✅ Leader election using Raft consensus
- ✅ Network partition handling
- ✅ Linearizable consistency
- ✅ Distributed semaphores
- ✅ Automatic lock release on client failure

### Additional Features (SHOULD/MAY)
- ✅ Read-write locks
- ✅ Lock wait queue visibility
- ⚠️ Distributed barriers (partial)

## API Endpoints

### Lock Operations
- `POST /locks/{name}/acquire` - Acquire a lock
- `POST /locks/{name}/release` - Release a lock
- `GET /locks/{name}/status` - Get lock status
- `POST /locks/{name}/renew` - Renew lock lease

### Semaphore Operations
- `POST /semaphores/{name}/acquire` - Acquire semaphore permit
- `POST /semaphores/{name}/release` - Release semaphore permit
- `GET /semaphores/{name}/status` - Get semaphore status

### Leader Election
- `POST /election/{name}/campaign` - Start leader campaign
- `POST /election/{name}/resign` - Resign leadership
- `GET /election/{name}/leader` - Get current leader

### Health & Monitoring
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /cluster/status` - Cluster status

## Performance Characteristics

- **Lock Acquisition**: P95 < 10ms, P99 < 50ms
- **Throughput**: 10,000+ operations/second
- **Leader Election**: < 1 second
- **Network Partition Recovery**: < 5 seconds

## Building and Running

### Prerequisites
- Go 1.21+ (for Go implementation)
- Docker 24.0+
- Make

### Build
```bash
make build
```

### Run Single Node (Development)
```bash
./distributed-lock --config config/single.yaml
```

### Run Cluster (Production)
```bash
# Node 1
./distributed-lock --config config/node1.yaml

# Node 2
./distributed-lock --config config/node2.yaml

# Node 3
./distributed-lock --config config/node3.yaml
```

### Docker
```bash
docker build -t distributed-lock .
docker run -p 8080:8080 -p 9090:9090 distributed-lock
```

## Testing

### Unit Tests
```bash
make test-unit
```

### Integration Tests
```bash
make test-integration
```

### Chaos Tests
```bash
make test-chaos
```

### Performance Tests
```bash
make test-performance
```

## Configuration

See `config/cluster.yaml` for cluster configuration options:

```yaml
cluster:
  node_id: "node-1"
  peers:
    - "node-2:9090"
    - "node-3:9090"
  
consensus:
  algorithm: "raft"
  election_timeout_ms: 300
  heartbeat_interval_ms: 100
  
locks:
  default_ttl_seconds: 30
  max_wait_time_seconds: 60
  cleanup_interval_seconds: 10
```

## Monitoring

The service exposes Prometheus metrics on port 9090:

- `lock_acquisitions_total` - Total lock acquisitions
- `lock_acquisition_duration_seconds` - Lock acquisition latency
- `active_locks_gauge` - Currently held locks
- `leader_elections_total` - Leader election count
- `consensus_commit_latency_seconds` - Consensus commit latency

## Security

- TLS encryption for all network communication
- Client authentication via mTLS or API keys
- Access control lists for lock namespaces
- Audit logging for all operations

## Limitations

- Maximum 100,000 concurrent locks
- Maximum cluster size: 7 nodes (for optimal performance)
- Lock names limited to 256 characters
- Client session timeout: 30 seconds

## License

MIT

---

## Japanese

# SYS-001: 分散ロックコーディネーターサービス - ベースライン実装

## 概要

このベースライン実装は、Raftコンセンサスアルゴリズムを使用した分散ロックコーディネーションサービスを提供します。分散相互排除、リーダー選出、線形化可能一貫性保証を実装しています。

## アーキテクチャ

```
┌─────────────────────────────────────────────┐
│              Client Applications            │
└─────────────┬───────────────────────────────┘
              │ Lock/Unlock Requests
              ▼
┌─────────────────────────────────────────────┐
│            gRPC/HTTP API Layer              │
├─────────────────────────────────────────────┤
│           Lock Manager Service              │
│  - Distributed Locks                        │
│  - Semaphores                               │
│  - Read-Write Locks                         │
├─────────────────────────────────────────────┤
│         Consensus Layer (Raft)              │
│  - Leader Election                          │
│  - Log Replication                          │
│  - Linearizable Reads                       │
├─────────────────────────────────────────────┤
│           State Machine                     │
│  - Lock Registry                            │
│  - Client Sessions                          │
│  - Lease Management                         │
└─────────────────────────────────────────────┘
```

## 機能

### コア機能 (必須)
- ✅ 分散相互排除ロック
- ✅ タイムアウト付きロック取得
- ✅ Raftコンセンサスによるリーダー選出
- ✅ ネットワーク分断処理
- ✅ 線形化可能一貫性
- ✅ 分散セマフォ
- ✅ クライアント障害時の自動ロック解放

### 追加機能 (推奨/任意)
- ✅ 読み書きロック
- ✅ ロック待機キューの可視化
- ⚠️ 分散バリア（部分実装）

## APIエンドポイント

### ロック操作
- `POST /locks/{name}/acquire` - ロックの取得
- `POST /locks/{name}/release` - ロックの解放
- `GET /locks/{name}/status` - ロック状態の取得
- `POST /locks/{name}/renew` - ロックリースの更新

### セマフォ操作
- `POST /semaphores/{name}/acquire` - セマフォ許可の取得
- `POST /semaphores/{name}/release` - セマフォ許可の解放
- `GET /semaphores/{name}/status` - セマフォ状態の取得

### リーダー選出
- `POST /election/{name}/campaign` - リーダー選挙の開始
- `POST /election/{name}/resign` - リーダーシップの辞任
- `GET /election/{name}/leader` - 現在のリーダーの取得

### ヘルス・モニタリング
- `GET /health` - ヘルスチェック
- `GET /metrics` - Prometheusメトリクス
- `GET /cluster/status` - クラスター状態

## パフォーマンス特性

- **ロック取得**: P95 < 10ms、P99 < 50ms
- **スループット**: 10,000+ 操作/秒
- **リーダー選出**: < 1秒
- **ネットワーク分断復旧**: < 5秒

## ビルドと実行

### 前提条件
- Go 1.21+（Go実装の場合）
- Docker 24.0+
- Make

### ビルド
```bash
make build
```

### 単一ノード実行（開発環境）
```bash
./distributed-lock --config config/single.yaml
```

### クラスター実行（本番環境）
```bash
# ノード1
./distributed-lock --config config/node1.yaml

# ノード2
./distributed-lock --config config/node2.yaml

# ノード3
./distributed-lock --config config/node3.yaml
```

### Docker
```bash
docker build -t distributed-lock .
docker run -p 8080:8080 -p 9090:9090 distributed-lock
```

## テスト

### 単体テスト
```bash
make test-unit
```

### 統合テスト
```bash
make test-integration
```

### カオステスト
```bash
make test-chaos
```

### パフォーマンステスト
```bash
make test-performance
```

## 設定

クラスター設定オプションについては `config/cluster.yaml` を参照してください：

```yaml
cluster:
  node_id: "node-1"
  peers:
    - "node-2:9090"
    - "node-3:9090"
  
consensus:
  algorithm: "raft"
  election_timeout_ms: 300
  heartbeat_interval_ms: 100
  
locks:
  default_ttl_seconds: 30
  max_wait_time_seconds: 60
  cleanup_interval_seconds: 10
```

## モニタリング

サービスはポート9090でPrometheusメトリクスを公開します：

- `lock_acquisitions_total` - 総ロック取得数
- `lock_acquisition_duration_seconds` - ロック取得レイテンシ
- `active_locks_gauge` - 現在保持されているロック数
- `leader_elections_total` - リーダー選出回数
- `consensus_commit_latency_seconds` - コンセンサスコミットレイテンシ

## セキュリティ

- 全ネットワーク通信のTLS暗号化
- mTLSまたはAPIキーによるクライアント認証
- ロック名前空間のアクセス制御リスト
- 全操作の監査ログ

## 制限事項

- 最大同時ロック数：100,000
- 最大クラスターサイズ：7ノード（最適なパフォーマンスのため）
- ロック名の文字数制限：256文字
- クライアントセッションタイムアウト：30秒

## ライセンス

MIT