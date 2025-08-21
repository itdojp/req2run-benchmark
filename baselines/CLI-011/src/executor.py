"""Job execution engine with resource management"""
import asyncio
import subprocess
import psutil
import signal
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import tempfile
import json

from models import (
    JobDefinition, JobExecution, JobStatus, JobType,
    ResourceLimits, JobEvent
)


class ResourceManager:
    """Manages system resources for job execution"""
    
    def __init__(self, global_limits: ResourceLimits):
        self.global_limits = global_limits
        self.current_usage = {
            'memory_mb': 0,
            'cpu_percent': 0.0,
            'active_jobs': 0
        }
        self.active_processes: Dict[str, psutil.Process] = {}
    
    def can_start_job(self, job_limits: ResourceLimits) -> bool:
        """Check if we can start a job given current resource usage"""
        # Check concurrent job limit
        if self.current_usage['active_jobs'] >= self.global_limits.max_concurrent_jobs:
            return False
        
        # Check memory limit (simplified - actual usage would need process monitoring)
        projected_memory = self.current_usage['memory_mb'] + job_limits.max_memory_mb
        if projected_memory > self.global_limits.max_memory_mb:
            return False
        
        return True
    
    def register_job(self, job_id: str, process: psutil.Process, limits: ResourceLimits):
        """Register a running job for resource tracking"""
        self.active_processes[job_id] = process
        self.current_usage['active_jobs'] += 1
        # Note: In a real implementation, we'd track actual memory usage
        self.current_usage['memory_mb'] += limits.max_memory_mb
    
    def unregister_job(self, job_id: str, limits: ResourceLimits):
        """Unregister a completed job"""
        if job_id in self.active_processes:
            del self.active_processes[job_id]
        
        self.current_usage['active_jobs'] = max(0, self.current_usage['active_jobs'] - 1)
        self.current_usage['memory_mb'] = max(0, self.current_usage['memory_mb'] - limits.max_memory_mb)
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        total_memory = 0
        total_cpu = 0.0
        
        for process in self.active_processes.values():
            try:
                memory_info = process.memory_info()
                total_memory += memory_info.rss / (1024 * 1024)  # Convert to MB
                total_cpu += process.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            'active_jobs': self.current_usage['active_jobs'],
            'memory_mb': total_memory,
            'cpu_percent': total_cpu,
            'limits': {
                'max_concurrent_jobs': self.global_limits.max_concurrent_jobs,
                'max_memory_mb': self.global_limits.max_memory_mb,
                'max_cpu_percent': self.global_limits.max_cpu_percent
            }
        }


class JobExecutor:
    """Executes individual jobs with proper resource management"""
    
    def __init__(self, resource_manager: ResourceManager):
        self.resource_manager = resource_manager
        self.event_callbacks: List[Callable[[JobEvent], None]] = []
    
    def add_event_callback(self, callback: Callable[[JobEvent], None]):
        """Add a callback for job events"""
        self.event_callbacks.append(callback)
    
    def _emit_event(self, job_id: str, event_type: str, details: Dict[str, Any] = None):
        """Emit a job event to all callbacks"""
        event = JobEvent(
            timestamp=datetime.utcnow(),
            job_id=job_id,
            event_type=event_type,
            details=details or {}
        )
        
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                # Don't let callback errors break execution
                print(f"Event callback error: {e}")
    
    async def execute_job(self, job_execution: JobExecution) -> JobExecution:
        """Execute a single job and return updated execution state"""
        job = job_execution.definition
        
        # Check if we can start this job
        if not self.resource_manager.can_start_job(job.resource_limits):
            job_execution.error_message = "Insufficient resources to start job"
            return job_execution
        
        try:
            job_execution.status = JobStatus.RUNNING
            job_execution.start_time = datetime.utcnow()
            job_execution.attempt += 1
            
            self._emit_event(job.id, "started", {
                "attempt": job_execution.attempt,
                "start_time": job_execution.start_time.isoformat()
            })
            
            # Execute based on job type
            if job.job_type == JobType.COMMAND:
                await self._execute_command(job_execution)
            elif job.job_type == JobType.SCRIPT:
                await self._execute_script(job_execution)
            elif job.job_type == JobType.PYTHON:
                await self._execute_python(job_execution)
            elif job.job_type == JobType.HTTP:
                await self._execute_http(job_execution)
            else:
                raise ValueError(f"Unsupported job type: {job.job_type}")
            
            job_execution.end_time = datetime.utcnow()
            
            # Determine final status
            if job_execution.exit_code == 0:
                job_execution.status = JobStatus.SUCCESS
                self._emit_event(job.id, "completed", {
                    "exit_code": job_execution.exit_code,
                    "duration_seconds": job_execution.duration.total_seconds() if job_execution.duration else 0
                })
            else:
                job_execution.status = JobStatus.FAILED
                self._emit_event(job.id, "failed", {
                    "exit_code": job_execution.exit_code,
                    "error_message": job_execution.error_message
                })
        
        except asyncio.CancelledError:
            job_execution.status = JobStatus.CANCELLED
            job_execution.end_time = datetime.utcnow()
            self._emit_event(job.id, "cancelled")
            raise
        
        except Exception as e:
            job_execution.status = JobStatus.FAILED
            job_execution.end_time = datetime.utcnow()
            job_execution.error_message = str(e)
            self._emit_event(job.id, "failed", {
                "error_message": str(e),
                "exception_type": type(e).__name__
            })
        
        return job_execution
    
    async def _execute_command(self, job_execution: JobExecution):
        """Execute a shell command"""
        job = job_execution.definition
        
        if not job.command:
            raise ValueError("Command job requires 'command' field")
        
        # Set up environment
        env = os.environ.copy()
        env.update(job.environment)
        
        # Set working directory
        cwd = job.working_directory or os.getcwd()
        
        try:
            # Create subprocess with timeout
            process = await asyncio.create_subprocess_shell(
                job.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )
            
            job_execution.pid = process.pid
            
            # Register with resource manager if we can get process handle
            try:
                ps_process = psutil.Process(process.pid)
                self.resource_manager.register_job(job.id, ps_process, job.resource_limits)
            except psutil.NoSuchProcess:
                pass
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=job.timeout
                )
                
                job_execution.stdout = stdout.decode('utf-8', errors='replace')
                job_execution.stderr = stderr.decode('utf-8', errors='replace')
                job_execution.exit_code = process.returncode
                
            except asyncio.TimeoutError:
                # Kill the process
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass
                
                job_execution.exit_code = -1
                job_execution.error_message = f"Job timed out after {job.timeout} seconds"
        
        finally:
            # Unregister from resource manager
            self.resource_manager.unregister_job(job.id, job.resource_limits)
    
    async def _execute_script(self, job_execution: JobExecution):
        """Execute a script file"""
        job = job_execution.definition
        
        if not job.script_path:
            raise ValueError("Script job requires 'script_path' field")
        
        script_path = Path(job.script_path)
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {job.script_path}")
        
        # Determine interpreter based on file extension
        if script_path.suffix == '.py':
            command = f"python {job.script_path}"
        elif script_path.suffix in ['.sh', '.bash']:
            command = f"bash {job.script_path}"
        elif script_path.suffix == '.js':
            command = f"node {job.script_path}"
        else:
            # Try to execute directly
            command = str(script_path)
        
        # Create a temporary job with the command
        temp_job = JobDefinition(
            id=job.id,
            name=job.name,
            job_type=JobType.COMMAND,
            command=command,
            working_directory=job.working_directory,
            environment=job.environment,
            dependencies=job.dependencies,
            timeout=job.timeout,
            resource_limits=job.resource_limits
        )
        
        temp_execution = JobExecution(
            job_id=job.id,
            definition=temp_job,
            attempt=job_execution.attempt
        )
        
        await self._execute_command(temp_execution)
        
        # Copy results back
        job_execution.stdout = temp_execution.stdout
        job_execution.stderr = temp_execution.stderr
        job_execution.exit_code = temp_execution.exit_code
        job_execution.pid = temp_execution.pid
    
    async def _execute_python(self, job_execution: JobExecution):
        """Execute Python code directly"""
        job = job_execution.definition
        
        if not job.command:
            raise ValueError("Python job requires 'command' field with Python code")
        
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(job.command)
            temp_file = f.name
        
        try:
            # Execute the temporary file
            temp_job = JobDefinition(
                id=job.id,
                name=job.name,
                job_type=JobType.COMMAND,
                command=f"python {temp_file}",
                working_directory=job.working_directory,
                environment=job.environment,
                dependencies=job.dependencies,
                timeout=job.timeout,
                resource_limits=job.resource_limits
            )
            
            temp_execution = JobExecution(
                job_id=job.id,
                definition=temp_job,
                attempt=job_execution.attempt
            )
            
            await self._execute_command(temp_execution)
            
            # Copy results back
            job_execution.stdout = temp_execution.stdout
            job_execution.stderr = temp_execution.stderr
            job_execution.exit_code = temp_execution.exit_code
            job_execution.pid = temp_execution.pid
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except OSError:
                pass
    
    async def _execute_http(self, job_execution: JobExecution):
        """Execute HTTP request (simplified implementation)"""
        job = job_execution.definition
        
        if not job.command:
            raise ValueError("HTTP job requires 'command' field with URL")
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(job.command) as response:
                    job_execution.stdout = await response.text()
                    job_execution.exit_code = 0 if response.status == 200 else 1
                    
                    if response.status != 200:
                        job_execution.stderr = f"HTTP {response.status}: {response.reason}"
        
        except ImportError:
            # Fallback to curl if aiohttp is not available
            curl_cmd = f"curl -s {job.command}"
            temp_job = JobDefinition(
                id=job.id,
                name=job.name,
                job_type=JobType.COMMAND,
                command=curl_cmd,
                working_directory=job.working_directory,
                environment=job.environment,
                dependencies=job.dependencies,
                timeout=job.timeout,
                resource_limits=job.resource_limits
            )
            
            temp_execution = JobExecution(
                job_id=job.id,
                definition=temp_job,
                attempt=job_execution.attempt
            )
            
            await self._execute_command(temp_execution)
            
            # Copy results back
            job_execution.stdout = temp_execution.stdout
            job_execution.stderr = temp_execution.stderr
            job_execution.exit_code = temp_execution.exit_code
            job_execution.pid = temp_execution.pid
    
    async def cancel_job(self, job_execution: JobExecution):
        """Cancel a running job"""
        if job_execution.pid and job_execution.status == JobStatus.RUNNING:
            try:
                # Try to terminate gracefully first
                os.kill(job_execution.pid, signal.SIGTERM)
                
                # Wait a bit for graceful shutdown
                await asyncio.sleep(2)
                
                # Force kill if still running
                try:
                    os.kill(job_execution.pid, signal.SIGKILL)
                except ProcessLookupError:
                    # Process already terminated
                    pass
                    
            except ProcessLookupError:
                # Process doesn't exist anymore
                pass
            
            job_execution.status = JobStatus.CANCELLED
            job_execution.end_time = datetime.utcnow()
            
            self._emit_event(job_execution.job_id, "cancelled", {
                "pid": job_execution.pid
            })