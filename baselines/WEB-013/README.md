# WEB-013: GraphQL API with N+1 Query Prevention

**Language:** [English](#english) | [日本語](#japanese)

---

## English

## Overview

A production-grade GraphQL API implementation featuring DataLoader pattern for N+1 query prevention, query depth limiting, complexity analysis, field-level authorization, and real-time subscriptions. The system ensures optimal database performance through intelligent batching and caching strategies.

## Key Features

### N+1 Query Prevention
- **DataLoader Pattern**: Automatic batching and caching of database queries
- **Smart Prefetching**: Intelligent data loading strategies
- **Query Optimization**: Minimized database round trips
- **Cache Management**: TTL-based cache invalidation

### Query Protection
- **Depth Limiting**: Prevent deeply nested queries (configurable max depth)
- **Complexity Analysis**: Calculate and limit query complexity
- **Query Whitelisting**: Optional production query whitelisting
- **Rate Limiting**: Per-client request throttling

### GraphQL Features
- **Schema-First Design**: Type-safe schema definition
- **Subscriptions**: Real-time updates via WebSocket
- **Batch Queries**: Support for batched GraphQL requests
- **Persisted Queries**: Reduce bandwidth with query persistence
- **Field Authorization**: Fine-grained access control

### Performance Optimization
- **Connection Pooling**: Efficient database connections
- **Async Execution**: Non-blocking I/O operations
- **Parallel Resolution**: Concurrent field resolution
- **Response Caching**: Smart caching strategies

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  GraphQL API Layer                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐            │
│  │              │         │              │            │
│  │   Schema     │◄────────│  Resolvers   │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│         ▲                        │                     │
│         │                        ▼                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   Query      │         │              │            │
│  │  Analysis    │◄────────│ DataLoaders  │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│         ▲                        │                     │
│         │                        ▼                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │    Auth &    │         │              │            │
│  │ Rate Limit   │◄────────│   Database   │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t graphql-api .

# Run with PostgreSQL
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@postgres/graphql_db \
  -e JWT_SECRET=your-secret-key \
  graphql-api

# Access GraphQL Playground
open http://localhost:8000/graphql/playground
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Setup PostgreSQL:**
```bash
# Create database
createdb graphql_db

# Run migrations (if using alembic)
alembic upgrade head
```

3. **Configure environment:**
```bash
export DATABASE_URL=postgresql://user:pass@localhost/graphql_db
export JWT_SECRET=your-secret-key
```

4. **Run the application:**
```bash
python src/main.py
```

## GraphQL Schema

### Queries
```graphql
query GetUserWithPosts($userId: ID!) {
  user(id: $userId) {
    id
    username
    posts {  # DataLoader prevents N+1
      id
      title
      comments {  # Nested DataLoader
        id
        content
        author {  # Another level of batching
          username
        }
      }
    }
  }
}
```

### Mutations
```graphql
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    id
    title
    content
    author {
      username
    }
  }
}
```

### Subscriptions
```graphql
subscription OnPostAdded($authorId: ID) {
  postAdded(authorId: $authorId) {
    id
    title
    author {
      username
    }
  }
}
```

## DataLoader Usage

### Basic Example
```python
# Without DataLoader (N+1 problem)
users = await db.fetch_all("SELECT * FROM users")
for user in users:
    posts = await db.fetch_all(
        "SELECT * FROM posts WHERE author_id = ?", 
        user['id']
    )
    # N queries for N users!

# With DataLoader (batched)
user_loader = UserLoader(db)
users = await user_loader.load_many([1, 2, 3, 4, 5])
# Single batched query!
```

### Custom DataLoader
```python
class PostsByUserLoader(DataLoader):
    async def batch_load(self, user_ids):
        query = """
            SELECT * FROM posts 
            WHERE author_id = ANY($1)
            ORDER BY created_at DESC
        """
        posts = await db.fetch_all(query, user_ids)
        
        # Group by user_id
        posts_by_user = defaultdict(list)
        for post in posts:
            posts_by_user[post['author_id']].append(post)
        
        # Return in same order as requested
        return [posts_by_user[uid] for uid in user_ids]
```

## Query Depth Limiting

### Configuration
```yaml
graphql:
  max_query_depth: 10
```

### Example Protection
```graphql
# This query would be rejected (depth > 10)
query DeeplyNested {
  user {
    posts {
      comments {
        author {
          posts {
            comments {
              author {
                posts {
                  comments {
                    author {
                      posts {  # Depth 11 - REJECTED!
                        title
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## Query Complexity Analysis

### Complexity Calculation
```python
# Simple field: 0 points
id, name, email

# Entity lookup: 1 point
user(id: "1")

# List query: base + (limit * nested)
posts(limit: 100)  # 10 + (100 * nested_complexity)
```

### Example Complexity
```graphql
query ComplexQuery {
  users(limit: 100) {         # 10 base
    id                         # 0
    posts(limit: 10) {        # 10 * 100 = 1000
      id                       # 0
      comments(limit: 5) {     # 5 * 10 * 100 = 5000
        content                # 0
      }
    }
  }
}
# Total complexity: 6010 (would be rejected if max is 1000)
```

## Field-Level Authorization

### Schema Directives
```graphql
type User {
  id: ID!
  username: String!
  email: String! @auth  # Requires authentication
  posts: [Post!]!
  profile: UserProfile @hasRole(role: "premium")
}

type Query {
  statistics: Statistics! @hasRole(role: "admin")
}
```

### Implementation
```python
@auth_directive
async def resolve_email(parent, info):
    # Only authenticated users can see email
    return parent['email']

@has_role_directive("admin")
async def resolve_statistics(parent, info):
    # Only admins can access statistics
    return await get_statistics()
```

## Rate Limiting

### Configuration
```yaml
rate_limiting:
  requests_per_minute: 100
  burst: 20
  complexity_per_minute: 10000
```

### Per-Field Rate Limiting
```graphql
type Query {
  searchPosts(query: String!): [Post!]! 
    @rateLimit(limit: 10, duration: 60)
}
```

## Performance Metrics

### Key Metrics
- **Query Execution Time**: P95 < 100ms
- **Database Queries per Request**: Minimized through batching
- **Cache Hit Rate**: >80% for repeated queries
- **Throughput**: 2000+ requests per second

### Monitoring
```bash
# Prometheus metrics
curl http://localhost:9090/metrics

# Key metrics to watch
graphql_query_duration_seconds
graphql_query_complexity
graphql_dataloader_batch_size
graphql_cache_hit_rate
```

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Performance Tests
```bash
# Test N+1 prevention
pytest tests/performance/test_dataloader.py

# Test query complexity
pytest tests/performance/test_complexity.py
```

### Load Testing
```bash
# Using k6
k6 run tests/load/graphql_load_test.js
```

## Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost/graphql_db
JWT_SECRET=your-secret-key
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
MAX_QUERY_DEPTH=10
MAX_QUERY_COMPLEXITY=1000
```

### Configuration File
```yaml
# config/graphql.yaml
graphql:
  max_query_depth: 10
  max_query_complexity: 1000
  introspection: true
  playground: true
  
dataloader:
  cache_ttl: 60
  max_batch_size: 100
  
rate_limiting:
  requests_per_minute: 100
  burst: 20
```

## Production Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  api:
    image: graphql-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/graphql
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=graphql
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      
  redis:
    image: redis:7
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graphql-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: graphql-api
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## Best Practices

1. **Always use DataLoaders** for related data fetching
2. **Set appropriate query limits** based on your use case
3. **Implement field-level caching** for expensive computations
4. **Use persisted queries** in production
5. **Monitor query performance** and optimize slow queries
6. **Implement query whitelisting** for public APIs
7. **Use subscriptions sparingly** due to connection overhead

## Troubleshooting

### N+1 Queries Still Occurring
- Check DataLoader registration
- Verify resolver implementation
- Enable query logging to identify issues

### High Query Complexity
- Review nested field limits
- Implement pagination
- Consider query splitting

### Performance Issues
- Check database indexes
- Review DataLoader batch sizes
- Enable query result caching

## License

MIT

---

## Japanese

# WEB-013: N+1クエリ防止機能付きGraphQL API

## 概要

N+1クエリ防止のDataLoaderパターン、クエリ深度制限、複雑度分析、フィールドレベル認可、リアルタイムサブスクリプションを特徴とする本格的なGraphQL API実装。システムはインテリジェントなバッチ処理とキャッシュ戦略で最適なデータベースパフォーマンスを保証します。

## 主要機能

### N+1クエリ防止
- **DataLoaderパターン**: データベースクエリの自動バッチ処理とキャッシュ
- **スマートプリフェッチ**: インテリジェントなデータロード戦略
- **クエリ最適化**: データベースラウンドトリップの最小化
- **キャッシュ管理**: TTLベースキャッシュ無効化

### クエリ保護
- **深度制限**: 深くネストされたクエリの防止（設定可能な最大深度）
- **複雑度分析**: クエリ複雑度の計算と制限
- **クエリホワイトリスト**: 本畫環境でのオプションクエリホワイトリスト
- **レート制限**: クライアント別リクエストスロットリング

### GraphQL機能
- **スキーマファースト設計**: 型安全なスキーマ定義
- **サブスクリプション**: WebSocket経由のリアルタイム更新
- **バッチクエリ**: バッチ化されたGraphQLリクエストのサポート
- **永続化クエリ**: クエリ永続化で帯域幅減少
- **フィールド認可**: 細かいアクセス制御

### パフォーマンス最適化
- **接続プール**: 効率的なデータベース接続
- **非同期実行**: ノンブロッキングI/O操作
- **並列解決**: 同時フィールド解決
- **レスポンスキャッシュ**: スマートキャッシュ戦略

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                  GraphQL APIレイヤー                       │
├─────────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐            │
│  │              │         │              │            │
│  │   スキーマ     │◄────────│  リゾルバー   │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│         ▲                        │                     │
│         │                        ▼                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   クエリ      │         │              │            │
│  │  分析    │◄────────│ DataLoaders  │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│         ▲                        │                     │
│         │                        ▼                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │    Auth &    │         │              │            │
│  │ Rate Limit   │◄────────│   Database   │            │
│  │              │         │              │            │
│  └──────────────┘         └──────────────┘            │
│                                                          │
└─────────────────────────────────────────────────────────────┘
```

## クイックスタート

### Dockerの使用

```bash
# イメージビルド
docker build -t graphql-api .

# PostgreSQLで実行
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@postgres/graphql_db \
  -e JWT_SECRET=your-secret-key \
  graphql-api

# GraphQL Playgroundへアクセス
open http://localhost:8000/graphql/playground
```

### 手動セットアップ

1. **依存関係インストール:**
```bash
pip install -r requirements.txt
```

2. **PostgreSQLセットアップ:**
```bash
# データベース作成
createdb graphql_db

# マイグレーション実行（alembic使用時）
alembic upgrade head
```

3. **環境設定:**
```bash
export DATABASE_URL=postgresql://user:pass@localhost/graphql_db
export JWT_SECRET=your-secret-key
```

4. **アプリケーション実行:**
```bash
python src/main.py
```

## GraphQLスキーマ

### クエリ
```graphql
query GetUserWithPosts($userId: ID!) {
  user(id: $userId) {
    id
    username
    posts {  # DataLoaderがN+1を防止
      id
      title
      comments {  # ネストされたDataLoader
        id
        content
        author {  # さらなるバッチ処理レベル
          username
        }
      }
    }
  }
}
```

### ミューテーション
```graphql
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    id
    title
    content
    author {
      username
    }
  }
}
```

### サブスクリプション
```graphql
subscription OnPostAdded($authorId: ID) {
  postAdded(authorId: $authorId) {
    id
    title
    author {
      username
    }
  }
}
```

## DataLoader使用法

### 基本例
```python
# DataLoaderなし（N+1問題）
users = await db.fetch_all("SELECT * FROM users")
for user in users:
    posts = await db.fetch_all(
        "SELECT * FROM posts WHERE author_id = ?", 
        user['id']
    )
    # NユーザーにNクエリ！

# DataLoaderあり（バッチ化）
user_loader = UserLoader(db)
users = await user_loader.load_many([1, 2, 3, 4, 5])
# 単一のバッチクエリ！
```

### カスタムDataLoader
```python
class PostsByUserLoader(DataLoader):
    async def batch_load(self, user_ids):
        query = """
            SELECT * FROM posts 
            WHERE author_id = ANY($1)
            ORDER BY created_at DESC
        """
        posts = await db.fetch_all(query, user_ids)
        
        # user_idでグループ化
        posts_by_user = defaultdict(list)
        for post in posts:
            posts_by_user[post['author_id']].append(post)
        
        # リクエストされた順序で返却
        return [posts_by_user[uid] for uid in user_ids]
```

## クエリ深度制限

### 設定
```yaml
graphql:
  max_query_depth: 10
```

### 保護例
```graphql
# このクエリは拒否される（深度 > 10）
query DeeplyNested {
  user {
    posts {
      comments {
        author {
          posts {
            comments {
              author {
                posts {
                  comments {
                    author {
                      posts {  # 深度11 - 拒否！
                        title
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## クエリ複雑度分析

### 複雑度計算
```python
# シンプルフィールド：0ポイント
id, name, email

# エンティティ検索：1ポイント
user(id: "1")

# リストクエリ：ベース + (制限 * ネスト)
posts(limit: 100)  # 10 + (100 * nested_complexity)
```

### 複雑度例
```graphql
query ComplexQuery {
  users(limit: 100) {         # 10ベース
    id                         # 0
    posts(limit: 10) {        # 10 * 100 = 1000
      id                       # 0
      comments(limit: 5) {     # 5 * 10 * 100 = 5000
        content                # 0
      }
    }
  }
}
# 総複雑度：6010 （最大1000の場合拒否される）
```

## フィールドレベル認可

### スキーマディレクティブ
```graphql
type User {
  id: ID!
  username: String!
  email: String! @auth  # 認証が必要
  posts: [Post!]!
  profile: UserProfile @hasRole(role: "premium")
}

type Query {
  statistics: Statistics! @hasRole(role: "admin")
}
```

### 実装
```python
@auth_directive
async def resolve_email(parent, info):
    # 認証済みユーザーのみメール表示可能
    return parent['email']

@has_role_directive("admin")
async def resolve_statistics(parent, info):
    # 管理者のみ統計情報アクセス可能
    return await get_statistics()
```

## レート制限

### 設定
```yaml
rate_limiting:
  requests_per_minute: 100
  burst: 20
  complexity_per_minute: 10000
```

### フィールド別レート制限
```graphql
type Query {
  searchPosts(query: String!): [Post!]! 
    @rateLimit(limit: 10, duration: 60)
}
```

## パフォーマンスメトリクス

### 主要メトリクス
- **クエリ実行時間**: P95 < 100ms
- **リクエスト当たりデータベースクエリ数**: バッチ処理で最小化
- **キャッシュヒット率**: >80%（繰り返しクエリ）
- **スループット**: 2000+リクエスト/秒

### 監視
```bash
# Prometheusメトリクス
curl http://localhost:9090/metrics

# 監視すべき主要メトリクス
graphql_query_duration_seconds
graphql_query_complexity
graphql_dataloader_batch_size
graphql_cache_hit_rate
```

## テスト

### ユニットテスト
```bash
pytest tests/unit/
```

### 統合テスト
```bash
pytest tests/integration/
```

### パフォーマンステスト
```bash
# N+1防止テスト
pytest tests/performance/test_dataloader.py

# クエリ複雑度テスト
pytest tests/performance/test_complexity.py
```

### 負荷テスト
```bash
# k6の使用
k6 run tests/load/graphql_load_test.js
```

## 設定

### 環境変数
```bash
DATABASE_URL=postgresql://user:pass@localhost/graphql_db
JWT_SECRET=your-secret-key
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
MAX_QUERY_DEPTH=10
MAX_QUERY_COMPLEXITY=1000
```

### 設定ファイル
```yaml
# config/graphql.yaml
graphql:
  max_query_depth: 10
  max_query_complexity: 1000
  introspection: true
  playground: true
  
dataloader:
  cache_ttl: 60
  max_batch_size: 100
  
rate_limiting:
  requests_per_minute: 100
  burst: 20
```

## 本畫デプロイメント

### Docker Compose
```yaml
version: '3.8'
services:
  api:
    image: graphql-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/graphql
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=graphql
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      
  redis:
    image: redis:7
```

## ベストプラクティス

1. **常にDataLoaderを使用** 関連データフェッチ用
2. **適切なクエリ制限を設定** ユースケースに基づいて
3. **フィールドレベルキャッシュを実装** 高コスト計算用
4. **本畫環境で永続化クエリを使用**
5. **クエリパフォーマンスを監視** し、遅いクエリを最適化
6. **パブリックAPIでクエリホワイトリストを実装**
7. **サブスクリプションは慎重に使用** 接続オーバーヘッドのため

## トラブルシューティング

### N+1クエリがまだ発生
- DataLoader登録を確認
- リゾルバー実装を検証
- クエリログを有効化して問題を特定

### 高クエリ複雑度
- ネストされたフィールド制限を確認
- ページネーションを実装
- クエリ分割を検討

### パフォーマンス問題
- データベースインデックスを確認
- DataLoaderバッチサイズを確認
- クエリ結果キャッシュを有効化

## ライセンス

MIT