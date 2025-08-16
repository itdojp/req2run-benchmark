# Contributing to Req2Run Benchmark

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

Thank you for considering contributing to the Req2Run Benchmark! This document provides guidelines and instructions for contributing.

### How to Contribute

#### Reporting Issues

1. **Check existing issues** to avoid duplicates
2. **Use issue templates** when available
3. **Provide detailed information**:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details

#### Submitting Pull Requests

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**:
   - Follow coding standards
   - Write tests for new features
   - Update documentation
4. **Test your changes**:
   ```bash
   pytest tests/
   ```
5. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add new problem category for IoT devices"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**

### Development Setup

#### Prerequisites

- Python 3.11+
- Docker 24.0+
- Git

#### Local Development

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/req2run-benchmark.git
cd req2run-benchmark

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8 req2run/
black --check req2run/
```

### Adding New Problems

1. **Create problem definition** in `problems/[difficulty]/[CATEGORY-ID].yaml`
2. **Follow the problem schema**:
   ```yaml
   problem_id: CATEGORY-001
   category: your_category
   difficulty: intermediate
   title: Problem Title
   description: |
     Detailed description
   functional_requirements:
     - id: FR-001
       description: Requirement description
       priority: must
   # ... see existing problems for full structure
   ```
3. **Add test cases** with clear expected outputs
4. **Validate your problem**:
   ```bash
   python -m req2run validate --problem problems/your-problem.yaml
   ```

### Code Style Guidelines

- **Python**: Follow PEP 8
- **YAML**: 2-space indentation
- **Markdown**: Use proper headings hierarchy
- **Commit messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/)

### Testing Guidelines

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage
- Include integration tests for complex features

### Documentation

- Update README.md if adding new features
- Document new APIs with docstrings
- Add examples for new functionality
- Keep documentation bilingual (English/Japanese)

### Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address all review comments
4. Squash commits if requested

### Community Guidelines

- Be respectful and inclusive
- Help others in discussions
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)

---

<a id="japanese"></a>
## 日本語

Req2Run Benchmarkへの貢献をご検討いただきありがとうございます！このドキュメントでは、貢献のためのガイドラインと手順を説明します。

### 貢献方法

#### Issue の報告

1. **既存のIssueを確認**して重複を避ける
2. 利用可能な場合は**Issueテンプレートを使用**
3. **詳細な情報を提供**：
   - 再現手順
   - 期待される動作
   - 実際の動作
   - 環境の詳細

#### プルリクエストの提出

1. **リポジトリをフォーク**
2. **フィーチャーブランチを作成**：
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **変更を実施**：
   - コーディング規約に従う
   - 新機能にはテストを書く
   - ドキュメントを更新
4. **変更をテスト**：
   ```bash
   pytest tests/
   ```
5. **明確なメッセージでコミット**：
   ```bash
   git commit -m "feat: IoTデバイス用の新しい問題カテゴリを追加"
   ```
6. **フォークにプッシュ**：
   ```bash
   git push origin feature/your-feature-name
   ```
7. **プルリクエストを作成**

### 開発環境のセットアップ

#### 前提条件

- Python 3.11+
- Docker 24.0+
- Git

#### ローカル開発

```bash
# フォークをクローン
git clone https://github.com/YOUR_USERNAME/req2run-benchmark.git
cd req2run-benchmark

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 開発モードでインストール
pip install -e .
pip install -r requirements-dev.txt

# テストを実行
pytest

# リンティングを実行
flake8 req2run/
black --check req2run/
```

### 新しい問題の追加

1. **問題定義を作成** `problems/[difficulty]/[CATEGORY-ID].yaml`
2. **問題スキーマに従う**：
   ```yaml
   problem_id: CATEGORY-001
   category: your_category
   difficulty: intermediate
   title: 問題タイトル
   description: |
     詳細な説明
   functional_requirements:
     - id: FR-001
       description: 要件の説明
       priority: must
   # ... 完全な構造は既存の問題を参照
   ```
3. 明確な期待出力を持つ**テストケースを追加**
4. **問題を検証**：
   ```bash
   python -m req2run validate --problem problems/your-problem.yaml
   ```

### コードスタイルガイドライン

- **Python**: PEP 8に従う
- **YAML**: 2スペースインデント
- **Markdown**: 適切な見出し階層を使用
- **コミットメッセージ**: [Conventional Commits](https://www.conventionalcommits.org/)に従う

### テストガイドライン

- 新機能には単体テストを書く
- PR提出前にすべてのテストが通ることを確認
- コードカバレッジ80%以上を目指す
- 複雑な機能には統合テストを含める

### ドキュメント

- 新機能追加時はREADME.mdを更新
- 新しいAPIはdocstringでドキュメント化
- 新機能の例を追加
- ドキュメントは二か国語（英語/日本語）を維持

### レビュープロセス

1. 自動チェックが通る必要がある
2. 少なくとも1人のメンテナーによるレビューが必要
3. すべてのレビューコメントに対応
4. 要求された場合はコミットをスカッシュ

### コミュニティガイドライン

- 敬意を持って包括的に
- ディスカッションで他の人を助ける
- [行動規範](CODE_OF_CONDUCT.md)に従う