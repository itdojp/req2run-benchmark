"""OpenTelemetry tracing configuration and utilities"""
import os
import sys
import time
import traceback
import functools
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager

from opentelemetry import trace, baggage, context, propagate
from opentelemetry.sdk.trace import TracerProvider, Span
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagators.composite import CompositeHTTPPropagator
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor

import structlog

logger = structlog.get_logger()


class TracingManager:
    """Manages OpenTelemetry tracing configuration and lifecycle"""
    
    def __init__(self, 
                 service_name: str,
                 service_version: str = "1.0.0",
                 environment: str = "development",
                 jaeger_endpoint: Optional[str] = None,
                 otlp_endpoint: Optional[str] = None,
                 zipkin_endpoint: Optional[str] = None,
                 console_exporter: bool = True):
        
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.tracer_provider = None
        self.tracer = None
        
        # Initialize tracing
        self._setup_tracer_provider()
        self._setup_exporters(
            jaeger_endpoint=jaeger_endpoint,
            otlp_endpoint=otlp_endpoint,
            zipkin_endpoint=zipkin_endpoint,
            console_exporter=console_exporter
        )
        self._setup_propagators()
        self._setup_auto_instrumentation()
        
        logger.info("OpenTelemetry tracing initialized", 
                   service=service_name, version=service_version)
    
    def _setup_tracer_provider(self):
        """Setup the tracer provider with resource attributes"""
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.environment,
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry",
            "host.name": os.getenv("HOSTNAME", "localhost"),
            "process.pid": str(os.getpid())
        })
        
        self.tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(self.tracer_provider)
        
        # Get tracer instance
        self.tracer = trace.get_tracer(
            instrumenting_module_name=__name__,
            instrumenting_library_version="1.0.0"
        )
    
    def _setup_exporters(self, 
                        jaeger_endpoint: Optional[str] = None,
                        otlp_endpoint: Optional[str] = None,
                        zipkin_endpoint: Optional[str] = None,
                        console_exporter: bool = True):
        """Setup span exporters"""
        
        exporters_added = 0
        
        # Console exporter for development
        if console_exporter:
            console_exporter_instance = ConsoleSpanExporter()
            console_processor = BatchSpanProcessor(console_exporter_instance)
            self.tracer_provider.add_span_processor(console_processor)
            exporters_added += 1
            logger.info("Console span exporter added")
        
        # Jaeger exporter
        if jaeger_endpoint:
            try:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=jaeger_endpoint.split(':')[0],
                    agent_port=int(jaeger_endpoint.split(':')[1]) if ':' in jaeger_endpoint else 6831,
                    collector_endpoint=f"http://{jaeger_endpoint}/api/traces" if not jaeger_endpoint.startswith('http') else jaeger_endpoint
                )
                jaeger_processor = BatchSpanProcessor(jaeger_exporter)
                self.tracer_provider.add_span_processor(jaeger_processor)
                exporters_added += 1
                logger.info("Jaeger span exporter added", endpoint=jaeger_endpoint)
            except Exception as e:
                logger.error("Failed to setup Jaeger exporter", error=str(e))
        
        # OTLP exporter
        if otlp_endpoint:
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                otlp_processor = BatchSpanProcessor(otlp_exporter)
                self.tracer_provider.add_span_processor(otlp_processor)
                exporters_added += 1
                logger.info("OTLP span exporter added", endpoint=otlp_endpoint)
            except Exception as e:
                logger.error("Failed to setup OTLP exporter", error=str(e))
        
        # Zipkin exporter
        if zipkin_endpoint:
            try:
                zipkin_exporter = ZipkinExporter(endpoint=zipkin_endpoint)
                zipkin_processor = BatchSpanProcessor(zipkin_exporter)
                self.tracer_provider.add_span_processor(zipkin_processor)
                exporters_added += 1
                logger.info("Zipkin span exporter added", endpoint=zipkin_endpoint)
            except Exception as e:
                logger.error("Failed to setup Zipkin exporter", error=str(e))
        
        if exporters_added == 0:
            logger.warning("No span exporters configured")
        else:
            logger.info("Span exporters configured", count=exporters_added)
    
    def _setup_propagators(self):
        """Setup trace and baggage propagators"""
        propagate.set_global_textmap(
            CompositeHTTPPropagator([
                TraceContextTextMapPropagator(),
                W3CBaggagePropagator()
            ])
        )
        logger.info("Trace and baggage propagators configured")
    
    def _setup_auto_instrumentation(self):
        """Setup automatic instrumentation for common libraries"""
        try:
            # HTTP libraries
            RequestsInstrumentor().instrument()
            URLLib3Instrumentor().instrument()
            
            logger.info("Auto-instrumentation enabled for HTTP libraries")
        except Exception as e:
            logger.error("Failed to setup auto-instrumentation", error=str(e))
    
    def get_tracer(self, name: Optional[str] = None) -> trace.Tracer:
        """Get a tracer instance"""
        if name:
            return trace.get_tracer(name)
        return self.tracer
    
    def shutdown(self):
        """Shutdown the tracing system"""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            logger.info("OpenTelemetry tracing shutdown completed")


# Global tracing manager instance
_tracing_manager: Optional[TracingManager] = None


def initialize_tracing(service_name: str,
                      service_version: str = "1.0.0",
                      environment: str = "development",
                      **kwargs) -> TracingManager:
    """Initialize global tracing configuration"""
    global _tracing_manager
    
    if _tracing_manager is not None:
        logger.warning("Tracing already initialized, skipping")
        return _tracing_manager
    
    _tracing_manager = TracingManager(
        service_name=service_name,
        service_version=service_version,
        environment=environment,
        **kwargs
    )
    
    return _tracing_manager


def get_tracer(name: Optional[str] = None) -> trace.Tracer:
    """Get the global tracer instance"""
    if _tracing_manager is None:
        raise RuntimeError("Tracing not initialized. Call initialize_tracing() first.")
    
    return _tracing_manager.get_tracer(name)


def shutdown_tracing():
    """Shutdown global tracing"""
    global _tracing_manager
    
    if _tracing_manager is not None:
        _tracing_manager.shutdown()
        _tracing_manager = None


def trace_operation(operation_name: str = None,
                   span_attributes: Optional[Dict[str, Any]] = None,
                   record_exception: bool = True):
    """Decorator for tracing function/method operations"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine span name
            span_name = operation_name or f"{func.__module__}.{func.__qualname__}"
            
            tracer = get_tracer()
            
            with tracer.start_as_current_span(span_name) as span:
                # Add default attributes
                span.set_attribute("operation.name", func.__name__)
                span.set_attribute("operation.module", func.__module__)
                
                # Add custom attributes
                if span_attributes:
                    for key, value in span_attributes.items():
                        span.set_attribute(key, value)
                
                # Add function arguments as attributes (be careful with sensitive data)
                if args:
                    span.set_attribute("operation.args_count", len(args))
                if kwargs:
                    span.set_attribute("operation.kwargs_count", len(kwargs))
                    # Optionally log specific kwargs (filter sensitive data)
                    safe_kwargs = {
                        k: v for k, v in kwargs.items() 
                        if not any(sensitive in k.lower() for sensitive in ['password', 'token', 'secret', 'key'])
                    }
                    for key, value in safe_kwargs.items():
                        if isinstance(value, (str, int, float, bool)):
                            span.set_attribute(f"operation.kwargs.{key}", value)
                
                try:
                    # Execute function
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    
                    # Record result info if it's not too large
                    if result is not None:
                        result_type = type(result).__name__
                        span.set_attribute("operation.result_type", result_type)
                        
                        if isinstance(result, (list, tuple, dict)):
                            span.set_attribute("operation.result_length", len(result))
                    
                    return result
                
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    
                    if record_exception:
                        # Record exception details
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))
                        
                        # Record stack trace
                        tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                        span.add_event(
                            name="exception",
                            attributes={
                                "exception.type": type(e).__name__,
                                "exception.message": str(e),
                                "exception.stacktrace": tb_str
                            }
                        )
                    
                    raise
        
        return wrapper
    return decorator


@contextmanager
def trace_span(span_name: str, 
               attributes: Optional[Dict[str, Any]] = None,
               tracer_name: Optional[str] = None):
    """Context manager for manual span creation"""
    tracer = get_tracer(tracer_name)
    
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.add_event(
                name="exception",
                attributes={
                    "exception.type": type(e).__name__,
                    "exception.message": str(e)
                }
            )
            raise


def add_span_attribute(key: str, value: Any):
    """Add attribute to current span"""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Add event to current span"""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.add_event(name, attributes or {})


def set_span_status(status_code: StatusCode, description: Optional[str] = None):
    """Set status of current span"""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_status(Status(status_code, description))


def get_trace_context() -> Dict[str, str]:
    """Get current trace context for propagation"""
    carrier = {}
    propagate.inject(carrier)
    return carrier


def inject_trace_context(carrier: Dict[str, str]):
    """Inject trace context from carrier"""
    ctx = propagate.extract(carrier)
    context.attach(ctx)


class TracingMiddleware:
    """Generic tracing middleware for different frameworks"""
    
    def __init__(self, app, service_name: str = "web-service"):
        self.app = app
        self.service_name = service_name
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        tracer = get_tracer("http-middleware")
        
        # Extract trace context from headers
        headers = dict(scope.get("headers", []))
        carrier = {}
        for name, value in headers.items():
            carrier[name.decode()] = value.decode()
        
        ctx = propagate.extract(carrier)
        
        with context.use_context(ctx):
            span_name = f"{scope['method']} {scope['path']}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add HTTP attributes
                span.set_attribute("http.method", scope["method"])
                span.set_attribute("http.url", scope["path"])
                span.set_attribute("http.scheme", scope["scheme"])
                span.set_attribute("http.user_agent", headers.get(b"user-agent", b"").decode())
                
                if "query_string" in scope and scope["query_string"]:
                    span.set_attribute("http.query_string", scope["query_string"].decode())
                
                # Capture response
                response_started = False
                status_code = None
                
                async def send_wrapper(message):
                    nonlocal response_started, status_code
                    
                    if message["type"] == "http.response.start":
                        response_started = True
                        status_code = message["status"]
                        span.set_attribute("http.status_code", status_code)
                        
                        # Set span status based on HTTP status
                        if 400 <= status_code < 500:
                            span.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
                        elif status_code >= 500:
                            span.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
                        else:
                            span.set_status(Status(StatusCode.OK))
                    
                    await send(message)
                
                try:
                    await self.app(scope, receive, send_wrapper)
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.add_event("exception", {
                        "exception.type": type(e).__name__,
                        "exception.message": str(e)
                    })
                    raise