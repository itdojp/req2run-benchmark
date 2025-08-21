# TS-001: Time-Series Database

**Languages / 言語:** [English](#english) | [日本語](#japanese)

## English

## Overview

High-performance time-series database optimized for metrics storage with compression, downsampling, and continuous aggregations.

## Architecture

### Core Components

1. **Storage Engine**
   - Time-partitioned data files
   - Columnar storage format
   - Compression (Gorilla, Snappy, Zstd)
   - Memory-mapped files

2. **Ingestion Pipeline**
   - Write-ahead log
   - In-memory buffer
   - Batch flushing
   - Out-of-order handling

3. **Query Engine**
   - Time-range optimization
   - Parallel query execution
   - Aggregation pushdown
   - Cache layer

4. **Compaction System**
   - Background compaction
   - Downsampling
   - Retention enforcement
   - Space reclamation

5. **Continuous Aggregations**
   - Materialized views
   - Incremental updates
   - Rollup hierarchies
   - Real-time refresh

## Features

### Data Model
- Multi-dimensional metrics
- Tags and fields
- Nanosecond precision
- Schema-on-write

### Compression
- Delta-of-delta timestamps
- XOR floating point
- Dictionary encoding
- Run-length encoding

### Query Language
```sql
SELECT mean(cpu_usage), max(memory)
FROM system_metrics
WHERE host = 'server-1'
  AND time >= now() - 1h
GROUP BY time(5m)
```

### Performance
- 1M+ points/sec ingestion
- Sub-millisecond queries
- 10x compression ratio
- Efficient range scans

## Testing

- Ingestion benchmarks
- Query performance tests
- Compression ratio validation
- Data integrity checks
- Concurrent load testing

## Deployment

```bash
# Build
cargo build --release

# Run database
./target/release/tsdb --config config/database.yaml

# Write data
curl -X POST http://localhost:8086/write \
  -d "cpu,host=server1 usage=0.64 1465839830100400200"

# Query data
curl -G http://localhost:8086/query \
  --data-urlencode "q=SELECT mean(usage) FROM cpu WHERE time > now() - 1h"
```

---

## Japanese

# TS-001: 時系列データベース

## 概要

圧縮、ダウンサンプリング、連続集計機能を備えた、メトリクス保存に最適化された高性能時系列データベースです。

## アーキテクチャ

### コアコンポーネント

1. **ストレージエンジン**
   - 時間分割データファイル
   - カラムナーストレージ形式
   - 圧縮（Gorilla、Snappy、Zstd）
   - メモリマップファイル

2. **インジェストパイプライン**
   - 先行書き込みログ
   - インメモリバッファ
   - バッチフラッシュ
   - 順序不同データの処理

3. **クエリエンジン**
   - 時間範囲最適化
   - 並列クエリ実行
   - 集計プッシュダウン
   - キャッシュレイヤー

4. **コンパクションシステム**
   - バックグラウンドコンパクション
   - ダウンサンプリング
   - 保存期間の強制
   - 領域回収

5. **連続集計**
   - マテリアライズドビュー
   - インクリメンタル更新
   - ロールアップ階層
   - リアルタイム更新

## 機能

### データモデル
- 多次元メトリクス
- タグとフィールド
- ナノ秒精度
- スキーマオンライト

### 圧縮
- デルタオブデルタタイムスタンプ
- XOR浮動小数点
- 辞書エンコーディング
- ランレングスエンコーディング

### クエリ言語
```sql
SELECT mean(cpu_usage), max(memory)
FROM system_metrics
WHERE host = 'server-1'
  AND time >= now() - 1h
GROUP BY time(5m)
```

### パフォーマンス
- 100万+ポイント/秒のインジェスト
- サブミリ秒クエリ
- 10倍圧縮率
- 効率的な範囲スキャン

## テスト

- インジェストベンチマーク
- クエリパフォーマンステスト
- 圧縮率の検証
- データ整合性チェック
- 同時負荷テスト

## デプロイメント

```bash
# ビルド
cargo build --release

# データベース実行
./target/release/tsdb --config config/database.yaml

# データ書き込み
curl -X POST http://localhost:8086/write \
  -d "cpu,host=server1 usage=0.64 1465839830100400200"

# データクエリ
curl -G http://localhost:8086/query \
  --data-urlencode "q=SELECT mean(usage) FROM cpu WHERE time > now() - 1h"
```