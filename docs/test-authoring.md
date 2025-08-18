# Test Authoring Guidelines
# テスト作成ガイドライン

## Overview / 概要

This document provides guidelines for creating comprehensive test suites for Req2Run benchmark problems. Tests must be rigorous, cover edge cases, and prevent gaming of the benchmark.

本ドキュメントは、Req2Runベンチマーク問題の包括的なテストスイート作成のためのガイドラインを提供します。テストは厳密で、エッジケースをカバーし、ベンチマークの不正を防ぐ必要があります。

## Test Categories / テストカテゴリ

### 1. Unit Tests (40% weight)
Tests individual functions and methods in isolation.

```python
def test_todo_creation():
    """Test that a todo can be created with valid data."""
    todo = create_todo(title="Test", description="Description")
    assert todo.id is not None
    assert todo.title == "Test"
    assert todo.completed is False
```

**Requirements:**
- Test all public functions/methods
- Include both positive and negative test cases
- Mock external dependencies
- Minimum 80% code coverage

### 2. Integration Tests (40% weight)
Tests interactions between components and API endpoints.

```python
def test_todo_crud_flow():
    """Test complete CRUD flow for todos."""
    # Create
    response = client.post("/todos", json={"title": "Test"})
    assert response.status_code == 201
    todo_id = response.json()["id"]
    
    # Read
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    
    # Update
    response = client.put(f"/todos/{todo_id}", json={"completed": True})
    assert response.status_code == 200
    
    # Delete
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 204
```

**Requirements:**
- Test all API endpoints
- Verify request/response formats
- Test authentication and authorization
- Test error handling

### 3. Property-Based Tests (20% weight)
Tests invariants and properties that should always hold.

```python
from hypothesis import given, strategies as st

@given(
    title=st.text(min_size=1, max_size=200),
    description=st.text(max_size=1000)
)
def test_todo_title_property(title, description):
    """Todo title should always be preserved exactly."""
    todo = create_todo(title=title, description=description)
    assert todo.title == title
    assert len(todo.title) <= 200
```

**Requirements:**
- Test boundary conditions
- Test with random valid inputs
- Verify invariants hold
- Include fuzz testing for security

## Test Augmentation Strategy / テスト強化戦略

Following EvalPlus methodology, augment tests to prevent trivial solutions:

### 1. Boundary Value Testing
```python
# Test minimum values
test_with_empty_string("")
test_with_zero(0)
test_with_negative(-1)

# Test maximum values
test_with_max_int(2**31 - 1)
test_with_long_string("x" * 10000)
test_with_many_items([i for i in range(10000)])

# Test edge cases
test_with_unicode("🚀 Unicode test")
test_with_special_chars("'; DROP TABLE--")
```

### 2. Failure Case Testing
```python
def test_invalid_authentication():
    """Test various authentication failure scenarios."""
    # Missing token
    response = client.get("/todos")
    assert response.status_code == 401
    
    # Invalid token
    headers = {"Authorization": "Bearer invalid"}
    response = client.get("/todos", headers=headers)
    assert response.status_code == 401
    
    # Expired token
    expired_token = create_expired_token()
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/todos", headers=headers)
    assert response.status_code == 401
```

### 3. Concurrency Testing
```python
import asyncio
import aiohttp

async def test_concurrent_requests():
    """Test handling of concurrent requests."""
    async def make_request(session, i):
        async with session.get(f"/todos?page={i}") as response:
            return response.status
    
    async with aiohttp.ClientSession() as session:
        tasks = [make_request(session, i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        assert all(status == 200 for status in results)
```

## Performance Test Requirements / パフォーマンステスト要件

### Load Testing with Locust
```python
from locust import HttpUser, task, between

class TodoUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/auth/login", json={
            "username": "test",
            "password": "password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def list_todos(self):
        self.client.get("/todos", headers=self.headers)
    
    @task(1)
    def create_todo(self):
        self.client.post("/todos", 
            json={"title": "Test", "description": "Test"},
            headers=self.headers
        )
```

**Metrics to Measure:**
- P95 and P99 latency
- Requests per second (RPS)
- Error rate under load
- Resource usage (CPU, memory)

## Security Test Requirements / セキュリティテスト要件

### 1. Input Validation Testing
```python
def test_sql_injection():
    """Test SQL injection prevention."""
    malicious_inputs = [
        "'; DROP TABLE todos--",
        "1' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users--"
    ]
    
    for payload in malicious_inputs:
        response = client.get(f"/todos?search={payload}")
        assert response.status_code in [200, 400]  # Not 500
        # Verify no data leak
        assert "users" not in response.text.lower()
```

### 2. Authentication Testing
```python
def test_jwt_security():
    """Test JWT token security."""
    # Test algorithm confusion
    fake_token = create_token_with_none_algorithm()
    response = client.get("/todos", 
        headers={"Authorization": f"Bearer {fake_token}"})
    assert response.status_code == 401
    
    # Test token tampering
    tampered_token = modify_token_payload(valid_token)
    response = client.get("/todos",
        headers={"Authorization": f"Bearer {tampered_token}"})
    assert response.status_code == 401
```

## Test Data Management / テストデータ管理

### Fixtures
```python
import pytest
from datetime import datetime

@pytest.fixture
def sample_user():
    """Provide a sample user for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }

@pytest.fixture
def sample_todos():
    """Provide sample todos for testing."""
    return [
        {"title": "Todo 1", "description": "Description 1", "completed": False},
        {"title": "Todo 2", "description": "Description 2", "completed": True},
        {"title": "Todo 3", "description": "Description 3", "completed": False}
    ]
```

### Test Isolation
```python
@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test."""
    yield
    # Cleanup after test
    truncate_all_tables()
```

## Coverage Requirements / カバレッジ要件

### Minimum Coverage Targets
- Line coverage: ≥ 80%
- Branch coverage: ≥ 70%
- Function coverage: ≥ 90%

### Coverage Measurement
```bash
# Python with pytest-cov
pytest --cov=src --cov-report=html --cov-report=term

# JavaScript with Jest
jest --coverage --coverageReporters=html

# Go with built-in coverage
go test -cover -coverprofile=coverage.out ./...
```

## Oracle Problem Prevention / オラクル問題の防止

To prevent implementations that pass tests but don't truly solve the problem:

### 1. Randomized Test Cases
```python
import random
import string

def test_with_random_data():
    """Test with randomly generated data."""
    for _ in range(100):
        title = ''.join(random.choices(string.ascii_letters, k=20))
        todo = create_todo(title=title)
        assert todo.title == title
```

### 2. Hidden Test Cases
- Keep 20% of test cases private
- Run these only during evaluation
- Rotate test cases periodically

### 3. Metamorphic Testing
```python
def test_metamorphic_relation():
    """Test that certain transformations preserve relationships."""
    todos1 = get_todos(limit=10)
    todos2 = get_todos(limit=20)
    
    # First 10 of limit=20 should equal limit=10
    assert todos2[:10] == todos1
```

## Test Quality Checklist / テスト品質チェックリスト

- [ ] All MUST requirements have corresponding tests
- [ ] Edge cases and boundary values are tested
- [ ] Error conditions are properly tested
- [ ] Performance requirements are validated
- [ ] Security vulnerabilities are checked
- [ ] Tests are deterministic and reproducible
- [ ] Test data is properly isolated
- [ ] Coverage targets are met
- [ ] Property-based tests are included
- [ ] Concurrency is tested where applicable

## References / 参考文献

- [EvalPlus Test Augmentation](https://github.com/evalplus/evalplus)
- [Hypothesis for Property-Based Testing](https://hypothesis.readthedocs.io/)
- [Locust for Load Testing](https://locust.io/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)