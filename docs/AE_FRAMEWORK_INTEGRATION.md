# AE Framework Integration Guide

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

### Overview

This guide provides comprehensive instructions for integrating the AE Framework with Req2Run Benchmark. The integration enables AI/LLM evaluation pipelines to use standardized benchmark problems from Req2Run.

### Quick Start

#### 1. Clone the Repository

```bash
# Clone req2run-benchmark repository
git clone https://github.com/itdojp/req2run-benchmark.git
cd req2run-benchmark
```

#### 2. Set Environment Variable

```bash
# Linux/Mac
export REQ2RUN_BENCHMARK_REPO=$(pwd)
echo "export REQ2RUN_BENCHMARK_REPO=$(pwd)" >> ~/.bashrc

# Windows PowerShell
$env:REQ2RUN_BENCHMARK_REPO = (Get-Location).Path
[Environment]::SetEnvironmentVariable("REQ2RUN_BENCHMARK_REPO", (Get-Location).Path, "User")

# Windows CMD
set REQ2RUN_BENCHMARK_REPO=%cd%
setx REQ2RUN_BENCHMARK_REPO "%cd%"
```

#### 3. Verify Installation

```python
import os
import json
from pathlib import Path

# Verify environment variable
repo_path = os.getenv("REQ2RUN_BENCHMARK_REPO")
if not repo_path:
    raise ValueError("REQ2RUN_BENCHMARK_REPO not set")

# List available problems
problems_dir = Path(repo_path) / "problems"
for difficulty in ["basic", "intermediate", "advanced", "expert"]:
    difficulty_dir = problems_dir / difficulty
    if difficulty_dir.exists():
        problems = list(difficulty_dir.glob("*.yaml"))
        print(f"{difficulty.capitalize()}: {len(problems)} problems")
```

### Integration Methods

#### Method 1: Environment Variable (Recommended)

```python
# ae_framework/config.py
import os
from pathlib import Path

class Req2RunConfig:
    def __init__(self):
        self.repo_path = os.getenv("REQ2RUN_BENCHMARK_REPO")
        if not self.repo_path:
            raise ValueError("REQ2RUN_BENCHMARK_REPO environment variable not set")
        
        self.repo_path = Path(self.repo_path)
        self.problems_dir = self.repo_path / "problems"
        self.schema_path = self.repo_path / "problems" / "schema" / "problem-schema.yaml"
    
    def get_problems(self, difficulty=None, category=None):
        """Get list of problems filtered by difficulty and category"""
        problems = []
        
        difficulties = [difficulty] if difficulty else ["basic", "intermediate", "advanced", "expert"]
        
        for diff in difficulties:
            diff_dir = self.problems_dir / diff
            if diff_dir.exists():
                for problem_file in diff_dir.glob("*.yaml"):
                    # Load and filter by category if specified
                    problems.append(problem_file)
        
        return problems
```

#### Method 2: Git Submodule

```bash
# Add as submodule
git submodule add https://github.com/itdojp/req2run-benchmark.git req2run-benchmark
git submodule update --init --recursive

# Update submodule
git submodule update --remote req2run-benchmark
```

#### Method 3: Python Package (Future)

```bash
# Not yet available, planned for future release
pip install req2run-benchmark
```

### Problem Discovery

#### Discovering Available Problems

```python
import yaml
from pathlib import Path

class ProblemDiscovery:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self.problems_dir = self.repo_path / "problems"
    
    def list_all_problems(self):
        """List all available problems"""
        problems = {}
        for difficulty in ["basic", "intermediate", "advanced", "expert"]:
            diff_dir = self.problems_dir / difficulty
            if diff_dir.exists():
                problems[difficulty] = []
                for problem_file in diff_dir.glob("*.yaml"):
                    with open(problem_file, 'r') as f:
                        problem_data = yaml.safe_load(f)
                        problems[difficulty].append({
                            'id': problem_data.get('id'),
                            'title': problem_data.get('title'),
                            'category': problem_data.get('category'),
                            'file': str(problem_file)
                        })
        return problems
    
    def get_problem_by_id(self, problem_id):
        """Get specific problem by ID"""
        for difficulty in ["basic", "intermediate", "advanced", "expert"]:
            diff_dir = self.problems_dir / difficulty
            if diff_dir.exists():
                problem_file = diff_dir / f"{problem_id}.yaml"
                if problem_file.exists():
                    with open(problem_file, 'r') as f:
                        return yaml.safe_load(f)
        return None
    
    def get_problems_by_category(self, category):
        """Get problems filtered by category"""
        matching_problems = []
        for difficulty in ["basic", "intermediate", "advanced", "expert"]:
            diff_dir = self.problems_dir / difficulty
            if diff_dir.exists():
                for problem_file in diff_dir.glob("*.yaml"):
                    with open(problem_file, 'r') as f:
                        problem_data = yaml.safe_load(f)
                        if problem_data.get('category') == category:
                            matching_problems.append(problem_data)
        return matching_problems
```

### Problem Schema

Problems follow a standardized YAML schema located at `problems/schema/problem-schema.yaml`:

```yaml
# Core fields
id: string           # Unique problem identifier (e.g., "CLI-001")
title: string        # Human-readable title
difficulty: enum     # basic, intermediate, advanced, expert
category: string     # cli_tool, web_api, data_processing, etc.

# Requirements
requirements:
  functional:        # MUST requirements (RFC 2119)
    - id: string
      description: string
      priority: enum # MUST, SHOULD, MAY
  non_functional:    # Performance, security, quality requirements
    - id: string
      description: string
      metric: string

# Test cases
test_cases:
  - id: string
    description: string
    input: any
    expected_output: any
    timeout: integer

# Evaluation criteria
evaluation:
  functional_weight: float
  performance_weight: float
  security_weight: float
  quality_weight: float
```

### Complete Integration Example

```python
# ae_framework/req2run_integration.py
import os
import yaml
import json
from pathlib import Path
from typing import List, Dict, Optional

class Req2RunIntegration:
    def __init__(self):
        # Get repository path from environment
        self.repo_path = os.getenv("REQ2RUN_BENCHMARK_REPO")
        if not self.repo_path:
            # Fallback to relative path if submodule
            if Path("req2run-benchmark").exists():
                self.repo_path = Path("req2run-benchmark")
            else:
                raise ValueError(
                    "Req2Run Benchmark repository not found. "
                    "Please set REQ2RUN_BENCHMARK_REPO environment variable "
                    "or clone the repository."
                )
        
        self.repo_path = Path(self.repo_path)
        self.problems_dir = self.repo_path / "problems"
        
        # Validate repository structure
        if not self.problems_dir.exists():
            raise ValueError(f"Problems directory not found at {self.problems_dir}")
    
    def get_available_difficulties(self) -> List[str]:
        """Get list of available difficulty levels"""
        difficulties = []
        for diff in ["basic", "intermediate", "advanced", "expert"]:
            if (self.problems_dir / diff).exists():
                difficulties.append(diff)
        return difficulties
    
    def get_available_categories(self) -> List[str]:
        """Get list of unique problem categories"""
        categories = set()
        for diff_dir in self.problems_dir.iterdir():
            if diff_dir.is_dir() and diff_dir.name != "schema":
                for problem_file in diff_dir.glob("*.yaml"):
                    with open(problem_file, 'r') as f:
                        data = yaml.safe_load(f)
                        if 'category' in data:
                            categories.add(data['category'])
        return sorted(list(categories))
    
    def load_problem(self, problem_id: str) -> Optional[Dict]:
        """Load a specific problem by ID"""
        for diff_dir in self.problems_dir.iterdir():
            if diff_dir.is_dir() and diff_dir.name != "schema":
                problem_file = diff_dir / f"{problem_id}.yaml"
                if problem_file.exists():
                    with open(problem_file, 'r') as f:
                        return yaml.safe_load(f)
        return None
    
    def list_problems(
        self, 
        difficulty: Optional[str] = None, 
        category: Optional[str] = None
    ) -> List[Dict]:
        """List problems with optional filtering"""
        problems = []
        
        # Determine which difficulties to search
        if difficulty:
            search_dirs = [self.problems_dir / difficulty]
        else:
            search_dirs = [
                self.problems_dir / d 
                for d in ["basic", "intermediate", "advanced", "expert"]
                if (self.problems_dir / d).exists()
            ]
        
        # Search and filter
        for diff_dir in search_dirs:
            for problem_file in diff_dir.glob("*.yaml"):
                with open(problem_file, 'r') as f:
                    data = yaml.safe_load(f)
                    
                    # Apply category filter if specified
                    if category and data.get('category') != category:
                        continue
                    
                    problems.append({
                        'id': data.get('id'),
                        'title': data.get('title'),
                        'difficulty': data.get('difficulty'),
                        'category': data.get('category'),
                        'path': str(problem_file)
                    })
        
        return problems
    
    def validate_problem(self, problem_id: str) -> bool:
        """Validate that a problem meets the schema requirements"""
        problem = self.load_problem(problem_id)
        if not problem:
            return False
        
        # Check required fields
        required_fields = ['id', 'title', 'difficulty', 'category', 'requirements']
        for field in required_fields:
            if field not in problem:
                print(f"Missing required field: {field}")
                return False
        
        # Validate difficulty
        valid_difficulties = ['basic', 'intermediate', 'advanced', 'expert']
        if problem.get('difficulty') not in valid_difficulties:
            print(f"Invalid difficulty: {problem.get('difficulty')}")
            return False
        
        return True
    
    def export_problems_json(self, output_file: str = "problems.json"):
        """Export all problems to JSON format"""
        all_problems = self.list_problems()
        with open(output_file, 'w') as f:
            json.dump(all_problems, f, indent=2)
        return output_file

# Usage example
if __name__ == "__main__":
    # Initialize integration
    req2run = Req2RunIntegration()
    
    # List all basic problems
    basic_problems = req2run.list_problems(difficulty="basic")
    print(f"Found {len(basic_problems)} basic problems")
    
    # Get specific problem
    problem = req2run.load_problem("CLI-001")
    if problem:
        print(f"Loaded: {problem['title']}")
    
    # List CLI tool problems
    cli_problems = req2run.list_problems(category="cli_tool")
    print(f"Found {len(cli_problems)} CLI tool problems")
```

### Troubleshooting

#### Common Issues and Solutions

1. **REQ2RUN_BENCHMARK_REPO not set**
   ```bash
   # Check if environment variable is set
   echo $REQ2RUN_BENCHMARK_REPO
   
   # Set it to the repository path
   export REQ2RUN_BENCHMARK_REPO=/path/to/req2run-benchmark
   ```

2. **Problems directory not found**
   ```bash
   # Verify repository structure
   ls -la $REQ2RUN_BENCHMARK_REPO/problems/
   
   # Should see: basic, intermediate, advanced, expert, schema
   ```

3. **YAML parsing errors**
   ```python
   # Install PyYAML if not available
   pip install pyyaml
   ```

4. **Permission denied errors**
   ```bash
   # Ensure read permissions
   chmod -R +r $REQ2RUN_BENCHMARK_REPO
   ```

### Best Practices

1. **Cache Problem Data**: Load problems once and cache them to avoid repeated file I/O
2. **Validate Early**: Validate problem files when loading to catch issues early
3. **Handle Missing Repository Gracefully**: Provide clear error messages and fallback options
4. **Use Type Hints**: Add type hints for better IDE support and documentation
5. **Log Integration Status**: Log successful integration and any issues for debugging

---

<a id="japanese"></a>
## 日本語

### 概要

このガイドは、AE FrameworkとReq2Run Benchmarkを統合するための包括的な手順を提供します。この統合により、AI/LLM評価パイプラインがReq2Runの標準化されたベンチマーク問題を使用できるようになります。

### クイックスタート

#### 1. リポジトリのクローン

```bash
# req2run-benchmarkリポジトリをクローン
git clone https://github.com/itdojp/req2run-benchmark.git
cd req2run-benchmark
```

#### 2. 環境変数の設定

```bash
# Linux/Mac
export REQ2RUN_BENCHMARK_REPO=$(pwd)
echo "export REQ2RUN_BENCHMARK_REPO=$(pwd)" >> ~/.bashrc

# Windows PowerShell
$env:REQ2RUN_BENCHMARK_REPO = (Get-Location).Path
[Environment]::SetEnvironmentVariable("REQ2RUN_BENCHMARK_REPO", (Get-Location).Path, "User")

# Windows CMD
set REQ2RUN_BENCHMARK_REPO=%cd%
setx REQ2RUN_BENCHMARK_REPO "%cd%"
```

#### 3. インストールの確認

```python
import os
import json
from pathlib import Path

# 環境変数の確認
repo_path = os.getenv("REQ2RUN_BENCHMARK_REPO")
if not repo_path:
    raise ValueError("REQ2RUN_BENCHMARK_REPOが設定されていません")

# 利用可能な問題のリスト
problems_dir = Path(repo_path) / "problems"
for difficulty in ["basic", "intermediate", "advanced", "expert"]:
    difficulty_dir = problems_dir / difficulty
    if difficulty_dir.exists():
        problems = list(difficulty_dir.glob("*.yaml"))
        print(f"{difficulty.capitalize()}: {len(problems)} 問題")
```

### 統合方法

#### 方法1: 環境変数（推奨）

```python
# ae_framework/config.py
import os
from pathlib import Path

class Req2RunConfig:
    def __init__(self):
        self.repo_path = os.getenv("REQ2RUN_BENCHMARK_REPO")
        if not self.repo_path:
            raise ValueError("REQ2RUN_BENCHMARK_REPO環境変数が設定されていません")
        
        self.repo_path = Path(self.repo_path)
        self.problems_dir = self.repo_path / "problems"
        self.schema_path = self.repo_path / "problems" / "schema" / "problem-schema.yaml"
    
    def get_problems(self, difficulty=None, category=None):
        """難易度とカテゴリでフィルタリングされた問題リストを取得"""
        problems = []
        
        difficulties = [difficulty] if difficulty else ["basic", "intermediate", "advanced", "expert"]
        
        for diff in difficulties:
            diff_dir = self.problems_dir / diff
            if diff_dir.exists():
                for problem_file in diff_dir.glob("*.yaml"):
                    # 必要に応じてカテゴリでフィルタリング
                    problems.append(problem_file)
        
        return problems
```

#### 方法2: Gitサブモジュール

```bash
# サブモジュールとして追加
git submodule add https://github.com/itdojp/req2run-benchmark.git req2run-benchmark
git submodule update --init --recursive

# サブモジュールの更新
git submodule update --remote req2run-benchmark
```

#### 方法3: Pythonパッケージ（将来）

```bash
# まだ利用できません。将来のリリースで予定
pip install req2run-benchmark
```

### 問題の検出

#### 利用可能な問題の検出

```python
import yaml
from pathlib import Path

class ProblemDiscovery:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self.problems_dir = self.repo_path / "problems"
    
    def list_all_problems(self):
        """すべての利用可能な問題をリスト"""
        problems = {}
        for difficulty in ["basic", "intermediate", "advanced", "expert"]:
            diff_dir = self.problems_dir / difficulty
            if diff_dir.exists():
                problems[difficulty] = []
                for problem_file in diff_dir.glob("*.yaml"):
                    with open(problem_file, 'r', encoding='utf-8') as f:
                        problem_data = yaml.safe_load(f)
                        problems[difficulty].append({
                            'id': problem_data.get('id'),
                            'title': problem_data.get('title'),
                            'category': problem_data.get('category'),
                            'file': str(problem_file)
                        })
        return problems
    
    def get_problem_by_id(self, problem_id):
        """IDで特定の問題を取得"""
        for difficulty in ["basic", "intermediate", "advanced", "expert"]:
            diff_dir = self.problems_dir / difficulty
            if diff_dir.exists():
                problem_file = diff_dir / f"{problem_id}.yaml"
                if problem_file.exists():
                    with open(problem_file, 'r', encoding='utf-8') as f:
                        return yaml.safe_load(f)
        return None
    
    def get_problems_by_category(self, category):
        """カテゴリでフィルタリングされた問題を取得"""
        matching_problems = []
        for difficulty in ["basic", "intermediate", "advanced", "expert"]:
            diff_dir = self.problems_dir / difficulty
            if diff_dir.exists():
                for problem_file in diff_dir.glob("*.yaml"):
                    with open(problem_file, 'r', encoding='utf-8') as f:
                        problem_data = yaml.safe_load(f)
                        if problem_data.get('category') == category:
                            matching_problems.append(problem_data)
        return matching_problems
```

### 問題スキーマ

問題は`problems/schema/problem-schema.yaml`にある標準化されたYAMLスキーマに従います：

```yaml
# コアフィールド
id: string           # 一意の問題識別子（例：「CLI-001」）
title: string        # 人間が読めるタイトル
difficulty: enum     # basic, intermediate, advanced, expert
category: string     # cli_tool, web_api, data_processing など

# 要件
requirements:
  functional:        # MUST要件（RFC 2119）
    - id: string
      description: string
      priority: enum # MUST, SHOULD, MAY
  non_functional:    # パフォーマンス、セキュリティ、品質要件
    - id: string
      description: string
      metric: string

# テストケース
test_cases:
  - id: string
    description: string
    input: any
    expected_output: any
    timeout: integer

# 評価基準
evaluation:
  functional_weight: float
  performance_weight: float
  security_weight: float
  quality_weight: float
```

### 完全な統合例

```python
# ae_framework/req2run_integration.py
import os
import yaml
import json
from pathlib import Path
from typing import List, Dict, Optional

class Req2RunIntegration:
    def __init__(self):
        # 環境からリポジトリパスを取得
        self.repo_path = os.getenv("REQ2RUN_BENCHMARK_REPO")
        if not self.repo_path:
            # サブモジュールの場合は相対パスにフォールバック
            if Path("req2run-benchmark").exists():
                self.repo_path = Path("req2run-benchmark")
            else:
                raise ValueError(
                    "Req2Run Benchmarkリポジトリが見つかりません。"
                    "REQ2RUN_BENCHMARK_REPO環境変数を設定するか、"
                    "リポジトリをクローンしてください。"
                )
        
        self.repo_path = Path(self.repo_path)
        self.problems_dir = self.repo_path / "problems"
        
        # リポジトリ構造の検証
        if not self.problems_dir.exists():
            raise ValueError(f"問題ディレクトリが{self.problems_dir}に見つかりません")
    
    def get_available_difficulties(self) -> List[str]:
        """利用可能な難易度レベルのリストを取得"""
        difficulties = []
        for diff in ["basic", "intermediate", "advanced", "expert"]:
            if (self.problems_dir / diff).exists():
                difficulties.append(diff)
        return difficulties
    
    def get_available_categories(self) -> List[str]:
        """一意の問題カテゴリのリストを取得"""
        categories = set()
        for diff_dir in self.problems_dir.iterdir():
            if diff_dir.is_dir() and diff_dir.name != "schema":
                for problem_file in diff_dir.glob("*.yaml"):
                    with open(problem_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        if 'category' in data:
                            categories.add(data['category'])
        return sorted(list(categories))
    
    def load_problem(self, problem_id: str) -> Optional[Dict]:
        """IDで特定の問題をロード"""
        for diff_dir in self.problems_dir.iterdir():
            if diff_dir.is_dir() and diff_dir.name != "schema":
                problem_file = diff_dir / f"{problem_id}.yaml"
                if problem_file.exists():
                    with open(problem_file, 'r', encoding='utf-8') as f:
                        return yaml.safe_load(f)
        return None
    
    def list_problems(
        self, 
        difficulty: Optional[str] = None, 
        category: Optional[str] = None
    ) -> List[Dict]:
        """オプションのフィルタリングで問題をリスト"""
        problems = []
        
        # 検索する難易度を決定
        if difficulty:
            search_dirs = [self.problems_dir / difficulty]
        else:
            search_dirs = [
                self.problems_dir / d 
                for d in ["basic", "intermediate", "advanced", "expert"]
                if (self.problems_dir / d).exists()
            ]
        
        # 検索とフィルタリング
        for diff_dir in search_dirs:
            for problem_file in diff_dir.glob("*.yaml"):
                with open(problem_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                    # 指定されている場合はカテゴリフィルタを適用
                    if category and data.get('category') != category:
                        continue
                    
                    problems.append({
                        'id': data.get('id'),
                        'title': data.get('title'),
                        'difficulty': data.get('difficulty'),
                        'category': data.get('category'),
                        'path': str(problem_file)
                    })
        
        return problems
    
    def validate_problem(self, problem_id: str) -> bool:
        """問題がスキーマ要件を満たしていることを検証"""
        problem = self.load_problem(problem_id)
        if not problem:
            return False
        
        # 必須フィールドをチェック
        required_fields = ['id', 'title', 'difficulty', 'category', 'requirements']
        for field in required_fields:
            if field not in problem:
                print(f"必須フィールドが不足: {field}")
                return False
        
        # 難易度を検証
        valid_difficulties = ['basic', 'intermediate', 'advanced', 'expert']
        if problem.get('difficulty') not in valid_difficulties:
            print(f"無効な難易度: {problem.get('difficulty')}")
            return False
        
        return True
    
    def export_problems_json(self, output_file: str = "problems.json"):
        """すべての問題をJSON形式でエクスポート"""
        all_problems = self.list_problems()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_problems, f, indent=2, ensure_ascii=False)
        return output_file

# 使用例
if __name__ == "__main__":
    # 統合の初期化
    req2run = Req2RunIntegration()
    
    # すべての基本問題をリスト
    basic_problems = req2run.list_problems(difficulty="basic")
    print(f"{len(basic_problems)}個の基本問題が見つかりました")
    
    # 特定の問題を取得
    problem = req2run.load_problem("CLI-001")
    if problem:
        print(f"ロード済み: {problem['title']}")
    
    # CLIツール問題をリスト
    cli_problems = req2run.list_problems(category="cli_tool")
    print(f"{len(cli_problems)}個のCLIツール問題が見つかりました")
```

### トラブルシューティング

#### よくある問題と解決策

1. **REQ2RUN_BENCHMARK_REPOが設定されていない**
   ```bash
   # 環境変数が設定されているか確認
   echo $REQ2RUN_BENCHMARK_REPO
   
   # リポジトリパスに設定
   export REQ2RUN_BENCHMARK_REPO=/path/to/req2run-benchmark
   ```

2. **問題ディレクトリが見つからない**
   ```bash
   # リポジトリ構造を確認
   ls -la $REQ2RUN_BENCHMARK_REPO/problems/
   
   # 以下が表示されるはず: basic, intermediate, advanced, expert, schema
   ```

3. **YAML解析エラー**
   ```python
   # PyYAMLがない場合はインストール
   pip install pyyaml
   ```

4. **アクセス拒否エラー**
   ```bash
   # 読み取り権限を確認
   chmod -R +r $REQ2RUN_BENCHMARK_REPO
   ```

### ベストプラクティス

1. **問題データのキャッシュ**: 繰り返しのファイルI/Oを避けるため、問題を一度ロードしてキャッシュ
2. **早期検証**: 問題をロードする際に検証して早期に問題を発見
3. **リポジトリ不在の適切な処理**: 明確なエラーメッセージとフォールバックオプションを提供
4. **型ヒントの使用**: より良いIDEサポートとドキュメントのために型ヒントを追加
5. **統合ステータスのログ**: デバッグのために成功した統合と問題をログに記録