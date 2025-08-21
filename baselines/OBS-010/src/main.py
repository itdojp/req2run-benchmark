"""
OBS-010: OpenTelemetry Comprehensive Tracing Coverage
Main application demonstrating comprehensive tracing instrumentation
"""
import asyncio
import os
import sys
import time
from typing import Dict, Any, Optional
from pathlib import Path

import click
import structlog
import yaml
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import tracing modules
from tracing import initialize_tracing, get_tracer, trace_operation, trace_span, TracingMiddleware
from build_tracer import BuildTracer
from startup_tracer import StartupTracer
from test_tracer import TestTracer

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class ObservabilityApp:
    """Main application class for demonstrating comprehensive tracing"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_configuration(config_path)
        self.startup_tracer = StartupTracer("obs-010-app")
        self.build_tracer = BuildTracer()
        self.test_tracer = TestTracer()
        
        # Initialize OpenTelemetry tracing
        self._initialize_tracing()
        
        # Create FastAPI app
        self.app = self._create_fastapi_app()
    
    def _load_configuration(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load application configuration"""
        default_config = {
            "app": {
                "name": "OBS-010 Observability Demo",
                "version": "1.0.0",
                "environment": "development"
            },
            "tracing": {
                "service_name": "obs-010-service",
                "service_version": "1.0.0",
                "jaeger_endpoint": os.getenv("JAEGER_ENDPOINT"),
                "otlp_endpoint": os.getenv("OTLP_ENDPOINT"),
                "zipkin_endpoint": os.getenv("ZIPKIN_ENDPOINT"),
                "console_exporter": True
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "reload": False
            },
            "database": {
                "url": "sqlite:///./obs_demo.db",
                "pool_size": 5
            },
            "logging": {
                "level": "INFO"
            },
            "security": {
                "secret_key": "demo-secret-key-change-in-production"
            },
            "performance": {
                "max_workers": 4
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    # Deep merge configurations
                    self._deep_merge_dict(default_config, file_config)
            except Exception as e:
                logger.warning("Failed to load config file, using defaults", 
                             config_path=config_path, error=str(e))
        
        return default_config
    
    def _deep_merge_dict(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """Deep merge two dictionaries"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge_dict(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _initialize_tracing(self):
        """Initialize OpenTelemetry tracing"""
        tracing_config = self.config["tracing"]
        
        initialize_tracing(
            service_name=tracing_config["service_name"],
            service_version=tracing_config["service_version"],
            environment=self.config["app"]["environment"],
            jaeger_endpoint=tracing_config.get("jaeger_endpoint"),
            otlp_endpoint=tracing_config.get("otlp_endpoint"),
            zipkin_endpoint=tracing_config.get("zipkin_endpoint"),
            console_exporter=tracing_config.get("console_exporter", True)
        )
        
        logger.info("Tracing initialized", service_name=tracing_config["service_name"])
    
    @trace_operation("app.startup")
    def startup(self) -> Dict[str, Any]:
        """Application startup with comprehensive tracing"""
        logger.info("Starting observability application")
        
        # Trace startup process
        startup_info = self.startup_tracer.trace_startup(self.config)
        
        logger.info("Application startup completed", 
                   duration=startup_info.get("start_time"))
        
        return startup_info
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create FastAPI application with tracing middleware"""
        app = FastAPI(
            title=self.config["app"]["name"],
            version=self.config["app"]["version"],
            description="OpenTelemetry comprehensive tracing demonstration"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add tracing middleware
        app.add_middleware(TracingMiddleware, service_name=self.config["tracing"]["service_name"])
        
        # Add routes
        self._setup_routes(app)
        
        return app
    
    def _setup_routes(self, app: FastAPI):
        """Setup FastAPI routes with tracing"""
        
        @app.get("/")
        @trace_operation("api.root")
        async def root():
            """Root endpoint"""
            return {
                "service": self.config["app"]["name"],
                "version": self.config["app"]["version"],
                "status": "healthy"
            }
        
        @app.get("/health")
        @trace_operation("api.health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "service": self.config["tracing"]["service_name"]
            }
        
        @app.post("/build")
        @trace_operation("api.build")
        async def trigger_build(request: Request):
            """Trigger build process with tracing"""
            try:
                request_data = await request.json()
            except:
                request_data = {}
            
            build_steps = request_data.get("steps", [
                {
                    "name": "install_dependencies",
                    "type": "python",
                    "module": "pip",
                    "args": ["install", "-r", "requirements.txt"]
                },
                {
                    "name": "run_linting",
                    "type": "command",
                    "command": "flake8 src/ --max-line-length=120"
                },
                {
                    "name": "run_type_check",
                    "type": "command",
                    "command": "mypy src/ --ignore-missing-imports"
                },
                {
                    "name": "build_package",
                    "type": "python",
                    "module": "build"
                }
            ])
            
            build_result = self.build_tracer.execute_build(build_steps)
            return build_result
        
        @app.post("/test")
        @trace_operation("api.test")
        async def trigger_tests(request: Request):
            """Trigger test execution with tracing"""
            try:
                request_data = await request.json()
            except:
                request_data = {}
            
            test_config = {
                "framework": request_data.get("framework", "pytest"),
                "parallel": request_data.get("parallel", False),
                "coverage": request_data.get("coverage", True),
                "verbose": request_data.get("verbose", True),
                "patterns": ["test_*.py", "*_test.py"],
                "directories": ["tests", "test"]
            }
            
            test_result = self.test_tracer.execute_test_suite(test_config)
            return test_result
        
        @app.post("/benchmark")
        @trace_operation("api.benchmark")
        async def trigger_benchmarks(request: Request):
            """Trigger performance benchmarks with tracing"""
            try:
                request_data = await request.json()
            except:
                request_data = {}
            
            benchmark_config = {
                "iterations": request_data.get("iterations", 100),
                "warmup": request_data.get("warmup", 10)
            }
            
            benchmark_result = self.test_tracer.execute_performance_tests(benchmark_config)
            return benchmark_result
        
        @app.get("/dependencies")
        @trace_operation("api.dependencies")
        async def analyze_dependencies():
            """Analyze project dependencies with tracing"""
            dependencies = self.build_tracer.analyze_dependencies()
            return dependencies
        
        @app.get("/artifacts")
        @trace_operation("api.artifacts")
        async def collect_artifacts():
            """Collect build artifacts with tracing"""
            artifacts = self.build_tracer.collect_build_artifacts()
            return {"artifacts": artifacts}
        
        @app.post("/simulate-error")
        @trace_operation("api.simulate_error")
        async def simulate_error():
            """Simulate an error for tracing demonstration"""
            with trace_span("error.simulation") as span:
                span.set_attribute("error.intentional", True)
                
                try:
                    # Simulate some processing
                    time.sleep(0.1)
                    
                    # Intentionally raise an error
                    raise ValueError("This is a simulated error for tracing demonstration")
                
                except Exception as e:
                    logger.error("Simulated error occurred", error=str(e))
                    raise
        
        @app.get("/trace-context")
        @trace_operation("api.trace_context")
        async def get_trace_context():
            """Get current trace context information"""
            from tracing import get_trace_context
            from opentelemetry import trace
            
            current_span = trace.get_current_span()
            span_context = current_span.get_span_context()
            
            return {
                "trace_id": format(span_context.trace_id, '032x'),
                "span_id": format(span_context.span_id, '016x'),
                "trace_flags": span_context.trace_flags,
                "trace_context": get_trace_context()
            }
    
    async def run_server(self):
        """Run the FastAPI server"""
        server_config = self.config["server"]
        
        config = uvicorn.Config(
            self.app,
            host=server_config["host"],
            port=server_config["port"],
            reload=server_config["reload"],
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()


@click.group()
def cli():
    """OBS-010: OpenTelemetry Comprehensive Tracing Coverage"""
    pass


@cli.command()
@click.option("--config", "-c", help="Configuration file path")
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=8000, help="Port to bind")
def serve(config: Optional[str], host: str, port: int):
    """Start the web server with tracing"""
    app = ObservabilityApp(config_path=config)
    
    # Override server config if provided
    if host != "0.0.0.0":
        app.config["server"]["host"] = host
    if port != 8000:
        app.config["server"]["port"] = port
    
    # Perform startup tracing
    startup_info = app.startup()
    logger.info("Startup tracing completed", startup_duration=startup_info.get("duration", 0))
    
    # Run server
    asyncio.run(app.run_server())


@cli.command()
@click.option("--config", "-c", help="Configuration file path")
def build(config: Optional[str]):
    """Run build process with tracing"""
    app = ObservabilityApp(config_path=config)
    app.startup()
    
    build_steps = [
        {
            "name": "check_environment",
            "type": "command",
            "command": "python --version && pip --version"
        },
        {
            "name": "install_dependencies",
            "type": "python",
            "module": "pip",
            "args": ["install", "-r", "requirements.txt"]
        },
        {
            "name": "analyze_dependencies",
            "type": "command",
            "command": "pip list"
        },
        {
            "name": "run_linting",
            "type": "command",
            "command": "echo 'Linting completed (simulated)'"
        }
    ]
    
    result = app.build_tracer.execute_build(build_steps)
    
    click.echo(f"Build completed: {'SUCCESS' if result['success'] else 'FAILED'}")
    click.echo(f"Duration: {result['total_duration']:.2f} seconds")
    
    if not result['success']:
        click.echo(f"Failed step: {result['failed_step']}")


@cli.command()
@click.option("--config", "-c", help="Configuration file path")
@click.option("--framework", default="pytest", help="Test framework to use")
@click.option("--coverage/--no-coverage", default=True, help="Enable coverage reporting")
def test(config: Optional[str], framework: str, coverage: bool):
    """Run tests with tracing"""
    app = ObservabilityApp(config_path=config)
    app.startup()
    
    test_config = {
        "framework": framework,
        "parallel": False,
        "coverage": coverage,
        "verbose": True,
        "patterns": ["test_*.py", "*_test.py"],
        "directories": ["tests", "test"]
    }
    
    result = app.test_tracer.execute_test_suite(test_config)
    
    click.echo(f"Tests completed: {result['passed']}/{result['total_tests']} passed")
    click.echo(f"Duration: {result['duration']:.2f} seconds")
    
    if result['coverage']:
        coverage_pct = result['coverage']['coverage_percentage']
        click.echo(f"Coverage: {coverage_pct:.1f}%")


@cli.command()
@click.option("--config", "-c", help="Configuration file path")
@click.option("--iterations", default=100, help="Number of benchmark iterations")
def benchmark(config: Optional[str], iterations: int):
    """Run performance benchmarks with tracing"""
    app = ObservabilityApp(config_path=config)
    app.startup()
    
    benchmark_config = {
        "iterations": iterations,
        "warmup": 10
    }
    
    result = app.test_tracer.execute_performance_tests(benchmark_config)
    
    click.echo(f"Benchmarks completed: {result['passed']}/{result['total_benchmarks']} passed")
    
    for benchmark_result in result['results']:
        name = benchmark_result['name']
        passed = "PASS" if benchmark_result['passed'] else "FAIL"
        avg_value = benchmark_result['measurements']['avg']
        metric_type = benchmark_result['metric_type']
        
        click.echo(f"  {name}: {passed} (avg: {avg_value:.2f} {metric_type})")


@cli.command()
@click.option("--config", "-c", help="Configuration file path")
def startup(config: Optional[str]):
    """Run startup process with tracing"""
    app = ObservabilityApp(config_path=config)
    
    startup_info = app.startup()
    
    click.echo("Startup tracing completed")
    click.echo(f"Environment: {startup_info['environment']['platform']}")
    click.echo(f"Dependencies loaded: {len(startup_info['dependencies']['imported_modules'])}")
    click.echo(f"Configuration valid: {startup_info['configuration']['valid']}")
    
    # Resources
    resources = startup_info['resources']
    click.echo(f"Database: {'✓' if resources['database']['available'] else '✗'}")
    click.echo(f"Cache: {'✓' if resources['cache']['available'] else '✗'}")
    
    # Health checks
    health = startup_info['health_checks']
    click.echo(f"Overall health: {'✓' if health['overall_healthy'] else '✗'}")


if __name__ == "__main__":
    cli()