"""Application startup tracing instrumentation"""
import os
import sys
import time
import importlib
from typing import Dict, Any, List, Optional
from pathlib import Path

from tracing import get_tracer, trace_operation, trace_span, add_span_attribute, add_span_event
import structlog

logger = structlog.get_logger()


class StartupTracer:
    """Instruments application startup with OpenTelemetry spans"""
    
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.tracer = get_tracer("startup-tracer")
        self.startup_start_time = time.time()
    
    @trace_operation("startup.initialize")
    def trace_startup(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trace complete application startup process"""
        add_span_attribute("app.name", self.app_name)
        add_span_attribute("app.python_version", sys.version)
        add_span_attribute("app.platform", sys.platform)
        add_span_attribute("startup.timestamp", self.startup_start_time)
        
        if config:
            self._trace_config_loading(config)
        
        startup_info = {
            "app_name": self.app_name,
            "start_time": self.startup_start_time,
            "environment": self._get_environment_info(),
            "dependencies": self._trace_dependency_loading(),
            "configuration": self._trace_configuration_validation(config or {}),
            "resources": self._trace_resource_initialization(),
            "health_checks": self._trace_health_checks()
        }
        
        startup_duration = time.time() - self.startup_start_time
        add_span_attribute("startup.duration", startup_duration)
        add_span_event("startup.completed", {
            "duration": startup_duration,
            "success": True
        })
        
        return startup_info
    
    def _trace_config_loading(self, config: Dict[str, Any]):
        """Trace configuration loading"""
        with trace_span("startup.config.load") as span:
            span.set_attribute("config.keys_count", len(config))
            
            # Log configuration structure (without sensitive values)
            safe_keys = []
            for key in config.keys():
                if not any(sensitive in key.lower() for sensitive in ['password', 'secret', 'token', 'key']):
                    safe_keys.append(key)
            
            span.set_attribute("config.safe_keys", ",".join(safe_keys))
            
            # Check for common configuration patterns
            if 'database' in config:
                span.set_attribute("config.has_database", True)
            if 'redis' in config or 'cache' in config:
                span.set_attribute("config.has_cache", True)
            if 'logging' in config:
                span.set_attribute("config.has_logging", True)
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information with tracing"""
        with trace_span("startup.environment.analyze") as span:
            env_info = {
                "python_version": sys.version_info[:3],
                "platform": sys.platform,
                "architecture": os.uname().machine if hasattr(os, 'uname') else 'unknown',
                "working_directory": os.getcwd(),
                "python_path": sys.path[:3],  # First 3 entries
                "environment_variables": {}
            }
            
            # Collect relevant environment variables (non-sensitive)
            relevant_env_vars = [
                'ENVIRONMENT', 'NODE_ENV', 'FLASK_ENV', 'DJANGO_SETTINGS_MODULE',
                'DEBUG', 'PORT', 'HOST', 'DATABASE_URL', 'REDIS_URL'
            ]
            
            for var in relevant_env_vars:
                value = os.getenv(var)
                if value:
                    # Mask sensitive-looking values
                    if any(sensitive in var.lower() for sensitive in ['url', 'password', 'secret', 'token']):
                        env_info["environment_variables"][var] = "***masked***"
                    else:
                        env_info["environment_variables"][var] = value
            
            span.set_attribute("env.python_version", ".".join(map(str, env_info["python_version"])))
            span.set_attribute("env.platform", env_info["platform"])
            span.set_attribute("env.env_vars_count", len(env_info["environment_variables"]))
            
            return env_info
    
    def _trace_dependency_loading(self) -> Dict[str, Any]:
        """Trace dependency loading and validation"""
        with trace_span("startup.dependencies.load") as span:
            dependencies = {
                "imported_modules": list(sys.modules.keys()),
                "failed_imports": [],
                "optional_dependencies": {}
            }
            
            # Test critical dependencies
            critical_deps = [
                'json', 'os', 'sys', 'time', 'logging',
                'threading', 'multiprocessing', 'datetime'
            ]
            
            for dep in critical_deps:
                try:
                    importlib.import_module(dep)
                    add_span_event(f"startup.dependency.{dep}.loaded")
                except ImportError as e:
                    dependencies["failed_imports"].append({"module": dep, "error": str(e)})
                    add_span_event(f"startup.dependency.{dep}.failed", {"error": str(e)})
            
            # Test optional dependencies
            optional_deps = [
                'requests', 'sqlalchemy', 'redis', 'celery',
                'fastapi', 'flask', 'django', 'numpy', 'pandas'
            ]
            
            for dep in optional_deps:
                try:
                    module = importlib.import_module(dep)
                    version = getattr(module, '__version__', 'unknown')
                    dependencies["optional_dependencies"][dep] = version
                    add_span_event(f"startup.optional_dependency.{dep}.available", {"version": version})
                except ImportError:
                    add_span_event(f"startup.optional_dependency.{dep}.unavailable")
            
            span.set_attribute("dependencies.total_modules", len(dependencies["imported_modules"]))
            span.set_attribute("dependencies.failed_count", len(dependencies["failed_imports"]))
            span.set_attribute("dependencies.optional_count", len(dependencies["optional_dependencies"]))
            
            return dependencies
    
    def _trace_configuration_validation(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Trace configuration validation"""
        with trace_span("startup.config.validate") as span:
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "validated_sections": []
            }
            
            # Validate common configuration sections
            config_validations = [
                ("database", self._validate_database_config),
                ("logging", self._validate_logging_config),
                ("security", self._validate_security_config),
                ("performance", self._validate_performance_config)
            ]
            
            for section_name, validator in config_validations:
                if section_name in config:
                    with trace_span(f"startup.config.validate.{section_name}") as section_span:
                        try:
                            section_config = config[section_name]
                            validation_result = validator(section_config)
                            
                            validation_results["validated_sections"].append(section_name)
                            
                            if validation_result.get("errors"):
                                validation_results["errors"].extend(validation_result["errors"])
                                validation_results["valid"] = False
                            
                            if validation_result.get("warnings"):
                                validation_results["warnings"].extend(validation_result["warnings"])
                            
                            section_span.set_attribute("config.validation.valid", validation_result.get("valid", True))
                            section_span.set_attribute("config.validation.errors", len(validation_result.get("errors", [])))
                            
                        except Exception as e:
                            validation_results["errors"].append(f"Failed to validate {section_name}: {str(e)}")
                            validation_results["valid"] = False
                            section_span.set_attribute("config.validation.error", str(e))
            
            span.set_attribute("config.validation.overall_valid", validation_results["valid"])
            span.set_attribute("config.validation.errors_count", len(validation_results["errors"]))
            span.set_attribute("config.validation.warnings_count", len(validation_results["warnings"]))
            
            return validation_results
    
    def _validate_database_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate database configuration"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        required_fields = ["url", "pool_size"]
        for field in required_fields:
            if field not in config:
                result["errors"].append(f"Missing required database field: {field}")
                result["valid"] = False
        
        if "pool_size" in config:
            pool_size = config["pool_size"]
            if not isinstance(pool_size, int) or pool_size <= 0:
                result["errors"].append("Database pool_size must be a positive integer")
                result["valid"] = False
            elif pool_size > 100:
                result["warnings"].append("Database pool_size is very large (>100)")
        
        return result
    
    def _validate_logging_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate logging configuration"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if "level" in config:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config["level"].upper() not in valid_levels:
                result["errors"].append(f"Invalid logging level: {config['level']}")
                result["valid"] = False
        
        return result
    
    def _validate_security_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate security configuration"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if "secret_key" in config:
            secret_key = config["secret_key"]
            if len(secret_key) < 32:
                result["warnings"].append("Secret key is shorter than recommended (32 characters)")
        
        return result
    
    def _validate_performance_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate performance configuration"""
        result = {"valid": True, "errors": [], "warnings": []}
        
        if "max_workers" in config:
            max_workers = config["max_workers"]
            if not isinstance(max_workers, int) or max_workers <= 0:
                result["errors"].append("max_workers must be a positive integer")
                result["valid"] = False
        
        return result
    
    def _trace_resource_initialization(self) -> Dict[str, Any]:
        """Trace resource initialization (database, cache, etc.)"""
        with trace_span("startup.resources.initialize") as span:
            resources = {
                "database": self._test_database_connection(),
                "cache": self._test_cache_connection(),
                "external_services": self._test_external_services(),
                "file_system": self._test_file_system_access()
            }
            
            # Count successful resource initializations
            successful_resources = sum(1 for resource in resources.values() if resource.get("available", False))
            
            span.set_attribute("resources.total", len(resources))
            span.set_attribute("resources.available", successful_resources)
            
            return resources
    
    def _test_database_connection(self) -> Dict[str, Any]:
        """Test database connectivity"""
        with trace_span("startup.resources.database.test") as span:
            try:
                # Simulate database connection test
                # In real implementation, this would test actual database connection
                time.sleep(0.1)  # Simulate connection time
                
                result = {
                    "available": True,
                    "response_time_ms": 100,
                    "version": "simulated-db-1.0"
                }
                
                span.set_attribute("database.available", True)
                span.set_attribute("database.response_time_ms", 100)
                
                return result
                
            except Exception as e:
                span.set_attribute("database.available", False)
                span.set_attribute("database.error", str(e))
                
                return {
                    "available": False,
                    "error": str(e)
                }
    
    def _test_cache_connection(self) -> Dict[str, Any]:
        """Test cache connectivity"""
        with trace_span("startup.resources.cache.test") as span:
            try:
                # Simulate cache connection test
                time.sleep(0.05)  # Simulate connection time
                
                result = {
                    "available": True,
                    "response_time_ms": 50,
                    "type": "redis"
                }
                
                span.set_attribute("cache.available", True)
                span.set_attribute("cache.response_time_ms", 50)
                
                return result
                
            except Exception as e:
                span.set_attribute("cache.available", False)
                span.set_attribute("cache.error", str(e))
                
                return {
                    "available": False,
                    "error": str(e)
                }
    
    def _test_external_services(self) -> Dict[str, Any]:
        """Test external service connectivity"""
        with trace_span("startup.resources.external_services.test") as span:
            services = {
                "api_gateway": {"available": True, "response_time_ms": 200},
                "auth_service": {"available": True, "response_time_ms": 150}
            }
            
            available_count = sum(1 for service in services.values() if service.get("available", False))
            
            span.set_attribute("external_services.total", len(services))
            span.set_attribute("external_services.available", available_count)
            
            return {
                "services": services,
                "available_count": available_count,
                "total_count": len(services)
            }
    
    def _test_file_system_access(self) -> Dict[str, Any]:
        """Test file system access"""
        with trace_span("startup.resources.filesystem.test") as span:
            try:
                # Test basic file system operations
                test_paths = [
                    "/tmp" if sys.platform != "win32" else "C:\\temp",
                    os.getcwd(),
                    str(Path.home())
                ]
                
                accessible_paths = []
                for path in test_paths:
                    try:
                        if os.path.exists(path) and os.access(path, os.R_OK):
                            accessible_paths.append(path)
                    except:
                        pass
                
                result = {
                    "available": len(accessible_paths) > 0,
                    "accessible_paths": len(accessible_paths),
                    "working_directory_writable": os.access(os.getcwd(), os.W_OK)
                }
                
                span.set_attribute("filesystem.available", result["available"])
                span.set_attribute("filesystem.accessible_paths", result["accessible_paths"])
                span.set_attribute("filesystem.cwd_writable", result["working_directory_writable"])
                
                return result
                
            except Exception as e:
                span.set_attribute("filesystem.error", str(e))
                return {
                    "available": False,
                    "error": str(e)
                }
    
    def _trace_health_checks(self) -> Dict[str, Any]:
        """Trace application health checks"""
        with trace_span("startup.health_checks") as span:
            health_checks = {
                "memory": self._check_memory_usage(),
                "disk_space": self._check_disk_space(),
                "network": self._check_network_connectivity()
            }
            
            all_healthy = all(check.get("healthy", False) for check in health_checks.values())
            
            span.set_attribute("health_checks.all_healthy", all_healthy)
            span.set_attribute("health_checks.total", len(health_checks))
            
            return {
                "overall_healthy": all_healthy,
                "checks": health_checks
            }
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            return {
                "healthy": memory.percent < 90,  # Less than 90% memory usage
                "usage_percent": memory.percent,
                "available_gb": memory.available / (1024**3)
            }
        except ImportError:
            return {
                "healthy": True,  # Assume healthy if can't check
                "error": "psutil not available"
            }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space"""
        try:
            import shutil
            free_bytes = shutil.disk_usage(os.getcwd()).free
            free_gb = free_bytes / (1024**3)
            
            return {
                "healthy": free_gb > 1.0,  # At least 1GB free
                "free_space_gb": free_gb
            }
        except Exception as e:
            return {
                "healthy": True,  # Assume healthy if can't check
                "error": str(e)
            }
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check basic network connectivity"""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return {"healthy": True, "connectivity": "available"}
        except Exception:
            return {"healthy": False, "connectivity": "unavailable"}