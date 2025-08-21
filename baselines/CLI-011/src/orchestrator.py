"""Main orchestrator for parallel job execution with DAG dependencies"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Callable
from collections import defaultdict

from models import (
    JobDefinition, JobExecution, JobStatus, ExecutionPlan,
    ResourceLimits, WorkflowDefinition, JobEvent, RetryConfig
)
from dag import DAGAnalyzer
from executor import JobExecutor, ResourceManager
from tenacity import retry, stop_after_attempt, wait_exponential


logger = logging.getLogger(__name__)


class JobOrchestrator:
    """Main orchestrator for parallel job execution"""
    
    def __init__(self, 
                 max_concurrent_jobs: int = 4,
                 global_resource_limits: Optional[ResourceLimits] = None):
        
        self.max_concurrent_jobs = max_concurrent_jobs
        self.global_resource_limits = global_resource_limits or ResourceLimits(
            max_concurrent_jobs=max_concurrent_jobs
        )
        
        # Core components
        self.resource_manager = ResourceManager(self.global_resource_limits)
        self.executor = JobExecutor(self.resource_manager)
        
        # State tracking
        self.current_execution: Optional[ExecutionPlan] = None
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.event_history: List[JobEvent] = []
        self.status_callbacks: List[Callable[[str, Dict], None]] = []
        
        # Setup event handling
        self.executor.add_event_callback(self._handle_job_event)
        
        # Graceful shutdown
        self._shutdown_event = asyncio.Event()
        self._cancelled = False
    
    def add_status_callback(self, callback: Callable[[str, Dict], None]):
        """Add callback for status updates"""
        self.status_callbacks.append(callback)
    
    def _emit_status(self, event_type: str, data: Dict):
        """Emit status update to all callbacks"""
        for callback in self.status_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def _handle_job_event(self, event: JobEvent):
        """Handle job events from executor"""
        self.event_history.append(event)
        
        # Update execution plan if we have one
        if self.current_execution and event.job_id in self.current_execution.jobs:
            job_exec = self.current_execution.jobs[event.job_id]
            
            if event.event_type == "completed":
                self.current_execution.completed_jobs.add(event.job_id)
                job_exec.status = JobStatus.SUCCESS
            elif event.event_type == "failed":
                self.current_execution.failed_jobs.add(event.job_id)
                job_exec.status = JobStatus.FAILED
            elif event.event_type == "cancelled":
                self.current_execution.cancelled_jobs.add(event.job_id)
                job_exec.status = JobStatus.CANCELLED
        
        # Emit status update
        self._emit_status("job_event", {
            "job_id": event.job_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "details": event.details
        })
    
    async def execute_workflow(self, workflow: WorkflowDefinition) -> ExecutionPlan:
        """Execute a complete workflow"""
        logger.info(f"Starting workflow execution: {workflow.name}")
        
        # Validate workflow
        validation_errors = workflow.validate_dependencies()
        if validation_errors:
            raise ValueError(f"Workflow validation failed: {validation_errors}")
        
        # Analyze DAG
        analyzer = DAGAnalyzer(workflow.jobs)
        is_valid, dag_errors = analyzer.validate_dag()
        
        if not is_valid:
            raise ValueError(f"DAG validation failed: {dag_errors}")
        
        # Create execution plan
        metadata = analyzer.get_metadata()
        execution_plan = ExecutionPlan(
            execution_id=f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            jobs={
                job.id: JobExecution(
                    job_id=job.id,
                    definition=job,
                    max_attempts=job.retry_config.max_attempts
                )
                for job in workflow.jobs
            },
            dag_metadata=metadata,
            start_time=datetime.utcnow(),
            status="running"
        )
        
        self.current_execution = execution_plan
        
        try:
            await self._execute_plan(execution_plan, analyzer)
            
            # Determine final status
            if execution_plan.failed_jobs:
                execution_plan.status = "failed"
            elif execution_plan.cancelled_jobs:
                execution_plan.status = "cancelled"
            else:
                execution_plan.status = "completed"
            
            logger.info(f"Workflow completed with status: {execution_plan.status}")
            
        except Exception as e:
            execution_plan.status = "error"
            logger.error(f"Workflow execution error: {e}")
            raise
        
        finally:
            # Cleanup any remaining tasks
            await self._cleanup_running_tasks()
        
        return execution_plan
    
    async def _execute_plan(self, plan: ExecutionPlan, analyzer: DAGAnalyzer):
        """Execute the execution plan"""
        
        while not plan.is_complete and not self._cancelled:
            # Get jobs ready to execute
            ready_jobs = analyzer.get_ready_jobs(
                plan.completed_jobs, 
                plan.failed_jobs | plan.cancelled_jobs
            )
            
            # Filter out jobs that are already running
            ready_jobs = [
                job_id for job_id in ready_jobs 
                if job_id not in self.running_tasks
            ]
            
            # Start new jobs up to concurrency limit
            available_slots = self.max_concurrent_jobs - len(self.running_tasks)
            jobs_to_start = ready_jobs[:available_slots]
            
            for job_id in jobs_to_start:
                await self._start_job(plan.jobs[job_id])
            
            # Wait for at least one job to complete or a short timeout
            if self.running_tasks:
                try:
                    await asyncio.wait(
                        list(self.running_tasks.values()),
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=1.0  # Short timeout to check for new ready jobs
                    )
                except asyncio.TimeoutError:
                    pass
                
                # Clean up completed tasks
                await self._cleanup_completed_tasks()
            else:
                # No jobs running and none ready - check if we're stuck
                if not ready_jobs and not plan.is_complete:
                    # All remaining jobs have failed dependencies
                    remaining_jobs = set(plan.jobs.keys()) - plan.completed_jobs - plan.failed_jobs - plan.cancelled_jobs
                    for job_id in remaining_jobs:
                        plan.jobs[job_id].status = JobStatus.SKIPPED
                        plan.cancelled_jobs.add(job_id)
                        self._emit_status("job_skipped", {"job_id": job_id, "reason": "dependency_failed"})
                    break
                
                # Brief pause to avoid busy waiting
                await asyncio.sleep(0.1)
    
    async def _start_job(self, job_execution: JobExecution):
        """Start executing a job"""
        logger.info(f"Starting job: {job_execution.job_id}")
        
        # Create task for job execution
        task = asyncio.create_task(
            self._execute_job_with_retry(job_execution)
        )
        
        self.running_tasks[job_execution.job_id] = task
        
        # Emit status
        self._emit_status("job_started", {
            "job_id": job_execution.job_id,
            "attempt": job_execution.attempt + 1
        })
    
    async def _execute_job_with_retry(self, job_execution: JobExecution):
        """Execute a job with retry logic"""
        retry_config = job_execution.definition.retry_config
        
        for attempt in range(retry_config.max_attempts):
            try:
                # Execute the job
                result = await self.executor.execute_job(job_execution)
                
                if result.status == JobStatus.SUCCESS:
                    logger.info(f"Job {job_execution.job_id} completed successfully")
                    return result
                
                elif result.status == JobStatus.FAILED and attempt < retry_config.max_attempts - 1:
                    # Job failed but we can retry
                    delay = retry_config.get_delay(attempt + 1)
                    logger.warning(
                        f"Job {job_execution.job_id} failed (attempt {attempt + 1}), "
                        f"retrying in {delay} seconds"
                    )
                    
                    self._emit_status("job_retrying", {
                        "job_id": job_execution.job_id,
                        "attempt": attempt + 1,
                        "delay_seconds": delay,
                        "error": result.error_message
                    })
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
                
                else:
                    # Job failed and no more retries
                    logger.error(f"Job {job_execution.job_id} failed after {attempt + 1} attempts")
                    return result
            
            except asyncio.CancelledError:
                logger.info(f"Job {job_execution.job_id} was cancelled")
                job_execution.status = JobStatus.CANCELLED
                return job_execution
            
            except Exception as e:
                logger.error(f"Unexpected error executing job {job_execution.job_id}: {e}")
                job_execution.status = JobStatus.FAILED
                job_execution.error_message = str(e)
                return job_execution
        
        return job_execution
    
    async def _cleanup_completed_tasks(self):
        """Clean up completed tasks"""
        completed_jobs = []
        
        for job_id, task in list(self.running_tasks.items()):
            if task.done():
                completed_jobs.append(job_id)
                try:
                    result = await task
                    logger.debug(f"Task for job {job_id} completed with status: {result.status}")
                except Exception as e:
                    logger.error(f"Task for job {job_id} raised exception: {e}")
                
                del self.running_tasks[job_id]
        
        return completed_jobs
    
    async def _cleanup_running_tasks(self):
        """Cancel and cleanup all running tasks"""
        if not self.running_tasks:
            return
        
        logger.info(f"Cancelling {len(self.running_tasks)} running tasks")
        
        # Cancel all running tasks
        for task in self.running_tasks.values():
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        self.running_tasks.clear()
    
    async def cancel_execution(self):
        """Cancel the current execution"""
        logger.info("Cancelling workflow execution")
        self._cancelled = True
        self._shutdown_event.set()
        
        # Cancel all running jobs
        for job_id, task in self.running_tasks.items():
            if not task.done():
                task.cancel()
                
                # Also try to cancel the job execution itself
                if self.current_execution and job_id in self.current_execution.jobs:
                    job_exec = self.current_execution.jobs[job_id]
                    await self.executor.cancel_job(job_exec)
        
        await self._cleanup_running_tasks()
    
    def get_status(self) -> Dict:
        """Get current orchestrator status"""
        status = {
            "running": self.current_execution is not None,
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "current_running_jobs": len(self.running_tasks),
            "resource_usage": self.resource_manager.get_resource_usage(),
            "cancelled": self._cancelled
        }
        
        if self.current_execution:
            plan = self.current_execution
            status.update({
                "execution_id": plan.execution_id,
                "status": plan.status,
                "total_jobs": plan.total_jobs,
                "completed_jobs": len(plan.completed_jobs),
                "failed_jobs": len(plan.failed_jobs),
                "cancelled_jobs": len(plan.cancelled_jobs),
                "running_jobs": list(self.running_tasks.keys()),
                "start_time": plan.start_time.isoformat(),
                "dag_metadata": {
                    "total_jobs": plan.dag_metadata.total_jobs,
                    "levels": plan.dag_metadata.levels,
                    "critical_path_length": plan.dag_metadata.critical_path_length,
                    "max_parallelism": plan.dag_metadata.max_parallelism
                }
            })
            
            if plan.is_complete:
                duration = datetime.utcnow() - plan.start_time
                status["duration_seconds"] = duration.total_seconds()
        
        return status
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a specific job"""
        if not self.current_execution or job_id not in self.current_execution.jobs:
            return None
        
        job_exec = self.current_execution.jobs[job_id]
        
        status = {
            "job_id": job_id,
            "name": job_exec.definition.name,
            "status": job_exec.status.value,
            "attempt": job_exec.attempt,
            "max_attempts": job_exec.max_attempts,
            "execution_id": job_exec.execution_id
        }
        
        if job_exec.start_time:
            status["start_time"] = job_exec.start_time.isoformat()
        
        if job_exec.end_time:
            status["end_time"] = job_exec.end_time.isoformat()
            status["duration_seconds"] = job_exec.duration.total_seconds()
        
        if job_exec.exit_code is not None:
            status["exit_code"] = job_exec.exit_code
        
        if job_exec.error_message:
            status["error_message"] = job_exec.error_message
        
        if job_exec.stdout:
            status["stdout"] = job_exec.stdout
        
        if job_exec.stderr:
            status["stderr"] = job_exec.stderr
        
        return status
    
    def get_execution_history(self) -> List[Dict]:
        """Get execution event history"""
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "job_id": event.job_id,
                "event_type": event.event_type,
                "details": event.details
            }
            for event in self.event_history
        ]