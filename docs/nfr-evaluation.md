# Non-Functional Requirements (NFR) Evaluation Guide

## Version 1.0.0

This document provides detailed guidelines for evaluating non-functional requirements in the Req2Run benchmark framework.

## Overview

Non-functional requirements (NFRs) assess the quality attributes of code beyond its functional correctness. These include performance, security, maintainability, reliability, and efficiency.

## Evaluation Categories

### 1. Code Complexity Metrics

#### Cyclomatic Complexity (McCabe)
- **Tool**: `radon` (Python), `gocyclo` (Go), `complexity-report` (JavaScript)
- **Scoring**:
  ```
  Score = 100 - (avg_complexity * 5)
  
  where:
  - complexity 1-5: Simple, low risk (100-75 points)
  - complexity 6-10: More complex, moderate risk (74-50 points)
  - complexity 11-20: Complex, high risk (49-25 points)
  - complexity 21+: Very complex, very high risk (24-0 points)
  ```
- **Per-function limits**:
  - MUST: No function exceeds complexity of 20
  - SHOULD: Average complexity below 10
  - MAY: All functions below complexity of 5

#### Cognitive Complexity
- **Tool**: `cognitive-complexity` (multi-language)
- **Measurement**: Difficulty for humans to understand code
- **Scoring**: Similar scale to cyclomatic complexity

### 2. Code Quality Indicators

#### Naming Conventions
- **Rules**:
  - **Python**: PEP 8 compliance
    - Functions/variables: `snake_case`
    - Classes: `PascalCase`
    - Constants: `UPPER_SNAKE_CASE`
  - **JavaScript/TypeScript**: 
    - Functions/variables: `camelCase`
    - Classes/Components: `PascalCase`
    - Constants: `UPPER_SNAKE_CASE`
  - **Go**: 
    - Exported: `PascalCase`
    - Unexported: `camelCase`

- **Scoring**:
  ```
  naming_score = (compliant_names / total_names) * 100
  ```

#### Documentation Coverage
- **Requirements**:
  - All public functions MUST have docstrings/comments
  - All classes MUST have class-level documentation
  - Complex algorithms SHOULD have inline comments
  - README MUST exist with setup/usage instructions

- **Scoring**:
  ```
  doc_score = (documented_entities / total_public_entities) * 100
  ```

#### Type Hints/Annotations
- **Python**: Type hints for all function parameters and returns
- **TypeScript**: Strict mode enabled, no `any` types
- **Go**: Inherently typed

- **Scoring**:
  ```
  type_score = (typed_functions / total_functions) * 100
  ```

### 3. Maintainability Metrics

#### Function Length
- **Limits**:
  - Maximum: 50 lines (excluding comments/docstrings)
  - Recommended: 20 lines
  - Ideal: 10 lines

- **Scoring**:
  ```
  length_score = 100 * (1 - (avg_length / 50))
  ```

#### File Organization
- **Requirements**:
  - Single responsibility per file
  - Logical directory structure
  - Separation of concerns

#### Dependency Management
- **Metrics**:
  - Direct dependencies count
  - Transitive dependencies count
  - Outdated dependencies
  - Security vulnerabilities in dependencies

### 4. Reliability Indicators

#### Error Handling
- **Requirements**:
  - All external I/O operations MUST have error handling
  - All network operations MUST have timeout handling
  - All resource allocations MUST have cleanup

- **Scoring**:
  ```
  error_handling_score = (handled_operations / total_risky_operations) * 100
  ```

#### Input Validation
- **Requirements**:
  - All user inputs MUST be validated
  - All API inputs MUST be sanitized
  - Boundary conditions MUST be checked

- **Scoring**:
  ```
  validation_score = (validated_inputs / total_inputs) * 100
  ```

#### Resource Management
- **Checks**:
  - Proper file handle closure
  - Database connection pooling
  - Memory leak prevention
  - Goroutine/thread cleanup

### 5. Performance Efficiency

#### Algorithm Efficiency
- **Measurement**: Time and space complexity
- **Scoring**:
  ```
  For each algorithm:
  - O(1), O(log n): 100 points
  - O(n): 80 points
  - O(n log n): 60 points
  - O(n²): 40 points
  - O(n³) or worse: 20 points
  ```

#### Resource Usage
- **Metrics**:
  - Peak memory usage
  - CPU utilization
  - I/O operations count
  - Network calls optimization

#### Caching Strategy
- **Evaluation**:
  - Appropriate use of memoization
  - Database query optimization
  - API response caching
  - Static asset optimization

### 6. Security Quality

#### Static Security Analysis
- **Tools**:
  - **Python**: `bandit`, `safety`
  - **JavaScript**: `eslint-plugin-security`, `snyk`
  - **Go**: `gosec`, `nancy`

- **Scoring**:
  ```
  security_score = 100 - (high_issues * 10) - (medium_issues * 5) - (low_issues * 2)
  ```

#### Secure Coding Practices
- **Checks**:
  - No hardcoded secrets
  - Proper input sanitization
  - SQL injection prevention
  - XSS prevention
  - CSRF protection
  - Secure random number generation

### 7. Testing Quality

#### Test Coverage
- **Metrics**:
  - Line coverage
  - Branch coverage
  - Function coverage

- **Scoring**:
  ```
  coverage_score = (line_coverage * 0.4) + (branch_coverage * 0.4) + (function_coverage * 0.2)
  ```

#### Test Quality
- **Indicators**:
  - Test isolation (no interdependencies)
  - Test speed (unit tests < 100ms)
  - Test clarity (descriptive names)
  - Edge case coverage
  - Property-based testing usage

## Composite NFR Score Calculation

```python
def calculate_nfr_score(metrics):
    """Calculate composite NFR score."""
    
    weights = {
        'complexity': 0.20,
        'naming': 0.10,
        'documentation': 0.15,
        'error_handling': 0.15,
        'validation': 0.10,
        'performance': 0.10,
        'security': 0.10,
        'testing': 0.10
    }
    
    total_score = 0
    for metric, weight in weights.items():
        total_score += metrics[metric] * weight
    
    return total_score
```

## Automated Evaluation Pipeline

### Step 1: Static Analysis
```bash
# Python
radon cc -s -a src/
pylint src/ --output-format=json
mypy src/ --json-output

# JavaScript
npx complexity-report src/
npx eslint src/ --format json

# Go
gocyclo -avg src/
golint -json src/
```

### Step 2: Security Scanning
```bash
# Python
bandit -r src/ -f json
safety check --json

# JavaScript
npx snyk test --json

# Go
gosec -fmt json ./...
```

### Step 3: Test Coverage
```bash
# Python
pytest --cov=src --cov-report=json

# JavaScript
npm test -- --coverage --json

# Go
go test -coverprofile=coverage.out -json ./...
```

### Step 4: Custom Metrics
```python
# Custom analyzer for naming conventions, documentation, etc.
python -m req2run.analyzers.nfr_analyzer --input src/ --output nfr_report.json
```

## NFR Improvement Guidelines

### For Developers

1. **Reduce Complexity**:
   - Extract methods for repeated code
   - Use early returns to reduce nesting
   - Split complex functions

2. **Improve Naming**:
   - Use descriptive, intention-revealing names
   - Avoid abbreviations
   - Be consistent with conventions

3. **Enhance Documentation**:
   - Write docstrings before implementation
   - Include examples in complex functions
   - Keep README up-to-date

4. **Strengthen Error Handling**:
   - Never silently catch exceptions
   - Provide meaningful error messages
   - Use proper logging levels

5. **Optimize Performance**:
   - Profile before optimizing
   - Use appropriate data structures
   - Implement caching where beneficial

## References

- [Code Complete 2nd Edition](https://www.oreilly.com/library/view/code-complete-2nd/0735619670/)
- [Clean Code: A Handbook of Agile Software Craftsmanship](https://www.oreilly.com/library/view/clean-code/9780136083238/)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [ISO/IEC 25010:2011 Software Quality Model](https://iso25000.com/index.php/en/iso-25000-standards/iso-25010)