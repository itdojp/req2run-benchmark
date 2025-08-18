# Evaluation Metrics Specification

## Version 1.0.0

This document defines the precise evaluation metrics and calculation methods used in the Req2Run benchmark framework.

## Overall Score Calculation

### Formula

```
Total_Score = 0.35 × Functional_Coverage + 
              0.25 × Test_Pass_Rate + 
              0.15 × Performance_Score + 
              0.15 × Code_Quality_Score + 
              0.10 × Security_Score
```

### Component Definitions

#### 1. Functional Coverage (35%)
- **Definition**: Percentage of required functionality successfully implemented
- **Calculation**: `(implemented_features / total_required_features) × 100`
- **Data Source**: Automated feature detection via AST analysis and API endpoint verification

#### 2. Test Pass Rate (25%)
- **Definition**: Percentage of test cases passed
- **Calculation**: `(passed_tests / total_tests) × 100`
- **Test Categories**:
  - Unit tests (40% weight)
  - Integration tests (40% weight)
  - Property-based tests (20% weight)

#### 3. Performance Score (15%)
- **Metrics**:
  - P95 Latency: Must meet specified threshold
  - Throughput (RPS): Must meet minimum requirements
  - Resource Usage: CPU < 80%, Memory < specified limit
- **Calculation**: 
  ```
  Performance_Score = 0.4 × latency_score + 
                     0.4 × throughput_score + 
                     0.2 × resource_score
  ```

#### 4. Code Quality Score (15%)
- **Metrics**:
  - Cyclomatic Complexity: < 10 per function (McCabe)
  - Code Coverage: > 80% line coverage
  - Linting: No high-severity issues
  - Documentation: Docstring coverage > 70%
- **Calculation**:
  ```
  Code_Quality = 0.25 × complexity_score + 
                0.25 × coverage_score + 
                0.25 × linting_score + 
                0.25 × documentation_score
  ```

#### 5. Security Score (10%)
- **Two-tier Evaluation**:
  - **Runtime Security (50%)**:
    - Network isolation compliance
    - Resource limit compliance
    - Syscall restrictions compliance
  - **Static Analysis (50%)**:
    - Bandit/Semgrep findings
    - High severity: -2 points each
    - Medium severity: -1 point each
    - Low severity: -0.5 points each
    - Maximum deduction: -10 points
- **Calculation**: 
  ```
  Security_Score = 0.5 × runtime_score + 0.5 × max(0, 100 - static_deductions)
  ```

## Scoring Rules

### Rounding
- All intermediate calculations use floating-point precision
- Final scores are rounded to 3 decimal places using HALF_UP rounding
- Display scores are shown as percentages with 1 decimal place

### Determinism
- Random seed fixed: `PYTHONHASHSEED=0`
- NumPy seed: `np.random.seed(42)`
- Python random: `random.seed(42)`
- All timestamps use UTC

### Pass Criteria
- **Pass Threshold**: Total Score ≥ 70.0%
- **Mandatory Requirements**:
  - Functional Coverage ≥ 100% (all MUST requirements)
  - No critical security vulnerabilities
  - No runtime failures

### Grade Classification
- **Gold**: Score ≥ 90.0%
- **Silver**: Score ≥ 80.0%
- **Bronze**: Score ≥ 70.0%
- **Fail**: Score < 70.0%

## Penalties and Bonuses

### Penalties
- **Timeout**: -5% if execution exceeds time limit
- **Crash**: -10% for unhandled exceptions
- **Security Violation**: -15% for sandbox escape attempts
- **Resource Overuse**: -5% per violation

### Bonuses
- **Early Completion**: +2% if completed in < 50% of time limit
- **Exceptional Performance**: +3% if P99 < 50% of P95 requirement
- **Clean Code**: +2% if cyclomatic complexity < 5 for all functions

## Version History

- **v1.0.0** (2024-12): Initial release with weighted scoring
- Future versions will maintain backward compatibility or provide migration tools

## Implementation Notes

The evaluation engine (`req2run.metrics.MetricsCalculator`) implements these formulas exactly as specified. Any deviation from this specification should be considered a bug.

### Example Calculation

```python
# Given scores
functional_coverage = 95.0  # 95%
test_pass_rate = 88.5      # 88.5%
performance_score = 75.0    # 75%
code_quality_score = 82.0   # 82%
security_score = 90.0       # 90%

# Calculate total
total_score = (0.35 * 95.0 + 
               0.25 * 88.5 + 
               0.15 * 75.0 + 
               0.15 * 82.0 + 
               0.10 * 90.0)
# = 33.25 + 22.125 + 11.25 + 12.3 + 9.0
# = 87.925 → 87.9% (Silver)
```

## References

- Pass@k metric: [HumanEval](https://github.com/openai/human-eval)
- Test augmentation: [EvalPlus](https://github.com/evalplus/evalplus)
- Performance evaluation: [EvalPerf](https://github.com/evalplus/evalperf)
- Security sandboxing: [nsjail](https://github.com/google/nsjail)
- Static analysis: [Bandit](https://github.com/PyCQA/bandit), [Semgrep](https://semgrep.dev)