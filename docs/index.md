# Req2Run Benchmark

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

Welcome to the Req2Run Benchmark documentation. This benchmark suite is designed to evaluate AI and LLM code generation capabilities across a wide range of programming challenges.

### Overview

Req2Run provides a comprehensive set of benchmark problems spanning multiple difficulty levels and technical domains:

- **35 Benchmark Problems** across various categories
- **4 Difficulty Levels**: Basic, Intermediate, Advanced, Expert
- **Multiple Languages**: Python, JavaScript, TypeScript, Go, Java, Rust
- **Diverse Domains**: Web APIs, Databases, CLI Tools, Machine Learning, Cryptography, and more
- **🌐 Full Internationalization**: Complete documentation available in English and Japanese

## Quick Links

- [Problem Catalog](PROBLEM_CATALOG.md) - Browse all available benchmark problems
- [Getting Started Guide](getting-started/quickstart.md) - Start using the benchmark
- [Contributing](development/contributing.md) - Add new problems or improvements
- [GitHub Repository](https://github.com/itdojp/req2run-benchmark)

## Features

### Comprehensive Problem Set
- Web API development (REST, GraphQL, WebSocket)
- Database engines and query processors
- Machine learning pipelines
- Cryptographic implementations
- Real-time systems
- Distributed systems

### Rigorous Evaluation
- Functional correctness testing
- Performance benchmarking
- Security validation
- Code quality metrics
- Resource usage monitoring

### Flexible Framework
- Language-agnostic problem definitions
- Docker-based isolation
- Automated evaluation pipeline
- Extensible architecture

## Getting Started

```bash
# Clone the repository
git clone https://github.com/itdojp/req2run-benchmark.git

# Install dependencies
pip install -r requirements.txt

# Run a benchmark
python -m req2run.evaluate --problem WEB-001
```

## Problem Categories

| Category | Count | Description |
|----------|-------|-------------|
| Web API | 7 | RESTful services, GraphQL, WebSockets |
| Database | 4 | SQL engines, time-series, event sourcing |
| CLI Tool | 3 | Terminal UIs, job orchestration |
| Machine Learning | 2 | ML pipelines, model serving |
| Cryptography | 2 | Zero-knowledge proofs, homomorphic encryption |
| Authentication | 2 | OAuth, RBAC/ABAC |
| Network Protocol | 2 | gRPC, reverse proxy |
| Others | 5+ | Blockchain, orchestration, observability |

## Contributing

We welcome contributions! Please see our [Contributing Guide](development/contributing.md) for details on:
- Adding new benchmark problems
- Improving existing problems
- Enhancing the evaluation framework
- Documentation improvements

## License

This project is licensed under the MIT License. See [LICENSE](about/license.md) for details.

---

<a id="japanese"></a>
## 日本語

Req2Run ベンチマークドキュメントへようこそ。このベンチマークスイートは、幅広いプログラミング課題にわたってAIとLLMのコード生成能力を評価するために設計されています。

### 概要

Req2Runは、複数の難易度レベルと技術領域にわたる包括的なベンチマーク問題セットを提供します：

- **35のベンチマーク問題** 様々なカテゴリにわたって
- **4つの難易度レベル**: Basic、Intermediate、Advanced、Expert
- **複数の言語**: Python、JavaScript、TypeScript、Go、Java、Rust
- **多様なドメイン**: Web API、データベース、CLIツール、機械学習、暗号化など
- **🌐 完全な国際化対応**: 全ドキュメントが英語と日本語で利用可能

### クイックリンク

- [問題カタログ](PROBLEM_CATALOG.md) - 利用可能なすべてのベンチマーク問題を閲覧
- [スタートガイド](getting-started/quickstart.md) - ベンチマークの使用開始
- [貢献](development/contributing.md) - 新しい問題や改善の追加
- [GitHubリポジトリ](https://github.com/itdojp/req2run-benchmark)

### 機能

#### 包括的な問題セット
- Web API開発（REST、GraphQL、WebSocket）
- データベースエンジンとクエリプロセッサ
- 機械学習パイプライン
- 暗号化実装
- リアルタイムシステム
- 分散システム

#### 厳密な評価
- 機能的正確性テスト
- パフォーマンスベンチマーク
- セキュリティ検証
- コード品質メトリクス
- リソース使用監視

#### 柔軟なフレームワーク
- 言語非依存の問題定義
- Dockerベースの分離
- 自動評価パイプライン
- 拡張可能なアーキテクチャ

### はじめに

```bash
# リポジトリのクローン
git clone https://github.com/itdojp/req2run-benchmark.git

# 依存関係のインストール
pip install -r requirements.txt

# ベンチマークの実行
python -m req2run.evaluate --problem WEB-001
```

### 問題カテゴリ

| カテゴリ | 数 | 説明 |
|----------|-------|-------------|
| Web API | 7 | RESTfulサービス、GraphQL、WebSocket |
| データベース | 4 | SQLエンジン、時系列、イベントソーシング |
| CLIツール | 3 | ターミナルUI、ジョブオーケストレーション |
| 機械学習 | 2 | MLパイプライン、モデルサービング |
| 暗号化 | 2 | ゼロ知識証明、準同型暗号化 |
| 認証 | 2 | OAuth、RBAC/ABAC |
| ネットワークプロトコル | 2 | gRPC、リバースプロキシ |
| その他 | 5+ | ブロックチェーン、オーケストレーション、可観測性 |

### 貢献

貢献を歓迎します！詳細については[貢献ガイド](development/contributing.md)をご覧ください：
- 新しいベンチマーク問題の追加
- 既存の問題の改善
- 評価フレームワークの強化
- ドキュメントの改善

### ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。詳細は[LICENSE](about/license.md)をご覧ください。