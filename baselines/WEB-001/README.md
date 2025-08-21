# WEB-001: Todo REST API Baseline Implementation

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

This is the baseline (reference) implementation for the WEB-001 problem: Todo REST API with JWT Authentication.

## Expected Score

- **Total Score**: 85.2%
- **Grade**: Silver
- **Breakdown**:
  - Functional Coverage: 100% (weight: 0.35) → 35.0
  - Test Pass Rate: 92% (weight: 0.25) → 23.0  
  - Performance Score: 78% (weight: 0.15) → 11.7
  - Code Quality: 85% (weight: 0.15) → 12.75
  - Security Score: 90% (weight: 0.10) → 9.0

## Implementation Overview

This baseline implementation uses:
- **Framework**: FastAPI (Python 3.11)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT with python-jose
- **Validation**: Pydantic models
- **Testing**: pytest with httpx

## Directory Structure

```
baselines/WEB-001/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container definition
├── src/
│   ├── main.py       # FastAPI application entry point
│   ├── models.py     # SQLAlchemy models
│   ├── schemas.py    # Pydantic schemas
│   ├── database.py   # Database configuration
│   ├── auth.py       # JWT authentication
│   ├── crud.py       # CRUD operations
│   └── config.py     # Application configuration
├── tests/
│   ├── test_unit.py       # Unit tests
│   ├── test_integration.py # Integration tests
│   ├── test_performance.py # Performance tests
│   ├── test_security.py    # Security tests
│   └── test_property.py    # Property-based tests
└── docs/
    └── setup.md      # Setup instructions

```

## Running the Implementation

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v --cov=src --cov-report=html
```

### Docker Deployment

```bash
# Build the image
docker build -t web-001-baseline .

# Run the container
docker run -p 8000:8000 web-001-baseline

# Run with resource limits (as per problem constraints)
docker run -p 8000:8000 \
  --cpus="1.0" \
  --memory="512m" \
  web-001-baseline
```

## API Endpoints

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and receive JWT token
- `GET /todos` - List all todos (paginated)
- `POST /todos` - Create a new todo
- `GET /todos/{id}` - Get a specific todo
- `PUT /todos/{id}` - Update a todo
- `DELETE /todos/{id}` - Delete a todo
- `GET /health` - Health check endpoint

## Performance Characteristics

- **P95 Latency**: ~95ms (requirement: 120ms)
- **P99 Latency**: ~150ms (requirement: 200ms)
- **Throughput**: ~65 RPS (requirement: 50 RPS)
- **Memory Usage**: ~450MB under load (limit: 512MB)
- **CPU Usage**: ~0.8 cores under load (limit: 1.0 core)

## Security Features

- JWT-based authentication with token expiration
- Password hashing with bcrypt
- Input validation via Pydantic
- SQL injection prevention via SQLAlchemy ORM
- No hardcoded secrets (uses environment variables)
- Rate limiting on authentication endpoints

## Code Quality Metrics

- **Test Coverage**: 92%
- **Cyclomatic Complexity**: Average 4.2, Max 8
- **Type Hints**: 100% coverage
- **Documentation**: All public functions documented
- **Linting**: Passes flake8 and black formatting

## Known Limitations

1. Uses SQLite instead of a production database (acceptable per requirements)
2. No distributed caching (single-instance deployment)
3. Basic rate limiting (in-memory, not distributed)

## Improvement Opportunities

While this baseline meets all requirements, potential improvements include:
- PostgreSQL for production deployment
- Redis for caching and distributed rate limiting
- OpenTelemetry for observability
- Alembic for database migrations

---

<a id="japanese"></a>
## 日本語

これは、WEB-001問題のベースライン（参照）実装です：JWT認証を使用したTodo REST API。

## 期待スコア

- **総合スコア**: 85.2%
- **グレード**: シルバー
- **内訳**:
  - 機能カバレッジ: 100% (重み: 0.35) → 35.0
  - テスト合格率: 92% (重み: 0.25) → 23.0  
  - パフォーマンススコア: 78% (重み: 0.15) → 11.7
  - コード品質: 85% (重み: 0.15) → 12.75
  - セキュリティスコア: 90% (重み: 0.10) → 9.0

## 実装概要

このベースライン実装では以下を使用:
- **フレームワーク**: FastAPI (Python 3.11)
- **データベース**: SQLite with SQLAlchemy ORM
- **認証**: JWT with python-jose
- **バリデーション**: Pydanticモデル
- **テスト**: pytest with httpx

## ディレクトリ構造

```
baselines/WEB-001/
├── README.md           # このファイル
├── requirements.txt    # Python依存関係
├── Dockerfile         # コンテナ定義
├── src/
│   ├── main.py       # FastAPIアプリケーションエントリポイント
│   ├── models.py     # SQLAlchemyモデル
│   ├── schemas.py    # Pydanticスキーマ
│   ├── database.py   # データベース設定
│   ├── auth.py       # JWT認証
│   ├── crud.py       # CRUD操作
│   └── config.py     # アプリケーション設定
├── tests/
│   ├── test_unit.py       # ユニットテスト
│   ├── test_integration.py # 統合テスト
│   ├── test_performance.py # パフォーマンステスト
│   ├── test_security.py    # セキュリティテスト
│   └── test_property.py    # プロパティベーステスト
└── docs/
    └── setup.md      # セットアップ手順

```

## 実装の実行

### ローカル開発

```bash
# 依存関係のインストール
pip install -r requirements.txt

# アプリケーションの実行
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# テストの実行
pytest tests/ -v --cov=src --cov-report=html
```

### Dockerデプロイメント

```bash
# イメージのビルド
docker build -t web-001-baseline .

# コンテナの実行
docker run -p 8000:8000 web-001-baseline

# リソース制限付きで実行（問題の制約に従って）
docker run -p 8000:8000 \
  --cpus="1.0" \
  --memory="512m" \
  web-001-baseline
```

## APIエンドポイント

- `POST /auth/register` - 新規ユーザー登録
- `POST /auth/login` - ログインしてJWTトークンを受け取る
- `GET /todos` - すべてのtodoをリスト（ページネーション付き）
- `POST /todos` - 新しいtodoを作成
- `GET /todos/{id}` - 特定のtodoを取得
- `PUT /todos/{id}` - todoを更新
- `DELETE /todos/{id}` - todoを削除
- `GET /health` - ヘルスチェックエンドポイント

## パフォーマンス特性

- **P95レイテンシ**: ~95ms（要件: 120ms）
- **P99レイテンシ**: ~150ms（要件: 200ms）
- **スループット**: ~65 RPS（要件: 50 RPS）
- **メモリ使用量**: 負荷時~450MB（制限: 512MB）
- **CPU使用率**: 負荷時~0.8コア（制限: 1.0コア）

## セキュリティ機能

- トークン有効期限付きJWTベース認証
- bcryptによるパスワードハッシュ化
- Pydantic経由の入力検証
- SQLAlchemy ORM経由のSQLインジェクション防止
- ハードコードされた秘密情報なし（環境変数を使用）
- 認証エンドポイントのレート制限

## コード品質メトリクス

- **テストカバレッジ**: 92%
- **循環的複雑度**: 平均4.2、最大8
- **型ヒント**: 100%カバレッジ
- **ドキュメント**: すべてのパブリック関数にドキュメント付き
- **リンティング**: flake8とblackフォーマットに合格

## 既知の制限事項

1. プロダクションデータベースの代わりにSQLiteを使用（要件上許容）
2. 分散キャッシュなし（単一インスタンスデプロイ）
3. 基本的なレート制限（インメモリ、分散されていない）

## 改善の機会

このベースラインはすべての要件を満たしていますが、潜在的な改善点には以下が含まれます：
- プロダクションデプロイメント用PostgreSQL
- キャッシングと分散レート制限用Redis
- 可観測性のためのOpenTelemetry
- データベースマイグレーション用Alembic