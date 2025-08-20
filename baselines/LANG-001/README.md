# LANG-001: SQL-like Query Language Interpreter Baseline Implementation

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