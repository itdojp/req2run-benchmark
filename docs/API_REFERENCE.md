# Req2Run API Reference

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

### Overview

The Req2Run API provides programmatic access to benchmark problems, validation, and evaluation capabilities. This document describes the available APIs and their usage.

### Python API

#### Installation

```bash
# Clone the repository
git clone https://github.com/itdojp/req2run-benchmark.git

# Install dependencies
pip install pyyaml
```

#### Core Classes

##### `Req2RunAPI`

Main API class for interacting with the benchmark.

```python
from req2run.api import Req2RunAPI

# Initialize API
api = Req2RunAPI()

# or with custom repository path
api = Req2RunAPI(repo_path="/path/to/req2run-benchmark")
```

##### Methods

###### `list_problems(difficulty=None, category=None, format='dict')`

List available problems with optional filtering.

**Parameters:**
- `difficulty` (str, optional): Filter by difficulty level ('basic', 'intermediate', 'advanced', 'expert')
- `category` (str, optional): Filter by category ('cli_tool', 'web_api', 'data_processing', etc.)
- `format` (str, optional): Output format ('dict', 'json', 'yaml')

**Returns:**
- List of problem dictionaries or formatted string

**Example:**
```python
# List all basic problems
basic_problems = api.list_problems(difficulty='basic')

# List all web API problems
web_problems = api.list_problems(category='web_api')

# Get as JSON
problems_json = api.list_problems(format='json')
```

###### `get_problem(problem_id)`

Retrieve a specific problem by ID.

**Parameters:**
- `problem_id` (str): Problem identifier (e.g., 'CLI-001')

**Returns:**
- Problem dictionary or None if not found

**Example:**
```python
problem = api.get_problem('CLI-001')
if problem:
    print(f"Title: {problem['title']}")
    print(f"Difficulty: {problem['difficulty']}")
```

###### `validate_problem(problem_path)`

Validate a problem file against the schema.

**Parameters:**
- `problem_path` (str): Path to problem YAML file

**Returns:**
- Tuple of (is_valid: bool, errors: list)

**Example:**
```python
is_valid, errors = api.validate_problem('problems/basic/CLI-001.yaml')
if not is_valid:
    for error in errors:
        print(f"Validation error: {error}")
```

###### `get_schema()`

Get the problem schema definition.

**Returns:**
- Schema dictionary

**Example:**
```python
schema = api.get_schema()
print(f"Required fields: {schema['required']}")
```

###### `get_categories()`

Get list of all available problem categories.

**Returns:**
- List of category strings

**Example:**
```python
categories = api.get_categories()
# ['cli_tool', 'web_api', 'data_processing', ...]
```

###### `get_difficulties()`

Get list of available difficulty levels.

**Returns:**
- List of difficulty strings

**Example:**
```python
difficulties = api.get_difficulties()
# ['basic', 'intermediate', 'advanced', 'expert']
```

### Command Line Interface

#### Basic Commands

##### List Problems

```bash
# List all problems
req2run list

# List by difficulty
req2run list --difficulty basic

# List by category
req2run list --category web_api

# Output as JSON
req2run list --format json > problems.json

# Output as YAML
req2run list --format yaml
```

##### Describe Problem

```bash
# Get problem details
req2run describe CLI-001

# Output as JSON
req2run describe CLI-001 --format json

# Show only requirements
req2run describe CLI-001 --section requirements

# Show only test cases
req2run describe CLI-001 --section test_cases
```

##### Validate Problem

```bash
# Validate a problem file
req2run validate problems/basic/CLI-001.yaml

# Validate all problems in a directory
req2run validate problems/basic/

# Strict validation (includes optional fields)
req2run validate problems/basic/CLI-001.yaml --strict
```

##### Export Problems

```bash
# Export all problems to JSON
req2run export --format json --output problems.json

# Export to CSV
req2run export --format csv --output problems.csv

# Export specific difficulty
req2run export --difficulty intermediate --format json
```

### REST API (Future)

*Note: REST API is planned for future release*

#### Endpoints

##### `GET /api/problems`

List all problems.

**Query Parameters:**
- `difficulty`: Filter by difficulty
- `category`: Filter by category
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)

**Response:**
```json
{
  "problems": [
    {
      "id": "CLI-001",
      "title": "File Processing CLI Tool",
      "difficulty": "basic",
      "category": "cli_tool"
    }
  ],
  "total": 35,
  "page": 1,
  "limit": 20
}
```

##### `GET /api/problems/{problem_id}`

Get specific problem details.

**Response:**
```json
{
  "id": "CLI-001",
  "title": "File Processing CLI Tool",
  "difficulty": "basic",
  "category": "cli_tool",
  "requirements": {
    "functional": [...],
    "non_functional": [...]
  },
  "test_cases": [...]
}
```

##### `POST /api/validate`

Validate a problem definition.

**Request Body:**
```json
{
  "problem": {
    "id": "NEW-001",
    "title": "New Problem",
    "difficulty": "basic",
    "category": "cli_tool",
    "requirements": {...}
  }
}
```

**Response:**
```json
{
  "valid": true,
  "errors": []
}
```

### Integration Examples

#### Example 1: Problem Discovery Service

```python
class ProblemDiscoveryService:
    def __init__(self):
        self.api = Req2RunAPI()
        self._cache = {}
    
    def discover_problems_for_level(self, user_level):
        """Discover appropriate problems based on user level"""
        difficulty_map = {
            'beginner': 'basic',
            'intermediate': 'intermediate',
            'advanced': 'advanced',
            'expert': 'expert'
        }
        
        difficulty = difficulty_map.get(user_level, 'basic')
        
        # Check cache
        cache_key = f"problems_{difficulty}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Fetch from API
        problems = self.api.list_problems(difficulty=difficulty)
        self._cache[cache_key] = problems
        
        return problems
    
    def get_random_problem(self, category=None):
        """Get a random problem, optionally filtered by category"""
        import random
        
        problems = self.api.list_problems(category=category)
        if problems:
            return random.choice(problems)
        return None
```

#### Example 2: Problem Validator

```python
class ProblemValidator:
    def __init__(self):
        self.api = Req2RunAPI()
        self.schema = self.api.get_schema()
    
    def validate_batch(self, problem_files):
        """Validate multiple problem files"""
        results = []
        for file in problem_files:
            is_valid, errors = self.api.validate_problem(file)
            results.append({
                'file': file,
                'valid': is_valid,
                'errors': errors
            })
        return results
    
    def validate_requirements(self, problem):
        """Validate that requirements follow RFC 2119"""
        errors = []
        rfc_keywords = ['MUST', 'SHOULD', 'MAY', 'SHALL', 'REQUIRED', 'OPTIONAL']
        
        for req in problem.get('requirements', {}).get('functional', []):
            priority = req.get('priority')
            if priority not in rfc_keywords:
                errors.append(f"Invalid priority: {priority}")
        
        return len(errors) == 0, errors
```

#### Example 3: Problem Exporter

```python
class ProblemExporter:
    def __init__(self):
        self.api = Req2RunAPI()
    
    def export_to_markdown(self, output_dir):
        """Export all problems to Markdown format"""
        from pathlib import Path
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        for difficulty in self.api.get_difficulties():
            problems = self.api.list_problems(difficulty=difficulty)
            
            for problem_summary in problems:
                problem = self.api.get_problem(problem_summary['id'])
                
                # Create Markdown file
                md_file = output_dir / f"{problem['id']}.md"
                with open(md_file, 'w') as f:
                    f.write(f"# {problem['title']}\n\n")
                    f.write(f"**Difficulty:** {problem['difficulty']}\n")
                    f.write(f"**Category:** {problem['category']}\n\n")
                    
                    f.write("## Requirements\n\n")
                    for req in problem.get('requirements', {}).get('functional', []):
                        f.write(f"- {req['description']}\n")
    
    def export_to_database(self, db_connection):
        """Export problems to database"""
        problems = self.api.list_problems()
        
        cursor = db_connection.cursor()
        for problem_summary in problems:
            problem = self.api.get_problem(problem_summary['id'])
            
            cursor.execute("""
                INSERT INTO problems (id, title, difficulty, category, data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                problem['id'],
                problem['title'],
                problem['difficulty'],
                problem['category'],
                json.dumps(problem)
            ))
        
        db_connection.commit()
```

### Error Handling

All API methods may raise the following exceptions:

- `FileNotFoundError`: Repository or problem file not found
- `ValueError`: Invalid parameters or configuration
- `yaml.YAMLError`: Problem file parsing error
- `PermissionError`: Insufficient permissions to read files

Example error handling:

```python
try:
    problem = api.get_problem('INVALID-999')
    if problem is None:
        print("Problem not found")
except FileNotFoundError:
    print("Repository not configured correctly")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

<a id="japanese"></a>
## 日本語

### 概要

Req2Run APIは、ベンチマーク問題、検証、評価機能へのプログラマティックアクセスを提供します。このドキュメントでは、利用可能なAPIとその使用方法について説明します。

### Python API

#### インストール

```bash
# リポジトリをクローン
git clone https://github.com/itdojp/req2run-benchmark.git

# 依存関係をインストール
pip install pyyaml
```

#### コアクラス

##### `Req2RunAPI`

ベンチマークと対話するためのメインAPIクラス。

```python
from req2run.api import Req2RunAPI

# APIを初期化
api = Req2RunAPI()

# またはカスタムリポジトリパスで
api = Req2RunAPI(repo_path="/path/to/req2run-benchmark")
```

##### メソッド

###### `list_problems(difficulty=None, category=None, format='dict')`

オプションのフィルタリングで利用可能な問題をリスト。

**パラメータ:**
- `difficulty` (str, optional): 難易度レベルでフィルタ ('basic', 'intermediate', 'advanced', 'expert')
- `category` (str, optional): カテゴリでフィルタ ('cli_tool', 'web_api', 'data_processing' など)
- `format` (str, optional): 出力形式 ('dict', 'json', 'yaml')

**戻り値:**
- 問題辞書のリストまたはフォーマットされた文字列

**例:**
```python
# すべての基本問題をリスト
basic_problems = api.list_problems(difficulty='basic')

# すべてのWeb API問題をリスト
web_problems = api.list_problems(category='web_api')

# JSONとして取得
problems_json = api.list_problems(format='json')
```

###### `get_problem(problem_id)`

IDで特定の問題を取得。

**パラメータ:**
- `problem_id` (str): 問題識別子（例：'CLI-001'）

**戻り値:**
- 問題辞書、見つからない場合はNone

**例:**
```python
problem = api.get_problem('CLI-001')
if problem:
    print(f"タイトル: {problem['title']}")
    print(f"難易度: {problem['difficulty']}")
```

###### `validate_problem(problem_path)`

スキーマに対して問題ファイルを検証。

**パラメータ:**
- `problem_path` (str): 問題YAMLファイルへのパス

**戻り値:**
- タプル (is_valid: bool, errors: list)

**例:**
```python
is_valid, errors = api.validate_problem('problems/basic/CLI-001.yaml')
if not is_valid:
    for error in errors:
        print(f"検証エラー: {error}")
```

###### `get_schema()`

問題スキーマ定義を取得。

**戻り値:**
- スキーマ辞書

**例:**
```python
schema = api.get_schema()
print(f"必須フィールド: {schema['required']}")
```

###### `get_categories()`

利用可能なすべての問題カテゴリのリストを取得。

**戻り値:**
- カテゴリ文字列のリスト

**例:**
```python
categories = api.get_categories()
# ['cli_tool', 'web_api', 'data_processing', ...]
```

###### `get_difficulties()`

利用可能な難易度レベルのリストを取得。

**戻り値:**
- 難易度文字列のリスト

**例:**
```python
difficulties = api.get_difficulties()
# ['basic', 'intermediate', 'advanced', 'expert']
```

### コマンドラインインターフェース

#### 基本コマンド

##### 問題のリスト

```bash
# すべての問題をリスト
req2run list

# 難易度でリスト
req2run list --difficulty basic

# カテゴリでリスト
req2run list --category web_api

# JSONとして出力
req2run list --format json > problems.json

# YAMLとして出力
req2run list --format yaml
```

##### 問題の説明

```bash
# 問題の詳細を取得
req2run describe CLI-001

# JSONとして出力
req2run describe CLI-001 --format json

# 要件のみ表示
req2run describe CLI-001 --section requirements

# テストケースのみ表示
req2run describe CLI-001 --section test_cases
```

##### 問題の検証

```bash
# 問題ファイルを検証
req2run validate problems/basic/CLI-001.yaml

# ディレクトリ内のすべての問題を検証
req2run validate problems/basic/

# 厳密な検証（オプションフィールドを含む）
req2run validate problems/basic/CLI-001.yaml --strict
```

##### 問題のエクスポート

```bash
# すべての問題をJSONにエクスポート
req2run export --format json --output problems.json

# CSVにエクスポート
req2run export --format csv --output problems.csv

# 特定の難易度をエクスポート
req2run export --difficulty intermediate --format json
```

### REST API（将来）

*注：REST APIは将来のリリースで予定されています*

#### エンドポイント

##### `GET /api/problems`

すべての問題をリスト。

**クエリパラメータ:**
- `difficulty`: 難易度でフィルタ
- `category`: カテゴリでフィルタ
- `page`: ページ番号（デフォルト：1）
- `limit`: ページあたりのアイテム数（デフォルト：20）

**レスポンス:**
```json
{
  "problems": [
    {
      "id": "CLI-001",
      "title": "ファイル処理CLIツール",
      "difficulty": "basic",
      "category": "cli_tool"
    }
  ],
  "total": 35,
  "page": 1,
  "limit": 20
}
```

##### `GET /api/problems/{problem_id}`

特定の問題の詳細を取得。

**レスポンス:**
```json
{
  "id": "CLI-001",
  "title": "ファイル処理CLIツール",
  "difficulty": "basic",
  "category": "cli_tool",
  "requirements": {
    "functional": [...],
    "non_functional": [...]
  },
  "test_cases": [...]
}
```

##### `POST /api/validate`

問題定義を検証。

**リクエストボディ:**
```json
{
  "problem": {
    "id": "NEW-001",
    "title": "新しい問題",
    "difficulty": "basic",
    "category": "cli_tool",
    "requirements": {...}
  }
}
```

**レスポンス:**
```json
{
  "valid": true,
  "errors": []
}
```

### 統合例

#### 例1：問題検出サービス

```python
class ProblemDiscoveryService:
    def __init__(self):
        self.api = Req2RunAPI()
        self._cache = {}
    
    def discover_problems_for_level(self, user_level):
        """ユーザーレベルに基づいて適切な問題を検出"""
        difficulty_map = {
            'beginner': 'basic',
            'intermediate': 'intermediate',
            'advanced': 'advanced',
            'expert': 'expert'
        }
        
        difficulty = difficulty_map.get(user_level, 'basic')
        
        # キャッシュをチェック
        cache_key = f"problems_{difficulty}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # APIから取得
        problems = self.api.list_problems(difficulty=difficulty)
        self._cache[cache_key] = problems
        
        return problems
    
    def get_random_problem(self, category=None):
        """ランダムな問題を取得、オプションでカテゴリでフィルタ"""
        import random
        
        problems = self.api.list_problems(category=category)
        if problems:
            return random.choice(problems)
        return None
```

#### 例2：問題検証ツール

```python
class ProblemValidator:
    def __init__(self):
        self.api = Req2RunAPI()
        self.schema = self.api.get_schema()
    
    def validate_batch(self, problem_files):
        """複数の問題ファイルを検証"""
        results = []
        for file in problem_files:
            is_valid, errors = self.api.validate_problem(file)
            results.append({
                'file': file,
                'valid': is_valid,
                'errors': errors
            })
        return results
    
    def validate_requirements(self, problem):
        """要件がRFC 2119に従っていることを検証"""
        errors = []
        rfc_keywords = ['MUST', 'SHOULD', 'MAY', 'SHALL', 'REQUIRED', 'OPTIONAL']
        
        for req in problem.get('requirements', {}).get('functional', []):
            priority = req.get('priority')
            if priority not in rfc_keywords:
                errors.append(f"無効な優先度: {priority}")
        
        return len(errors) == 0, errors
```

#### 例3：問題エクスポーター

```python
class ProblemExporter:
    def __init__(self):
        self.api = Req2RunAPI()
    
    def export_to_markdown(self, output_dir):
        """すべての問題をMarkdown形式でエクスポート"""
        from pathlib import Path
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        for difficulty in self.api.get_difficulties():
            problems = self.api.list_problems(difficulty=difficulty)
            
            for problem_summary in problems:
                problem = self.api.get_problem(problem_summary['id'])
                
                # Markdownファイルを作成
                md_file = output_dir / f"{problem['id']}.md"
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {problem['title']}\n\n")
                    f.write(f"**難易度:** {problem['difficulty']}\n")
                    f.write(f"**カテゴリ:** {problem['category']}\n\n")
                    
                    f.write("## 要件\n\n")
                    for req in problem.get('requirements', {}).get('functional', []):
                        f.write(f"- {req['description']}\n")
    
    def export_to_database(self, db_connection):
        """問題をデータベースにエクスポート"""
        problems = self.api.list_problems()
        
        cursor = db_connection.cursor()
        for problem_summary in problems:
            problem = self.api.get_problem(problem_summary['id'])
            
            cursor.execute("""
                INSERT INTO problems (id, title, difficulty, category, data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                problem['id'],
                problem['title'],
                problem['difficulty'],
                problem['category'],
                json.dumps(problem)
            ))
        
        db_connection.commit()
```

### エラーハンドリング

すべてのAPIメソッドは以下の例外を発生させる可能性があります：

- `FileNotFoundError`: リポジトリまたは問題ファイルが見つからない
- `ValueError`: 無効なパラメータまたは設定
- `yaml.YAMLError`: 問題ファイルの解析エラー
- `PermissionError`: ファイルを読み取るための権限が不足

エラーハンドリングの例：

```python
try:
    problem = api.get_problem('INVALID-999')
    if problem is None:
        print("問題が見つかりません")
except FileNotFoundError:
    print("リポジトリが正しく設定されていません")
except Exception as e:
    print(f"予期しないエラー: {e}")
```