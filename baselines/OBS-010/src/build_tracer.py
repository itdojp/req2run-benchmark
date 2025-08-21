"""Build process tracing instrumentation"""
import os
import subprocess
import sys
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from tracing import get_tracer, trace_operation, trace_span, add_span_attribute, add_span_event
import structlog

logger = structlog.get_logger()


class BuildTracer:
    """Instruments build operations with OpenTelemetry spans"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.tracer = get_tracer("build-tracer")
    
    @trace_operation("build.execute")
    def execute_build(self, build_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute complete build process with tracing"""
        start_time = time.time()
        
        add_span_attribute("build.project_path", str(self.project_path))
        add_span_attribute("build.steps_count", len(build_steps))
        add_span_event("build.started")
        
        results = {
            "success": True,
            "steps": [],
            "total_duration": 0,
            "failed_step": None
        }
        
        for i, step in enumerate(build_steps):
            step_name = step.get("name", f"step_{i}")
            
            with trace_span(f"build.step.{step_name}") as span:
                span.set_attribute("build.step.index", i)
                span.set_attribute("build.step.name", step_name)
                span.set_attribute("build.step.type", step.get("type", "command"))
                
                step_result = self._execute_build_step(step)
                results["steps"].append(step_result)
                
                if not step_result["success"]:
                    results["success"] = False
                    results["failed_step"] = step_name
                    span.set_attribute("build.step.failed", True)
                    break
                else:
                    span.set_attribute("build.step.success", True)
        
        end_time = time.time()
        results["total_duration"] = end_time - start_time
        
        add_span_attribute("build.success", results["success"])
        add_span_attribute("build.duration", results["total_duration"])
        add_span_event("build.completed", {
            "success": results["success"],
            "duration": results["total_duration"]
        })
        
        return results
    
    def _execute_build_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual build step"""
        step_type = step.get("type", "command")
        step_name = step.get("name", "unnamed_step")
        
        add_span_attribute("build.step.command", step.get("command", ""))
        add_span_attribute("build.step.working_directory", step.get("cwd", str(self.project_path)))
        
        step_start = time.time()
        
        try:
            if step_type == "command":
                result = self._execute_command_step(step)
            elif step_type == "python":
                result = self._execute_python_step(step)
            elif step_type == "npm":
                result = self._execute_npm_step(step)
            elif step_type == "docker":
                result = self._execute_docker_step(step)
            else:
                raise ValueError(f"Unknown step type: {step_type}")
            
            step_end = time.time()
            result["duration"] = step_end - step_start
            
            add_span_attribute("build.step.exit_code", result.get("exit_code", 0))
            add_span_attribute("build.step.duration", result["duration"])
            
            return result
            
        except Exception as e:
            step_end = time.time()
            
            add_span_attribute("build.step.error", str(e))
            add_span_attribute("build.step.duration", step_end - step_start)
            
            return {
                "success": False,
                "error": str(e),
                "duration": step_end - step_start,
                "step_name": step_name
            }
    
    def _execute_command_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute shell command step"""
        command = step["command"]
        cwd = step.get("cwd", self.project_path)
        env = step.get("env", {})
        timeout = step.get("timeout", 300)  # 5 minutes default
        
        # Merge environment variables
        process_env = os.environ.copy()
        process_env.update(env)
        
        add_span_event("build.step.command.started", {"command": command})
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                env=process_env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            
            add_span_event("build.step.command.completed", {
                "exit_code": result.returncode,
                "success": success
            })
            
            return {
                "success": success,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
            
        except subprocess.TimeoutExpired:
            add_span_event("build.step.command.timeout", {"timeout": timeout})
            raise Exception(f"Command timed out after {timeout} seconds")
        
        except Exception as e:
            add_span_event("build.step.command.error", {"error": str(e)})
            raise
    
    def _execute_python_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python script/module step"""
        script = step.get("script")
        module = step.get("module")
        args = step.get("args", [])
        
        if script:
            command = f"{sys.executable} {script}"
        elif module:
            command = f"{sys.executable} -m {module}"
        else:
            raise ValueError("Python step must specify 'script' or 'module'")
        
        if args:
            command += " " + " ".join(args)
        
        # Use command execution
        return self._execute_command_step({
            "command": command,
            "cwd": step.get("cwd", self.project_path),
            "env": step.get("env", {}),
            "timeout": step.get("timeout", 300)
        })
    
    def _execute_npm_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute npm command step"""
        npm_command = step.get("npm_command", "install")
        args = step.get("args", [])
        
        command = f"npm {npm_command}"
        if args:
            command += " " + " ".join(args)
        
        return self._execute_command_step({
            "command": command,
            "cwd": step.get("cwd", self.project_path),
            "env": step.get("env", {}),
            "timeout": step.get("timeout", 600)  # npm can be slow
        })
    
    def _execute_docker_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Docker command step"""
        docker_command = step.get("docker_command", "build")
        args = step.get("args", [])
        
        command = f"docker {docker_command}"
        if args:
            command += " " + " ".join(args)
        
        return self._execute_command_step({
            "command": command,
            "cwd": step.get("cwd", self.project_path),
            "env": step.get("env", {}),
            "timeout": step.get("timeout", 1800)  # Docker can be very slow
        })
    
    @trace_operation("build.dependency_analysis")
    def analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies with tracing"""
        dependencies = {
            "python": self._analyze_python_dependencies(),
            "node": self._analyze_node_dependencies(),
            "docker": self._analyze_docker_dependencies()
        }
        
        total_deps = sum(len(deps) for deps in dependencies.values())
        add_span_attribute("build.dependencies.total", total_deps)
        
        for lang, deps in dependencies.items():
            add_span_attribute(f"build.dependencies.{lang}.count", len(deps))
        
        return dependencies
    
    def _analyze_python_dependencies(self) -> List[str]:
        """Analyze Python dependencies"""
        deps = []
        
        # Check requirements.txt
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                deps.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])
        
        # Check pyproject.toml
        pyproject_file = self.project_path / "pyproject.toml"
        if pyproject_file.exists():
            # Simplified parsing - in production, use tomli/tomllib
            try:
                with open(pyproject_file, 'r') as f:
                    content = f.read()
                    if 'dependencies' in content:
                        add_span_event("build.dependencies.python.pyproject_found")
            except Exception as e:
                logger.warning("Failed to parse pyproject.toml", error=str(e))
        
        return deps
    
    def _analyze_node_dependencies(self) -> List[str]:
        """Analyze Node.js dependencies"""
        deps = []
        
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    
                deps.extend(data.get("dependencies", {}).keys())
                deps.extend(data.get("devDependencies", {}).keys())
                
                add_span_event("build.dependencies.node.package_json_found", {
                    "dependencies": len(data.get("dependencies", {})),
                    "devDependencies": len(data.get("devDependencies", {}))
                })
                
            except Exception as e:
                logger.warning("Failed to parse package.json", error=str(e))
        
        return deps
    
    def _analyze_docker_dependencies(self) -> List[str]:
        """Analyze Docker dependencies"""
        deps = []
        
        dockerfile = self.project_path / "Dockerfile"
        if dockerfile.exists():
            try:
                with open(dockerfile, 'r') as f:
                    lines = f.readlines()
                    
                from_images = [
                    line.split()[1] for line in lines 
                    if line.strip().upper().startswith('FROM')
                ]
                deps.extend(from_images)
                
                add_span_event("build.dependencies.docker.dockerfile_found", {
                    "from_images": len(from_images)
                })
                
            except Exception as e:
                logger.warning("Failed to parse Dockerfile", error=str(e))
        
        return deps
    
    @trace_operation("build.artifact_collection")
    def collect_build_artifacts(self, patterns: List[str] = None) -> List[str]:
        """Collect build artifacts with tracing"""
        if patterns is None:
            patterns = [
                "*.whl", "*.egg", "dist/*", "build/*",  # Python
                "node_modules/", "*.tgz",  # Node.js
                "target/", "*.jar",  # Java
                "bin/", "*.exe",  # Go/C++
                "*.docker"  # Docker
            ]
        
        artifacts = []
        
        for pattern in patterns:
            with trace_span(f"build.artifacts.collect.{pattern}") as span:
                try:
                    from glob import glob
                    matches = glob(str(self.project_path / pattern), recursive=True)
                    artifacts.extend(matches)
                    
                    span.set_attribute("build.artifacts.pattern", pattern)
                    span.set_attribute("build.artifacts.matches", len(matches))
                    
                except Exception as e:
                    span.set_attribute("build.artifacts.error", str(e))
                    logger.warning("Failed to collect artifacts", pattern=pattern, error=str(e))
        
        add_span_attribute("build.artifacts.total", len(artifacts))
        
        return artifacts