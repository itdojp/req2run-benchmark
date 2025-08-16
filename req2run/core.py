"""
Core components for Req2Run evaluation framework
"""

import yaml
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class Difficulty(Enum):
    """Problem difficulty levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Priority(Enum):
    """Requirement priority levels"""
    MUST = "must"
    SHOULD = "should"
    NICE_TO_HAVE = "nice_to_have"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class Requirement:
    """Functional or non-functional requirement"""
    id: str
    description: str
    priority: Priority
    validated: bool = False
    validation_message: str = ""


@dataclass
class TestCase:
    """Test case definition"""
    id: str
    description: str
    input: Dict[str, Any]
    expected_output: Dict[str, Any]
    status: TestStatus = TestStatus.PENDING
    actual_output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class EvaluationCriteria:
    """Evaluation metric criteria"""
    metric: str
    weight: float
    threshold: float
    measurement: str
    score: float = 0.0
    passed: bool = False


@dataclass
class Problem:
    """Problem definition"""
    problem_id: str
    category: str
    difficulty: Difficulty
    title: str
    description: str
    functional_requirements: List[Requirement]
    non_functional_requirements: List[Dict[str, str]]
    input_specification: Dict[str, Any]
    output_specification: Dict[str, Any]
    test_cases: List[TestCase]
    deployment_requirements: Dict[str, Any]
    evaluation_criteria: List[EvaluationCriteria]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def load(cls, problem_id: str, problems_dir: Path = Path("problems")) -> "Problem":
        """Load problem from YAML file"""
        # Search for problem file in directory structure
        for difficulty_dir in problems_dir.iterdir():
            if difficulty_dir.is_dir():
                for problem_file in difficulty_dir.glob(f"{problem_id}*.yaml"):
                    return cls.from_yaml(problem_file)
        
        raise FileNotFoundError(f"Problem {problem_id} not found in {problems_dir}")
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "Problem":
        """Create Problem instance from YAML file"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Parse functional requirements
        functional_reqs = [
            Requirement(
                id=req['id'],
                description=req['description'],
                priority=Priority(req['priority'])
            )
            for req in data.get('functional_requirements', [])
        ]
        
        # Parse test cases
        test_cases = [
            TestCase(
                id=tc.get('id', f"TC-{i:03d}"),
                description=tc.get('description', ''),
                input=tc.get('input', {}),
                expected_output=tc.get('expected_output', {})
            )
            for i, tc in enumerate(data.get('test_cases', []), 1)
        ]
        
        # Parse evaluation criteria
        criteria = [
            EvaluationCriteria(
                metric=ec['metric'],
                weight=ec['weight'],
                threshold=ec['threshold'],
                measurement=ec.get('measurement', '')
            )
            for ec in data.get('evaluation_criteria', [])
        ]
        
        return cls(
            problem_id=data['problem_id'],
            category=data['category'],
            difficulty=Difficulty(data['difficulty']),
            title=data['title'],
            description=data['description'],
            functional_requirements=functional_reqs,
            non_functional_requirements=data.get('non_functional_requirements', []),
            input_specification=data.get('input_specification', {}),
            output_specification=data.get('output_specification', {}),
            test_cases=test_cases,
            deployment_requirements=data.get('deployment_requirements', {}),
            evaluation_criteria=criteria,
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert problem to dictionary"""
        return {
            'problem_id': self.problem_id,
            'category': self.category,
            'difficulty': self.difficulty.value,
            'title': self.title,
            'description': self.description,
            'functional_requirements': [
                {
                    'id': req.id,
                    'description': req.description,
                    'priority': req.priority.value,
                    'validated': req.validated
                }
                for req in self.functional_requirements
            ],
            'test_cases': [
                {
                    'id': tc.id,
                    'description': tc.description,
                    'status': tc.status.value,
                    'execution_time': tc.execution_time
                }
                for tc in self.test_cases
            ],
            'evaluation_criteria': [
                {
                    'metric': ec.metric,
                    'weight': ec.weight,
                    'threshold': ec.threshold,
                    'score': ec.score,
                    'passed': ec.passed
                }
                for ec in self.evaluation_criteria
            ]
        }


@dataclass
class Result:
    """Evaluation result"""
    problem_id: str
    submission_id: str
    timestamp: datetime
    total_score: float
    status: str  # 'passed', 'failed', 'error'
    execution_time: float
    functional_coverage: float
    test_pass_rate: float
    performance_score: float
    security_score: float
    code_quality_score: float
    test_results: List[TestCase]
    criteria_results: List[EvaluationCriteria]
    logs: List[str]
    artifacts: Dict[str, str]  # paths to generated artifacts
    
    def to_json(self) -> str:
        """Convert result to JSON string"""
        data = {
            'problem_id': self.problem_id,
            'submission_id': self.submission_id,
            'timestamp': self.timestamp.isoformat(),
            'total_score': self.total_score,
            'status': self.status,
            'execution_time': self.execution_time,
            'metrics': {
                'functional_coverage': self.functional_coverage,
                'test_pass_rate': self.test_pass_rate,
                'performance_score': self.performance_score,
                'security_score': self.security_score,
                'code_quality_score': self.code_quality_score
            },
            'test_results': [
                {
                    'id': tc.id,
                    'description': tc.description,
                    'status': tc.status.value,
                    'execution_time': tc.execution_time,
                    'error': tc.error_message
                }
                for tc in self.test_results
            ],
            'criteria_results': [
                {
                    'metric': ec.metric,
                    'score': ec.score,
                    'threshold': ec.threshold,
                    'passed': ec.passed
                }
                for ec in self.criteria_results
            ],
            'artifacts': self.artifacts
        }
        return json.dumps(data, indent=2)
    
    def save(self, output_dir: Path):
        """Save result to file"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON result
        result_file = output_dir / f"{self.submission_id}_result.json"
        with open(result_file, 'w') as f:
            f.write(self.to_json())
        
        # Save logs
        log_file = output_dir / f"{self.submission_id}_logs.txt"
        with open(log_file, 'w') as f:
            f.write('\n'.join(self.logs))
        
        logger.info(f"Results saved to {output_dir}")


class Evaluator:
    """Main evaluation orchestrator"""
    
    def __init__(self, 
                 problem: Problem,
                 environment: str = "docker",
                 timeout: int = 3600,
                 working_dir: Optional[Path] = None):
        self.problem = problem
        self.environment = environment
        self.timeout = timeout
        self.working_dir = working_dir or Path.cwd() / "workdir"
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
    def evaluate(self, 
                 submission_path: Path,
                 submission_id: Optional[str] = None,
                 verbose: bool = False) -> Result:
        """
        Execute full evaluation pipeline
        
        Args:
            submission_path: Path to submission code/artifacts
            submission_id: Unique identifier for this submission
            verbose: Enable verbose logging
            
        Returns:
            Result object with evaluation results
        """
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
        
        submission_id = submission_id or f"{self.problem.problem_id}_{int(time.time())}"
        logger.info(f"Starting evaluation for {submission_id}")
        
        start_time = time.time()
        logs = []
        
        try:
            # Phase 1: Build and Deploy
            logs.append(f"[{datetime.now()}] Phase 1: Build and Deploy")
            deployment_success = self._deploy(submission_path, logs)
            
            if not deployment_success:
                return self._create_failed_result(
                    submission_id, 
                    "Deployment failed",
                    time.time() - start_time,
                    logs
                )
            
            # Phase 2: Functional Testing
            logs.append(f"[{datetime.now()}] Phase 2: Functional Testing")
            test_results = self._run_tests(logs)
            
            # Phase 3: Performance Testing
            logs.append(f"[{datetime.now()}] Phase 3: Performance Testing")
            performance_score = self._run_performance_tests(logs)
            
            # Phase 4: Security Scanning
            logs.append(f"[{datetime.now()}] Phase 4: Security Scanning")
            security_score = self._run_security_scan(logs)
            
            # Phase 5: Code Quality Analysis
            logs.append(f"[{datetime.now()}] Phase 5: Code Quality Analysis")
            code_quality_score = self._analyze_code_quality(submission_path, logs)
            
            # Calculate final scores
            result = self._calculate_final_result(
                submission_id,
                test_results,
                performance_score,
                security_score,
                code_quality_score,
                time.time() - start_time,
                logs
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            return self._create_failed_result(
                submission_id,
                f"Evaluation error: {str(e)}",
                time.time() - start_time,
                logs
            )
        finally:
            # Cleanup
            self._cleanup(logs)
    
    def _deploy(self, submission_path: Path, logs: List[str]) -> bool:
        """Deploy submission in target environment"""
        # Implementation would handle Docker/K8s deployment
        logs.append("Deployment initiated...")
        # Placeholder for actual deployment logic
        return True
    
    def _run_tests(self, logs: List[str]) -> List[TestCase]:
        """Execute functional test cases"""
        test_results = []
        for test_case in self.problem.test_cases:
            logs.append(f"Running test: {test_case.id} - {test_case.description}")
            # Placeholder for actual test execution
            test_case.status = TestStatus.PASSED
            test_case.execution_time = 0.1
            test_results.append(test_case)
        return test_results
    
    def _run_performance_tests(self, logs: List[str]) -> float:
        """Run performance benchmarks"""
        logs.append("Running performance tests...")
        # Placeholder for actual performance testing
        return 0.85
    
    def _run_security_scan(self, logs: List[str]) -> float:
        """Execute security scanning"""
        logs.append("Running security scan...")
        # Placeholder for actual security scanning
        return 1.0
    
    def _analyze_code_quality(self, submission_path: Path, logs: List[str]) -> float:
        """Analyze code quality metrics"""
        logs.append("Analyzing code quality...")
        # Placeholder for actual code quality analysis
        return 0.9
    
    def _calculate_final_result(self, 
                                submission_id: str,
                                test_results: List[TestCase],
                                performance_score: float,
                                security_score: float,
                                code_quality_score: float,
                                execution_time: float,
                                logs: List[str]) -> Result:
        """Calculate final evaluation result"""
        
        # Calculate test pass rate
        passed_tests = sum(1 for tc in test_results if tc.status == TestStatus.PASSED)
        test_pass_rate = passed_tests / len(test_results) if test_results else 0
        
        # Calculate functional coverage
        validated_reqs = sum(1 for req in self.problem.functional_requirements if req.validated)
        functional_coverage = validated_reqs / len(self.problem.functional_requirements)
        
        # Calculate weighted total score
        criteria_results = []
        total_score = 0.0
        
        for criterion in self.problem.evaluation_criteria:
            if "機能" in criterion.metric or "functional" in criterion.metric.lower():
                score = functional_coverage
            elif "テスト" in criterion.metric or "test" in criterion.metric.lower():
                score = test_pass_rate
            elif "性能" in criterion.metric or "performance" in criterion.metric.lower():
                score = performance_score
            elif "セキュリティ" in criterion.metric or "security" in criterion.metric.lower():
                score = security_score
            elif "品質" in criterion.metric or "quality" in criterion.metric.lower():
                score = code_quality_score
            else:
                score = 0.5  # Default score
            
            criterion.score = score
            criterion.passed = score >= criterion.threshold
            total_score += score * criterion.weight
            criteria_results.append(criterion)
        
        # Determine overall status
        status = "passed" if total_score >= 0.7 else "failed"
        
        return Result(
            problem_id=self.problem.problem_id,
            submission_id=submission_id,
            timestamp=datetime.now(),
            total_score=total_score,
            status=status,
            execution_time=execution_time,
            functional_coverage=functional_coverage,
            test_pass_rate=test_pass_rate,
            performance_score=performance_score,
            security_score=security_score,
            code_quality_score=code_quality_score,
            test_results=test_results,
            criteria_results=criteria_results,
            logs=logs,
            artifacts={}
        )
    
    def _create_failed_result(self, 
                             submission_id: str,
                             error_message: str,
                             execution_time: float,
                             logs: List[str]) -> Result:
        """Create a failed result object"""
        logs.append(f"ERROR: {error_message}")
        
        return Result(
            problem_id=self.problem.problem_id,
            submission_id=submission_id,
            timestamp=datetime.now(),
            total_score=0.0,
            status="error",
            execution_time=execution_time,
            functional_coverage=0.0,
            test_pass_rate=0.0,
            performance_score=0.0,
            security_score=0.0,
            code_quality_score=0.0,
            test_results=[],
            criteria_results=[],
            logs=logs,
            artifacts={}
        )
    
    def _cleanup(self, logs: List[str]):
        """Clean up evaluation environment"""
        logs.append("Cleaning up evaluation environment...")
        # Placeholder for actual cleanup logic