# Req2Run API Documentation

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

### Core Module (`req2run.core`)

#### Problem Class

Represents a benchmark problem definition.

```python
class Problem:
    """Problem definition for evaluation"""
    
    @classmethod
    def load(cls, problem_id: str, problems_dir: Path = Path("problems")) -> Problem:
        """
        Load problem from YAML file
        
        Args:
            problem_id: Problem identifier (e.g., "WEB-001")
            problems_dir: Directory containing problem definitions
            
        Returns:
            Problem instance
            
        Raises:
            FileNotFoundError: If problem not found
        """
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> Problem:
        """
        Create Problem instance from YAML file
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            Problem instance
        """
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert problem to dictionary
        
        Returns:
            Dictionary representation
        """
```

#### Evaluator Class

Main evaluation orchestrator.

```python
class Evaluator:
    """Evaluation orchestrator"""
    
    def __init__(self, 
                 problem: Problem,
                 environment: str = "docker",
                 timeout: int = 3600,
                 working_dir: Optional[Path] = None):
        """
        Initialize evaluator
        
        Args:
            problem: Problem to evaluate
            environment: Execution environment ("docker", "kubernetes", "local")
            timeout: Maximum evaluation time in seconds
            working_dir: Working directory for evaluation
        """
    
    def evaluate(self, 
                 submission_path: Path,
                 submission_id: Optional[str] = None,
                 verbose: bool = False) -> Result:
        """
        Execute full evaluation pipeline
        
        Args:
            submission_path: Path to submission code
            submission_id: Unique identifier for submission
            verbose: Enable verbose logging
            
        Returns:
            Result object with evaluation results
        """
```

#### Result Class

Evaluation result container.

```python
class Result:
    """Evaluation result"""
    
    def to_json(self) -> str:
        """
        Convert result to JSON string
        
        Returns:
            JSON representation
        """
    
    def save(self, output_dir: Path):
        """
        Save result to file
        
        Args:
            output_dir: Directory to save results
        """
```

### Runner Module (`req2run.runner`)

#### create_runner Function

Factory function for creating execution runners.

```python
def create_runner(environment: str = "docker", 
                  config: Dict[str, Any] = None) -> Runner:
    """
    Create appropriate runner for environment
    
    Args:
        environment: Execution environment ("docker", "kubernetes", "local")
        config: Runner-specific configuration
        
    Returns:
        Runner instance
        
    Raises:
        ValueError: If unknown environment
    """
```

#### Runner Classes

Base class and implementations for different environments.

```python
class Runner(ABC):
    """Abstract base class for execution runners"""
    
    @abstractmethod
    def build(self, submission_path: Path, 
              dockerfile_path: Optional[Path] = None) -> BuildResult:
        """Build submission into executable artifact"""
    
    @abstractmethod
    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        """Deploy built artifact"""
    
    @abstractmethod
    def execute(self, command: str, timeout: int = 60) -> ExecutionResult:
        """Execute command in deployed environment"""
    
    @abstractmethod
    def cleanup(self):
        """Clean up all created resources"""

class DockerRunner(Runner):
    """Docker-based execution runner"""
    
class KubernetesRunner(Runner):
    """Kubernetes-based execution runner"""
    
class LocalRunner(Runner):
    """Local process-based execution runner"""
```

### Metrics Module (`req2run.metrics`)

#### MetricsCalculator Class

Calculate and aggregate evaluation metrics.

```python
class MetricsCalculator:
    """Metrics calculation and aggregation"""
    
    def calculate_functional_coverage(self, 
                                     requirements: List[Any],
                                     test_results: List[Any]) -> float:
        """
        Calculate functional requirements coverage
        
        Returns:
            Coverage percentage (0.0 to 1.0)
        """
    
    def calculate_performance_metrics(self, 
                                     benchmark_results: Dict[str, Any]) -> PerformanceMetrics:
        """
        Calculate performance metrics from benchmark results
        
        Returns:
            PerformanceMetrics object
        """
    
    def calculate_security_score(self, 
                                scan_results: Dict[str, Any]) -> SecurityMetrics:
        """
        Calculate security score from scan results
        
        Returns:
            SecurityMetrics object
        """
    
    def calculate_code_quality(self, 
                              analysis_results: Dict[str, Any]) -> QualityMetrics:
        """
        Calculate code quality metrics
        
        Returns:
            QualityMetrics object
        """
    
    def aggregate_scores(self, 
                        metrics: Dict[str, float],
                        weights: Dict[str, float]) -> float:
        """
        Calculate weighted aggregate score
        
        Returns:
            Weighted average score (0.0 to 1.0)
        """
```

### Reporter Module (`req2run.reporter`)

#### Reporter Class

Generate evaluation reports in various formats.

```python
class Reporter:
    """Report generation"""
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize reporter
        
        Args:
            template_dir: Directory containing report templates
        """
    
    def generate_html_report(self, 
                           results: List[Dict[str, Any]], 
                           output_path: str) -> None:
        """Generate HTML report"""
    
    def generate_markdown_report(self, 
                                results: List[Dict[str, Any]], 
                                output_path: str) -> None:
        """Generate Markdown report"""
    
    def generate_json_report(self, 
                           results: List[Dict[str, Any]], 
                           output_path: str) -> None:
        """Generate JSON report"""
    
    def generate_leaderboard(self, 
                           results: List[Dict[str, Any]]) -> str:
        """Generate leaderboard markdown"""
```

### CLI Module (`req2run.cli`)

Command-line interface functions.

```python
# Evaluate single problem
python -m req2run evaluate --problem WEB-001 --submission ./solution

# Batch evaluation
python -m req2run batch-evaluate --difficulty intermediate --submission ./solution

# List problems
python -m req2run list --difficulty advanced --format json

# Generate report
python -m req2run report --results ./results --format html --output report.html

# Validate problem definition
python -m req2run validate --problem ./problems/TEST-001.yaml
```

---

<a id="japanese"></a>
## 日本語

### コアモジュール (`req2run.core`)

#### Problem クラス

ベンチマーク問題定義を表します。

```python
class Problem:
    """評価用問題定義"""
    
    @classmethod
    def load(cls, problem_id: str, problems_dir: Path = Path("problems")) -> Problem:
        """
        YAMLファイルから問題をロード
        
        引数:
            problem_id: 問題識別子（例："WEB-001"）
            problems_dir: 問題定義を含むディレクトリ
            
        戻り値:
            Problemインスタンス
            
        例外:
            FileNotFoundError: 問題が見つからない場合
        """
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> Problem:
        """
        YAMLファイルからProblemインスタンスを作成
        
        引数:
            yaml_path: YAMLファイルへのパス
            
        戻り値:
            Problemインスタンス
        """
    
    def to_dict(self) -> Dict[str, Any]:
        """
        問題を辞書に変換
        
        戻り値:
            辞書表現
        """
```

#### Evaluator クラス

メイン評価オーケストレーター。

```python
class Evaluator:
    """評価オーケストレーター"""
    
    def __init__(self, 
                 problem: Problem,
                 environment: str = "docker",
                 timeout: int = 3600,
                 working_dir: Optional[Path] = None):
        """
        評価器を初期化
        
        引数:
            problem: 評価する問題
            environment: 実行環境（"docker"、"kubernetes"、"local"）
            timeout: 最大評価時間（秒）
            working_dir: 評価用作業ディレクトリ
        """
    
    def evaluate(self, 
                 submission_path: Path,
                 submission_id: Optional[str] = None,
                 verbose: bool = False) -> Result:
        """
        完全な評価パイプラインを実行
        
        引数:
            submission_path: 提出コードへのパス
            submission_id: 提出物の一意識別子
            verbose: 詳細ログを有効化
            
        戻り値:
            評価結果を含むResultオブジェクト
        """
```

#### Result クラス

評価結果コンテナ。

```python
class Result:
    """評価結果"""
    
    def to_json(self) -> str:
        """
        結果をJSON文字列に変換
        
        戻り値:
            JSON表現
        """
    
    def save(self, output_dir: Path):
        """
        結果をファイルに保存
        
        引数:
            output_dir: 結果を保存するディレクトリ
        """
```

### ランナーモジュール (`req2run.runner`)

#### create_runner 関数

実行ランナーを作成するファクトリ関数。

```python
def create_runner(environment: str = "docker", 
                  config: Dict[str, Any] = None) -> Runner:
    """
    環境に適したランナーを作成
    
    引数:
        environment: 実行環境（"docker"、"kubernetes"、"local"）
        config: ランナー固有の設定
        
    戻り値:
        Runnerインスタンス
        
    例外:
        ValueError: 未知の環境の場合
    """
```

#### Runner クラス

異なる環境用の基底クラスと実装。

```python
class Runner(ABC):
    """実行ランナーの抽象基底クラス"""
    
    @abstractmethod
    def build(self, submission_path: Path, 
              dockerfile_path: Optional[Path] = None) -> BuildResult:
        """提出物を実行可能アーティファクトにビルド"""
    
    @abstractmethod
    def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        """ビルドされたアーティファクトをデプロイ"""
    
    @abstractmethod
    def execute(self, command: str, timeout: int = 60) -> ExecutionResult:
        """デプロイされた環境でコマンドを実行"""
    
    @abstractmethod
    def cleanup(self):
        """作成されたすべてのリソースをクリーンアップ"""

class DockerRunner(Runner):
    """Dockerベースの実行ランナー"""
    
class KubernetesRunner(Runner):
    """Kubernetesベースの実行ランナー"""
    
class LocalRunner(Runner):
    """ローカルプロセスベースの実行ランナー"""
```

### メトリクスモジュール (`req2run.metrics`)

#### MetricsCalculator クラス

評価メトリクスを計算・集計。

```python
class MetricsCalculator:
    """メトリクス計算と集計"""
    
    def calculate_functional_coverage(self, 
                                     requirements: List[Any],
                                     test_results: List[Any]) -> float:
        """
        機能要件カバレッジを計算
        
        戻り値:
            カバレッジ率（0.0〜1.0）
        """
    
    def calculate_performance_metrics(self, 
                                     benchmark_results: Dict[str, Any]) -> PerformanceMetrics:
        """
        ベンチマーク結果からパフォーマンスメトリクスを計算
        
        戻り値:
            PerformanceMetricsオブジェクト
        """
    
    def calculate_security_score(self, 
                                scan_results: Dict[str, Any]) -> SecurityMetrics:
        """
        スキャン結果からセキュリティスコアを計算
        
        戻り値:
            SecurityMetricsオブジェクト
        """
    
    def calculate_code_quality(self, 
                              analysis_results: Dict[str, Any]) -> QualityMetrics:
        """
        コード品質メトリクスを計算
        
        戻り値:
            QualityMetricsオブジェクト
        """
    
    def aggregate_scores(self, 
                        metrics: Dict[str, float],
                        weights: Dict[str, float]) -> float:
        """
        重み付き集計スコアを計算
        
        戻り値:
            重み付き平均スコア（0.0〜1.0）
        """
```

### レポーターモジュール (`req2run.reporter`)

#### Reporter クラス

様々な形式で評価レポートを生成。

```python
class Reporter:
    """レポート生成"""
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        レポーターを初期化
        
        引数:
            template_dir: レポートテンプレートを含むディレクトリ
        """
    
    def generate_html_report(self, 
                           results: List[Dict[str, Any]], 
                           output_path: str) -> None:
        """HTMLレポートを生成"""
    
    def generate_markdown_report(self, 
                                results: List[Dict[str, Any]], 
                                output_path: str) -> None:
        """Markdownレポートを生成"""
    
    def generate_json_report(self, 
                           results: List[Dict[str, Any]], 
                           output_path: str) -> None:
        """JSONレポートを生成"""
    
    def generate_leaderboard(self, 
                           results: List[Dict[str, Any]]) -> str:
        """リーダーボードmarkdownを生成"""
```

### CLIモジュール (`req2run.cli`)

コマンドラインインターフェース機能。

```python
# 単一問題を評価
python -m req2run evaluate --problem WEB-001 --submission ./solution

# バッチ評価
python -m req2run batch-evaluate --difficulty intermediate --submission ./solution

# 問題一覧
python -m req2run list --difficulty advanced --format json

# レポート生成
python -m req2run report --results ./results --format html --output report.html

# 問題定義の検証
python -m req2run validate --problem ./problems/TEST-001.yaml
```