"""
CLI-011: Parallel Job Orchestrator with DAG Execution
Main CLI application
"""
import asyncio
import logging
import signal
import sys
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from models import WorkflowDefinition, JobDefinition, JobType, RetryConfig, ResourceLimits
from orchestrator import JobOrchestrator
from dag import DAGAnalyzer


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


class JobOrchestratorCLI:
    """Main CLI application for the job orchestrator"""
    
    def __init__(self):
        self.orchestrator: Optional[JobOrchestrator] = None
        self.shutdown_event = asyncio.Event()
        self.live_display: Optional[Live] = None
        self.progress: Optional[Progress] = None
        self.progress_tasks: Dict[str, TaskID] = {}
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def shutdown(self):
        """Graceful shutdown"""
        if self.orchestrator:
            await self.orchestrator.cancel_execution()
        
        if self.live_display:
            self.live_display.stop()
        
        self.shutdown_event.set()
    
    def status_callback(self, event_type: str, data: Dict):
        """Handle status updates from orchestrator"""
        if event_type == "job_started":
            job_id = data["job_id"]
            if self.progress and job_id not in self.progress_tasks:
                self.progress_tasks[job_id] = self.progress.add_task(
                    f"[cyan]{job_id}[/cyan]", total=100
                )
        
        elif event_type == "job_event":
            job_id = data["job_id"]
            event = data["event_type"]
            
            if self.progress and job_id in self.progress_tasks:
                if event == "completed":
                    self.progress.update(self.progress_tasks[job_id], completed=100)
                elif event == "failed":
                    self.progress.update(
                        self.progress_tasks[job_id], 
                        completed=100,
                        description=f"[red]{job_id} (FAILED)[/red]"
                    )
                elif event == "cancelled":
                    self.progress.update(
                        self.progress_tasks[job_id], 
                        completed=100,
                        description=f"[yellow]{job_id} (CANCELLED)[/yellow]"
                    )
    
    def create_status_display(self) -> Panel:
        """Create real-time status display"""
        if not self.orchestrator:
            return Panel("No active execution", title="Status")
        
        status = self.orchestrator.get_status()
        
        if not status["running"]:
            return Panel("No active execution", title="Status")
        
        # Create status table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="dim")
        table.add_column("Value")
        
        table.add_row("Execution ID", status.get("execution_id", "N/A"))
        table.add_row("Status", status.get("status", "unknown"))
        table.add_row("Total Jobs", str(status.get("total_jobs", 0)))
        table.add_row("Completed", str(status.get("completed_jobs", 0)))
        table.add_row("Failed", str(status.get("failed_jobs", 0)))
        table.add_row("Running", str(status.get("current_running_jobs", 0)))
        
        # Resource usage
        resources = status.get("resource_usage", {})
        table.add_row("Active Jobs", str(resources.get("active_jobs", 0)))
        table.add_row("Memory (MB)", f"{resources.get('memory_mb', 0):.1f}")
        table.add_row("CPU %", f"{resources.get('cpu_percent', 0):.1f}")
        
        return Panel(table, title="Execution Status")
    
    async def run_with_live_display(self, workflow: WorkflowDefinition):
        """Run workflow with live display"""
        
        # Setup progress tracking
        self.progress = Progress()
        
        # Create orchestrator
        self.orchestrator = JobOrchestrator(
            max_concurrent_jobs=4
        )
        self.orchestrator.add_status_callback(self.status_callback)
        
        # Setup live display
        self.live_display = Live(
            self.create_status_display(),
            refresh_per_second=2,
            console=console
        )
        
        try:
            self.live_display.start()
            
            # Start execution
            execution_task = asyncio.create_task(
                self.orchestrator.execute_workflow(workflow)
            )
            
            # Update display periodically
            display_task = asyncio.create_task(self._update_display_loop())
            
            # Wait for completion or shutdown
            done, pending = await asyncio.wait(
                [execution_task, display_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Get execution result
            if execution_task in done:
                execution_plan = await execution_task
                return execution_plan
            else:
                # Shutdown was triggered
                return None
        
        finally:
            if self.live_display:
                self.live_display.stop()
    
    async def _update_display_loop(self):
        """Update live display periodically"""
        try:
            while not self.shutdown_event.is_set():
                if self.live_display and self.orchestrator:
                    self.live_display.update(self.create_status_display())
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass


@click.group()
def cli():
    """Parallel Job Orchestrator with DAG Execution"""
    pass


@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
@click.option('--max-concurrent', '-c', default=4, help='Maximum concurrent jobs')
@click.option('--dry-run', is_flag=True, help='Validate workflow without execution')
@click.option('--output', '-o', help='Output results to file')
@click.option('--live', is_flag=True, default=True, help='Show live progress display')
def run(workflow_file: str, max_concurrent: int, dry_run: bool, output: str, live: bool):
    """Execute a workflow from file"""
    
    async def _run():
        # Load workflow
        workflow_path = Path(workflow_file)
        
        try:
            if workflow_path.suffix.lower() in ['.yaml', '.yml']:
                with open(workflow_path, 'r') as f:
                    workflow_data = yaml.safe_load(f)
            else:
                with open(workflow_path, 'r') as f:
                    workflow_data = json.load(f)
            
            workflow = WorkflowDefinition(**workflow_data)
            
        except Exception as e:
            console.print(f"[red]Error loading workflow: {e}[/red]")
            sys.exit(1)
        
        # Validate workflow
        validation_errors = workflow.validate_dependencies()
        if validation_errors:
            console.print("[red]Workflow validation failed:[/red]")
            for error in validation_errors:
                console.print(f"  - {error}")
            sys.exit(1)
        
        # Analyze DAG
        analyzer = DAGAnalyzer(workflow.jobs)
        is_valid, dag_errors = analyzer.validate_dag()
        
        if not is_valid:
            console.print("[red]DAG validation failed:[/red]")
            for error in dag_errors:
                console.print(f"  - {error}")
            sys.exit(1)
        
        # Show DAG info
        metadata = analyzer.get_metadata()
        console.print(f"[green]Workflow loaded successfully:[/green] {workflow.name}")
        console.print(f"  Total jobs: {metadata.total_jobs}")
        console.print(f"  Execution levels: {metadata.levels}")
        console.print(f"  Critical path length: {metadata.critical_path_length}")
        console.print(f"  Max parallelism: {metadata.max_parallelism}")
        
        if dry_run:
            console.print("[yellow]Dry run - workflow would execute successfully[/yellow]")
            
            # Show execution order
            execution_order = analyzer.get_execution_order()
            console.print("\n[cyan]Execution Order:[/cyan]")
            for level, jobs in enumerate(execution_order):
                console.print(f"  Level {level}: {', '.join(jobs)}")
            
            return
        
        # Execute workflow
        app = JobOrchestratorCLI()
        app.setup_signal_handlers()
        
        console.print(f"\n[green]Starting execution with max {max_concurrent} concurrent jobs...[/green]")
        
        try:
            if live:
                execution_plan = await app.run_with_live_display(workflow)
            else:
                orchestrator = JobOrchestrator(max_concurrent_jobs=max_concurrent)
                execution_plan = await orchestrator.execute_workflow(workflow)
            
            if execution_plan:
                # Show results
                console.print(f"\n[green]Execution completed:[/green] {execution_plan.status}")
                console.print(f"  Completed jobs: {len(execution_plan.completed_jobs)}")
                console.print(f"  Failed jobs: {len(execution_plan.failed_jobs)}")
                console.print(f"  Cancelled jobs: {len(execution_plan.cancelled_jobs)}")
                
                # Save results if requested
                if output:
                    results = {
                        "execution_id": execution_plan.execution_id,
                        "status": execution_plan.status,
                        "start_time": execution_plan.start_time.isoformat(),
                        "jobs": {
                            job_id: {
                                "status": job.status.value,
                                "start_time": job.start_time.isoformat() if job.start_time else None,
                                "end_time": job.end_time.isoformat() if job.end_time else None,
                                "exit_code": job.exit_code,
                                "error_message": job.error_message,
                                "stdout": job.stdout,
                                "stderr": job.stderr
                            }
                            for job_id, job in execution_plan.jobs.items()
                        }
                    }
                    
                    with open(output, 'w') as f:
                        json.dump(results, f, indent=2)
                    
                    console.print(f"[green]Results saved to: {output}[/green]")
                
                # Exit with appropriate code
                if execution_plan.status == "completed":
                    sys.exit(0)
                else:
                    sys.exit(1)
            else:
                console.print("[yellow]Execution was cancelled[/yellow]")
                sys.exit(1)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Execution interrupted by user[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Execution failed: {e}[/red]")
            logger.error("Execution failed", exc_info=True)
            sys.exit(1)
    
    asyncio.run(_run())


@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output analysis to file')
def analyze(workflow_file: str, output: str):
    """Analyze workflow DAG structure"""
    
    # Load workflow
    workflow_path = Path(workflow_file)
    
    try:
        if workflow_path.suffix.lower() in ['.yaml', '.yml']:
            with open(workflow_path, 'r') as f:
                workflow_data = yaml.safe_load(f)
        else:
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
        
        workflow = WorkflowDefinition(**workflow_data)
        
    except Exception as e:
        console.print(f"[red]Error loading workflow: {e}[/red]")
        sys.exit(1)
    
    # Analyze DAG
    analyzer = DAGAnalyzer(workflow.jobs)
    is_valid, errors = analyzer.validate_dag()
    metadata = analyzer.get_metadata()
    
    # Create analysis table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Property", style="dim")
    table.add_column("Value")
    
    table.add_row("Workflow Name", workflow.name)
    table.add_row("Total Jobs", str(metadata.total_jobs))
    table.add_row("Valid DAG", "✓" if is_valid else "✗")
    table.add_row("Has Cycles", "✗" if metadata.has_cycles else "✓")
    table.add_row("Execution Levels", str(metadata.levels))
    table.add_row("Critical Path Length", str(metadata.critical_path_length))
    table.add_row("Max Parallelism", str(metadata.max_parallelism))
    
    console.print(table)
    
    if errors:
        console.print("\n[red]Validation Errors:[/red]")
        for error in errors:
            console.print(f"  - {error}")
    
    # Show execution order
    if is_valid:
        execution_order = analyzer.get_execution_order()
        console.print("\n[cyan]Execution Order:[/cyan]")
        for level, jobs in enumerate(execution_order):
            console.print(f"  Level {level}: {', '.join(jobs)}")
    
    # Save analysis if requested
    if output:
        analysis = {
            "workflow_name": workflow.name,
            "valid": is_valid,
            "errors": errors,
            "metadata": {
                "total_jobs": metadata.total_jobs,
                "levels": metadata.levels,
                "critical_path_length": metadata.critical_path_length,
                "has_cycles": metadata.has_cycles,
                "max_parallelism": metadata.max_parallelism
            },
            "execution_order": analyzer.get_execution_order() if is_valid else []
        }
        
        with open(output, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        console.print(f"\n[green]Analysis saved to: {output}[/green]")


@cli.command()
@click.option('--name', '-n', required=True, help='Workflow name')
@click.option('--output', '-o', required=True, help='Output file path')
def create(name: str, output: str):
    """Create a sample workflow file"""
    
    # Create sample workflow
    sample_workflow = {
        "name": name,
        "version": "1.0.0",
        "description": "Sample workflow generated by job orchestrator",
        "jobs": [
            {
                "id": "setup",
                "name": "Setup Environment",
                "job_type": "command",
                "command": "echo 'Setting up environment'",
                "dependencies": [],
                "timeout": 60
            },
            {
                "id": "build",
                "name": "Build Application",
                "job_type": "command", 
                "command": "echo 'Building application'",
                "dependencies": ["setup"],
                "timeout": 300
            },
            {
                "id": "test_unit",
                "name": "Unit Tests",
                "job_type": "command",
                "command": "echo 'Running unit tests'",
                "dependencies": ["build"],
                "timeout": 180
            },
            {
                "id": "test_integration",
                "name": "Integration Tests", 
                "job_type": "command",
                "command": "echo 'Running integration tests'",
                "dependencies": ["build"],
                "timeout": 300
            },
            {
                "id": "deploy",
                "name": "Deploy Application",
                "job_type": "command",
                "command": "echo 'Deploying application'",
                "dependencies": ["test_unit", "test_integration"],
                "timeout": 600
            }
        ]
    }
    
    output_path = Path(output)
    
    if output_path.suffix.lower() in ['.yaml', '.yml']:
        with open(output_path, 'w') as f:
            yaml.dump(sample_workflow, f, default_flow_style=False, indent=2)
    else:
        with open(output_path, 'w') as f:
            json.dump(sample_workflow, f, indent=2)
    
    console.print(f"[green]Sample workflow created: {output}[/green]")


if __name__ == "__main__":
    cli()