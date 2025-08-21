# DB-010: Two-Phase Money Transfer with SERIALIZABLE Isolation - Baseline Implementation

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

This baseline implementation provides a robust financial transaction system with strong consistency guarantees, implementing two-phase commit protocol with SERIALIZABLE isolation level. It ensures ACID properties, exactly-once processing through idempotency, and comprehensive audit logging.

## Features Implemented

### Core Features (MUST)
- ✅ Atomic money transfers between accounts
- ✅ SERIALIZABLE isolation level for all transactions
- ✅ Exactly-once execution with idempotency keys
- ✅ Balance consistency invariants maintained
- ✅ Prevention of negative balances
- ✅ Optimistic locking with retry logic
- ✅ Complete audit trail for all transactions
- ✅ Deadlock-free concurrent transfers

### Additional Features (SHOULD)
- ✅ Transaction timeouts
- ✅ Transaction status queries

## Architecture

```
┌─────────────────────────────────────────────┐
│              REST API Layer                 │
│         (FastAPI + Pydantic Models)         │
├─────────────────────────────────────────────┤
│          Transaction Manager                │
│    (Two-Phase Commit + Retry Logic)         │
├─────────────────────────────────────────────┤
│         Idempotency Manager                 │
│      (Exactly-Once Processing)              │
├─────────────────────────────────────────────┤
│           Database Layer                    │
│    (PostgreSQL + SERIALIZABLE)              │
└─────────────────────────────────────────────┘
```

## API Endpoints

### Account Management
- `POST /accounts` - Create new account
- `GET /accounts/{account_id}` - Get account details
- `GET /accounts/{account_id}/balance` - Get current balance

### Transfers
- `POST /transfers` - Execute money transfer
- `GET /transfers/{transaction_id}/status` - Get transaction status

### Audit
- `GET /audit-logs` - Query audit logs

### Admin
- `POST /admin/reset` - Reset database (debug mode only)

## Transaction Guarantees

### ACID Properties
- **Atomicity**: All-or-nothing execution
- **Consistency**: Balance invariants always maintained
- **Isolation**: SERIALIZABLE isolation prevents anomalies
- **Durability**: Committed transactions persist

### Consistency Invariants
1. No negative balances allowed
2. Total money in system remains constant
3. Every debit has corresponding credit
4. Audit trail completeness

### Concurrency Control
- Row-level locking with SELECT FOR UPDATE
- Consistent lock ordering to prevent deadlocks
- Automatic retry on serialization failures
- Optimistic locking with version numbers

## Example Usage

### Create Accounts
```bash
curl -X POST http://localhost:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{"initial_balance": 1000.00}'
```

### Transfer Money
```bash
curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "from_account_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "to_account_id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22",
    "amount": 100.00,
    "idempotency_key": "unique_key_123"
  }'
```

### Check Transaction Status
```bash
curl http://localhost:8000/transfers/{transaction_id}/status
```

## Performance Characteristics

- **P95 Latency**: < 150ms
- **P99 Latency**: < 500ms
- **Throughput**: 100+ TPS
- **Concurrent Transactions**: 20 max
- **Retry Strategy**: Exponential backoff

## Database Schema

### Tables
- `accounts` - Account balances and metadata
- `transactions` - Transaction records
- `audit_logs` - Complete audit trail
- `idempotency_records` - Idempotency cache

### Indexes
- Balance lookups
- Account transaction history
- Audit log queries
- Idempotency key lookups

## Running the System

### Prerequisites
- PostgreSQL 13+
- Python 3.11+
- Docker (optional)

### Docker Setup
```bash
# Start PostgreSQL
docker run -d \
  --name postgres-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=transactions \
  -p 5432:5432 \
  postgres:15

# Build and run application
docker build -t db-010-baseline .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/transactions \
  db-010-baseline
```

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/transactions

# Run migrations
python -m src.main --migrate

# Start application
uvicorn src.main:app --host 0.0.0.0 --port 8000
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

### Property Tests
```bash
pytest tests/property/ -v
```

### Performance Tests
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## Configuration

### Environment Variables
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DB_POOL_MIN=10
DB_POOL_MAX=20
TRANSACTION_TIMEOUT=30
IDEMPOTENCY_TTL=86400
MAX_RETRY_ATTEMPTS=3
```

### Configuration Files
- `config/database.yaml` - Database settings
- `config/transaction.yaml` - Transaction parameters

## Monitoring

### Prometheus Metrics
- `transactions_total` - Transaction count by status
- `transaction_duration_seconds` - Processing latency
- `failed_transactions_total` - Failure reasons
- `account_balance` - Current balances

### Health Check
```bash
curl http://localhost:8000/health
```

## Security Considerations

1. **SQL Injection**: Parameterized queries only
2. **Race Conditions**: SERIALIZABLE isolation
3. **Double Spending**: Idempotency protection
4. **Audit Trail**: Immutable log records
5. **Balance Checks**: Database constraints

## Troubleshooting

### Common Issues

1. **Serialization Failures**
   - Automatic retry handles most cases
   - Check for long-running transactions

2. **Deadlocks**
   - Consistent lock ordering prevents most deadlocks
   - Monitor for circular wait conditions

3. **Performance Degradation**
   - Check connection pool exhaustion
   - Review transaction duration metrics
   - Ensure proper indexing

## License

MIT

---

<a id="japanese"></a>
## 日本語

# DB-010: SERIALIZABLE分離レベルでの二相送金 - ベースライン実装

## 概要

強力な一貫性保証を持つ堅牢な金融取引システムを提供するベースライン実装。SERIALIZABLE分離レベルで二相コミットプロトコルを実装しています。ACID特性、冪等性による厳密な一度限りの処理、包括的な監査ログを保証します。

## 実装された機能

### コア機能 (MUST)
- ✅ アカウント間のアトミックな送金
- ✅ すべてのトランザクションでSERIALIZABLE分離レベル
- ✅ 冪等性キーによる厳密な一度限りの実行
- ✅ 残高整合性不変条件の維持
- ✅ 残高のマイナス化防止
- ✅ リトライロジック付き楽観的ロック
- ✅ すべてのトランザクションの完全な監査証跡
- ✅ デッドロックフリーな並行転送

### 追加機能 (SHOULD)
- ✅ トランザクションタイムアウト
- ✅ トランザクションステータスクエリ

## アーキテクチャ

```
┌─────────────────────────────────────────────┐
│              REST APIレイヤー               │
│         (FastAPI + Pydanticモデル)          │
├─────────────────────────────────────────────┤
│          トランザクションマネージャー          │
│    (二相コミット + リトライロジック)          │
├─────────────────────────────────────────────┤
│           冪等性マネージャー                 │
│        (厳密な一度限りの処理)                │
├─────────────────────────────────────────────┤
│           データベースレイヤー               │
│      (PostgreSQL + SERIALIZABLE)           │
└─────────────────────────────────────────────┘
```

## APIエンドポイント

### アカウント管理
- `POST /accounts` - 新規アカウント作成
- `GET /accounts/{account_id}` - アカウント詳細の取得
- `GET /accounts/{account_id}/balance` - 現在残高の取得

### 送金
- `POST /transfers` - 送金の実行
- `GET /transfers/{transaction_id}/status` - トランザクションステータスの取得

### 監査
- `GET /audit-logs` - 監査ログのクエリ

### 管理者
- `POST /admin/reset` - データベースのリセット（デバッグモードのみ）

## トランザクション保証

### ACID特性
- **原子性**: 全か無かの実行
- **一貫性**: 残高不変条件は常に維持される
- **分離性**: SERIALIZABLE分離により異常を防止
- **永続性**: コミット済みトランザクションは永続化

### 整合性不変条件
1. マイナス残高は許可されない
2. システム内の総金額は一定
3. すべての借方には対応する貸方がある
4. 監査証跡の完全性

### 並行制御
- SELECT FOR UPDATEによる行レベルロック
- デッドロック防止のための一貫したロック順序
- シリアライゼーション失敗時の自動リトライ
- バージョン番号による楽観的ロック

## 使用例

### アカウント作成
```bash
curl -X POST http://localhost:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{"initial_balance": 1000.00}'
```

### 送金
```bash
curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "from_account_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "to_account_id": "b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a22",
    "amount": 100.00,
    "idempotency_key": "unique_key_123"
  }'
```

### トランザクションステータス確認
```bash
curl http://localhost:8000/transfers/{transaction_id}/status
```

## パフォーマンス特性

- **P95レイテンシ**: < 150ms
- **P99レイテンシ**: < 500ms
- **スループット**: 100+ TPS
- **同時トランザクション**: 最大20
- **リトライ戦略**: 指数バックオフ

## データベーススキーマ

### テーブル
- `accounts` - アカウント残高とメタデータ
- `transactions` - トランザクションレコード
- `audit_logs` - 完全な監査証跡
- `idempotency_records` - 冪等性キャッシュ

### インデックス
- 残高検索
- アカウントトランザクション履歴
- 監査ログクエリ
- 冪等性キー検索

## システムの実行

### 前提条件
- PostgreSQL 13+
- Python 3.11+
- Docker（オプション）

### Dockerセットアップ
```bash
# PostgreSQLの起動
docker run -d \
  --name postgres-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=transactions \
  -p 5432:5432 \
  postgres:15

# アプリケーションのビルドと実行
docker build -t db-010-baseline .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/transactions \
  db-010-baseline
```

### ローカルセットアップ
```bash
# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/transactions

# マイグレーションの実行
python -m src.main --migrate

# アプリケーションの起動
uvicorn src.main:app --host 0.0.0.0 --port 8000
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

### プロパティテスト
```bash
pytest tests/property/ -v
```

### パフォーマンステスト
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## 設定

### 環境変数
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DB_POOL_MIN=10
DB_POOL_MAX=20
TRANSACTION_TIMEOUT=30
IDEMPOTENCY_TTL=86400
MAX_RETRY_ATTEMPTS=3
```

### 設定ファイル
- `config/database.yaml` - データベース設定
- `config/transaction.yaml` - トランザクションパラメータ

## 監視

### Prometheusメトリクス
- `transactions_total` - ステータス別トランザクション数
- `transaction_duration_seconds` - 処理レイテンシ
- `failed_transactions_total` - 失敗理由
- `account_balance` - 現在残高

### ヘルスチェック
```bash
curl http://localhost:8000/health
```

## セキュリティ考慮事項

1. **SQLインジェクション**: パラメータ化クエリのみ
2. **レース条件**: SERIALIZABLE分離
3. **二重支出**: 冪等性保護
4. **監査証跡**: 不変ログレコード
5. **残高チェック**: データベース制約

## トラブルシューティング

### 一般的な問題

1. **シリアライゼーション失敗**
   - 自動リトライがほとんどのケースを処理
   - 長時間実行トランザクションをチェック

2. **デッドロック**
   - 一貫したロック順序がほとんどのデッドロックを防止
   - 循環待機条件を監視

3. **パフォーマンス劣化**
   - 接続プール枯渇をチェック
   - トランザクション期間メトリクスを確認
   - 適切なインデックスを確保

## ライセンス

MIT