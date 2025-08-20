#!/usr/bin/env python3
"""
Tests for the UFAI Bench CLI tool
"""

import os
import json
import yaml
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the bench module (assuming it's structured as a module)
import importlib.util
spec = importlib.util.spec_from_file_location("bench", "../bench")
bench_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench_module)

BenchmarkRunner = bench_module.BenchmarkRunner


class TestBenchmarkRunner(unittest.TestCase):
    """Test cases for BenchmarkRunner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "bench.yaml")
        self.create_test_config()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_config(self):
        """Create a test bench.yaml configuration."""
        config = {
            "version": "1.0",
            "framework": {
                "name": "TestFramework",
                "language": "python",
                "version": "1.0.0"
            },
            "commands": {
                "build": "echo 'Building...'",
                "test": "echo 'Testing...'",
                "performance": {
                    "script": "echo 'Performance testing...'",
                    "endpoint": "http://localhost:8000",
                    "duration": 60
                },
                "security": "echo 'Security scanning...'"
            },
            "compliance": {
                "level": "L2",
                "features": ["build", "test", "performance"]
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f)
    
    def test_load_config(self):
        """Test configuration loading."""
        runner = BenchmarkRunner(self.config_file)
        
        self.assertIsNotNone(runner.config)
        self.assertEqual(runner.config["version"], "1.0")
        self.assertEqual(runner.config["framework"]["name"], "TestFramework")
    
    def test_load_config_file_not_found(self):
        """Test configuration loading with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            BenchmarkRunner("non_existent.yaml")
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Success output",
            stderr=""
        )
        
        runner = BenchmarkRunner(self.config_file)
        result = runner.run_command("echo 'test'", "test")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("stdout", result)
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test failed command execution."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error output"
        )
        
        runner = BenchmarkRunner(self.config_file)
        result = runner.run_command("false", "test")
        
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["exit_code"], 1)
    
    @patch('subprocess.run')
    def test_run_command_timeout(self, mock_run):
        """Test command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)
        
        runner = BenchmarkRunner(self.config_file)
        result = runner.run_command({"script": "sleep 10", "timeout": 5}, "test")
        
        self.assertEqual(result["status"], "timeout")
    
    @patch.object(BenchmarkRunner, 'run_command')
    def test_run_build(self, mock_run):
        """Test build stage execution."""
        mock_run.return_value = {
            "status": "success",
            "duration": 10,
            "exit_code": 0
        }
        
        runner = BenchmarkRunner(self.config_file)
        success = runner.run_build()
        
        self.assertTrue(success)
        self.assertIn("build", runner.results["stages"])
    
    @patch.object(BenchmarkRunner, 'run_command')
    def test_run_test(self, mock_run):
        """Test test stage execution."""
        mock_run.return_value = {
            "status": "success",
            "duration": 20,
            "exit_code": 0,
            "stdout": "10 passed"
        }
        
        runner = BenchmarkRunner(self.config_file)
        success = runner.run_test()
        
        self.assertTrue(success)
        self.assertIn("test", runner.results["stages"])
    
    @patch.object(BenchmarkRunner, 'run_command')
    def test_run_performance(self, mock_run):
        """Test performance stage execution."""
        mock_run.return_value = {
            "status": "success",
            "duration": 60,
            "exit_code": 0,
            "stdout": "1000 req/s"
        }
        
        runner = BenchmarkRunner(self.config_file)
        success = runner.run_performance()
        
        self.assertTrue(success)
        self.assertIn("performance", runner.results["stages"])
    
    @patch.object(BenchmarkRunner, 'run_command')
    def test_run_security(self, mock_run):
        """Test security stage execution."""
        mock_run.return_value = {
            "status": "success",
            "duration": 30,
            "exit_code": 0,
            "stdout": "critical: 0"
        }
        
        runner = BenchmarkRunner(self.config_file)
        success = runner.run_security()
        
        self.assertTrue(success)
        self.assertIn("security", runner.results["stages"])
    
    @patch.object(BenchmarkRunner, 'run_build')
    @patch.object(BenchmarkRunner, 'run_test')
    @patch.object(BenchmarkRunner, 'run_performance')
    @patch.object(BenchmarkRunner, 'run_security')
    def test_run_all(self, mock_security, mock_perf, mock_test, mock_build):
        """Test running all stages."""
        mock_build.return_value = True
        mock_test.return_value = True
        mock_perf.return_value = True
        mock_security.return_value = True
        
        runner = BenchmarkRunner(self.config_file)
        success = runner.run_all()
        
        self.assertTrue(success)
        self.assertEqual(runner.results["overall"]["score"], 100.0)
    
    def test_parse_test_metrics(self):
        """Test parsing test metrics from output."""
        runner = BenchmarkRunner(self.config_file)
        
        output = "====== 25 passed, 2 failed ======"
        metrics = runner._parse_test_metrics(output)
        
        self.assertEqual(metrics.get("passed"), 25)
        
        output = "Coverage: 85%"
        metrics = runner._parse_test_metrics(output)
        self.assertEqual(metrics.get("coverage"), 85)
    
    def test_parse_performance_metrics(self):
        """Test parsing performance metrics from output."""
        runner = BenchmarkRunner(self.config_file)
        
        output = "Requests per second: 5420.5 req/s"
        metrics = runner._parse_performance_metrics(output)
        self.assertEqual(metrics.get("requests_per_second"), 5420.5)
        
        output = "p50 latency: 15.2ms"
        metrics = runner._parse_performance_metrics(output)
        self.assertEqual(metrics.get("latency_p50"), 15.2)
    
    def test_parse_security_metrics(self):
        """Test parsing security metrics from output."""
        runner = BenchmarkRunner(self.config_file)
        
        output = "Critical: 0, High: 2, Medium: 5, Low: 10"
        metrics = runner._parse_security_metrics(output)
        
        self.assertEqual(metrics["vulnerabilities"]["critical"], 0)
        self.assertEqual(metrics["vulnerabilities"]["high"], 2)
        self.assertEqual(metrics["vulnerabilities"]["medium"], 5)
        self.assertEqual(metrics["vulnerabilities"]["low"], 10)
    
    def test_calculate_grade(self):
        """Test grade calculation from score."""
        runner = BenchmarkRunner(self.config_file)
        
        self.assertEqual(runner._calculate_grade(95), "A+")
        self.assertEqual(runner._calculate_grade(92), "A")
        self.assertEqual(runner._calculate_grade(85), "B+")
        self.assertEqual(runner._calculate_grade(80), "B")
        self.assertEqual(runner._calculate_grade(75), "C+")
        self.assertEqual(runner._calculate_grade(70), "C")
        self.assertEqual(runner._calculate_grade(60), "D")
        self.assertEqual(runner._calculate_grade(50), "F")
    
    def test_save_results(self):
        """Test saving results to JSON file."""
        runner = BenchmarkRunner(self.config_file)
        runner.results["overall"]["score"] = 85.5
        
        output_file = os.path.join(self.temp_dir, "results.json")
        runner.save_results(output_file)
        
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r') as f:
            saved_results = json.load(f)
        
        self.assertEqual(saved_results["overall"]["score"], 85.5)
    
    @patch('builtins.print')
    def test_generate_report_text(self, mock_print):
        """Test text report generation."""
        runner = BenchmarkRunner(self.config_file)
        runner.results["stages"]["build"] = {
            "status": "success",
            "duration": 10
        }
        runner.results["overall"]["score"] = 90
        runner.results["overall"]["grade"] = "A"
        
        runner.generate_report("text")
        
        # Verify print was called
        self.assertTrue(mock_print.called)


class TestBenchCLI(unittest.TestCase):
    """Test cases for CLI interface."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.bench_script = os.path.join(
            os.path.dirname(__file__), "..", "bench"
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_cli_version(self):
        """Test version command."""
        result = subprocess.run(
            [sys.executable, self.bench_script, "version"],
            capture_output=True,
            text=True
        )
        
        self.assertIn("bench version", result.stdout)
    
    def test_cli_init(self):
        """Test init command."""
        original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            result = subprocess.run(
                [sys.executable, self.bench_script, "init"],
                capture_output=True,
                text=True
            )
            
            self.assertEqual(result.returncode, 0)
            self.assertTrue(os.path.exists("bench.yaml"))
            
            with open("bench.yaml", 'r') as f:
                config = yaml.safe_load(f)
            
            self.assertEqual(config["version"], "1.0")
        finally:
            os.chdir(original_dir)
    
    def test_cli_validate(self):
        """Test validate command."""
        # Create a valid config
        config_file = os.path.join(self.temp_dir, "bench.yaml")
        config = {
            "version": "1.0",
            "framework": {"name": "Test", "language": "python"},
            "commands": {"build": "echo test"}
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        result = subprocess.run(
            [sys.executable, self.bench_script, "validate", "-c", config_file],
            capture_output=True,
            text=True
        )
        
        self.assertIn("Configuration is valid", result.stdout)


class TestCompliance(unittest.TestCase):
    """Test cases for compliance level determination."""
    
    def test_l0_compliance(self):
        """Test L0 compliance requirements."""
        results = {
            "stages": {
                "build": {"status": "success"}
            },
            "compliance": {
                "features": ["build"]
            },
            "overall": {"score": 40}
        }
        
        # This would be part of the compliance module
        level = self.determine_compliance_level(results)
        self.assertEqual(level, "L0")
    
    def test_l1_compliance(self):
        """Test L1 compliance requirements."""
        results = {
            "stages": {
                "build": {"status": "success"},
                "test": {"status": "success", "metrics": {"pass_rate": 85}}
            },
            "compliance": {
                "features": ["build", "test"]
            },
            "overall": {"score": 55}
        }
        
        level = self.determine_compliance_level(results)
        self.assertEqual(level, "L1")
    
    def determine_compliance_level(self, results):
        """Simplified compliance level determination for testing."""
        features = results["compliance"]["features"]
        score = results["overall"]["score"]
        
        if score >= 90 and len(features) >= 6:
            return "L5"
        elif "coverage" in features and score >= 80:
            return "L4"
        elif "security" in features and score >= 70:
            return "L3"
        elif "performance" in features and score >= 60:
            return "L2"
        elif "test" in features and score >= 50:
            return "L1"
        elif "build" in features:
            return "L0"
        return None


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete benchmark flow."""
    
    @patch('subprocess.run')
    def test_complete_benchmark_flow(self, mock_run):
        """Test a complete benchmark execution flow."""
        # Mock successful command executions
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Success",
            stderr=""
        )
        
        # Create config
        temp_dir = tempfile.mkdtemp()
        config_file = os.path.join(temp_dir, "bench.yaml")
        
        config = {
            "version": "1.0",
            "framework": {
                "name": "IntegrationTest",
                "language": "python"
            },
            "commands": {
                "build": "echo build",
                "test": "echo test",
                "performance": "echo perf",
                "security": "echo sec"
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        try:
            # Run benchmark
            runner = BenchmarkRunner(config_file)
            success = runner.run_all()
            
            self.assertTrue(success)
            self.assertIn("build", runner.results["stages"])
            self.assertIn("test", runner.results["stages"])
            self.assertIn("performance", runner.results["stages"])
            self.assertIn("security", runner.results["stages"])
            self.assertIn("score", runner.results["overall"])
            self.assertIn("grade", runner.results["overall"])
            
            # Save results
            results_file = os.path.join(temp_dir, "results.json")
            runner.save_results(results_file)
            self.assertTrue(os.path.exists(results_file))
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()