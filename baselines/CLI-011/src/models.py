"""Data models for the job orchestrator"""
import uuid
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class JobType(Enum):
    """Types of jobs"""
    COMMAND = "command"
    SCRIPT = "script"
    HTTP = "http"
    PYTHON = "python"


@dataclass
class RetryConfig:
    """Retry configuration with exponential backoff"""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt"""
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        return min(delay, self.max_delay)


@dataclass
class ResourceLimits:
    """Resource limits for job execution"""
    max_memory_mb: int = 1024
    max_cpu_percent: float = 100.0
    max_execution_time: int = 3600  # seconds
    max_concurrent_jobs: int = 4


class JobDefinition(BaseModel):
    """Job definition with all configuration"""
    id: str = Field(..., description="Unique job identifier")
    name: str = Field(..., description="Human-readable job name")
    job_type: JobType = Field(..., description="Type of job to execute")
    command: Optional[str] = Field(None, description="Command to execute")
    script_path: Optional[str] = Field(None, description="Path to script file")
    working_directory: Optional[str] = Field(None, description="Working directory")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    dependencies: List[str] = Field(default_factory=list, description="Job dependencies (job IDs)")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Conditional execution rules")
    retry_config: RetryConfig = Field(default_factory=RetryConfig, description="Retry configuration")
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits, description="Resource limits")
    timeout: int = Field(default=3600, description="Job timeout in seconds")
    tags: List[str] = Field(default_factory=list, description="Job tags for filtering")
    
    class Config:
        use_enum_values = True


@dataclass
class JobExecution:
    """Runtime job execution state"""
    job_id: str
    definition: JobDefinition
    status: JobStatus = JobStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    attempt: int = 0
    max_attempts: int = 3
    pid: Optional[int] = None
    error_message: Optional[str] = None
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate execution duration"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def is_running(self) -> bool:
        """Check if job is currently running"""
        return self.status == JobStatus.RUNNING
    
    @property
    def is_finished(self) -> bool:
        """Check if job has finished (success, failed, or cancelled)"""
        return self.status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.SKIPPED]
    
    @property
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return (
            self.status == JobStatus.FAILED and 
            self.attempt < self.max_attempts
        )


@dataclass
class DAGMetadata:
    """Metadata about the DAG structure"""
    total_jobs: int
    levels: int
    critical_path_length: int
    has_cycles: bool
    max_parallelism: int


@dataclass
class ExecutionPlan:
    """Execution plan for the DAG"""
    execution_id: str
    jobs: Dict[str, JobExecution]
    dag_metadata: DAGMetadata
    start_time: datetime
    status: str = "planning"
    completed_jobs: Set[str] = field(default_factory=set)
    failed_jobs: Set[str] = field(default_factory=set)
    cancelled_jobs: Set[str] = field(default_factory=set)
    
    @property
    def total_jobs(self) -> int:
        """Total number of jobs"""
        return len(self.jobs)
    
    @property
    def pending_jobs(self) -> Set[str]:
        """Jobs that are pending execution"""
        return {
            job_id for job_id, job in self.jobs.items()
            if job.status == JobStatus.PENDING
        }
    
    @property
    def running_jobs(self) -> Set[str]:
        """Jobs that are currently running"""
        return {
            job_id for job_id, job in self.jobs.items()
            if job.status == JobStatus.RUNNING
        }
    
    @property
    def is_complete(self) -> bool:
        """Check if all jobs have finished"""
        return len(self.completed_jobs) + len(self.failed_jobs) + len(self.cancelled_jobs) == self.total_jobs


@dataclass
class JobEvent:
    """Event representing a job state change"""
    timestamp: datetime
    job_id: str
    event_type: str  # started, completed, failed, cancelled, retrying
    details: Dict[str, Any] = field(default_factory=dict)
    execution_id: str = ""


class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""
    name: str = Field(..., description="Workflow name")
    version: str = Field(default="1.0.0", description="Workflow version")
    description: str = Field(default="", description="Workflow description")
    jobs: List[JobDefinition] = Field(..., description="List of job definitions")
    global_config: Dict[str, Any] = Field(default_factory=dict, description="Global configuration")
    
    def get_job_by_id(self, job_id: str) -> Optional[JobDefinition]:
        """Get job definition by ID"""
        for job in self.jobs:
            if job.id == job_id:
                return job
        return None
    
    def validate_dependencies(self) -> List[str]:
        """Validate that all dependencies exist"""
        job_ids = {job.id for job in self.jobs}
        errors = []
        
        for job in self.jobs:
            for dep_id in job.dependencies:
                if dep_id not in job_ids:
                    errors.append(f"Job '{job.id}' depends on non-existent job '{dep_id}'")
        
        return errors