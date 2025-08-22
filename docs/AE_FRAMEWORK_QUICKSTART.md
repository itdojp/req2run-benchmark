# AE Framework Quick Start Guide

## 🚀 5-Minute Integration

### Step 1: Set Environment Variable

```bash
# Clone and set path
git clone https://github.com/itdojp/req2run-benchmark.git
cd req2run-benchmark
export REQ2RUN_BENCHMARK_REPO=$(pwd)
```

### Step 2: Install Dependencies

```bash
pip install pyyaml
```

### Step 3: Use in AE Framework

```python
# ae_framework_integration.py
import os
import yaml
from pathlib import Path

# Get repository path
repo_path = os.getenv("REQ2RUN_BENCHMARK_REPO")
if not repo_path:
    print("❌ REQ2RUN_BENCHMARK_REPO not set!")
    print("💡 Run: export REQ2RUN_BENCHMARK_REPO=/path/to/req2run-benchmark")
    exit(1)

# List available problems
problems_dir = Path(repo_path) / "problems"

# Get basic problems for testing
basic_dir = problems_dir / "basic"
if basic_dir.exists():
    problems = list(basic_dir.glob("*.yaml"))
    print(f"✅ Found {len(problems)} basic problems")
    
    # Load first problem
    with open(problems[0], 'r') as f:
        problem = yaml.safe_load(f)
        print(f"📋 Problem: {problem['id']} - {problem['title']}")
else:
    print("❌ Problems directory not found!")
```

### Step 4: Verify Integration

```bash
python ae_framework_integration.py
# Output:
# ✅ Found 5 basic problems
# 📋 Problem: CLI-001 - File Processing CLI Tool
```

## 📁 Expected Repository Structure

```
$REQ2RUN_BENCHMARK_REPO/
├── problems/
│   ├── basic/           # ✅ Basic problems (CLI-001, WEB-001, etc.)
│   ├── intermediate/    # ✅ Intermediate problems
│   ├── advanced/        # ✅ Advanced problems
│   ├── expert/          # ✅ Expert problems
│   └── schema/          # ✅ problem-schema.yaml
└── baselines/           # Reference implementations
```

## 🔍 Problem Discovery Code

```python
def discover_problems():
    """Discover all available problems"""
    repo_path = Path(os.getenv("REQ2RUN_BENCHMARK_REPO"))
    problems_dir = repo_path / "problems"
    
    all_problems = {}
    for difficulty in ["basic", "intermediate", "advanced", "expert"]:
        diff_dir = problems_dir / difficulty
        if diff_dir.exists():
            all_problems[difficulty] = [
                f.stem for f in diff_dir.glob("*.yaml")
            ]
    
    return all_problems

# Usage
problems = discover_problems()
print(f"Available: {problems}")
# Output: {'basic': ['CLI-001', 'WEB-001', ...], ...}
```

## 🎯 Load Specific Problem

```python
def load_problem(problem_id):
    """Load a specific problem by ID"""
    repo_path = Path(os.getenv("REQ2RUN_BENCHMARK_REPO"))
    
    # Search in all difficulty levels
    for difficulty in ["basic", "intermediate", "advanced", "expert"]:
        problem_file = repo_path / "problems" / difficulty / f"{problem_id}.yaml"
        if problem_file.exists():
            with open(problem_file, 'r') as f:
                return yaml.safe_load(f)
    
    return None

# Usage
problem = load_problem("CLI-001")
if problem:
    print(f"Loaded: {problem['title']}")
    print(f"Category: {problem['category']}")
    print(f"Requirements: {len(problem['requirements']['functional'])} functional")
```

## ⚠️ Common Issues

### Issue: REQ2RUN_BENCHMARK_REPO not set
```bash
# Solution: Set environment variable
export REQ2RUN_BENCHMARK_REPO=/absolute/path/to/req2run-benchmark
```

### Issue: Problems not found
```bash
# Solution: Verify structure
ls -la $REQ2RUN_BENCHMARK_REPO/problems/
# Should show: basic, intermediate, advanced, expert, schema
```

### Issue: YAML parsing error
```bash
# Solution: Install PyYAML
pip install pyyaml
```

## 📚 Next Steps

1. Read full integration guide: [AE_FRAMEWORK_INTEGRATION.md](AE_FRAMEWORK_INTEGRATION.md)
2. Explore API reference: [API_REFERENCE.md](API_REFERENCE.md)
3. Understand repository structure: [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md)

## 💬 Support

- Issue Tracker: https://github.com/itdojp/req2run-benchmark/issues
- AE Framework Issue: https://github.com/itdojp/ae-framework/issues/171

---

# AE Framework クイックスタートガイド

## 🚀 5分間統合

### ステップ1: 環境変数を設定

```bash
# クローンしてパスを設定
git clone https://github.com/itdojp/req2run-benchmark.git
cd req2run-benchmark
export REQ2RUN_BENCHMARK_REPO=$(pwd)
```

### ステップ2: 依存関係をインストール

```bash
pip install pyyaml
```

### ステップ3: AE Frameworkで使用

```python
# ae_framework_integration.py
import os
import yaml
from pathlib import Path

# リポジトリパスを取得
repo_path = os.getenv("REQ2RUN_BENCHMARK_REPO")
if not repo_path:
    print("❌ REQ2RUN_BENCHMARK_REPOが設定されていません！")
    print("💡 実行: export REQ2RUN_BENCHMARK_REPO=/path/to/req2run-benchmark")
    exit(1)

# 利用可能な問題をリスト
problems_dir = Path(repo_path) / "problems"

# テスト用の基本問題を取得
basic_dir = problems_dir / "basic"
if basic_dir.exists():
    problems = list(basic_dir.glob("*.yaml"))
    print(f"✅ {len(problems)}個の基本問題が見つかりました")
    
    # 最初の問題をロード
    with open(problems[0], 'r') as f:
        problem = yaml.safe_load(f)
        print(f"📋 問題: {problem['id']} - {problem['title']}")
else:
    print("❌ 問題ディレクトリが見つかりません！")
```

### ステップ4: 統合を確認

```bash
python ae_framework_integration.py
# 出力:
# ✅ 5個の基本問題が見つかりました
# 📋 問題: CLI-001 - ファイル処理CLIツール
```

## 📁 期待されるリポジトリ構造

```
$REQ2RUN_BENCHMARK_REPO/
├── problems/
│   ├── basic/           # ✅ 基本問題（CLI-001、WEB-001など）
│   ├── intermediate/    # ✅ 中級問題
│   ├── advanced/        # ✅ 上級問題
│   ├── expert/          # ✅ エキスパート問題
│   └── schema/          # ✅ problem-schema.yaml
└── baselines/           # リファレンス実装
```

## 🔍 問題検出コード

```python
def discover_problems():
    """すべての利用可能な問題を検出"""
    repo_path = Path(os.getenv("REQ2RUN_BENCHMARK_REPO"))
    problems_dir = repo_path / "problems"
    
    all_problems = {}
    for difficulty in ["basic", "intermediate", "advanced", "expert"]:
        diff_dir = problems_dir / difficulty
        if diff_dir.exists():
            all_problems[difficulty] = [
                f.stem for f in diff_dir.glob("*.yaml")
            ]
    
    return all_problems

# 使用法
problems = discover_problems()
print(f"利用可能: {problems}")
# 出力: {'basic': ['CLI-001', 'WEB-001', ...], ...}
```

## 🎯 特定の問題をロード

```python
def load_problem(problem_id):
    """IDで特定の問題をロード"""
    repo_path = Path(os.getenv("REQ2RUN_BENCHMARK_REPO"))
    
    # すべての難易度レベルで検索
    for difficulty in ["basic", "intermediate", "advanced", "expert"]:
        problem_file = repo_path / "problems" / difficulty / f"{problem_id}.yaml"
        if problem_file.exists():
            with open(problem_file, 'r') as f:
                return yaml.safe_load(f)
    
    return None

# 使用法
problem = load_problem("CLI-001")
if problem:
    print(f"ロード済み: {problem['title']}")
    print(f"カテゴリ: {problem['category']}")
    print(f"要件: {len(problem['requirements']['functional'])}個の機能要件")
```

## ⚠️ よくある問題

### 問題: REQ2RUN_BENCHMARK_REPOが設定されていない
```bash
# 解決策: 環境変数を設定
export REQ2RUN_BENCHMARK_REPO=/absolute/path/to/req2run-benchmark
```

### 問題: 問題が見つからない
```bash
# 解決策: 構造を確認
ls -la $REQ2RUN_BENCHMARK_REPO/problems/
# 表示されるべき: basic, intermediate, advanced, expert, schema
```

### 問題: YAML解析エラー
```bash
# 解決策: PyYAMLをインストール
pip install pyyaml
```

## 📚 次のステップ

1. 完全な統合ガイドを読む: [AE_FRAMEWORK_INTEGRATION.md](AE_FRAMEWORK_INTEGRATION.md)
2. APIリファレンスを探索: [API_REFERENCE.md](API_REFERENCE.md)
3. リポジトリ構造を理解: [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md)

## 💬 サポート

- Issueトラッカー: https://github.com/itdojp/req2run-benchmark/issues
- AE Framework Issue: https://github.com/itdojp/ae-framework/issues/171