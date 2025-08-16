"""
Unit tests for core module
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import yaml

from req2run.core import (
    Problem, Evaluator, Result, TestCase, Requirement,
    Difficulty, Priority, TestStatus, EvaluationCriteria
)


@pytest.fixture
def sample_problem_yaml():
    """Create a sample problem YAML file"""
    problem_data = {
        'problem_id': 'TEST-001',
        'category': 'test',
        'difficulty': 'intermediate',
        'title': 'Test Problem',
        'description': 'A test problem for unit testing',
        'functional_requirements': [
            {
                'id': 'FR-001',
                'description': 'Test requirement 1',
                'priority': 'must'
            },
            {
                'id': 'FR-002',
                'description': 'Test requirement 2',
                'priority': 'should'
            }
        ],
        'non_functional_requirements': [
            {
                'type': 'performance',
                'constraint': 'Response time < 100ms',
                'measurement': 'Load test'
            }
        ],
        'input_specification': {
            'format': 'JSON',
            'examples': [{'test': 'data'}]
        },
        'output_specification': {
            'format': 'JSON',
            'examples': [{'result': 'data'}]
        },
        'test_cases': [
            {
                'id': 'TC-001',
                'description': 'Basic test',
                'input': {'method': 'GET', 'endpoint': '/test'},
                'expected_output': {'status': 200}
            }
        ],
        'deployment_requirements': {
            'environment': 'docker',
            'dependencies': ['redis']
        },
        'evaluation_criteria': [
            {
                'metric': 'Functional coverage',
                'weight': 0.5,
                'threshold': 0.8,
                'measurement': 'Test execution'
            },
            {
                'metric': 'Performance',
                'weight': 0.5,
                'threshold': 0.7,
                'measurement': 'Benchmark'
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(problem_data, f)
        return Path(f.name)


class TestProblem:
    """Test Problem class"""
    
    def test_load_from_yaml(self, sample_problem_yaml):
        """Test loading problem from YAML"""
        problem = Problem.from_yaml(sample_problem_yaml)
        
        assert problem.problem_id == 'TEST-001'
        assert problem.category == 'test'
        assert problem.difficulty == Difficulty.INTERMEDIATE
        assert problem.title == 'Test Problem'
        assert len(problem.functional_requirements) == 2
        assert len(problem.test_cases) == 1
        assert len(problem.evaluation_criteria) == 2
        
        # Check requirement parsing
        req1 = problem.functional_requirements[0]
        assert req1.id == 'FR-001'
        assert req1.priority == Priority.MUST
        
        # Check test case parsing
        tc1 = problem.test_cases[0]
        assert tc1.id == 'TC-001'
        assert tc1.status == TestStatus.PENDING
        
        # Check evaluation criteria
        ec1 = problem.evaluation_criteria[0]
        assert ec1.metric == 'Functional coverage'
        assert ec1.weight == 0.5
        assert ec1.threshold == 0.8
    
    def test_to_dict(self, sample_problem_yaml):
        """Test converting problem to dictionary"""
        problem = Problem.from_yaml(sample_problem_yaml)
        problem_dict = problem.to_dict()
        
        assert problem_dict['problem_id'] == 'TEST-001'
        assert problem_dict['difficulty'] == 'intermediate'
        assert len(problem_dict['functional_requirements']) == 2
        assert len(problem_dict['test_cases']) == 1
        assert len(problem_dict['evaluation_criteria']) == 2


class TestResult:
    """Test Result class"""
    
    def test_result_creation(self):
        """Test creating a result object"""
        result = Result(
            problem_id='TEST-001',
            submission_id='SUB-001',
            timestamp=datetime.now(),
            total_score=0.85,
            status='passed',
            execution_time=120.5,
            functional_coverage=0.9,
            test_pass_rate=0.95,
            performance_score=0.8,
            security_score=1.0,
            code_quality_score=0.75,
            test_results=[],
            criteria_results=[],
            logs=['Test log entry'],
            artifacts={'report': '/path/to/report.html'}
        )
        
        assert result.problem_id == 'TEST-001'
        assert result.submission_id == 'SUB-001'
        assert result.total_score == 0.85
        assert result.status == 'passed'
        assert result.execution_time == 120.5
        assert len(result.logs) == 1
    
    def test_result_to_json(self):
        """Test converting result to JSON"""
        result = Result(
            problem_id='TEST-001',
            submission_id='SUB-001',
            timestamp=datetime.now(),
            total_score=0.85,
            status='passed',
            execution_time=120.5,
            functional_coverage=0.9,
            test_pass_rate=0.95,
            performance_score=0.8,
            security_score=1.0,
            code_quality_score=0.75,
            test_results=[],
            criteria_results=[],
            logs=['Test log'],
            artifacts={}
        )
        
        json_str = result.to_json()
        assert 'TEST-001' in json_str
        assert 'SUB-001' in json_str
        assert '0.85' in json_str
    
    def test_result_save(self, tmp_path):
        """Test saving result to file"""
        result = Result(
            problem_id='TEST-001',
            submission_id='SUB-001',
            timestamp=datetime.now(),
            total_score=0.85,
            status='passed',
            execution_time=120.5,
            functional_coverage=0.9,
            test_pass_rate=0.95,
            performance_score=0.8,
            security_score=1.0,
            code_quality_score=0.75,
            test_results=[],
            criteria_results=[],
            logs=['Test log entry 1', 'Test log entry 2'],
            artifacts={}
        )
        
        output_dir = tmp_path / 'results'
        result.save(output_dir)
        
        # Check files were created
        assert (output_dir / 'SUB-001_result.json').exists()
        assert (output_dir / 'SUB-001_logs.txt').exists()
        
        # Check log content
        with open(output_dir / 'SUB-001_logs.txt', 'r') as f:
            logs = f.read()
            assert 'Test log entry 1' in logs
            assert 'Test log entry 2' in logs


class TestEvaluator:
    """Test Evaluator class"""
    
    @pytest.fixture
    def mock_problem(self):
        """Create a mock problem"""
        problem = Problem(
            problem_id='TEST-001',
            category='test',
            difficulty=Difficulty.INTERMEDIATE,
            title='Test Problem',
            description='Test description',
            functional_requirements=[
                Requirement('FR-001', 'Test req', Priority.MUST)
            ],
            non_functional_requirements=[],
            input_specification={},
            output_specification={},
            test_cases=[
                TestCase(
                    id='TC-001',
                    description='Test case',
                    input={'test': 'input'},
                    expected_output={'test': 'output'}
                )
            ],
            deployment_requirements={},
            evaluation_criteria=[
                EvaluationCriteria(
                    metric='Test metric',
                    weight=1.0,
                    threshold=0.7,
                    measurement='Test'
                )
            ]
        )
        return problem
    
    def test_evaluator_initialization(self, mock_problem, tmp_path):
        """Test creating an evaluator"""
        evaluator = Evaluator(
            problem=mock_problem,
            environment='local',
            timeout=60,
            working_dir=tmp_path
        )
        
        assert evaluator.problem == mock_problem
        assert evaluator.environment == 'local'
        assert evaluator.timeout == 60
        assert evaluator.working_dir == tmp_path
    
    def test_failed_result_creation(self, mock_problem, tmp_path):
        """Test creating a failed result"""
        evaluator = Evaluator(
            problem=mock_problem,
            environment='local',
            working_dir=tmp_path
        )
        
        result = evaluator._create_failed_result(
            submission_id='SUB-001',
            error_message='Test error',
            execution_time=10.5,
            logs=['Log 1', 'Log 2']
        )
        
        assert result.problem_id == 'TEST-001'
        assert result.submission_id == 'SUB-001'
        assert result.status == 'error'
        assert result.total_score == 0.0
        assert result.execution_time == 10.5
        assert 'ERROR: Test error' in result.logs


class TestRequirement:
    """Test Requirement class"""
    
    def test_requirement_creation(self):
        """Test creating a requirement"""
        req = Requirement(
            id='FR-001',
            description='Test requirement',
            priority=Priority.MUST
        )
        
        assert req.id == 'FR-001'
        assert req.description == 'Test requirement'
        assert req.priority == Priority.MUST
        assert req.validated == False
        assert req.validation_message == ''


class TestTestCase:
    """Test TestCase class"""
    
    def test_testcase_creation(self):
        """Test creating a test case"""
        tc = TestCase(
            id='TC-001',
            description='Test case',
            input={'method': 'GET'},
            expected_output={'status': 200}
        )
        
        assert tc.id == 'TC-001'
        assert tc.description == 'Test case'
        assert tc.input == {'method': 'GET'}
        assert tc.expected_output == {'status': 200}
        assert tc.status == TestStatus.PENDING
        assert tc.execution_time == 0.0


class TestEvaluationCriteria:
    """Test EvaluationCriteria class"""
    
    def test_criteria_creation(self):
        """Test creating evaluation criteria"""
        criteria = EvaluationCriteria(
            metric='Performance',
            weight=0.3,
            threshold=0.8,
            measurement='Benchmark'
        )
        
        assert criteria.metric == 'Performance'
        assert criteria.weight == 0.3
        assert criteria.threshold == 0.8
        assert criteria.measurement == 'Benchmark'
        assert criteria.score == 0.0
        assert criteria.passed == False