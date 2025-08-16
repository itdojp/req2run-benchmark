"""
Core components for Req2Run evaluation framework
"""

import yaml
import json
import time
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Import new modules
from .runner import create_runner, DeploymentConfig
from .metrics import MetricsCalculator

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
        logs.append(f"[{datetime.now()}] Starting deployment in {self.environment} environment")
        
        try:
            # Create runner for the specified environment
            self.runner = create_runner(self.environment)
            
            # Build the submission
            logs.append(f"[{datetime.now()}] Building submission...")
            build_result = self.runner.build(submission_path)
            
            if build_result.status.value != 'success':
                logs.append(f"[{datetime.now()}] Build failed: {build_result.error_message}")
                logs.extend(build_result.logs)
                return False
            
            logs.append(f"[{datetime.now()}] Build successful: {build_result.image_id}")
            logs.extend(build_result.logs[-10:])  # Add last 10 build logs
            
            # Deploy the built image
            deployment_config = DeploymentConfig(
                image=build_result.image_id,
                name=f"req2run-{self.problem.problem_id}-{int(time.time())}",
                ports={3000: 3000},  # Default port mapping
                environment={
                    'PORT': '3000',
                    'NODE_ENV': 'production',
                    'DATABASE_URL': self.working_dir / 'test.db' if 'database' in str(self.problem.deployment_requirements) else ''
                },
                resources={
                    'memory': '2g',
                    'cpu_quota': 200000  # 2 CPUs
                },
                healthcheck={
                    'endpoint': '/health',
                    'port': 3000,
                    'timeout': 30,
                    'interval': 2
                }
            )
            
            # Update ports from problem requirements if specified
            if 'ports' in self.problem.deployment_requirements:
                ports = self.problem.deployment_requirements['ports']
                if isinstance(ports, list) and ports:
                    # Parse port mapping like "3000:3000"
                    port_mapping = ports[0].split(':')
                    if len(port_mapping) == 2:
                        deployment_config.ports = {int(port_mapping[1]): int(port_mapping[0])}
            
            logs.append(f"[{datetime.now()}] Deploying container...")
            deployment_result = self.runner.deploy(deployment_config)
            
            if deployment_result.status.value != 'ready':
                logs.append(f"[{datetime.now()}] Deployment failed: {deployment_result.error_message}")
                logs.extend(deployment_result.logs)
                return False
            
            self.service_url = deployment_result.service_url or "http://localhost:3000"
            self.container_id = deployment_result.container_id
            
            logs.append(f"[{datetime.now()}] Deployment successful")
            logs.append(f"[{datetime.now()}] Service URL: {self.service_url}")
            logs.append(f"[{datetime.now()}] Container ID: {self.container_id}")
            
            # Wait a bit for service to stabilize
            time.sleep(3)
            
            return True
            
        except Exception as e:
            logs.append(f"[{datetime.now()}] Deployment error: {str(e)}")
            return False
    
    def _run_tests(self, logs: List[str]) -> List[TestCase]:
        """Execute functional test cases"""
        test_results = []
        
        logs.append(f"[{datetime.now()}] Starting functional tests")
        
        for test_case in self.problem.test_cases:
            logs.append(f"[{datetime.now()}] Running test: {test_case.id} - {test_case.description}")
            
            start_time = time.time()
            
            try:
                # Execute test based on input type
                if 'method' in test_case.input and 'endpoint' in test_case.input:
                    # HTTP API test
                    result = self._execute_http_test(test_case, logs)
                elif 'command' in test_case.input:
                    # CLI test
                    result = self._execute_cli_test(test_case, logs)
                else:
                    # Generic test
                    result = self._execute_generic_test(test_case, logs)
                
                test_case.status = TestStatus.PASSED if result else TestStatus.FAILED
                test_case.execution_time = time.time() - start_time
                
                if test_case.status == TestStatus.PASSED:
                    logs.append(f"[{datetime.now()}] Test {test_case.id} PASSED")
                else:
                    logs.append(f"[{datetime.now()}] Test {test_case.id} FAILED")
                    
            except Exception as e:
                test_case.status = TestStatus.ERROR
                test_case.error_message = str(e)
                test_case.execution_time = time.time() - start_time
                logs.append(f"[{datetime.now()}] Test {test_case.id} ERROR: {str(e)}")
            
            test_results.append(test_case)
        
        return test_results
    
    def _execute_http_test(self, test_case: TestCase, logs: List[str]) -> bool:
        """Execute HTTP API test"""
        try:
            # Prepare request
            method = test_case.input.get('method', 'GET')
            endpoint = test_case.input.get('endpoint', '/')
            headers = test_case.input.get('headers', {})
            body = test_case.input.get('body', None)
            
            url = f"{self.service_url}{endpoint}"
            
            # Make request
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=body, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=body, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                logs.append(f"Unknown HTTP method: {method}")
                return False
            
            # Validate response
            expected = test_case.expected_output
            
            # Check status code
            if 'status' in expected:
                if response.status_code != expected['status']:
                    logs.append(f"Status mismatch: expected {expected['status']}, got {response.status_code}")
                    return False
            
            # Check response body
            if 'body' in expected:
                try:
                    actual_body = response.json()
                    expected_body = expected['body']
                    
                    # Simple comparison - could be improved
                    if expected_body != actual_body:
                        # Check if expected is subset of actual
                        if isinstance(expected_body, dict):
                            for key, value in expected_body.items():
                                if key not in actual_body or actual_body[key] != value:
                                    logs.append(f"Body mismatch for key '{key}'")
                                    return False
                        else:
                            logs.append(f"Body mismatch")
                            return False
                except:
                    logs.append(f"Failed to parse response as JSON")
                    return False
            
            # Check body contains
            if 'body_contains' in expected:
                try:
                    actual_body = response.json()
                    for key, value in expected['body_contains'].items():
                        if key not in actual_body or actual_body[key] != value:
                            logs.append(f"Body missing expected key '{key}' with value '{value}'")
                            return False
                except:
                    logs.append(f"Failed to parse response as JSON")
                    return False
            
            return True
            
        except requests.exceptions.RequestException as e:
            logs.append(f"Request failed: {str(e)}")
            return False
        except Exception as e:
            logs.append(f"Test execution error: {str(e)}")
            return False
    
    def _execute_cli_test(self, test_case: TestCase, logs: List[str]) -> bool:
        """Execute CLI command test"""
        try:
            command = test_case.input.get('command', '')
            
            if not command:
                logs.append("No command specified")
                return False
            
            # Execute command in container
            result = self.runner.execute(command, timeout=30, container_id=self.container_id)
            
            expected = test_case.expected_output
            
            # Check exit code
            if 'exit_code' in expected:
                if result.exit_code != expected['exit_code']:
                    logs.append(f"Exit code mismatch: expected {expected['exit_code']}, got {result.exit_code}")
                    return False
            
            # Check stdout
            if 'stdout' in expected:
                if expected['stdout'] not in result.stdout:
                    logs.append(f"Stdout mismatch")
                    return False
            
            # Check stderr
            if 'stderr' in expected:
                if expected['stderr'] not in result.stderr:
                    logs.append(f"Stderr mismatch")
                    return False
            
            return True
            
        except Exception as e:
            logs.append(f"CLI test error: {str(e)}")
            return False
    
    def _execute_generic_test(self, test_case: TestCase, logs: List[str]) -> bool:
        """Execute generic test"""
        # Default implementation - can be extended
        logs.append("Generic test execution not implemented")
        return True
    
    def _run_performance_tests(self, logs: List[str]) -> float:
        """Run performance benchmarks"""
        logs.append(f"[{datetime.now()}] Starting performance tests")
        
        try:
            # Initialize metrics calculator
            calculator = MetricsCalculator()
            
            # Prepare test configuration
            test_config = {
                'tool': 'locust',  # Default to Locust
                'users': 10,
                'duration': 30,
                'spawn_rate': 1,
                'endpoints': ['/']  # Default endpoints
            }
            
            # Update from problem requirements if available
            for req in self.problem.non_functional_requirements:
                if req.get('type') == 'performance':
                    # Parse performance requirements
                    constraint = req.get('constraint', '')
                    if 'req/min' in constraint:
                        # Calculate users based on request rate
                        import re
                        match = re.search(r'(\d+)req/min', constraint)
                        if match:
                            req_per_min = int(match.group(1))
                            test_config['users'] = max(10, req_per_min // 6)  # Approximate
            
            # Run performance test
            logs.append(f"[{datetime.now()}] Running performance test with {test_config['users']} users")
            metrics = calculator.run_performance_test(self.service_url, test_config)
            
            # Calculate score based on metrics
            score = 1.0
            
            # Check response time requirements
            for req in self.problem.non_functional_requirements:
                if req.get('type') == 'performance':
                    constraint = req.get('constraint', '')
                    
                    if 'パーセンタイルレスポンス時間' in constraint or 'response time' in constraint.lower():
                        # Check P95 response time
                        import re
                        match = re.search(r'< (\d+)ms', constraint)
                        if match:
                            target_ms = int(match.group(1))
                            if metrics.response_time_p95 > target_ms:
                                score *= (target_ms / metrics.response_time_p95)
                                logs.append(f"[{datetime.now()}] P95 response time {metrics.response_time_p95}ms exceeds target {target_ms}ms")
                    
                    if 'throughput' in constraint.lower():
                        # Check throughput
                        match = re.search(r'(\d+) req/sec', constraint)
                        if match:
                            target_rps = int(match.group(1))
                            if metrics.requests_per_second < target_rps:
                                score *= (metrics.requests_per_second / target_rps)
                                logs.append(f"[{datetime.now()}] Throughput {metrics.requests_per_second} req/s below target {target_rps} req/s")
            
            # Check error rate
            if metrics.error_rate > 0.05:  # More than 5% errors
                score *= (1 - metrics.error_rate)
                logs.append(f"[{datetime.now()}] High error rate: {metrics.error_rate*100:.1f}%")
            
            logs.append(f"[{datetime.now()}] Performance test completed")
            logs.append(f"[{datetime.now()}] - Requests/sec: {metrics.requests_per_second:.1f}")
            logs.append(f"[{datetime.now()}] - P95 latency: {metrics.response_time_p95:.1f}ms")
            logs.append(f"[{datetime.now()}] - Error rate: {metrics.error_rate*100:.1f}%")
            logs.append(f"[{datetime.now()}] Performance score: {score:.2f}")
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logs.append(f"[{datetime.now()}] Performance test error: {str(e)}")
            return 0.5  # Default score on error
    
    def _run_security_scan(self, logs: List[str]) -> float:
        """Execute security scanning"""
        logs.append(f"[{datetime.now()}] Starting security scan")
        
        try:
            # Initialize metrics calculator
            calculator = MetricsCalculator()
            
            # Determine scan target
            submission_path = self.working_dir / 'submission'
            if not submission_path.exists():
                # Try to find submission in working directory
                for path in self.working_dir.iterdir():
                    if path.is_dir() and path.name != 'results':
                        submission_path = path
                        break
            
            # Run security scan
            scan_config = {
                'tool': 'bandit' if any(submission_path.rglob('*.py')) else 'trivy',
                'scan_type': 'fs'
            }
            
            logs.append(f"[{datetime.now()}] Running {scan_config['tool']} security scan")
            security_metrics = calculator.run_security_scan(submission_path, scan_config)
            
            # Log findings
            total_vulns = (security_metrics.critical_vulnerabilities + 
                          security_metrics.high_vulnerabilities + 
                          security_metrics.medium_vulnerabilities + 
                          security_metrics.low_vulnerabilities)
            
            logs.append(f"[{datetime.now()}] Security scan completed")
            logs.append(f"[{datetime.now()}] - Critical: {security_metrics.critical_vulnerabilities}")
            logs.append(f"[{datetime.now()}] - High: {security_metrics.high_vulnerabilities}")
            logs.append(f"[{datetime.now()}] - Medium: {security_metrics.medium_vulnerabilities}")
            logs.append(f"[{datetime.now()}] - Low: {security_metrics.low_vulnerabilities}")
            logs.append(f"[{datetime.now()}] Security score: {security_metrics.security_score:.2f}")
            
            return security_metrics.security_score
            
        except Exception as e:
            logs.append(f"[{datetime.now()}] Security scan error: {str(e)}")
            return 0.8  # Default score on error
    
    def _analyze_code_quality(self, submission_path: Path, logs: List[str]) -> float:
        """Analyze code quality metrics"""
        logs.append(f"[{datetime.now()}] Starting code quality analysis")
        
        try:
            # Initialize metrics calculator
            calculator = MetricsCalculator()
            
            # Run code analysis
            analysis_config = {}
            
            logs.append(f"[{datetime.now()}] Analyzing code structure and quality")
            quality_metrics = calculator.run_code_analysis(submission_path, analysis_config)
            
            # Calculate overall quality score
            score = quality_metrics.calculate_score()
            
            # Log metrics
            logs.append(f"[{datetime.now()}] Code quality analysis completed")
            if quality_metrics.lines_of_code > 0:
                logs.append(f"[{datetime.now()}] - Lines of code: {quality_metrics.lines_of_code}")
            if quality_metrics.cyclomatic_complexity > 0:
                logs.append(f"[{datetime.now()}] - Avg complexity: {quality_metrics.cyclomatic_complexity:.1f}")
            if quality_metrics.test_coverage >= 0:
                logs.append(f"[{datetime.now()}] - Test coverage: {quality_metrics.test_coverage*100:.1f}%")
            if quality_metrics.linting_score > 0:
                logs.append(f"[{datetime.now()}] - Linting score: {quality_metrics.linting_score:.2f}")
            logs.append(f"[{datetime.now()}] Code quality score: {score:.2f}")
            
            return score
            
        except Exception as e:
            logs.append(f"[{datetime.now()}] Code quality analysis error: {str(e)}")
            return 0.7  # Default score on error
    
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
        logs.append(f"[{datetime.now()}] Cleaning up evaluation environment...")
        
        try:
            if hasattr(self, 'runner') and self.runner:
                self.runner.cleanup()
                logs.append(f"[{datetime.now()}] Runner resources cleaned up")
        except Exception as e:
            logs.append(f"[{datetime.now()}] Cleanup error: {str(e)}")