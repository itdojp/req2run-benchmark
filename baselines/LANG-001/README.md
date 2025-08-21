# LANG-001: SQL-like Query Language Interpreter Baseline Implementation

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

This is a reference implementation for the LANG-001 problem: SQL-like Query Language Interpreter with B+Tree indexing, query optimization, and transaction support.

## Problem Requirements

### Functional Requirements (MUST)
- **MUST** implement SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY clauses
- **MUST** support aggregate functions: COUNT, SUM, AVG, MIN, MAX
- **MUST** implement B+Tree indexing structure for high-speed retrieval
- **MUST** provide query execution plan optimization and EXPLAIN output
- **MUST** support loading tables from CSV files
- **MUST** implement SQL parser with proper error handling
- **MUST** support data types: INTEGER, TEXT, REAL, and NULL values
- **MUST** implement proper memory management for large datasets

### Non-Functional Requirements
- **SHOULD** implement ACID transaction support (BEGIN, COMMIT, ROLLBACK)
- **MUST** achieve <100ms indexed scans on 1M rows
- **MUST** handle 1000 queries per second
- **MUST** support 100 concurrent users

## Implementation Details

### Technology Stack
- **Language**: Python 3.11
- **Parser**: Custom recursive descent parser
- **Indexing**: B+Tree implementation
- **Storage**: Custom page-based storage engine
- **Testing**: pytest with performance benchmarks
- **CLI**: Click framework

### Project Structure
```
LANG-001/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── lexer.py         # SQL tokenization
│   │   ├── parser.py        # Recursive descent parser
│   │   ├── ast_nodes.py     # Abstract syntax tree nodes
│   │   └── sql_grammar.py   # SQL grammar definitions
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── btree.py         # B+Tree implementation
│   │   ├── storage_engine.py # Page-based storage
│   │   ├── table.py         # Table management
│   │   └── index.py         # Index management
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── query_planner.py # Query optimization
│   │   ├── executor.py      # Query execution engine
│   │   ├── operators.py     # Query operators (Join, Scan, etc.)
│   │   └── aggregation.py   # Aggregate functions
│   ├── transaction/
│   │   ├── __init__.py
│   │   ├── transaction_manager.py # Transaction control
│   │   ├── lock_manager.py  # Concurrency control
│   │   └── log_manager.py   # Write-ahead logging
│   ├── types/
│   │   ├── __init__.py
│   │   ├── data_types.py    # SQL data types
│   │   └── schema.py        # Table schemas
│   └── cli/
│       ├── __init__.py
│       └── commands.py      # CLI commands
├── tests/
│   ├── unit/
│   │   ├── test_parser.py
│   │   ├── test_btree.py
│   │   ├── test_executor.py
│   │   └── test_aggregation.py
│   ├── integration/
│   │   ├── test_sql_queries.py
│   │   ├── test_transactions.py
│   │   └── test_csv_import.py
│   ├── performance/
│   │   ├── test_index_performance.py
│   │   └── test_concurrent_queries.py
│   └── fixtures/
│       ├── test_schema.sql
│       └── sample_data/
├── test_data/
│   ├── customers.csv
│   ├── orders.csv
│   ├── products.csv
│   └── large_dataset_1m.csv
├── Dockerfile
├── requirements.txt
├── config.yaml
└── README.md
```

## Expected Performance Metrics

Expected scores for this baseline:
- **Functional Coverage**: 100% (all MUST requirements)
- **Test Pass Rate**: 95% (comprehensive test suite)
- **Performance**: 90% (meets strict performance requirements)  
- **Code Quality**: 85% (clean, well-documented code)
- **Security**: 80% (basic input validation)
- **Total Score: 92%** (Gold)

## Usage Examples

### Interactive SQL Shell
```bash
# Start interactive shell
./sql-interpreter

sql> CREATE TABLE users (id INTEGER, name TEXT, age INTEGER);
sql> INSERT INTO users VALUES (1, 'Alice', 30);
sql> SELECT * FROM users WHERE age > 25;
sql> EXPLAIN SELECT * FROM users WHERE age > 25;
```

## References

- [Database System Concepts](https://db-book.com/) - Silberschatz, Galvin, Gagne
- [CMU 15-445 Database Systems](https://15445.courses.cs.cmu.edu/) - Course materials
- [B+Tree Analysis](https://en.wikipedia.org/wiki/B%2B_tree) - Wikipedia
- [SQL-92 Standard](https://www.iso.org/standard/16663.html) - ISO/IEC 9075

---

<a id="japanese"></a>
## 日本語

# LANG-001: SQL風クエリ言語インタープリター ベースライン実装

## 概要

LANG-001問題のリファレンス実装です：B+Treeインデックシング、クエリ最適化、トランザクションサポートを備えたSQL風クエリ言語インタープリターです。

## 問題要件

### 機能要件（必須）
- **必須** SELECT、FROM、WHERE、JOIN、GROUP BY、ORDER BY 句の実装
- **必須** 集約関数のサポート: COUNT、SUM、AVG、MIN、MAX
- **必須** 高速検索のためのB+Treeインデックシング構造の実装
- **必須** クエリ実行プランの最適化とEXPLAIN出力の提供
- **必須** CSVファイルからのテーブル読み込みサポート
- **必須** 適切なエラーハンドリングを備えたSQLパーサーの実装
- **必須** データタイプのサポート: INTEGER、TEXT、REAL、NULL値
- **必須** 大規模データセットのための適切なメモリ管理の実装

### 非機能要件
- **推奨** ACIDトランザクションサポートの実装（BEGIN、COMMIT、ROLLBACK）
- **必須** 1M行のインデックススキャンで100ms未満の達成
- **必須** 1秒あたリ1000クエリの処理
- **必須** 100同時ユーザーのサポート

## 実装詳細

### 技術スタック
- **言語**: Python 3.11
- **パーサー**: カスタム再帰下降パーサー
- **インデックシング**: B+Tree実装
- **ストレージ**: カスタムページベースストレージエンジン
- **テスト**: パフォーマンスベンチマークを含むpytest
- **CLI**: Clickフレームワーク

### プロジェクト構造
```
LANG-001/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLIエントリポイント
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── lexer.py         # SQLトークン化
│   │   ├── parser.py        # 再帰下降パーサー
│   │   ├── ast_nodes.py     # 抽象構文木ノード
│   │   └── sql_grammar.py   # SQL文法定義
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── btree.py         # B+Tree実装
│   │   ├── storage_engine.py # ページベースストレージ
│   │   ├── table.py         # テーブル管理
│   │   └── index.py         # インデックス管理
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── query_planner.py # クエリ最適化
│   │   ├── executor.py      # クエリ実行エンジン
│   │   ├── operators.py     # クエリ演算子（Join、Scanなど）
│   │   └── aggregation.py   # 集約関数
│   ├── transaction/
│   │   ├── __init__.py
│   │   ├── transaction_manager.py # トランザクション制御
│   │   ├── lock_manager.py  # 並行制御
│   │   └── log_manager.py   # 先行書き込みログ
│   ├── types/
│   │   ├── __init__.py
│   │   ├── data_types.py    # SQLデータタイプ
│   │   └── schema.py        # テーブルスキーマ
│   └── cli/
│       ├── __init__.py
│       └── commands.py      # CLIコマンド
├── tests/
│   ├── unit/
│   │   ├── test_parser.py
│   │   ├── test_btree.py
│   │   ├── test_executor.py
│   │   └── test_aggregation.py
│   ├── integration/
│   │   ├── test_sql_queries.py
│   │   ├── test_transactions.py
│   │   └── test_csv_import.py
│   ├── performance/
│   │   ├── test_index_performance.py
│   │   └── test_concurrent_queries.py
│   └── fixtures/
│       ├── test_schema.sql
│       └── sample_data/
├── test_data/
│   ├── customers.csv
│   │   ├── orders.csv
│   │   ├── products.csv
│   │   └── large_dataset_1m.csv
├── Dockerfile
├── requirements.txt
├── config.yaml
└── README.md
```

## 期待パフォーマンス指標

このベースラインの期待スコア:
- **機能カバレッジ**: 100%（全ての必須要件）
- **テスト合格率**: 95%（網羅的テストスイート）
- **パフォーマンス**: 90%（厳しいパフォーマンス要件を満たす）
- **コード品質**: 85%（クリーンでよく文書化されたコード）
- **セキュリティ**: 80%（基本的な入力検証）
- **総合スコア: 92%** （ゴールド）

## 使用例

### インタラクティブSQLシェル
```bash
# インタラクティブシェルを起動
./sql-interpreter

sql> CREATE TABLE users (id INTEGER, name TEXT, age INTEGER);
sql> INSERT INTO users VALUES (1, 'Alice', 30);
sql> SELECT * FROM users WHERE age > 25;
sql> EXPLAIN SELECT * FROM users WHERE age > 25;
```

## 参考資料

- [Database System Concepts](https://db-book.com/) - Silberschatz, Galvin, Gagne
- [CMU 15-445 Database Systems](https://15445.courses.cs.cmu.edu/) - コース資料
- [B+Tree分析](https://en.wikipedia.org/wiki/B%2B_tree) - Wikipedia
- [SQL-92標準](https://www.iso.org/standard/16663.html) - ISO/IEC 9075