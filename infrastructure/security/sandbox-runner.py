#!/usr/bin/env python3
"""
Sandbox runner for secure code execution in Req2Run benchmark.
Supports both nsjail and firejail as sandbox backends.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import time


class SandboxRunner:
    """Manages sandboxed execution of benchmark submissions."""
    
    def __init__(self, backend: str = "auto"):
        """
        Initialize sandbox runner.
        
        Args:
            backend: Sandbox backend - "nsjail", "firejail", or "auto"
        """
        self.backend = self._detect_backend(backend)
        self.config_dir = Path(__file__).parent
        
    def _detect_backend(self, preference: str) -> str:
        """Detect available sandbox backend."""
        if preference != "auto":
            return preference
            
        # Check for nsjail
        if shutil.which("nsjail"):
            return "nsjail"
        
        # Check for firejail
        if shutil.which("firejail"):
            return "firejail"
            
        raise RuntimeError("No sandbox backend found. Install nsjail or firejail.")
    
    def prepare_environment(self, submission_path: Path, problem_id: str) -> Path:
        """
        Prepare sandboxed environment for execution.
        
        Args:
            submission_path: Path to submission code
            problem_id: Problem identifier
            
        Returns:
            Path to prepared sandbox directory
        """
        # Create temporary sandbox directory
        sandbox_dir = Path(tempfile.mkdtemp(prefix=f"req2run_{problem_id}_"))
        
        # Copy submission code
        app_dir = sandbox_dir / "app"
        if submission_path.is_dir():
            shutil.copytree(submission_path, app_dir)
        else:
            app_dir.mkdir(parents=True)
            shutil.copy2(submission_path, app_dir)
        
        # Set permissions
        os.chmod(app_dir, 0o755)
        for root, dirs, files in os.walk(app_dir):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o755)
            for f in files:
                os.chmod(os.path.join(root, f), 0o644)
        
        return sandbox_dir
    
    def run_nsjail(
        self, 
        command: str, 
        sandbox_dir: Path,
        timeout: int = 300,
        memory_limit: int = 2048,
        cpu_limit: int = 2
    ) -> Tuple[int, str, str]:
        """
        Run command in nsjail sandbox.
        
        Args:
            command: Command to execute
            sandbox_dir: Sandbox directory
            timeout: Execution timeout in seconds
            memory_limit: Memory limit in MB
            cpu_limit: CPU core limit
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        config_file = self.config_dir / "nsjail.cfg"
        
        nsjail_cmd = [
            "nsjail",
            "--config", str(config_file),
            "--bindmount", f"{sandbox_dir}/app:/app",
            "--time_limit", str(timeout),
            "--rlimit_as", str(memory_limit),
            "--max_cpus", str(cpu_limit),
            "--",
            "/bin/bash", "-c", command
        ]
        
        try:
            result = subprocess.run(
                nsjail_cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 10  # Grace period
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Execution timeout exceeded"
        except Exception as e:
            return -1, "", str(e)
    
    def run_firejail(
        self,
        command: str,
        sandbox_dir: Path,
        timeout: int = 300,
        memory_limit: int = 2048,
        cpu_limit: int = 2
    ) -> Tuple[int, str, str]:
        """
        Run command in firejail sandbox.
        
        Args:
            command: Command to execute
            sandbox_dir: Sandbox directory
            timeout: Execution timeout in seconds
            memory_limit: Memory limit in MB
            cpu_limit: CPU core limit
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        profile_file = self.config_dir / "firejail.profile"
        
        firejail_cmd = [
            "firejail",
            f"--profile={profile_file}",
            "--quiet",
            f"--timeout={timeout}",
            f"--rlimit-as={memory_limit}m",
            f"--cpu={cpu_limit}",
            f"--private={sandbox_dir}/app",
            "--",
            "/bin/bash", "-c", command
        ]
        
        try:
            result = subprocess.run(
                firejail_cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 10
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Execution timeout exceeded"
        except Exception as e:
            return -1, "", str(e)
    
    def execute(
        self,
        command: str,
        submission_path: Path,
        problem_id: str,
        timeout: int = 300,
        memory_limit: int = 2048,
        cpu_limit: int = 2
    ) -> Dict[str, Any]:
        """
        Execute command in sandbox.
        
        Args:
            command: Command to execute
            submission_path: Path to submission code
            problem_id: Problem identifier
            timeout: Execution timeout in seconds
            memory_limit: Memory limit in MB
            cpu_limit: CPU core limit
            
        Returns:
            Execution result dictionary
        """
        start_time = time.time()
        
        # Prepare sandbox environment
        sandbox_dir = self.prepare_environment(submission_path, problem_id)
        
        try:
            # Execute in sandbox
            if self.backend == "nsjail":
                returncode, stdout, stderr = self.run_nsjail(
                    command, sandbox_dir, timeout, memory_limit, cpu_limit
                )
            elif self.backend == "firejail":
                returncode, stdout, stderr = self.run_firejail(
                    command, sandbox_dir, timeout, memory_limit, cpu_limit
                )
            else:
                raise ValueError(f"Unknown backend: {self.backend}")
            
            execution_time = time.time() - start_time
            
            return {
                "success": returncode == 0,
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
                "execution_time": execution_time,
                "backend": self.backend,
                "limits": {
                    "timeout": timeout,
                    "memory_mb": memory_limit,
                    "cpu_cores": cpu_limit
                }
            }
            
        finally:
            # Cleanup sandbox directory
            if sandbox_dir.exists():
                shutil.rmtree(sandbox_dir, ignore_errors=True)
    
    def validate_submission(self, submission_path: Path) -> bool:
        """
        Validate submission before execution.
        
        Args:
            submission_path: Path to submission
            
        Returns:
            True if valid, False otherwise
        """
        if not submission_path.exists():
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            "__import__",
            "eval(",
            "exec(",
            "compile(",
            "open('/etc",
            "open('/proc",
            "subprocess",
            "os.system",
            "socket."
        ]
        
        if submission_path.is_file():
            files = [submission_path]
        else:
            files = list(submission_path.rglob("*.py")) + \
                   list(submission_path.rglob("*.js")) + \
                   list(submission_path.rglob("*.go"))
        
        for file_path in files:
            try:
                content = file_path.read_text()
                for pattern in suspicious_patterns:
                    if pattern in content:
                        print(f"Warning: Suspicious pattern '{pattern}' found in {file_path}")
                        # Don't reject, just warn
            except Exception:
                pass
        
        return True


def main():
    """CLI interface for sandbox runner."""
    parser = argparse.ArgumentParser(description="Req2Run Sandbox Runner")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("submission", help="Path to submission code")
    parser.add_argument("--problem", default="test", help="Problem ID")
    parser.add_argument("--backend", choices=["nsjail", "firejail", "auto"],
                       default="auto", help="Sandbox backend")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Execution timeout in seconds")
    parser.add_argument("--memory", type=int, default=2048,
                       help="Memory limit in MB")
    parser.add_argument("--cpu", type=int, default=2,
                       help="CPU core limit")
    parser.add_argument("--json", action="store_true",
                       help="Output in JSON format")
    
    args = parser.parse_args()
    
    # Create runner
    runner = SandboxRunner(backend=args.backend)
    
    # Validate submission
    submission_path = Path(args.submission)
    if not runner.validate_submission(submission_path):
        print("Invalid submission", file=sys.stderr)
        sys.exit(1)
    
    # Execute
    result = runner.execute(
        args.command,
        submission_path,
        args.problem,
        timeout=args.timeout,
        memory_limit=args.memory,
        cpu_limit=args.cpu
    )
    
    # Output result
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print("Execution successful")
        else:
            print(f"Execution failed with code {result['returncode']}")
        
        if result["stdout"]:
            print("\nSTDOUT:")
            print(result["stdout"])
        
        if result["stderr"]:
            print("\nSTDERR:")
            print(result["stderr"])
        
        print(f"\nExecution time: {result['execution_time']:.2f}s")
        print(f"Backend: {result['backend']}")
    
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()