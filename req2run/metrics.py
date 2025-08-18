"""
Metrics calculation and aggregation for Req2Run evaluations
"""

import time
import statistics
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import subprocess

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""

    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    QUALITY = "quality"
    RESOURCE = "resource"


@dataclass
class PerformanceMetrics:
    """Performance measurement results"""

    response_time_p50: float = 0.0
    response_time_p95: float = 0.0
    response_time_p99: float = 0.0
    throughput: float = 0.0
    error_rate: float = 0.0
    requests_per_second: float = 0.0
    concurrent_users: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "response_time": {
                "p50": self.response_time_p50,
                "p95": self.response_time_p95,
                "p99": self.response_time_p99,
                "avg": self.avg_response_time,
                "min": self.min_response_time,
                "max": self.max_response_time,
            },
            "throughput": {
                "requests_per_second": self.requests_per_second,
                "total_requests": self.total_requests,
                "successful": self.successful_requests,
                "failed": self.failed_requests,
                "error_rate": self.error_rate,
            },
        }


@dataclass
class SecurityMetrics:
    """Security scan results"""

    critical_vulnerabilities: int = 0
    high_vulnerabilities: int = 0
    medium_vulnerabilities: int = 0
    low_vulnerabilities: int = 0
    security_score: float = 0.0
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    passed_checks: int = 0
    failed_checks: int = 0

    def calculate_score(self) -> float:
        """Calculate security score based on vulnerabilities"""
        if self.critical_vulnerabilities > 0:
            return 0.0
        elif self.high_vulnerabilities > 0:
            return 0.3
        elif self.medium_vulnerabilities > 0:
            return 0.6
        elif self.low_vulnerabilities > 0:
            return 0.8
        else:
            return 1.0


@dataclass
class QualityMetrics:
    """Code quality metrics"""

    cyclomatic_complexity: float = 0.0
    test_coverage: float = 0.0
    code_duplication: float = 0.0
    maintainability_index: float = 0.0
    technical_debt_ratio: float = 0.0
    lines_of_code: int = 0
    number_of_functions: int = 0
    number_of_classes: int = 0
    documentation_coverage: float = 0.0
    linting_score: float = 0.0

    def calculate_score(self) -> float:
        """Calculate overall quality score"""
        scores = []

        # Complexity score (lower is better)
        if self.cyclomatic_complexity > 0:
            complexity_score = max(0, 1 - (self.cyclomatic_complexity - 5) / 15)
            scores.append(complexity_score)

        # Coverage score
        if self.test_coverage >= 0:
            scores.append(self.test_coverage)

        # Duplication score (lower is better)
        if self.code_duplication >= 0:
            duplication_score = max(0, 1 - self.code_duplication)
            scores.append(duplication_score)

        # Linting score
        if self.linting_score > 0:
            scores.append(self.linting_score)

        return statistics.mean(scores) if scores else 0.5


@dataclass
class ResourceMetrics:
    """Resource usage metrics"""

    cpu_usage_avg: float = 0.0
    cpu_usage_peak: float = 0.0
    memory_usage_avg: float = 0.0
    memory_usage_peak: float = 0.0
    disk_io_read: float = 0.0
    disk_io_write: float = 0.0
    network_io_in: float = 0.0
    network_io_out: float = 0.0
    container_size: float = 0.0
    build_time: float = 0.0
    startup_time: float = 0.0


class MetricsCalculator:
    """Calculate and aggregate evaluation metrics"""

    def __init__(self):
        self.metrics_cache = {}

    def calculate_functional_coverage(
        self, requirements: List[Any], test_results: List[Any]
    ) -> float:
        """
        Calculate functional requirements coverage

        Args:
            requirements: List of functional requirements
            test_results: List of test execution results

        Returns:
            Coverage percentage (0.0 to 1.0)
        """
        if not requirements:
            return 0.0

        # Count validated requirements
        validated = 0
        for req in requirements:
            # Check if requirement has associated passing tests
            if hasattr(req, "validated") and req.validated:
                validated += 1
            elif hasattr(req, "id"):
                # Check if any test validates this requirement
                for test in test_results:
                    if hasattr(test, "validates") and req.id in test.validates:
                        if test.status == "passed":
                            validated += 1
                            break

        return validated / len(requirements)

    def calculate_test_pass_rate(self, test_results: List[Any]) -> float:
        """
        Calculate test pass rate

        Args:
            test_results: List of test execution results

        Returns:
            Pass rate (0.0 to 1.0)
        """
        if not test_results:
            return 0.0

        passed = sum(
            1
            for test in test_results
            if hasattr(test, "status") and test.status.value == "passed"
        )

        return passed / len(test_results)

    def calculate_performance_metrics(
        self, benchmark_results: Dict[str, Any]
    ) -> PerformanceMetrics:
        """
        Calculate performance metrics from benchmark results

        Args:
            benchmark_results: Raw benchmark data

        Returns:
            PerformanceMetrics object
        """
        metrics = PerformanceMetrics()

        if "response_times" in benchmark_results:
            times = benchmark_results["response_times"]
            if times:
                metrics.avg_response_time = statistics.mean(times)
                metrics.min_response_time = min(times)
                metrics.max_response_time = max(times)
                metrics.response_time_p50 = self._percentile(times, 50)
                metrics.response_time_p95 = self._percentile(times, 95)
                metrics.response_time_p99 = self._percentile(times, 99)

        if "requests" in benchmark_results:
            req_data = benchmark_results["requests"]
            metrics.total_requests = req_data.get("total", 0)
            metrics.successful_requests = req_data.get("successful", 0)
            metrics.failed_requests = req_data.get("failed", 0)

            if metrics.total_requests > 0:
                metrics.error_rate = metrics.failed_requests / metrics.total_requests

        if "throughput" in benchmark_results:
            metrics.requests_per_second = benchmark_results["throughput"].get("rps", 0)
            metrics.throughput = benchmark_results["throughput"].get(
                "bytes_per_second", 0
            )

        if "duration" in benchmark_results and benchmark_results["duration"] > 0:
            duration = benchmark_results["duration"]
            if metrics.total_requests > 0:
                metrics.requests_per_second = metrics.total_requests / duration

        return metrics

    def calculate_security_score(self, scan_results: Dict[str, Any]) -> SecurityMetrics:
        """
        Calculate security score from scan results

        Args:
            scan_results: Security scan output

        Returns:
            SecurityMetrics object
        """
        metrics = SecurityMetrics()

        # Parse vulnerability counts
        if "vulnerabilities" in scan_results:
            for vuln in scan_results["vulnerabilities"]:
                severity = vuln.get("severity", "").lower()
                if severity == "critical":
                    metrics.critical_vulnerabilities += 1
                elif severity == "high":
                    metrics.high_vulnerabilities += 1
                elif severity == "medium":
                    metrics.medium_vulnerabilities += 1
                elif severity == "low":
                    metrics.low_vulnerabilities += 1

                metrics.vulnerabilities.append(vuln)

        # Parse check results
        if "checks" in scan_results:
            for check in scan_results["checks"]:
                if check.get("passed", False):
                    metrics.passed_checks += 1
                else:
                    metrics.failed_checks += 1

        # Calculate score
        metrics.security_score = metrics.calculate_score()

        return metrics

    def calculate_code_quality(
        self, analysis_results: Dict[str, Any]
    ) -> QualityMetrics:
        """
        Calculate code quality metrics

        Args:
            analysis_results: Static analysis results

        Returns:
            QualityMetrics object
        """
        metrics = QualityMetrics()

        # Extract metrics from analysis results
        if "complexity" in analysis_results:
            metrics.cyclomatic_complexity = analysis_results["complexity"].get(
                "average", 0
            )

        if "coverage" in analysis_results:
            metrics.test_coverage = (
                analysis_results["coverage"].get("percentage", 0) / 100
            )

        if "duplication" in analysis_results:
            metrics.code_duplication = (
                analysis_results["duplication"].get("percentage", 0) / 100
            )

        if "maintainability" in analysis_results:
            metrics.maintainability_index = analysis_results["maintainability"].get(
                "index", 0
            )

        if "statistics" in analysis_results:
            stats = analysis_results["statistics"]
            metrics.lines_of_code = stats.get("lines", 0)
            metrics.number_of_functions = stats.get("functions", 0)
            metrics.number_of_classes = stats.get("classes", 0)

        if "linting" in analysis_results:
            linting = analysis_results["linting"]
            if "score" in linting:
                metrics.linting_score = (
                    linting["score"] / 10
                )  # Assuming score out of 10
            elif "errors" in linting and "warnings" in linting:
                # Calculate score based on errors and warnings
                errors = linting.get("errors", 0)
                warnings = linting.get("warnings", 0)
                if metrics.lines_of_code > 0:
                    issues_per_line = (errors + warnings * 0.5) / metrics.lines_of_code
                    metrics.linting_score = max(0, 1 - issues_per_line)

        return metrics

    def calculate_resource_metrics(
        self, resource_data: Dict[str, Any]
    ) -> ResourceMetrics:
        """
        Calculate resource usage metrics

        Args:
            resource_data: Resource monitoring data

        Returns:
            ResourceMetrics object
        """
        metrics = ResourceMetrics()

        if "cpu" in resource_data:
            cpu_values = resource_data["cpu"]
            if isinstance(cpu_values, list) and cpu_values:
                metrics.cpu_usage_avg = statistics.mean(cpu_values)
                metrics.cpu_usage_peak = max(cpu_values)
            else:
                metrics.cpu_usage_avg = cpu_values.get("average", 0)
                metrics.cpu_usage_peak = cpu_values.get("peak", 0)

        if "memory" in resource_data:
            memory_values = resource_data["memory"]
            if isinstance(memory_values, list) and memory_values:
                metrics.memory_usage_avg = statistics.mean(memory_values)
                metrics.memory_usage_peak = max(memory_values)
            else:
                metrics.memory_usage_avg = memory_values.get("average", 0)
                metrics.memory_usage_peak = memory_values.get("peak", 0)

        if "disk_io" in resource_data:
            metrics.disk_io_read = resource_data["disk_io"].get("read", 0)
            metrics.disk_io_write = resource_data["disk_io"].get("write", 0)

        if "network_io" in resource_data:
            metrics.network_io_in = resource_data["network_io"].get("in", 0)
            metrics.network_io_out = resource_data["network_io"].get("out", 0)

        if "container" in resource_data:
            metrics.container_size = resource_data["container"].get("size", 0)

        if "timing" in resource_data:
            metrics.build_time = resource_data["timing"].get("build", 0)
            metrics.startup_time = resource_data["timing"].get("startup", 0)

        return metrics

    def aggregate_scores(
        self, metrics: Dict[str, float], weights: Dict[str, float]
    ) -> float:
        """
        Calculate weighted aggregate score

        Args:
            metrics: Dictionary of metric scores
            weights: Dictionary of metric weights

        Returns:
            Weighted average score (0.0 to 1.0)
        """
        if not metrics or not weights:
            return 0.0

        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0

        weighted_sum = 0.0
        for metric_name, score in metrics.items():
            weight = weights.get(metric_name, 0)
            weighted_sum += score * weight

        return weighted_sum / total_weight

    def run_performance_test(
        self, service_url: str, test_config: Dict[str, Any]
    ) -> PerformanceMetrics:
        """
        Run performance test against service

        Args:
            service_url: URL of the service to test
            test_config: Test configuration

        Returns:
            PerformanceMetrics object
        """
        tool = test_config.get("tool", "locust")

        if tool == "locust":
            return self._run_locust_test(service_url, test_config)
        elif tool == "ab":
            return self._run_ab_test(service_url, test_config)
        elif tool == "wrk":
            return self._run_wrk_test(service_url, test_config)
        else:
            logger.warning(f"Unknown performance test tool: {tool}")
            return PerformanceMetrics()

    def run_security_scan(
        self, target_path: Path, scan_config: Dict[str, Any]
    ) -> SecurityMetrics:
        """
        Run security scan on code/container

        Args:
            target_path: Path to scan
            scan_config: Scan configuration

        Returns:
            SecurityMetrics object
        """
        tool = scan_config.get("tool", "bandit")

        if tool == "bandit" and target_path.suffix == ".py":
            return self._run_bandit_scan(target_path, scan_config)
        elif tool == "trivy":
            return self._run_trivy_scan(target_path, scan_config)
        elif tool == "safety":
            return self._run_safety_scan(target_path, scan_config)
        else:
            logger.warning(f"Unknown security scan tool: {tool}")
            return SecurityMetrics()

    def run_code_analysis(
        self, code_path: Path, analysis_config: Dict[str, Any]
    ) -> QualityMetrics:
        """
        Run static code analysis

        Args:
            code_path: Path to code
            analysis_config: Analysis configuration

        Returns:
            QualityMetrics object
        """
        language = self._detect_language(code_path)

        if language == "python":
            return self._analyze_python_code(code_path, analysis_config)
        elif language == "javascript":
            return self._analyze_javascript_code(code_path, analysis_config)
        elif language == "go":
            return self._analyze_go_code(code_path, analysis_config)
        else:
            logger.warning(f"Code analysis not implemented for: {language}")
            return QualityMetrics()

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1

        if upper >= len(sorted_values):
            return sorted_values[lower]

        weight = index - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight

    def _run_locust_test(
        self, service_url: str, config: Dict[str, Any]
    ) -> PerformanceMetrics:
        """Run Locust performance test"""
        metrics = PerformanceMetrics()

        try:
            # Create locustfile
            locustfile = self._create_locustfile(service_url, config)

            # Run Locust
            users = config.get("users", 10)
            duration = config.get("duration", 60)
            spawn_rate = config.get("spawn_rate", 1)

            cmd = [
                "locust",
                "-f",
                locustfile,
                "--headless",
                "--users",
                str(users),
                "--spawn-rate",
                str(spawn_rate),
                "--run-time",
                f"{duration}s",
                "--csv",
                "locust_results",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=duration + 30
            )

            # Parse results
            if result.returncode == 0:
                metrics = self._parse_locust_results("locust_results_stats.csv")

        except Exception as e:
            logger.error(f"Locust test failed: {str(e)}")

        return metrics

    def _run_ab_test(
        self, service_url: str, config: Dict[str, Any]
    ) -> PerformanceMetrics:
        """Run Apache Bench test"""
        metrics = PerformanceMetrics()

        try:
            requests = config.get("requests", 1000)
            concurrency = config.get("concurrency", 10)

            cmd = ["ab", "-n", str(requests), "-c", str(concurrency), service_url]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                metrics = self._parse_ab_output(result.stdout)

        except Exception as e:
            logger.error(f"AB test failed: {str(e)}")

        return metrics

    def _run_wrk_test(
        self, service_url: str, config: Dict[str, Any]
    ) -> PerformanceMetrics:
        """Run wrk performance test"""
        metrics = PerformanceMetrics()

        try:
            threads = config.get("threads", 2)
            connections = config.get("connections", 10)
            duration = config.get("duration", 30)

            cmd = [
                "wrk",
                "-t",
                str(threads),
                "-c",
                str(connections),
                "-d",
                f"{duration}s",
                "--latency",
                service_url,
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=duration + 10
            )

            if result.returncode == 0:
                metrics = self._parse_wrk_output(result.stdout)

        except Exception as e:
            logger.error(f"wrk test failed: {str(e)}")

        return metrics

    def _run_bandit_scan(
        self, target_path: Path, config: Dict[str, Any]
    ) -> SecurityMetrics:
        """Run Bandit security scan for Python"""
        metrics = SecurityMetrics()

        try:
            cmd = ["bandit", "-r", str(target_path), "-f", "json"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode in [0, 1]:  # Bandit returns 1 if issues found
                data = json.loads(result.stdout)

                for issue in data.get("results", []):
                    severity = issue.get("issue_severity", "").lower()
                    if severity == "high":
                        metrics.high_vulnerabilities += 1
                    elif severity == "medium":
                        metrics.medium_vulnerabilities += 1
                    elif severity == "low":
                        metrics.low_vulnerabilities += 1

                    metrics.vulnerabilities.append(
                        {
                            "type": "bandit",
                            "severity": severity,
                            "message": issue.get("issue_text", ""),
                            "file": issue.get("filename", ""),
                            "line": issue.get("line_number", 0),
                        }
                    )

                metrics.security_score = metrics.calculate_score()

        except Exception as e:
            logger.error(f"Bandit scan failed: {str(e)}")

        return metrics

    def _run_trivy_scan(
        self, target_path: Path, config: Dict[str, Any]
    ) -> SecurityMetrics:
        """Run Trivy container/code scan"""
        metrics = SecurityMetrics()

        try:
            scan_type = config.get("scan_type", "fs")
            cmd = ["trivy", scan_type, "--format", "json", str(target_path)]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                data = json.loads(result.stdout)

                for result_item in data.get("Results", []):
                    for vuln in result_item.get("Vulnerabilities", []):
                        severity = vuln.get("Severity", "").upper()
                        if severity == "CRITICAL":
                            metrics.critical_vulnerabilities += 1
                        elif severity == "HIGH":
                            metrics.high_vulnerabilities += 1
                        elif severity == "MEDIUM":
                            metrics.medium_vulnerabilities += 1
                        elif severity == "LOW":
                            metrics.low_vulnerabilities += 1

                        metrics.vulnerabilities.append(
                            {
                                "type": "trivy",
                                "severity": severity,
                                "id": vuln.get("VulnerabilityID", ""),
                                "package": vuln.get("PkgName", ""),
                                "title": vuln.get("Title", ""),
                            }
                        )

                metrics.security_score = metrics.calculate_score()

        except Exception as e:
            logger.error(f"Trivy scan failed: {str(e)}")

        return metrics

    def _run_safety_scan(
        self, target_path: Path, config: Dict[str, Any]
    ) -> SecurityMetrics:
        """Run Safety dependency scan for Python"""
        metrics = SecurityMetrics()

        try:
            requirements_file = target_path / "requirements.txt"
            if not requirements_file.exists():
                return metrics

            cmd = ["safety", "check", "--file", str(requirements_file), "--json"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.stdout:
                data = json.loads(result.stdout)

                for vuln in data:
                    metrics.high_vulnerabilities += 1
                    metrics.vulnerabilities.append(
                        {
                            "type": "safety",
                            "severity": "high",
                            "package": vuln.get("package", ""),
                            "vulnerability": vuln.get("vulnerability", ""),
                            "affected_versions": vuln.get("affected_versions", ""),
                        }
                    )

                metrics.security_score = metrics.calculate_score()

        except Exception as e:
            logger.error(f"Safety scan failed: {str(e)}")

        return metrics

    def _analyze_python_code(
        self, code_path: Path, config: Dict[str, Any]
    ) -> QualityMetrics:
        """Analyze Python code quality"""
        metrics = QualityMetrics()

        try:
            # Run pylint
            cmd = ["pylint", str(code_path), "--output-format=json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.stdout:
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    errors = sum(1 for m in data if m.get("type") == "error")
                    warnings = sum(1 for m in data if m.get("type") == "warning")

                    # Count lines of code
                    lines = 0
                    for py_file in code_path.rglob("*.py"):
                        with open(py_file, "r") as f:
                            lines += len(f.readlines())

                    metrics.lines_of_code = lines

                    if lines > 0:
                        issues_per_line = (errors + warnings * 0.5) / lines
                        metrics.linting_score = max(0, min(1, 1 - issues_per_line))

            # Run coverage if available
            if (code_path / ".coverage").exists():
                cmd = ["coverage", "report", "--format=json"]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, cwd=code_path, timeout=30
                )

                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    metrics.test_coverage = (
                        data.get("totals", {}).get("percent_covered", 0) / 100
                    )

        except Exception as e:
            logger.error(f"Python code analysis failed: {str(e)}")

        return metrics

    def _analyze_javascript_code(
        self, code_path: Path, config: Dict[str, Any]
    ) -> QualityMetrics:
        """Analyze JavaScript code quality"""
        metrics = QualityMetrics()

        try:
            # Run ESLint
            cmd = ["eslint", str(code_path), "--format=json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.stdout:
                data = json.loads(result.stdout)
                total_errors = sum(r.get("errorCount", 0) for r in data)
                total_warnings = sum(r.get("warningCount", 0) for r in data)

                # Count lines
                lines = 0
                for js_file in code_path.rglob("*.js"):
                    with open(js_file, "r") as f:
                        lines += len(f.readlines())

                metrics.lines_of_code = lines

                if lines > 0:
                    issues_per_line = (total_errors + total_warnings * 0.5) / lines
                    metrics.linting_score = max(0, min(1, 1 - issues_per_line))

        except Exception as e:
            logger.error(f"JavaScript code analysis failed: {str(e)}")

        return metrics

    def _analyze_go_code(
        self, code_path: Path, config: Dict[str, Any]
    ) -> QualityMetrics:
        """Analyze Go code quality"""
        metrics = QualityMetrics()

        try:
            # Run go vet
            cmd = ["go", "vet", "./..."]
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=code_path, timeout=60
            )

            # Count issues
            issues = len(result.stderr.split("\n")) if result.stderr else 0

            # Count lines
            lines = 0
            for go_file in code_path.rglob("*.go"):
                with open(go_file, "r") as f:
                    lines += len(f.readlines())

            metrics.lines_of_code = lines

            if lines > 0:
                metrics.linting_score = max(0, min(1, 1 - issues / lines))

        except Exception as e:
            logger.error(f"Go code analysis failed: {str(e)}")

        return metrics

    def _detect_language(self, path: Path) -> str:
        """Detect programming language"""
        if list(path.rglob("*.py")):
            return "python"
        elif list(path.rglob("*.js")) or list(path.rglob("*.ts")):
            return "javascript"
        elif list(path.rglob("*.go")):
            return "go"
        elif list(path.rglob("*.java")):
            return "java"
        elif list(path.rglob("*.rs")):
            return "rust"
        else:
            return "unknown"

    def _create_locustfile(self, service_url: str, config: Dict[str, Any]) -> str:
        """Create Locust test file"""
        endpoints = config.get("endpoints", ["/"])

        locustfile_content = f"""
from locust import HttpUser, task, between

class BenchmarkUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def test_endpoints(self):
        endpoints = {endpoints}
        for endpoint in endpoints:
            self.client.get(endpoint)
"""

        filename = "locustfile_temp.py"
        with open(filename, "w") as f:
            f.write(locustfile_content)

        return filename

    def _parse_locust_results(self, csv_file: str) -> PerformanceMetrics:
        """Parse Locust CSV results"""
        metrics = PerformanceMetrics()

        try:
            import csv

            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Name") == "Aggregated":
                        metrics.total_requests = int(row.get("Request Count", 0))
                        metrics.failed_requests = int(row.get("Failure Count", 0))
                        metrics.avg_response_time = float(
                            row.get("Average Response Time", 0)
                        )
                        metrics.min_response_time = float(
                            row.get("Min Response Time", 0)
                        )
                        metrics.max_response_time = float(
                            row.get("Max Response Time", 0)
                        )
                        metrics.response_time_p50 = float(row.get("50%", 0))
                        metrics.response_time_p95 = float(row.get("95%", 0))
                        metrics.response_time_p99 = float(row.get("99%", 0))
                        metrics.requests_per_second = float(row.get("Requests/s", 0))

                        if metrics.total_requests > 0:
                            metrics.error_rate = (
                                metrics.failed_requests / metrics.total_requests
                            )
                            metrics.successful_requests = (
                                metrics.total_requests - metrics.failed_requests
                            )

        except Exception as e:
            logger.error(f"Failed to parse Locust results: {str(e)}")

        return metrics

    def _parse_ab_output(self, output: str) -> PerformanceMetrics:
        """Parse Apache Bench output"""
        metrics = PerformanceMetrics()

        try:
            lines = output.split("\n")
            for line in lines:
                if "Requests per second:" in line:
                    metrics.requests_per_second = float(
                        line.split(":")[1].split("[")[0].strip()
                    )
                elif "Time per request:" in line and "mean" in line:
                    metrics.avg_response_time = float(
                        line.split(":")[1].split("[")[0].strip()
                    )
                elif "Complete requests:" in line:
                    metrics.successful_requests = int(line.split(":")[1].strip())
                elif "Failed requests:" in line:
                    metrics.failed_requests = int(line.split(":")[1].strip())

            metrics.total_requests = (
                metrics.successful_requests + metrics.failed_requests
            )
            if metrics.total_requests > 0:
                metrics.error_rate = metrics.failed_requests / metrics.total_requests

        except Exception as e:
            logger.error(f"Failed to parse AB output: {str(e)}")

        return metrics

    def _parse_wrk_output(self, output: str) -> PerformanceMetrics:
        """Parse wrk output"""
        metrics = PerformanceMetrics()

        try:
            lines = output.split("\n")
            for line in lines:
                if "Requests/sec:" in line:
                    metrics.requests_per_second = float(line.split(":")[1].strip())
                elif "Latency" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        # Parse avg latency (convert to ms if needed)
                        avg_str = parts[1]
                        if avg_str.endswith("ms"):
                            metrics.avg_response_time = float(avg_str[:-2])
                        elif avg_str.endswith("s"):
                            metrics.avg_response_time = float(avg_str[:-1]) * 1000
                elif "requests in" in line:
                    # Extract total requests
                    parts = line.split()
                    metrics.total_requests = int(parts[0])
                elif "Socket errors:" in line:
                    # Parse errors
                    parts = line.split(",")
                    for part in parts:
                        if "timeout" in part:
                            count = int("".join(filter(str.isdigit, part)))
                            metrics.failed_requests += count

            metrics.successful_requests = (
                metrics.total_requests - metrics.failed_requests
            )
            if metrics.total_requests > 0:
                metrics.error_rate = metrics.failed_requests / metrics.total_requests

        except Exception as e:
            logger.error(f"Failed to parse wrk output: {str(e)}")

        return metrics
