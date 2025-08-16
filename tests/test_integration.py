"""
Integration tests for Req2Run evaluation system
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
import time

from req2run.core import Problem, Evaluator
from req2run.runner import DockerRunner, LocalRunner
from req2run.metrics import MetricsCalculator, PerformanceMetrics, SecurityMetrics, QualityMetrics
from req2run.reporter import Reporter


@pytest.fixture
def sample_flask_app():
    """Create a sample Flask application for testing"""
    app_dir = Path(tempfile.mkdtemp())
    
    # Create app.py
    app_code = """
from flask import Flask, jsonify, request
import os

app = Flask(__name__)

tasks = []

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/tasks', methods=['GET', 'POST'])
def handle_tasks():
    if request.method == 'POST':
        task = request.json
        task['id'] = len(tasks) + 1
        tasks.append(task)
        return jsonify(task), 201
    else:
        return jsonify({'tasks': tasks}), 200

@app.route('/tasks/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_task(task_id):
    task = next((t for t in tasks if t.get('id') == task_id), None)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    if request.method == 'GET':
        return jsonify(task), 200
    elif request.method == 'PUT':
        task.update(request.json)
        return jsonify(task), 200
    elif request.method == 'DELETE':
        tasks.remove(task)
        return '', 204

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
"""
    
    with open(app_dir / 'app.py', 'w') as f:
        f.write(app_code)
    
    # Create requirements.txt
    with open(app_dir / 'requirements.txt', 'w') as f:
        f.write('flask>=2.0.0\n')
    
    # Create Dockerfile
    dockerfile = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["python", "app.py"]
"""
    
    with open(app_dir / 'Dockerfile', 'w') as f:
        f.write(dockerfile)
    
    yield app_dir
    
    # Cleanup
    shutil.rmtree(app_dir, ignore_errors=True)


@pytest.mark.integration
class TestEndToEndEvaluation:
    """End-to-end integration tests"""
    
    @pytest.mark.skipif(not shutil.which('docker'), reason="Docker not available")
    def test_docker_evaluation(self, sample_flask_app):
        """Test complete evaluation with Docker runner"""
        # Create a test problem
        problem = self._create_test_problem()
        
        # Create evaluator
        evaluator = Evaluator(
            problem=problem,
            environment='docker',
            timeout=300
        )
        
        # Run evaluation
        result = evaluator.evaluate(
            submission_path=sample_flask_app,
            submission_id='test-docker-001'
        )
        
        # Verify result
        assert result is not None
        assert result.problem_id == 'TEST-API-001'
        assert result.submission_id == 'test-docker-001'
        assert result.status in ['passed', 'failed', 'error']
        assert result.execution_time > 0
        assert 0 <= result.total_score <= 1
        assert len(result.logs) > 0
    
    def test_local_evaluation(self, sample_flask_app):
        """Test evaluation with local runner"""
        # Create a test problem
        problem = self._create_test_problem()
        
        # Create evaluator
        evaluator = Evaluator(
            problem=problem,
            environment='local',
            timeout=60
        )
        
        # Run evaluation
        result = evaluator.evaluate(
            submission_path=sample_flask_app,
            submission_id='test-local-001'
        )
        
        # Verify result
        assert result is not None
        assert result.problem_id == 'TEST-API-001'
        assert result.submission_id == 'test-local-001'
        assert result.execution_time > 0
        assert len(result.logs) > 0
    
    def _create_test_problem(self):
        """Create a test problem for integration testing"""
        from req2run.core import (
            Problem, Requirement, TestCase, EvaluationCriteria,
            Difficulty, Priority, TestStatus
        )
        
        return Problem(
            problem_id='TEST-API-001',
            category='web_api',
            difficulty=Difficulty.INTERMEDIATE,
            title='Test API',
            description='Test API for integration testing',
            functional_requirements=[
                Requirement('FR-001', 'Health endpoint', Priority.MUST),
                Requirement('FR-002', 'CRUD operations', Priority.MUST)
            ],
            non_functional_requirements=[
                {
                    'type': 'performance',
                    'constraint': 'Response time < 500ms',
                    'measurement': 'Load test'
                }
            ],
            input_specification={'format': 'REST API'},
            output_specification={'format': 'JSON'},
            test_cases=[
                TestCase(
                    id='TC-001',
                    description='Health check',
                    input={'method': 'GET', 'endpoint': '/health'},
                    expected_output={'status': 200}
                ),
                TestCase(
                    id='TC-002',
                    description='Create task',
                    input={
                        'method': 'POST',
                        'endpoint': '/tasks',
                        'body': {'title': 'Test Task'}
                    },
                    expected_output={'status': 201}
                )
            ],
            deployment_requirements={
                'environment': 'docker',
                'ports': ['3000:3000']
            },
            evaluation_criteria=[
                EvaluationCriteria(
                    metric='Functional coverage',
                    weight=0.5,
                    threshold=0.8,
                    measurement='Test execution'
                ),
                EvaluationCriteria(
                    metric='Performance',
                    weight=0.3,
                    threshold=0.7,
                    measurement='Response time'
                ),
                EvaluationCriteria(
                    metric='Code quality',
                    weight=0.2,
                    threshold=0.6,
                    measurement='Static analysis'
                )
            ]
        )


@pytest.mark.integration
class TestReporter:
    """Test report generation"""
    
    def test_html_report_generation(self, tmp_path):
        """Test HTML report generation"""
        reporter = Reporter()
        
        # Create sample results
        results = [
            {
                'problem_id': 'TEST-001',
                'submission_id': 'SUB-001',
                'timestamp': '2024-01-01T00:00:00',
                'total_score': 0.85,
                'status': 'passed',
                'execution_time': 120.5,
                'metrics': {
                    'functional_coverage': 0.9,
                    'test_pass_rate': 0.95,
                    'performance_score': 0.8,
                    'security_score': 1.0,
                    'code_quality_score': 0.75
                }
            },
            {
                'problem_id': 'TEST-002',
                'submission_id': 'SUB-002',
                'timestamp': '2024-01-01T01:00:00',
                'total_score': 0.65,
                'status': 'failed',
                'execution_time': 95.3,
                'metrics': {
                    'functional_coverage': 0.7,
                    'test_pass_rate': 0.6,
                    'performance_score': 0.6,
                    'security_score': 0.8,
                    'code_quality_score': 0.7
                }
            }
        ]
        
        # Generate report
        output_path = tmp_path / 'report.html'
        reporter.generate_html_report(results, str(output_path))
        
        # Verify report was created
        assert output_path.exists()
        
        # Check content
        with open(output_path, 'r') as f:
            content = f.read()
            assert 'TEST-001' in content
            assert 'SUB-001' in content
            assert '85' in content  # Score percentage
    
    def test_markdown_report_generation(self, tmp_path):
        """Test Markdown report generation"""
        reporter = Reporter()
        
        # Create sample results
        results = [
            {
                'problem_id': 'TEST-001',
                'submission_id': 'SUB-001',
                'timestamp': '2024-01-01T00:00:00',
                'total_score': 0.85,
                'status': 'passed',
                'execution_time': 120.5,
                'metrics': {
                    'functional_coverage': 0.9,
                    'test_pass_rate': 0.95,
                    'performance_score': 0.8,
                    'security_score': 1.0,
                    'code_quality_score': 0.75
                }
            }
        ]
        
        # Generate report
        output_path = tmp_path / 'report.md'
        reporter.generate_markdown_report(results, str(output_path))
        
        # Verify report was created
        assert output_path.exists()
        
        # Check content
        with open(output_path, 'r') as f:
            content = f.read()
            assert '# Req2Run Evaluation Report' in content
            assert 'TEST-001' in content
            assert 'SUB-001' in content
    
    def test_json_report_generation(self, tmp_path):
        """Test JSON report generation"""
        reporter = Reporter()
        
        # Create sample results
        results = [
            {
                'problem_id': 'TEST-001',
                'submission_id': 'SUB-001',
                'timestamp': '2024-01-01T00:00:00',
                'total_score': 0.85,
                'status': 'passed',
                'execution_time': 120.5
            }
        ]
        
        # Generate report
        output_path = tmp_path / 'report.json'
        reporter.generate_json_report(results, str(output_path))
        
        # Verify report was created
        assert output_path.exists()
        
        # Check content
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert 'metadata' in data
            assert 'summary' in data
            assert 'detailed_results' in data
            assert data['metadata']['total_problems'] == 1
    
    def test_leaderboard_generation(self):
        """Test leaderboard generation"""
        reporter = Reporter()
        
        # Create sample results
        results = [
            {
                'problem_id': 'TEST-001',
                'submission_id': 'Team-A',
                'total_score': 0.95,
                'status': 'passed',
                'execution_time': 100
            },
            {
                'problem_id': 'TEST-001',
                'submission_id': 'Team-B',
                'total_score': 0.85,
                'status': 'passed',
                'execution_time': 120
            },
            {
                'problem_id': 'TEST-001',
                'submission_id': 'Team-C',
                'total_score': 0.65,
                'status': 'failed',
                'execution_time': 150
            }
        ]
        
        # Generate leaderboard
        leaderboard = reporter.generate_leaderboard(results)
        
        # Check content
        assert '# Req2Run Leaderboard' in leaderboard
        assert 'Team-A' in leaderboard
        assert 'Team-B' in leaderboard
        assert 'Team-C' in leaderboard
        assert '95.0%' in leaderboard  # Top score
        
        # Check ordering (Team-A should be first)
        lines = leaderboard.split('\n')
        table_lines = [l for l in lines if '|' in l and 'Team-' in l]
        assert 'Team-A' in table_lines[0]


@pytest.mark.integration
class TestMetricsCalculator:
    """Test metrics calculation"""
    
    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation"""
        calculator = MetricsCalculator()
        
        # Create sample benchmark data
        benchmark_data = {
            'response_times': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            'requests': {
                'total': 1000,
                'successful': 950,
                'failed': 50
            },
            'duration': 60,
            'throughput': {
                'rps': 16.67
            }
        }
        
        # Calculate metrics
        metrics = calculator.calculate_performance_metrics(benchmark_data)
        
        # Verify metrics
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.avg_response_time == 55.0
        assert metrics.min_response_time == 10
        assert metrics.max_response_time == 100
        assert metrics.response_time_p50 == 55.0
        assert metrics.total_requests == 1000
        assert metrics.successful_requests == 950
        assert metrics.failed_requests == 50
        assert metrics.error_rate == 0.05
    
    def test_security_metrics_calculation(self):
        """Test security metrics calculation"""
        calculator = MetricsCalculator()
        
        # Create sample scan data
        scan_data = {
            'vulnerabilities': [
                {'severity': 'high'},
                {'severity': 'high'},
                {'severity': 'medium'},
                {'severity': 'low'},
                {'severity': 'low'},
                {'severity': 'low'}
            ]
        }
        
        # Calculate metrics
        metrics = calculator.calculate_security_score(scan_data)
        
        # Verify metrics
        assert isinstance(metrics, SecurityMetrics)
        assert metrics.high_vulnerabilities == 2
        assert metrics.medium_vulnerabilities == 1
        assert metrics.low_vulnerabilities == 3
        assert metrics.security_score == 0.3  # Due to high vulnerabilities
    
    def test_code_quality_calculation(self):
        """Test code quality metrics calculation"""
        calculator = MetricsCalculator()
        
        # Create sample analysis data
        analysis_data = {
            'complexity': {'average': 8},
            'coverage': {'percentage': 75},
            'duplication': {'percentage': 5},
            'statistics': {
                'lines': 1000,
                'functions': 50,
                'classes': 10
            },
            'linting': {'score': 8.5}
        }
        
        # Calculate metrics
        metrics = calculator.calculate_code_quality(analysis_data)
        
        # Verify metrics
        assert isinstance(metrics, QualityMetrics)
        assert metrics.cyclomatic_complexity == 8
        assert metrics.test_coverage == 0.75
        assert metrics.code_duplication == 0.05
        assert metrics.lines_of_code == 1000
        assert metrics.linting_score == 0.85
    
    def test_aggregate_scores(self):
        """Test score aggregation"""
        calculator = MetricsCalculator()
        
        # Create sample metrics and weights
        metrics = {
            'functional': 0.9,
            'performance': 0.8,
            'security': 1.0,
            'quality': 0.7
        }
        
        weights = {
            'functional': 0.4,
            'performance': 0.3,
            'security': 0.2,
            'quality': 0.1
        }
        
        # Calculate aggregate
        score = calculator.aggregate_scores(metrics, weights)
        
        # Verify calculation
        expected = (0.9 * 0.4 + 0.8 * 0.3 + 1.0 * 0.2 + 0.7 * 0.1)
        assert abs(score - expected) < 0.001