# AUTH-011: RBAC/ABAC Hybrid Authorization System - Baseline Implementation

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

A high-performance, production-grade authorization system that combines Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) with advanced features including policy inheritance, time-based policies, permission delegation, and comprehensive audit logging.

## Key Features

### RBAC (Role-Based Access Control)
- Hierarchical role structure with inheritance
- Permission-based access control
- Role composition and parent roles
- Dynamic role assignment

### ABAC (Attribute-Based Access Control)
- Subject, resource, action, and environment attributes
- Complex attribute matching with operators
- JSONPath-based condition evaluation
- Dynamic attribute-based policies

### Hybrid Authorization
- Combines RBAC and ABAC for flexible access control
- Policy composition with multiple resolution strategies
- Priority-based policy evaluation
- Conflict resolution (deny_overrides, allow_overrides, first_match, priority_based)

### Advanced Features
- **Time-based Policies**: Restrict access based on time constraints
- **Permission Delegation**: Users can delegate their permissions temporarily
- **Policy Inheritance**: Policies can inherit from parent policies
- **Constant-time Evaluation**: Optimized for O(1) policy lookups
- **Dynamic Policy Updates**: Update policies without system restart
- **Comprehensive Audit Logging**: Track all authorization decisions

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  API Layer  │────▶│   Policy    │
│             │     │  (FastAPI)  │     │   Engine    │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Audit    │     │   Cache     │
                    │   Manager   │     │   Layer     │
                    └─────────────┘     └─────────────┘
```

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t auth-system .

# Run the container
docker run -p 8000:8000 auth-system

# Health check
curl http://localhost:8000/health
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the application:**
```bash
cd src
python main.py
```

## API Endpoints

### Authorization

- `POST /api/v1/authorize` - Main authorization endpoint
- `POST /api/v1/batch-authorize` - Batch authorization for multiple requests

### Policy Management

- `GET /api/v1/policies` - List all policies (admin only)
- `POST /api/v1/policies` - Create new policy (admin only)
- `PUT /api/v1/policies/{policy_id}` - Update policy (admin only)
- `DELETE /api/v1/policies/{policy_id}` - Delete policy (admin only)

### Role Management

- `GET /api/v1/roles` - List all roles
- `POST /api/v1/roles` - Create new role (admin only)

### Delegation

- `POST /api/v1/delegations` - Create permission delegation

### Audit

- `GET /api/v1/audit-logs` - Get audit logs (admin only)

### Health

- `GET /health` - Health check endpoint

## Usage Examples

### Basic Authorization Request

```bash
curl -X POST http://localhost:8000/api/v1/authorize \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_john" \
  -d '{
    "subject": "user_john",
    "action": "read",
    "resource": "/documents/public",
    "context": {
      "ip": "192.168.1.1",
      "time": "2024-01-21T10:30:00Z"
    }
  }'
```

### Create RBAC Policy

```bash
curl -X POST http://localhost:8000/api/v1/policies \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_admin" \
  -d '{
    "name": "Developer Access",
    "type": "rbac",
    "effect": "allow",
    "priority": 70,
    "roles": ["role_developer"],
    "permissions": ["read", "write", "deploy"],
    "resources": ["/code/*", "/deployments/*"]
  }'
```

### Create ABAC Policy

```bash
curl -X POST http://localhost:8000/api/v1/policies \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_admin" \
  -d '{
    "name": "Sensitive Data Protection",
    "type": "abac",
    "effect": "deny",
    "priority": 90,
    "subject_attributes": {
      "clearance": {
        "operator": "less_than",
        "value": "secret"
      }
    },
    "resource_attributes": {
      "classification": {
        "operator": "in",
        "value": ["secret", "top_secret"]
      }
    }
  }'
```

### Batch Authorization

```bash
curl -X POST http://localhost:8000/api/v1/batch-authorize \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_john" \
  -d '[
    {
      "subject": "user_john",
      "action": "read",
      "resource": "/documents/public"
    },
    {
      "subject": "user_john",
      "action": "write",
      "resource": "/documents/private"
    }
  ]'
```

### Create Permission Delegation

```bash
curl -X POST http://localhost:8000/api/v1/delegations \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_admin" \
  -d '{
    "delegator": "user_admin",
    "delegate": "user_john",
    "permissions": ["admin", "audit"],
    "valid_until": "2024-01-22T00:00:00Z"
  }'
```

## Configuration

### RBAC Configuration (`config/rbac.yaml`)

Define roles, permissions, and hierarchies:

```yaml
roles:
  - id: role_admin
    name: admin
    permissions:
      - read
      - write
      - delete
      - admin
    parent_roles: []
```

### ABAC Configuration (`config/abac.yaml`)

Define attributes and attribute-based policies:

```yaml
attributes:
  subject:
    - name: department
      type: string
      values: [IT, HR, Finance]
    - name: clearance
      type: string
      values: [public, confidential, secret]
```

### Policies Configuration (`config/policies.yaml`)

Define authorization policies:

```yaml
policies:
  - id: policy_1
    name: Admin Access
    type: rbac
    effect: allow
    priority: 100
    roles: [role_admin]
    permissions: ["*"]
```

## Policy Evaluation

### Evaluation Order

1. Time-based constraints check
2. RBAC policy evaluation
3. ABAC policy evaluation
4. Delegation check
5. Conflict resolution
6. Final decision

### Conflict Resolution Strategies

- **deny_overrides**: Any deny policy overrides allow policies
- **allow_overrides**: Any allow policy overrides deny policies
- **first_match**: First matching policy determines the outcome
- **priority_based**: Highest priority policy determines the outcome

## Performance

- **Policy Evaluation**: < 5ms P99 latency
- **Throughput**: > 10,000 requests per second
- **Cache Hit Rate**: > 90% for repeated requests
- **Memory Usage**: < 2GB under normal load

## Security Considerations

1. **Authentication**: Ensure proper authentication before authorization
2. **TLS**: Always use HTTPS in production
3. **API Keys**: Rotate admin API keys regularly
4. **Audit Logs**: Monitor audit logs for suspicious activity
5. **Policy Review**: Regularly review and update policies
6. **Least Privilege**: Follow principle of least privilege

## Monitoring

### Metrics

- Authorization request rate
- Decision latency (P50, P95, P99)
- Policy hit rate
- Cache effectiveness
- Audit log volume

### Health Checks

The `/health` endpoint provides:
- System status
- Component health
- Version information

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
pytest tests/performance/ -v --benchmark-only
```

## License

MIT

---

<a id="japanese"></a>
## 日本語

## 概要

ロールベースアクセス制御（RBAC）と属性ベースアクセス制御（ABAC）を組み合わせた高性能、本番対応の認可システムです。ポリシー継承、時間ベースポリシー、権限委譲、包括的な監査ログなどの高度な機能を含みます。

## 主な機能

### RBAC（ロールベースアクセス制御）
- 継承を持つ階層ロール構造
- 権限ベースのアクセス制御
- ロール合成と親ロール
- 動的ロール割り当て

### ABAC（属性ベースアクセス制御）
- 主体、リソース、アクション、環境の属性
- 演算子を使った複雑な属性マッチング
- JSONPathベースの条件評価
- 動的属性ベースポリシー

### ハイブリッド認可
- 柔軟なアクセス制御のためのRBACとABACの組み合わせ
- 複数の解決戦略を持つポリシー合成
- 優先度ベースのポリシー評価
- 競合解決（deny_overrides、allow_overrides、first_match、priority_based）

### 高度な機能
- **時間ベースポリシー**: 時間制約に基づくアクセス制限
- **権限委譲**: ユーザーが一時的に権限を委譲可能
- **ポリシー継承**: ポリシーが親ポリシーから継承可能
- **定数時間評価**: O(1)ポリシールックアップに最適化
- **動的ポリシー更新**: システム再起動なしでポリシー更新
- **包括的な監査ログ**: すべての認可決定を追跡

## アーキテクチャ

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  API Layer  │────▶│   Policy    │
│             │     │  (FastAPI)  │     │   Engine    │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Audit    │     │   Cache     │
                    │   Manager   │     │   Layer     │
                    └─────────────┘     └─────────────┘
```

## クイックスタート

### Dockerを使用

```bash
# イメージのビルド
docker build -t auth-system .

# コンテナの実行
docker run -p 8000:8000 auth-system

# ヘルスチェック
curl http://localhost:8000/health
```

### 手動セットアップ

1. **依存関係のインストール:**
```bash
pip install -r requirements.txt
```

2. **アプリケーションの実行:**
```bash
cd src
python main.py
```

## APIエンドポイント

### 認可

- `POST /api/v1/authorize` - メイン認可エンドポイント
- `POST /api/v1/batch-authorize` - 複数リクエストのバッチ認可

### ポリシー管理

- `GET /api/v1/policies` - すべてのポリシーリスト（管理者のみ）
- `POST /api/v1/policies` - 新しいポリシー作成（管理者のみ）
- `PUT /api/v1/policies/{policy_id}` - ポリシー更新（管理者のみ）
- `DELETE /api/v1/policies/{policy_id}` - ポリシー削除（管理者のみ）

### ロール管理

- `GET /api/v1/roles` - すべてのロールリスト
- `POST /api/v1/roles` - 新しいロール作成（管理者のみ）

### 委譲

- `POST /api/v1/delegations` - 権限委譲作成

### 監査

- `GET /api/v1/audit-logs` - 監査ログ取得（管理者のみ）

### ヘルス

- `GET /health` - ヘルスチェックエンドポイント

## 使用例

### 基本的な認可リクエスト

```bash
curl -X POST http://localhost:8000/api/v1/authorize \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_john" \
  -d '{
    "subject": "user_john",
    "action": "read",
    "resource": "/documents/public",
    "context": {
      "ip": "192.168.1.1",
      "time": "2024-01-21T10:30:00Z"
    }
  }'
```

### RBACポリシーの作成

```bash
curl -X POST http://localhost:8000/api/v1/policies \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_admin" \
  -d '{
    "name": "Developer Access",
    "type": "rbac",
    "effect": "allow",
    "priority": 70,
    "roles": ["role_developer"],
    "permissions": ["read", "write", "deploy"],
    "resources": ["/code/*", "/deployments/*"]
  }'
```

### ABACポリシーの作成

```bash
curl -X POST http://localhost:8000/api/v1/policies \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_admin" \
  -d '{
    "name": "Sensitive Data Protection",
    "type": "abac",
    "effect": "deny",
    "priority": 90,
    "subject_attributes": {
      "clearance": {
        "operator": "less_than",
        "value": "secret"
      }
    },
    "resource_attributes": {
      "classification": {
        "operator": "in",
        "value": ["secret", "top_secret"]
      }
    }
  }'
```

### バッチ認可

```bash
curl -X POST http://localhost:8000/api/v1/batch-authorize \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_john" \
  -d '[
    {
      "subject": "user_john",
      "action": "read",
      "resource": "/documents/public"
    },
    {
      "subject": "user_john",
      "action": "write",
      "resource": "/documents/private"
    }
  ]'
```

### 権限委譲の作成

```bash
curl -X POST http://localhost:8000/api/v1/delegations \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_admin" \
  -d '{
    "delegator": "user_admin",
    "delegate": "user_john",
    "permissions": ["admin", "audit"],
    "valid_until": "2024-01-22T00:00:00Z"
  }'
```

## 設定

### RBAC設定 (`config/rbac.yaml`)

ロール、権限、階層を定義：

```yaml
roles:
  - id: role_admin
    name: admin
    permissions:
      - read
      - write
      - delete
      - admin
    parent_roles: []
```

### ABAC設定 (`config/abac.yaml`)

属性と属性ベースポリシーを定義：

```yaml
attributes:
  subject:
    - name: department
      type: string
      values: [IT, HR, Finance]
    - name: clearance
      type: string
      values: [public, confidential, secret]
```

### ポリシー設定 (`config/policies.yaml`)

認可ポリシーを定義：

```yaml
policies:
  - id: policy_1
    name: Admin Access
    type: rbac
    effect: allow
    priority: 100
    roles: [role_admin]
    permissions: ["*"]
```

## ポリシー評価

### 評価順序

1. 時間ベース制約チェック
2. RBACポリシー評価
3. ABACポリシー評価
4. 委譲チェック
5. 競合解決
6. 最終決定

### 競合解決戦略

- **deny_overrides**: 拒否ポリシーが許可ポリシーを上書き
- **allow_overrides**: 許可ポリシーが拒否ポリシーを上書き
- **first_match**: 最初にマッチしたポリシーが結果を決定
- **priority_based**: 最高優先度ポリシーが結果を決定

## パフォーマンス

- **ポリシー評価**: < 5ms P99レイテンシ
- **スループット**: > 10,000 リクエスト/秒
- **キャッシュヒット率**: 繰り返しリクエストで > 90%
- **メモリ使用量**: 通常負荷で < 2GB

## セキュリティ考慮事項

1. **認証**: 認可前に適切な認証を確実に行う
2. **TLS**: 本番環境では常にHTTPSを使用
3. **APIキー**: 管理者APIキーを定期的にローテーション
4. **監査ログ**: 不審なアクティビティを監視
5. **ポリシーレビュー**: 定期的なポリシーレビューと更新
6. **最小権限**: 最小権限の原則に従う

## 監視

### メトリクス

- 認可リクエスト率
- 決定レイテンシ（P50、P95、P99）
- ポリシーヒット率
- キャッシュ効率
- 監査ログ量

### ヘルスチェック

`/health`エンドポイントが提供：
- システムステータス
- コンポーネントヘルス
- バージョン情報

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
pytest tests/performance/ -v --benchmark-only
```

## ライセンス

MIT