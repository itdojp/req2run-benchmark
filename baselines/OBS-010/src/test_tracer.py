"""Test execution tracing instrumentation"""
import sys
import time
import traceback
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from tracing import get_tracer, trace_operation, trace_span, add_span_attribute, add_span_event
import structlog

logger = structlog.get_logger()


class TestTracer:
    """Instruments test execution with OpenTelemetry spans"""
    
    def __init__(self, test_framework: str = "pytest"):
        self.test_framework = test_framework
        self.tracer = get_tracer("test-tracer")
        self.test_results = []
    
    @trace_operation("test.suite.execute")
    def execute_test_suite(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complete test suite with tracing"""
        suite_start = time.time()
        
        add_span_attribute("test.framework", self.test_framework)
        add_span_attribute("test.config.parallel", test_config.get("parallel", False))
        add_span_attribute("test.config.coverage", test_config.get("coverage", False))
        add_span_attribute("test.config.verbose", test_config.get("verbose", False))
        
        suite_results = {
            "framework": self.test_framework,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "duration": 0,
            "coverage": None,
            "test_files": [],
            "failed_tests": []
        }
        
        # Discover and execute tests
        test_discovery = self._discover_tests(test_config)
        suite_results["test_files"] = test_discovery["test_files"]
        
        for test_file in test_discovery["test_files"]:
            file_results = self._execute_test_file(test_file, test_config)
            
            suite_results["total_tests"] += file_results["total_tests"]
            suite_results["passed"] += file_results["passed"]
            suite_results["failed"] += file_results["failed"]
            suite_results["skipped"] += file_results["skipped"]
            suite_results["errors"] += file_results["errors"]
            suite_results["failed_tests"].extend(file_results["failed_tests"])
        
        # Collect coverage if enabled
        if test_config.get("coverage", False):
            suite_results["coverage"] = self._collect_coverage_data()
        
        suite_end = time.time()
        suite_results["duration"] = suite_end - suite_start
        
        # Add suite-level attributes
        add_span_attribute("test.suite.total", suite_results["total_tests"])
        add_span_attribute("test.suite.passed", suite_results["passed"])
        add_span_attribute("test.suite.failed", suite_results["failed"])
        add_span_attribute("test.suite.skipped", suite_results["skipped"])
        add_span_attribute("test.suite.duration", suite_results["duration"])
        add_span_attribute("test.suite.success_rate", 
                          suite_results["passed"] / max(suite_results["total_tests"], 1))
        
        add_span_event("test.suite.completed", {
            "total": suite_results["total_tests"],
            "passed": suite_results["passed"],
            "failed": suite_results["failed"],
            "duration": suite_results["duration"]
        })
        
        return suite_results
    
    def _discover_tests(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Discover test files with tracing"""
        with trace_span("test.discovery") as span:
            test_patterns = test_config.get("patterns", ["test_*.py", "*_test.py"])
            test_directories = test_config.get("directories", ["tests", "test"])
            
            discovered_files = []
            
            for directory in test_directories:
                dir_path = Path(directory)
                if dir_path.exists():
                    for pattern in test_patterns:
                        test_files = list(dir_path.glob(pattern))
                        discovered_files.extend([str(f) for f in test_files])
            
            # Also check current directory
            for pattern in test_patterns:
                test_files = list(Path(".").glob(pattern))
                discovered_files.extend([str(f) for f in test_files])
            
            # Remove duplicates
            discovered_files = list(set(discovered_files))
            
            span.set_attribute("test.discovery.files_found", len(discovered_files))
            span.set_attribute("test.discovery.patterns", ",".join(test_patterns))
            span.set_attribute("test.discovery.directories", ",".join(test_directories))
            
            return {
                "test_files": discovered_files,
                "patterns_used": test_patterns,
                "directories_searched": test_directories
            }
    
    def _execute_test_file(self, test_file: str, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual test file with tracing"""
        with trace_span(f"test.file.{Path(test_file).stem}") as span:
            span.set_attribute("test.file.path", test_file)
            
            file_start = time.time()
            
            # Simulate test execution based on framework
            if self.test_framework == "pytest":
                file_results = self._execute_pytest_file(test_file, test_config)
            elif self.test_framework == "unittest":
                file_results = self._execute_unittest_file(test_file, test_config)
            else:
                file_results = self._execute_generic_test_file(test_file, test_config)
            
            file_end = time.time()
            file_results["duration"] = file_end - file_start
            
            span.set_attribute("test.file.total", file_results["total_tests"])
            span.set_attribute("test.file.passed", file_results["passed"])
            span.set_attribute("test.file.failed", file_results["failed"])
            span.set_attribute("test.file.duration", file_results["duration"])
            
            return file_results
    
    def _execute_pytest_file(self, test_file: str, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pytest test file"""
        # In real implementation, this would use pytest's API
        # For simulation, we'll create mock test results
        
        mock_tests = [
            {"name": "test_basic_functionality", "status": "passed", "duration": 0.1},
            {"name": "test_edge_cases", "status": "passed", "duration": 0.2},
            {"name": "test_error_handling", "status": "failed", "duration": 0.15, "error": "AssertionError: Expected 5, got 4"},
            {"name": "test_performance", "status": "passed", "duration": 0.5},
            {"name": "test_integration", "status": "skipped", "reason": "Integration tests disabled"},
        ]
        
        file_results = {
            "total_tests": len(mock_tests),
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "failed_tests": [],
            "test_details": []
        }
        
        for test in mock_tests:
            test_result = self._execute_individual_test(test_file, test)
            file_results["test_details"].append(test_result)
            
            if test_result["status"] == "passed":
                file_results["passed"] += 1
            elif test_result["status"] == "failed":
                file_results["failed"] += 1
                file_results["failed_tests"].append({
                    "file": test_file,
                    "test": test_result["name"],
                    "error": test_result.get("error", "Unknown error")
                })
            elif test_result["status"] == "skipped":
                file_results["skipped"] += 1
            else:
                file_results["errors"] += 1
        
        return file_results
    
    def _execute_unittest_file(self, test_file: str, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute unittest test file"""
        # Similar to pytest but with unittest-specific handling
        return self._execute_pytest_file(test_file, test_config)  # Simplified
    
    def _execute_generic_test_file(self, test_file: str, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test file with generic framework"""
        return self._execute_pytest_file(test_file, test_config)  # Simplified
    
    def _execute_individual_test(self, test_file: str, test_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual test with tracing"""
        test_name = test_info["name"]
        
        with trace_span(f"test.case.{test_name}") as span:
            span.set_attribute("test.name", test_name)
            span.set_attribute("test.file", test_file)
            
            test_start = time.time()
            
            # Simulate test execution
            time.sleep(test_info.get("duration", 0.1))
            
            test_end = time.time()
            actual_duration = test_end - test_start
            
            test_result = {
                "name": test_name,
                "status": test_info["status"],
                "duration": actual_duration,
                "file": test_file
            }
            
            # Handle test outcomes
            if test_info["status"] == "passed":
                span.set_attribute("test.result", "passed")
                add_span_event("test.passed", {"test_name": test_name})
                
            elif test_info["status"] == "failed":
                span.set_attribute("test.result", "failed")
                error_msg = test_info.get("error", "Test failed")
                test_result["error"] = error_msg
                
                span.set_attribute("test.error", error_msg)
                add_span_event("test.failed", {
                    "test_name": test_name,
                    "error": error_msg
                })
                
            elif test_info["status"] == "skipped":
                span.set_attribute("test.result", "skipped")
                reason = test_info.get("reason", "Test skipped")
                test_result["skip_reason"] = reason
                
                span.set_attribute("test.skip_reason", reason)
                add_span_event("test.skipped", {
                    "test_name": test_name,
                    "reason": reason
                })
            
            span.set_attribute("test.duration", actual_duration)
            
            return test_result
    
    def _collect_coverage_data(self) -> Dict[str, Any]:
        """Collect test coverage data with tracing"""
        with trace_span("test.coverage.collect") as span:
            # Simulate coverage data collection
            mock_coverage = {
                "total_lines": 1000,
                "covered_lines": 850,
                "coverage_percentage": 85.0,
                "files": {
                    "src/main.py": {"lines": 100, "covered": 95, "percentage": 95.0},
                    "src/utils.py": {"lines": 50, "covered": 40, "percentage": 80.0},
                    "src/models.py": {"lines": 200, "covered": 160, "percentage": 80.0}
                },
                "uncovered_lines": {
                    "src/main.py": [23, 45, 67],
                    "src/utils.py": [12, 34, 56, 78, 90, 101, 123, 145, 167, 189]
                }
            }
            
            span.set_attribute("coverage.total_lines", mock_coverage["total_lines"])
            span.set_attribute("coverage.covered_lines", mock_coverage["covered_lines"])
            span.set_attribute("coverage.percentage", mock_coverage["coverage_percentage"])
            span.set_attribute("coverage.files_count", len(mock_coverage["files"]))
            
            add_span_event("test.coverage.collected", {
                "percentage": mock_coverage["coverage_percentage"],
                "total_lines": mock_coverage["total_lines"],
                "covered_lines": mock_coverage["covered_lines"]
            })
            
            return mock_coverage
    
    @trace_operation("test.performance.benchmark")
    def execute_performance_tests(self, benchmark_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute performance benchmarks with tracing"""
        add_span_attribute("benchmark.iterations", benchmark_config.get("iterations", 100))
        add_span_attribute("benchmark.warmup", benchmark_config.get("warmup", 10))
        
        benchmarks = [
            {"name": "api_response_time", "metric": "latency"},
            {"name": "database_query_performance", "metric": "throughput"},
            {"name": "memory_usage_test", "metric": "memory"},
            {"name": "cpu_intensive_task", "metric": "cpu_time"}
        ]
        
        benchmark_results = {
            "total_benchmarks": len(benchmarks),
            "passed": 0,
            "failed": 0,
            "results": []
        }
        
        for benchmark in benchmarks:
            result = self._execute_benchmark(benchmark, benchmark_config)
            benchmark_results["results"].append(result)
            
            if result["passed"]:
                benchmark_results["passed"] += 1
            else:
                benchmark_results["failed"] += 1
        
        add_span_attribute("benchmark.total", benchmark_results["total_benchmarks"])
        add_span_attribute("benchmark.passed", benchmark_results["passed"])
        add_span_attribute("benchmark.failed", benchmark_results["failed"])
        
        return benchmark_results
    
    def _execute_benchmark(self, benchmark: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual benchmark with tracing"""
        benchmark_name = benchmark["name"]
        metric_type = benchmark["metric"]
        
        with trace_span(f"benchmark.{benchmark_name}") as span:
            span.set_attribute("benchmark.name", benchmark_name)
            span.set_attribute("benchmark.metric_type", metric_type)
            
            iterations = config.get("iterations", 100)
            warmup_iterations = config.get("warmup", 10)
            
            span.set_attribute("benchmark.iterations", iterations)
            span.set_attribute("benchmark.warmup_iterations", warmup_iterations)
            
            # Simulate benchmark execution
            measurements = []
            
            # Warmup phase
            with trace_span(f"benchmark.{benchmark_name}.warmup"):
                for i in range(warmup_iterations):
                    time.sleep(0.001)  # Simulate warmup
            
            # Measurement phase
            with trace_span(f"benchmark.{benchmark_name}.measure") as measure_span:
                for i in range(iterations):
                    start = time.time()
                    
                    # Simulate benchmark operation
                    if metric_type == "latency":
                        time.sleep(0.002)  # Simulate operation
                        measurement = (time.time() - start) * 1000  # ms
                    elif metric_type == "throughput":
                        time.sleep(0.001)
                        measurement = 1000.0  # ops/sec (simulated)
                    elif metric_type == "memory":
                        measurement = 50.0  # MB (simulated)
                    else:  # cpu_time
                        time.sleep(0.001)
                        measurement = (time.time() - start) * 1000  # ms
                    
                    measurements.append(measurement)
                
                # Calculate statistics
                avg_measurement = sum(measurements) / len(measurements)
                min_measurement = min(measurements)
                max_measurement = max(measurements)
                
                measure_span.set_attribute("benchmark.avg_value", avg_measurement)
                measure_span.set_attribute("benchmark.min_value", min_measurement)
                measure_span.set_attribute("benchmark.max_value", max_measurement)
            
            # Determine if benchmark passed (simplified)
            thresholds = {
                "latency": 10.0,  # ms
                "throughput": 500.0,  # ops/sec
                "memory": 100.0,  # MB
                "cpu_time": 5.0  # ms
            }
            
            threshold = thresholds.get(metric_type, float('inf'))
            
            if metric_type == "throughput":
                passed = avg_measurement >= threshold  # Higher is better
            else:
                passed = avg_measurement <= threshold  # Lower is better
            
            span.set_attribute("benchmark.passed", passed)
            span.set_attribute("benchmark.threshold", threshold)
            
            result = {
                "name": benchmark_name,
                "metric_type": metric_type,
                "passed": passed,
                "measurements": {
                    "avg": avg_measurement,
                    "min": min_measurement,
                    "max": max_measurement,
                    "iterations": iterations
                },
                "threshold": threshold
            }
            
            add_span_event(f"benchmark.{benchmark_name}.completed", {
                "passed": passed,
                "avg_value": avg_measurement,
                "threshold": threshold
            })
            
            return result
    
    @trace_operation("test.cleanup")
    def cleanup_test_environment(self) -> Dict[str, Any]:
        """Cleanup test environment with tracing"""
        cleanup_tasks = [
            "remove_temporary_files",
            "reset_database_state",
            "clear_cache",
            "restore_configuration"
        ]
        
        cleanup_results = {
            "tasks_completed": [],
            "tasks_failed": [],
            "total_tasks": len(cleanup_tasks)
        }
        
        for task in cleanup_tasks:
            with trace_span(f"test.cleanup.{task}") as span:
                try:
                    # Simulate cleanup task
                    time.sleep(0.1)
                    
                    cleanup_results["tasks_completed"].append(task)
                    span.set_attribute("cleanup.task.success", True)
                    
                except Exception as e:
                    cleanup_results["tasks_failed"].append({"task": task, "error": str(e)})
                    span.set_attribute("cleanup.task.success", False)
                    span.set_attribute("cleanup.task.error", str(e))
        
        add_span_attribute("cleanup.completed_tasks", len(cleanup_results["tasks_completed"]))
        add_span_attribute("cleanup.failed_tasks", len(cleanup_results["tasks_failed"]))
        
        return cleanup_results