"""Circuit breaker implementation for backend protection"""
import logging
import time
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass, field

from .config import ProxyConfig

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreaker:
    """Circuit breaker for a single backend"""
    backend_id: str
    failure_threshold: int
    success_threshold: int
    timeout: float
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    total_requests: int = 0
    total_failures: int = 0
    
    def record_success(self):
        """Record a successful request"""
        self.total_requests += 1
        
        if self.state == CircuitState.CLOSED:
            self.failure_count = 0
            
        elif self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._transition_to_closed()
                
    def record_failure(self):
        """Record a failed request"""
        self.total_requests += 1
        self.total_failures += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()
                
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
    
    def can_request(self) -> bool:
        """Check if requests are allowed"""
        current_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
            
        elif self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time and \
               current_time - self.last_failure_time >= self.timeout:
                self._transition_to_half_open()
                return True
            return False
            
        elif self.state == CircuitState.HALF_OPEN:
            return True
            
        return False
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        if self.state != CircuitState.OPEN:
            logger.warning(f"Circuit breaker for {self.backend_id} opened")
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            self.failure_count = 0
            self.success_count = 0
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        if self.state != CircuitState.CLOSED:
            logger.info(f"Circuit breaker for {self.backend_id} closed")
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()
            self.failure_count = 0
            self.success_count = 0
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        if self.state != CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker for {self.backend_id} half-open")
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = time.time()
            self.success_count = 0
    
    def get_status(self) -> Dict:
        """Get circuit breaker status"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "failure_rate": self.total_failures / max(1, self.total_requests),
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change
        }


class CircuitBreakerManager:
    """Manages circuit breakers for all backends"""
    
    def __init__(self, config: ProxyConfig):
        self.config = config
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Initialize circuit breakers for each backend
        for backend in config.backends:
            self.circuit_breakers[backend.id] = CircuitBreaker(
                backend_id=backend.id,
                failure_threshold=config.circuit_breaker_failure_threshold,
                success_threshold=config.circuit_breaker_success_threshold,
                timeout=config.circuit_breaker_timeout
            )
    
    def can_request(self, backend_id: str) -> bool:
        """Check if requests are allowed for a backend"""
        if backend_id not in self.circuit_breakers:
            # No circuit breaker for this backend, allow request
            return True
        
        return self.circuit_breakers[backend_id].can_request()
    
    def record_success(self, backend_id: str):
        """Record a successful request"""
        if backend_id in self.circuit_breakers:
            self.circuit_breakers[backend_id].record_success()
    
    def record_failure(self, backend_id: str):
        """Record a failed request"""
        if backend_id in self.circuit_breakers:
            self.circuit_breakers[backend_id].record_failure()
    
    def get_status(self) -> Dict[str, Dict]:
        """Get status of all circuit breakers"""
        return {
            backend_id: cb.get_status()
            for backend_id, cb in self.circuit_breakers.items()
        }
    
    def reset(self, backend_id: Optional[str] = None):
        """Reset circuit breaker(s)"""
        if backend_id:
            if backend_id in self.circuit_breakers:
                self.circuit_breakers[backend_id]._transition_to_closed()
        else:
            # Reset all circuit breakers
            for cb in self.circuit_breakers.values():
                cb._transition_to_closed()