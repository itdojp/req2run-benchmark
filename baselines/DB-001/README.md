# DB-001: In-Memory Database Engine

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

High-performance in-memory database engine with full ACID compliance, MVCC concurrency control, and SQL query interface.

## Architecture

### Core Components

1. **Storage Engine**
   - In-memory B+Tree indexes
   - Row-oriented storage format
   - Memory-mapped file persistence
   - Write-Ahead Logging (WAL)

2. **Transaction Manager**
   - Multi-Version Concurrency Control (MVCC)
   - Snapshot isolation
   - Two-phase commit protocol
   - Deadlock detection and resolution

3. **Query Engine**
   - SQL parser and analyzer
   - Cost-based query optimizer
   - Execution plan generation
   - Prepared statement cache

4. **Index Manager**
   - Primary key B+Tree index
   - Secondary indexes
   - Composite indexes
   - Index-only scans

5. **Recovery System**
   - WAL-based recovery
   - Checkpoint management
   - Point-in-time recovery
   - Crash recovery

## Implementation Details

### B+Tree Index Structure

```rust
pub struct BPlusTree<K, V> {
    root: NodeId,
    order: usize,
    nodes: Arena<Node<K, V>>,
    height: usize,
}

impl<K: Ord + Clone, V: Clone> BPlusTree<K, V> {
    pub fn insert(&mut self, key: K, value: V) -> Result<()> {
        // Split nodes if necessary
        // Maintain sorted order
        // Update parent pointers
    }
    
    pub fn search(&self, key: &K) -> Option<&V> {
        // Binary search through internal nodes
        // Linear scan in leaf nodes
    }
    
    pub fn range_scan(&self, start: &K, end: &K) -> RangeIterator<K, V> {
        // Find start leaf
        // Iterate through linked leaves
    }
}
```

### MVCC Implementation

```rust
pub struct MVCCManager {
    versions: HashMap<RowId, Vec<RowVersion>>,
    active_transactions: BTreeMap<TransactionId, Snapshot>,
    timestamp_oracle: AtomicU64,
}

pub struct RowVersion {
    data: Vec<u8>,
    created_by: TransactionId,
    created_at: Timestamp,
    deleted_by: Option<TransactionId>,
    deleted_at: Option<Timestamp>,
}

impl MVCCManager {
    pub fn read(&self, row_id: RowId, snapshot: &Snapshot) -> Option<Vec<u8>> {
        // Find visible version for snapshot
        // Check transaction isolation level
    }
    
    pub fn write(&mut self, row_id: RowId, data: Vec<u8>, tx: TransactionId) {
        // Create new version
        // Maintain version chain
    }
}
```

### Query Execution

```rust
pub struct QueryExecutor {
    planner: QueryPlanner,
    optimizer: CostBasedOptimizer,
    cache: PreparedStatementCache,
}

impl QueryExecutor {
    pub fn execute(&mut self, sql: &str) -> Result<QueryResult> {
        // Parse SQL
        let ast = parse_sql(sql)?;
        
        // Generate logical plan
        let logical_plan = self.planner.plan(&ast)?;
        
        // Optimize plan
        let physical_plan = self.optimizer.optimize(logical_plan)?;
        
        // Execute plan
        self.execute_plan(physical_plan)
    }
}
```

## SQL Support

### DDL Operations
- `CREATE TABLE`
- `ALTER TABLE`
- `DROP TABLE`
- `CREATE INDEX`
- `DROP INDEX`

### DML Operations
- `SELECT` with JOIN, GROUP BY, ORDER BY, HAVING
- `INSERT` with multiple rows
- `UPDATE` with conditions
- `DELETE` with conditions
- `UPSERT` (INSERT ON CONFLICT)

### Transaction Control
- `BEGIN`
- `COMMIT`
- `ROLLBACK`
- `SAVEPOINT`
- `RELEASE SAVEPOINT`

## Performance Optimizations

1. **Lock-Free Data Structures**
   - Atomic operations for hot paths
   - RCU (Read-Copy-Update) for metadata
   - Lock-free skip lists for memtables

2. **Memory Management**
   - Custom allocator with arena allocation
   - Memory pooling for common objects
   - Zero-copy deserialization

3. **Query Optimization**
   - Statistics-based cardinality estimation
   - Join reordering
   - Predicate pushdown
   - Index selection

4. **Parallel Execution**
   - Parallel table scans
   - Parallel aggregation
   - Async I/O for WAL writes

## Recovery and Durability

### Write-Ahead Logging
```rust
pub struct WAL {
    active_segment: File,
    archived_segments: Vec<PathBuf>,
    buffer: RingBuffer,
    fsync_interval: Duration,
}

impl WAL {
    pub async fn append(&mut self, entry: LogEntry) -> Result<LSN> {
        // Write to buffer
        // Periodic fsync
        // Return log sequence number
    }
    
    pub async fn recover(&mut self, checkpoint: LSN) -> Result<Vec<LogEntry>> {
        // Read from checkpoint
        // Apply log entries
        // Rebuild state
    }
}
```

### Checkpoint Management
- Incremental checkpoints
- Background checkpoint threads
- Checkpoint coordination with WAL

## Testing Strategy

### Unit Tests
- B+Tree operations
- MVCC visibility rules
- Lock manager
- Query parser

### Integration Tests
- Transaction isolation levels
- Concurrent operations
- Recovery scenarios
- Query correctness

### Performance Tests
- TPC-C benchmark
- YCSB workloads
- Concurrent stress tests
- Memory usage analysis

### Property-Based Tests
- B+Tree invariants
- Transaction serializability
- Index consistency
- Recovery completeness

## Configuration

### Database Configuration
```yaml
database:
  max_connections: 1000
  shared_buffers: 8GB
  work_mem: 256MB
  checkpoint_interval: 5m
  wal_level: replica
  
storage:
  data_directory: /var/lib/db001/data
  wal_directory: /var/lib/db001/wal
  temp_directory: /tmp/db001
  
performance:
  parallel_workers: 8
  async_io: true
  prefetch_size: 1MB
  cache_size: 4GB
```

## Deployment

```bash
# Build
cargo build --release

# Run with configuration
./target/release/db001 --config config/database.yaml

# Health check
curl http://localhost:8080/health

# Connect with SQL client
psql -h localhost -p 5432 -d testdb
```

## Monitoring Metrics

- Transactions per second
- Query latency (p50, p95, p99)
- Lock contention rate
- Buffer hit ratio
- WAL write throughput
- Active connections
- Memory usage
- CPU utilization

## Dependencies

### Rust Implementation
- `tokio`: Async runtime
- `bytes`: Efficient byte buffers
- `crossbeam`: Lock-free data structures
- `parking_lot`: Fast synchronization primitives
- `bincode`: Binary serialization
- `nom`: Parser combinators for SQL
- `prometheus`: Metrics collection

---

<a id="japanese"></a>
## 日本語

## 概要

完全なACIDコンプライアンス、MVCC同時実行制御、SQLクエリインターフェースを備えた高性能インメモリデータベースエンジン。

## アーキテクチャ

### コアコンポーネント

1. **ストレージエンジン**
   - インメモリB+Treeインデックス
   - 行指向ストレージ形式
   - メモリマップドファイル永続化
   - Write-Ahead Logging (WAL)

2. **トランザクションマネージャー**
   - マルチバージョン同時実行制御（MVCC）
   - スナップショット分離
   - 二相コミットプロトコル
   - デッドロック検出と解決

3. **クエリエンジン**
   - SQLパーサーとアナライザー
   - コストベースクエリオプティマイザー
   - 実行計画生成
   - プリペアドステートメントキャッシュ

4. **インデックスマネージャー**
   - プライマリキーB+Treeインデックス
   - セカンダリインデックス
   - 複合インデックス
   - インデックスのみスキャン

5. **リカバリシステム**
   - WALベースリカバリ
   - チェックポイント管理
   - ポイントインタイムリカバリ
   - クラッシュリカバリ

## 実装詳細

### B+Treeインデックス構造

```rust
pub struct BPlusTree<K, V> {
    root: NodeId,
    order: usize,
    nodes: Arena<Node<K, V>>,
    height: usize,
}

impl<K: Ord + Clone, V: Clone> BPlusTree<K, V> {
    pub fn insert(&mut self, key: K, value: V) -> Result<()> {
        // 必要に応じてノードを分割
        // ソート順を維持
        // 親ポインタを更新
    }
    
    pub fn search(&self, key: &K) -> Option<&V> {
        // 内部ノードでバイナリサーチ
        // リーフノードで線形スキャン
    }
    
    pub fn range_scan(&self, start: &K, end: &K) -> RangeIterator<K, V> {
        // 開始リーフを検索
        // リンクされたリーフを反復
    }
}
```

### MVCC実装

```rust
pub struct MVCCManager {
    versions: HashMap<RowId, Vec<RowVersion>>,
    active_transactions: BTreeMap<TransactionId, Snapshot>,
    timestamp_oracle: AtomicU64,
}

pub struct RowVersion {
    data: Vec<u8>,
    created_by: TransactionId,
    created_at: Timestamp,
    deleted_by: Option<TransactionId>,
    deleted_at: Option<Timestamp>,
}

impl MVCCManager {
    pub fn read(&self, row_id: RowId, snapshot: &Snapshot) -> Option<Vec<u8>> {
        // スナップショット用の可視バージョンを検索
        // トランザクション分離レベルを確認
    }
    
    pub fn write(&mut self, row_id: RowId, data: Vec<u8>, tx: TransactionId) {
        // 新しいバージョンを作成
        // バージョンチェーンを維持
    }
}
```

### クエリ実行

```rust
pub struct QueryExecutor {
    planner: QueryPlanner,
    optimizer: CostBasedOptimizer,
    cache: PreparedStatementCache,
}

impl QueryExecutor {
    pub fn execute(&mut self, sql: &str) -> Result<QueryResult> {
        // SQLをパース
        let ast = parse_sql(sql)?;
        
        // 論理計画を生成
        let logical_plan = self.planner.plan(&ast)?;
        
        // 計画を最適化
        let physical_plan = self.optimizer.optimize(logical_plan)?;
        
        // 計画を実行
        self.execute_plan(physical_plan)
    }
}
```

## SQLサポート

### DDL操作
- `CREATE TABLE`
- `ALTER TABLE`
- `DROP TABLE`
- `CREATE INDEX`
- `DROP INDEX`

### DML操作
- `SELECT` （JOIN、GROUP BY、ORDER BY、HAVING付き）
- `INSERT` （複数行）
- `UPDATE` （条件付き）
- `DELETE` （条件付き）
- `UPSERT` (INSERT ON CONFLICT)

### トランザクション制御
- `BEGIN`
- `COMMIT`
- `ROLLBACK`
- `SAVEPOINT`
- `RELEASE SAVEPOINT`

## パフォーマンス最適化

1. **ロックフリーデータ構造**
   - ホットパス用のアトミック操作
   - メタデータ用のRCU（Read-Copy-Update）
   - memtables用のロックフリースキップリスト

2. **メモリ管理**
   - アリーナ割り当て付きカスタムアロケータ
   - 一般的なオブジェクト用のメモリプーリング
   - ゼロコピーデシリアライゼーション

3. **クエリ最適化**
   - 統計ベースのカーディナリティ推定
   - JOINの再順序付け
   - 述語プッシュダウン
   - インデックス選択

4. **並列実行**
   - 並列テーブルスキャン
   - 並列集約
   - WAL書き込み用の非同期I/O

## リカバリと耐久性

### Write-Ahead Logging
```rust
pub struct WAL {
    active_segment: File,
    archived_segments: Vec<PathBuf>,
    buffer: RingBuffer,
    fsync_interval: Duration,
}

impl WAL {
    pub async fn append(&mut self, entry: LogEntry) -> Result<LSN> {
        // バッファに書き込み
        // 定期的なfsync
        // ログシーケンス番号を返す
    }
    
    pub async fn recover(&mut self, checkpoint: LSN) -> Result<Vec<LogEntry>> {
        // チェックポイントから読み取り
        // ログエントリを適用
        // 状態を再構築
    }
}
```

### チェックポイント管理
- インクリメンタルチェックポイント
- バックグラウンドチェックポイントスレッド
- WALとのチェックポイント調整

## テスト戦略

### ユニットテスト
- B+Tree操作
- MVCC可視性ルール
- ロックマネージャー
- クエリパーサー

### 統合テスト
- トランザクション分離レベル
- 同時操作
- リカバリシナリオ
- クエリ正確性

### パフォーマンステスト
- TPC-Cベンチマーク
- YCSBワークロード
- 同時ストレステスト
- メモリ使用量分析

### プロパティベーステスト
- B+Tree不変条件
- トランザクションシリアライズ可能性
- インデックス一貫性
- リカバリ完全性

## 設定

### データベース設定
```yaml
database:
  max_connections: 1000
  shared_buffers: 8GB
  work_mem: 256MB
  checkpoint_interval: 5m
  wal_level: replica
  
storage:
  data_directory: /var/lib/db001/data
  wal_directory: /var/lib/db001/wal
  temp_directory: /tmp/db001
  
performance:
  parallel_workers: 8
  async_io: true
  prefetch_size: 1MB
  cache_size: 4GB
```

## デプロイメント

```bash
# ビルド
cargo build --release

# 設定で実行
./target/release/db001 --config config/database.yaml

# ヘルスチェック
curl http://localhost:8080/health

# SQLクライアントで接続
psql -h localhost -p 5432 -d testdb
```

## 監視メトリクス

- 毎秒のトランザクション数
- クエリレイテンシ（p50、p95、p99）
- ロック競合率
- バッファヒット率
- WAL書き込みスループット
- アクティブ接続数
- メモリ使用量
- CPU使用率

## 依存関係

### Rust実装
- `tokio`: 非同期ランタイム
- `bytes`: 効率的なバイトバッファ
- `crossbeam`: ロックフリーデータ構造
- `parking_lot`: 高速同期プリミティブ
- `bincode`: バイナリシリアライゼーション
- `nom`: SQL用パーサーコンビネータ
- `prometheus`: メトリクス収集