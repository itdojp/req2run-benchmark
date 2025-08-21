"""Configuration for reverse proxy"""
import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
import yaml


@dataclass
class BackendConfig:
    """Backend server configuration"""
    id: str
    url: str
    weight: int = 1
    health_check_enabled: bool = True


@dataclass
class ProxyConfig:
    """Proxy configuration"""
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080
    access_log: bool = True
    
    # Backend settings
    backends: List[BackendConfig] = field(default_factory=list)
    load_balancing_algorithm: str = "round_robin"  # round_robin, random, weighted, least_connections
    
    # Timeout settings
    request_timeout: float = 30.0
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    
    # Retry settings
    max_retries: int = 3
    retry_delay_base: float = 0.1
    retry_delay_max: float = 2.0
    
    # Circuit breaker settings
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_success_threshold: int = 2
    circuit_breaker_timeout: float = 30.0
    
    # Rate limiting settings
    rate_limit_enabled: bool = True
    rate_limit_algorithm: str = "token_bucket"  # token_bucket or sliding_window
    rate_limit_requests_per_second: int = 100
    rate_limit_burst: int = 200
    rate_limit_window: int = 60  # seconds
    rate_limit_per_client: bool = True
    rate_limit_per_client_requests: int = 10
    rate_limit_per_client_burst: int = 20
    
    # Health check settings
    health_check_enabled: bool = True
    health_check_path: str = "/health"
    health_check_interval: float = 10.0
    health_check_timeout: float = 5.0
    health_check_threshold: int = 3
    
    # Connection pool settings
    connection_pool_size: int = 1000
    connections_per_host: int = 100
    
    # CORS settings
    cors_enabled: bool = True
    
    # Request settings
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "ProxyConfig":
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = "config/proxy.yaml"
        
        config_file = Path(config_path)
        if not config_file.exists():
            # Return default configuration
            return cls.default()
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProxyConfig":
        """Create configuration from dictionary"""
        config = cls()
        
        # Server settings
        if "server" in data:
            server = data["server"]
            config.host = server.get("host", config.host)
            config.port = server.get("port", config.port)
            config.access_log = server.get("access_log", config.access_log)
        
        # Backend settings
        if "backends" in data:
            config.backends = [
                BackendConfig(**backend) for backend in data["backends"]
            ]
        
        if "load_balancing" in data:
            lb = data["load_balancing"]
            config.load_balancing_algorithm = lb.get("algorithm", config.load_balancing_algorithm)
        
        # Timeout settings
        if "timeouts" in data:
            timeouts = data["timeouts"]
            config.request_timeout = timeouts.get("request", config.request_timeout)
            config.connect_timeout = timeouts.get("connect", config.connect_timeout)
            config.read_timeout = timeouts.get("read", config.read_timeout)
        
        # Retry settings
        if "retry" in data:
            retry = data["retry"]
            config.max_retries = retry.get("max_attempts", config.max_retries)
            config.retry_delay_base = retry.get("delay_base", config.retry_delay_base)
            config.retry_delay_max = retry.get("delay_max", config.retry_delay_max)
        
        # Circuit breaker settings
        if "circuit_breaker" in data:
            cb = data["circuit_breaker"]
            config.circuit_breaker_enabled = cb.get("enabled", config.circuit_breaker_enabled)
            config.circuit_breaker_failure_threshold = cb.get("failure_threshold", config.circuit_breaker_failure_threshold)
            config.circuit_breaker_success_threshold = cb.get("success_threshold", config.circuit_breaker_success_threshold)
            config.circuit_breaker_timeout = cb.get("timeout", config.circuit_breaker_timeout)
        
        # Rate limiting settings
        if "rate_limit" in data:
            rl = data["rate_limit"]
            config.rate_limit_enabled = rl.get("enabled", config.rate_limit_enabled)
            config.rate_limit_algorithm = rl.get("algorithm", config.rate_limit_algorithm)
            config.rate_limit_requests_per_second = rl.get("requests_per_second", config.rate_limit_requests_per_second)
            config.rate_limit_burst = rl.get("burst", config.rate_limit_burst)
            config.rate_limit_window = rl.get("window", config.rate_limit_window)
            
            if "per_client" in rl:
                pc = rl["per_client"]
                config.rate_limit_per_client = pc.get("enabled", config.rate_limit_per_client)
                config.rate_limit_per_client_requests = pc.get("requests_per_second", config.rate_limit_per_client_requests)
                config.rate_limit_per_client_burst = pc.get("burst", config.rate_limit_per_client_burst)
        
        # Health check settings
        if "health_check" in data:
            hc = data["health_check"]
            config.health_check_enabled = hc.get("enabled", config.health_check_enabled)
            config.health_check_path = hc.get("path", config.health_check_path)
            config.health_check_interval = hc.get("interval", config.health_check_interval)
            config.health_check_timeout = hc.get("timeout", config.health_check_timeout)
            config.health_check_threshold = hc.get("failure_threshold", config.health_check_threshold)
        
        # Connection pool settings
        if "connection_pool" in data:
            cp = data["connection_pool"]
            config.connection_pool_size = cp.get("size", config.connection_pool_size)
            config.connections_per_host = cp.get("per_host", config.connections_per_host)
        
        # Other settings
        config.cors_enabled = data.get("cors_enabled", config.cors_enabled)
        config.max_request_size = data.get("max_request_size", config.max_request_size)
        
        return config
    
    @classmethod
    def default(cls) -> "ProxyConfig":
        """Create default configuration"""
        return cls(
            backends=[
                BackendConfig(
                    id="backend1",
                    url="http://localhost:8001",
                    weight=1
                ),
                BackendConfig(
                    id="backend2",
                    url="http://localhost:8002",
                    weight=1
                )
            ]
        )