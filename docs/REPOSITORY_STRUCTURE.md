# Req2Run Repository Structure

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

### Overview

This document describes the complete structure of the Req2Run Benchmark repository, including directory organization, file naming conventions, and the purpose of each component.

### Repository Layout

```
req2run-benchmark/
├── problems/                      # Problem definitions
│   ├── basic/                     # Basic difficulty problems
│   │   ├── CLI-001.yaml          # File Processing CLI Tool
│   │   ├── WEB-001.yaml          # Simple REST API
│   │   └── ...
│   ├── intermediate/              # Intermediate difficulty problems
│   │   ├── CLI-010.yaml          # TUI Dashboard
│   │   ├── WEB-010.yaml          # WebSocket Chat Server
│   │   └── ...
│   ├── advanced/                  # Advanced difficulty problems
│   │   ├── DATA-001.yaml         # Real-time Log Aggregation
│   │   ├── AUTH-010.yaml         # OAuth 2.0 Provider
│   │   └── ...
│   ├── expert/                    # Expert difficulty problems
│   │   ├── SYS-001.yaml          # Distributed Lock Coordinator
│   │   ├── CHAIN-001.yaml        # Smart Contract Platform
│   │   └── ...
│   └── schema/                    # Schema definitions
│       └── problem-schema.yaml    # Problem definition schema
│
├── baselines/                     # Reference implementations
│   ├── CLI-001/                   # Implementation for CLI-001
│   │   ├── README.md             # Problem-specific documentation
│   │   ├── requirements.txt      # Python dependencies
│   │   ├── Dockerfile            # Container definition
│   │   ├── src/                  # Source code
│   │   └── tests/                # Test cases
│   └── ...
│
├── req2run/                       # Core framework code
│   ├── __init__.py               # Package initialization
│   ├── api.py                    # API module
│   ├── cli.py                    # CLI interface
│   ├── core.py                   # Core functionality
│   ├── metrics.py                # Metrics calculation
│   ├── runner.py                 # Execution runner
│   └── reporter.py               # Report generation
│
├── tests/                         # Framework tests
│   ├── unit/                     # Unit tests
│   │   ├── test_api.py
│   │   ├── test_cli.py
│   │   └── test_core.py
│   └── integration/              # Integration tests
│       ├── test_integration.py
│       └── test_e2e.py
│
├── scripts/                       # Utility scripts
│   ├── setup-env.sh              # Environment setup (Linux/Mac)
│   ├── setup-env.ps1             # Environment setup (PowerShell)
│   ├── setup-env.bat             # Environment setup (Windows CMD)
│   └── validate-all.py           # Validate all problems
│
├── docs/                          # Documentation
│   ├── README.md                 # Main documentation
│   ├── ENVIRONMENT_SETUP.md      # Environment setup guide
│   ├── DEPENDENCY_TROUBLESHOOTING.md # Dependency troubleshooting
│   ├── AE_FRAMEWORK_INTEGRATION.md   # AE Framework integration
│   ├── API_REFERENCE.md          # API documentation
│   ├── REPOSITORY_STRUCTURE.md   # This file
│   └── AE_FRAMEWORK_QUICKSTART.md # Quick start for AE Framework
│
├── examples/                      # Integration examples
│   ├── python/                   # Python examples
│   │   ├── basic_usage.py
│   │   └── advanced_integration.py
│   ├── javascript/               # JavaScript examples
│   │   └── problem_discovery.js
│   └── frameworks/               # Framework integrations
│       ├── ae-framework/
│       ├── langchain/
│       └── autogen/
│
├── .github/                       # GitHub configuration
│   ├── workflows/                # GitHub Actions
│   │   ├── ci.yml               # Continuous Integration
│   │   ├── validate.yml         # Problem validation
│   │   └── release.yml          # Release workflow
│   └── ISSUE_TEMPLATE/           # Issue templates
│
├── docker/                        # Docker configurations
│   ├── Dockerfile                # Main Docker image
│   ├── docker-compose.yml        # Development compose
│   └── docker-compose.test.yml   # Testing compose
│
├── requirements.txt               # Python dependencies
├── setup.py                      # Python package setup
├── README.md                     # Repository README
├── LICENSE                       # MIT License
└── .gitignore                    # Git ignore rules
```

### Directory Descriptions

#### `/problems`

Contains all benchmark problem definitions in YAML format.

**Structure:**
- Organized by difficulty level: `basic/`, `intermediate/`, `advanced/`, `expert/`
- Each problem file is named with its ID (e.g., `CLI-001.yaml`)
- Schema definition in `schema/problem-schema.yaml`

**Naming Convention:**
- Format: `{CATEGORY}-{NUMBER}.yaml`
- Categories: CLI, WEB, DATA, AUTH, NET, CRYPTO, SYS, etc.
- Numbers: 001-999, with ranges indicating difficulty:
  - 001-009: Basic implementations
  - 010-099: Intermediate complexity
  - 100+: Advanced/Expert level

#### `/baselines`

Reference implementations for each problem.

**Structure:**
- Each problem has its own directory named by problem ID
- Standard files in each baseline:
  - `README.md`: Bilingual documentation
  - `requirements.txt` or `package.json`: Dependencies
  - `Dockerfile`: Container definition
  - `src/`: Source code
  - `tests/`: Test cases
  - `config/`: Configuration files (if needed)

#### `/req2run`

Core framework implementation.

**Modules:**
- `api.py`: Programmatic API for problem access
- `cli.py`: Command-line interface
- `core.py`: Core evaluation logic
- `metrics.py`: Metric calculation functions
- `runner.py`: Execution environment management
- `reporter.py`: Result reporting and formatting

#### `/tests`

Framework test suite.

**Organization:**
- `unit/`: Unit tests for individual modules
- `integration/`: Integration tests for complete workflows
- Test files follow `test_*.py` naming convention

#### `/scripts`

Utility and helper scripts.

**Contents:**
- Environment setup scripts for different platforms
- Problem validation scripts
- Bulk operations scripts
- Development utilities

#### `/docs`

Comprehensive documentation.

**Key Documents:**
- Setup and installation guides
- API references
- Integration guides
- Troubleshooting documentation
- Architecture documentation

#### `/examples`

Sample code and integration examples.

**Organization:**
- Language-specific examples
- Framework integration samples
- Common usage patterns
- Best practices demonstrations

### File Naming Conventions

#### Problem Files
- Format: `{CATEGORY}-{NUMBER}.yaml`
- Example: `CLI-001.yaml`, `WEB-010.yaml`
- Always uppercase category, zero-padded numbers

#### Python Files
- Snake_case for modules: `problem_loader.py`
- Test files prefixed with `test_`: `test_api.py`

#### Documentation
- Uppercase for main docs: `README.md`, `LICENSE`
- Title case with underscores: `ENVIRONMENT_SETUP.md`
- Bilingual docs include both languages in same file

#### Configuration
- YAML for problem definitions and configs
- JSON for data files
- `.env` for environment variables

### Problem Categories

| Code | Category | Description |
|------|----------|-------------|
| CLI | cli_tool | Command-line interface tools |
| WEB | web_api | Web APIs and services |
| DATA | data_processing | Data processing pipelines |
| AUTH | authentication | Authentication and authorization |
| NET | network_protocol | Network protocols and services |
| CRYPTO | cryptography | Cryptographic implementations |
| SYS | system_utility | System utilities and tools |
| DB | database | Database implementations |
| ML | machine_learning | Machine learning pipelines |
| CHAIN | blockchain | Blockchain and smart contracts |
| ORCH | orchestration | Container orchestration |
| MESH | service_mesh | Service mesh implementations |
| RTC | real_time_communication | Real-time communication |
| GQL | api_gateway | GraphQL and API gateways |
| FN | runtime_platform | Serverless and functions |
| LANG | language_processor | Language processors |
| TS | time_series | Time-series databases |
| OBS | observability | Observability and monitoring |

### Version Control

#### Branch Structure
- `main`: Stable release branch
- `develop`: Development branch
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches
- `release/*`: Release preparation branches

#### Commit Message Format
```
type: description

- Detail 1
- Detail 2

Closes #issue_number
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

### Integration Points

#### Environment Variables
- `REQ2RUN_BENCHMARK_REPO`: Repository root path
- `REQ2RUN_CONFIG`: Configuration file path
- `REQ2RUN_LOG_LEVEL`: Logging level (DEBUG, INFO, WARN, ERROR)

#### Entry Points
- CLI: `python -m req2run.cli`
- API: `from req2run.api import Req2RunAPI`
- Docker: `docker run req2run/benchmark`

---

<a id="japanese"></a>
## 日本語

### 概要

このドキュメントでは、Req2Run Benchmarkリポジトリの完全な構造について、ディレクトリ構成、ファイル命名規則、各コンポーネントの目的を含めて説明します。

### リポジトリレイアウト

```
req2run-benchmark/
├── problems/                      # 問題定義
│   ├── basic/                     # 基本難易度の問題
│   │   ├── CLI-001.yaml          # ファイル処理CLIツール
│   │   ├── WEB-001.yaml          # シンプルなREST API
│   │   └── ...
│   ├── intermediate/              # 中級難易度の問題
│   │   ├── CLI-010.yaml          # TUIダッシュボード
│   │   ├── WEB-010.yaml          # WebSocketチャットサーバー
│   │   └── ...
│   ├── advanced/                  # 上級難易度の問題
│   │   ├── DATA-001.yaml         # リアルタイムログ集約
│   │   ├── AUTH-010.yaml         # OAuth 2.0プロバイダー
│   │   └── ...
│   ├── expert/                    # エキスパート難易度の問題
│   │   ├── SYS-001.yaml          # 分散ロックコーディネーター
│   │   ├── CHAIN-001.yaml        # スマートコントラクトプラットフォーム
│   │   └── ...
│   └── schema/                    # スキーマ定義
│       └── problem-schema.yaml    # 問題定義スキーマ
│
├── baselines/                     # リファレンス実装
│   ├── CLI-001/                   # CLI-001の実装
│   │   ├── README.md             # 問題固有のドキュメント
│   │   ├── requirements.txt      # Python依存関係
│   │   ├── Dockerfile            # コンテナ定義
│   │   ├── src/                  # ソースコード
│   │   └── tests/                # テストケース
│   └── ...
│
├── req2run/                       # コアフレームワークコード
│   ├── __init__.py               # パッケージ初期化
│   ├── api.py                    # APIモジュール
│   ├── cli.py                    # CLIインターフェース
│   ├── core.py                   # コア機能
│   ├── metrics.py                # メトリクス計算
│   ├── runner.py                 # 実行ランナー
│   └── reporter.py               # レポート生成
│
├── tests/                         # フレームワークテスト
│   ├── unit/                     # ユニットテスト
│   │   ├── test_api.py
│   │   ├── test_cli.py
│   │   └── test_core.py
│   └── integration/              # 統合テスト
│       ├── test_integration.py
│       └── test_e2e.py
│
├── scripts/                       # ユーティリティスクリプト
│   ├── setup-env.sh              # 環境セットアップ（Linux/Mac）
│   ├── setup-env.ps1             # 環境セットアップ（PowerShell）
│   ├── setup-env.bat             # 環境セットアップ（Windows CMD）
│   └── validate-all.py           # すべての問題を検証
│
├── docs/                          # ドキュメント
│   ├── README.md                 # メインドキュメント
│   ├── ENVIRONMENT_SETUP.md      # 環境セットアップガイド
│   ├── DEPENDENCY_TROUBLESHOOTING.md # 依存関係トラブルシューティング
│   ├── AE_FRAMEWORK_INTEGRATION.md   # AE Framework統合
│   ├── API_REFERENCE.md          # APIドキュメント
│   ├── REPOSITORY_STRUCTURE.md   # このファイル
│   └── AE_FRAMEWORK_QUICKSTART.md # AE Frameworkクイックスタート
│
├── examples/                      # 統合例
│   ├── python/                   # Python例
│   │   ├── basic_usage.py
│   │   └── advanced_integration.py
│   ├── javascript/               # JavaScript例
│   │   └── problem_discovery.js
│   └── frameworks/               # フレームワーク統合
│       ├── ae-framework/
│       ├── langchain/
│       └── autogen/
│
├── .github/                       # GitHub設定
│   ├── workflows/                # GitHub Actions
│   │   ├── ci.yml               # 継続的インテグレーション
│   │   ├── validate.yml         # 問題検証
│   │   └── release.yml          # リリースワークフロー
│   └── ISSUE_TEMPLATE/           # Issueテンプレート
│
├── docker/                        # Docker設定
│   ├── Dockerfile                # メインDockerイメージ
│   ├── docker-compose.yml        # 開発用compose
│   └── docker-compose.test.yml   # テスト用compose
│
├── requirements.txt               # Python依存関係
├── setup.py                      # Pythonパッケージセットアップ
├── README.md                     # リポジトリREADME
├── LICENSE                       # MITライセンス
└── .gitignore                    # Git無視ルール
```

### ディレクトリの説明

#### `/problems`

YAML形式のすべてのベンチマーク問題定義を含みます。

**構造:**
- 難易度レベルで整理: `basic/`、`intermediate/`、`advanced/`、`expert/`
- 各問題ファイルはIDで命名（例：`CLI-001.yaml`）
- スキーマ定義は`schema/problem-schema.yaml`に配置

**命名規則:**
- 形式: `{CATEGORY}-{NUMBER}.yaml`
- カテゴリ: CLI、WEB、DATA、AUTH、NET、CRYPTO、SYSなど
- 番号: 001-999、範囲は難易度を示す：
  - 001-009: 基本実装
  - 010-099: 中級複雑度
  - 100+: 上級/エキスパートレベル

#### `/baselines`

各問題のリファレンス実装。

**構造:**
- 各問題は問題IDで命名された独自のディレクトリを持つ
- 各ベースラインの標準ファイル：
  - `README.md`: バイリンガルドキュメント
  - `requirements.txt`または`package.json`: 依存関係
  - `Dockerfile`: コンテナ定義
  - `src/`: ソースコード
  - `tests/`: テストケース
  - `config/`: 設定ファイル（必要な場合）

#### `/req2run`

コアフレームワーク実装。

**モジュール:**
- `api.py`: 問題アクセスのためのプログラマティックAPI
- `cli.py`: コマンドラインインターフェース
- `core.py`: コア評価ロジック
- `metrics.py`: メトリクス計算関数
- `runner.py`: 実行環境管理
- `reporter.py`: 結果レポートとフォーマット

#### `/tests`

フレームワークテストスイート。

**構成:**
- `unit/`: 個別モジュールのユニットテスト
- `integration/`: 完全なワークフローの統合テスト
- テストファイルは`test_*.py`命名規則に従う

#### `/scripts`

ユーティリティとヘルパースクリプト。

**内容:**
- 異なるプラットフォーム用の環境セットアップスクリプト
- 問題検証スクリプト
- バルク操作スクリプト
- 開発ユーティリティ

#### `/docs`

包括的なドキュメント。

**主要ドキュメント:**
- セットアップとインストールガイド
- APIリファレンス
- 統合ガイド
- トラブルシューティングドキュメント
- アーキテクチャドキュメント

#### `/examples`

サンプルコードと統合例。

**構成:**
- 言語固有の例
- フレームワーク統合サンプル
- 一般的な使用パターン
- ベストプラクティスのデモンストレーション

### ファイル命名規則

#### 問題ファイル
- 形式: `{CATEGORY}-{NUMBER}.yaml`
- 例: `CLI-001.yaml`、`WEB-010.yaml`
- 常に大文字のカテゴリ、ゼロパディングされた番号

#### Pythonファイル
- モジュールにはsnake_case: `problem_loader.py`
- テストファイルは`test_`で始まる: `test_api.py`

#### ドキュメント
- メインドキュメントは大文字: `README.md`、`LICENSE`
- アンダースコア付きタイトルケース: `ENVIRONMENT_SETUP.md`
- バイリンガルドキュメントは同じファイルに両言語を含む

#### 設定
- 問題定義と設定にはYAML
- データファイルにはJSON
- 環境変数には`.env`

### 問題カテゴリ

| コード | カテゴリ | 説明 |
|--------|----------|------|
| CLI | cli_tool | コマンドラインインターフェースツール |
| WEB | web_api | Web APIとサービス |
| DATA | data_processing | データ処理パイプライン |
| AUTH | authentication | 認証と認可 |
| NET | network_protocol | ネットワークプロトコルとサービス |
| CRYPTO | cryptography | 暗号化実装 |
| SYS | system_utility | システムユーティリティとツール |
| DB | database | データベース実装 |
| ML | machine_learning | 機械学習パイプライン |
| CHAIN | blockchain | ブロックチェーンとスマートコントラクト |
| ORCH | orchestration | コンテナオーケストレーション |
| MESH | service_mesh | サービスメッシュ実装 |
| RTC | real_time_communication | リアルタイム通信 |
| GQL | api_gateway | GraphQLとAPIゲートウェイ |
| FN | runtime_platform | サーバーレスと関数 |
| LANG | language_processor | 言語プロセッサ |
| TS | time_series | 時系列データベース |
| OBS | observability | 可観測性と監視 |

### バージョン管理

#### ブランチ構造
- `main`: 安定版リリースブランチ
- `develop`: 開発ブランチ
- `feature/*`: 機能ブランチ
- `fix/*`: バグ修正ブランチ
- `release/*`: リリース準備ブランチ

#### コミットメッセージ形式
```
type: 説明

- 詳細1
- 詳細2

Closes #issue_number
```

タイプ: `feat`、`fix`、`docs`、`test`、`refactor`、`chore`

### 統合ポイント

#### 環境変数
- `REQ2RUN_BENCHMARK_REPO`: リポジトリルートパス
- `REQ2RUN_CONFIG`: 設定ファイルパス
- `REQ2RUN_LOG_LEVEL`: ログレベル（DEBUG、INFO、WARN、ERROR）

#### エントリーポイント
- CLI: `python -m req2run.cli`
- API: `from req2run.api import Req2RunAPI`
- Docker: `docker run req2run/benchmark`