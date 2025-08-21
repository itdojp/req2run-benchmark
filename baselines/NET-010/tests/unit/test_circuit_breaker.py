"""Unit tests for circuit breaker"""
import pytest
import time
from src.circuit_breaker import CircuitBreaker, CircuitState


def test_circuit_breaker_initial_state():
    """Test circuit breaker starts in closed state"""
    cb = CircuitBreaker(
        backend_id="test",
        failure_threshold=3,
        success_threshold=2,
        timeout=1.0
    )
    
    assert cb.state == CircuitState.CLOSED
    assert cb.can_request() is True


def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold failures"""
    cb = CircuitBreaker(
        backend_id="test",
        failure_threshold=3,
        success_threshold=2,
        timeout=1.0
    )
    
    # Record failures
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_request() is False


def test_circuit_breaker_half_open_after_timeout():
    """Test circuit breaker transitions to half-open after timeout"""
    cb = CircuitBreaker(
        backend_id="test",
        failure_threshold=2,
        success_threshold=2,
        timeout=0.1  # 100ms timeout
    )
    
    # Open the circuit
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    
    # Should still be open immediately
    assert cb.can_request() is False
    
    # Wait for timeout
    time.sleep(0.15)
    
    # Should transition to half-open
    assert cb.can_request() is True
    assert cb.state == CircuitState.HALF_OPEN


def test_circuit_breaker_closes_after_successes():
    """Test circuit breaker closes after success threshold in half-open"""
    cb = CircuitBreaker(
        backend_id="test",
        failure_threshold=2,
        success_threshold=2,
        timeout=0.1
    )
    
    # Open the circuit
    cb.record_failure()
    cb.record_failure()
    
    # Wait for timeout
    time.sleep(0.15)
    cb.can_request()  # Transition to half-open
    
    # Record successes
    cb.record_success()
    assert cb.state == CircuitState.HALF_OPEN
    
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_reopens_on_failure_in_half_open():
    """Test circuit breaker reopens on failure in half-open state"""
    cb = CircuitBreaker(
        backend_id="test",
        failure_threshold=2,
        success_threshold=2,
        timeout=0.1
    )
    
    # Open the circuit
    cb.record_failure()
    cb.record_failure()
    
    # Wait for timeout
    time.sleep(0.15)
    cb.can_request()  # Transition to half-open
    
    # Record failure in half-open
    cb.record_failure()
    assert cb.state == CircuitState.OPEN