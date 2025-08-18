# Req2Run Evaluation Metrics Specification
# Req2Run 評価メトリクス仕様

## Version 1.0.0

This document defines the precise evaluation metrics and calculation methods used in the Req2Run benchmark framework.  
本ドキュメントは、Req2Runベンチマークフレームワークで使用される評価メトリクスと計算方法を正確に定義します。

## Overall Score Calculation

### Formula / 計算式

```
Total_Score = 0.35 × Functional_Coverage + 
              0.25 × Test_Pass_Rate + 
              0.15 × Performance_Score + 
              0.15 × Code_Quality_Score + 
              0.10 × Security_Score
```

**Mathematical Notation**:
```
S_total = Σ(w_i × s_i) where i ∈ {func, test, perf, qual, sec}
w = [0.35, 0.25, 0.15, 0.15, 0.10]  # weights vector
s = [s_func, s_test, s_perf, s_qual, s_sec]  # scores vector
```

### Component Definitions

#### 1. Functional Coverage (35%)
- **Definition**: Percentage of required functionality successfully implemented
- **Calculation**: 
  ```python
  Functional_Coverage = (passed_requirements / total_requirements) × 100
  
  Where:
  - passed_requirements: Count of MUST requirements passing all tests
  - total_requirements: Total count of MUST requirements (RFC 2119)
  ```
- **RFC 2119 Requirement Levels**:
  - **MUST/REQUIRED/SHALL**: Mandatory (100% must pass)
  - **SHOULD/RECOMMENDED**: Strongly recommended (+2% bonus if all implemented)
  - **MAY/OPTIONAL**: Optional (no penalty if not implemented)
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

### Determinism / 決定性
- Random seed fixed: `PYTHONHASHSEED=42`
- NumPy seed: `np.random.seed(42)`
- Python random: `random.seed(42)`
- TensorFlow: `tf.random.set_seed(42)`
- PyTorch: `torch.manual_seed(42)`
- All timestamps use UTC
- Filesystem operations use sorted order

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

## Cost and Efficiency Metrics / コスト・効率指標

### Generation Efficiency
```python
Generation_Efficiency = Total_Score / Generation_Cost

Where:
- Generation_Cost = (tokens_used / 1000) × token_price_per_1k + 
                   (generation_time_seconds / 3600) × compute_hourly_rate
```

### Execution Efficiency
```python
Execution_Efficiency = Total_Score / Execution_Time_Seconds
```

### Score per Dollar
```python
Score_Per_Dollar = Total_Score / Total_Cost_USD
```

## Result Schema / 結果スキーマ

```json
{
  "version": "1.0.0",
  "problem_id": "WEB-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "model": {
    "name": "gpt-4",
    "version": "2024-01-01",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "scores": {
    "total": 87.925,
    "functional_coverage": 95.0,
    "test_pass_rate": 88.5,
    "performance": 75.0,
    "code_quality": 82.0,
    "security": 90.0,
    "grade": "Silver"
  },
  "generation": {
    "tokens_used": 15234,
    "time_seconds": 187,
    "cost_usd": 0.457,
    "attempts": 1
  },
  "execution": {
    "wall_time_seconds": 45.3,
    "cpu_seconds": 42.1,
    "peak_memory_mb": 512,
    "peak_cpu_percent": 85
  },
  "artifacts": {
    "submission": "artifacts/WEB-001/submission.tar.gz",
    "logs": "artifacts/WEB-001/execution.log",
    "report": "artifacts/WEB-001/report.html"
  }
}
```

## Comparison with Existing Benchmarks / 既存ベンチマークとの比較

| Benchmark | Focus | Primary Metric | Req2Run Distinction |
|-----------|-------|----------------|--------------------|
| HumanEval/MBPP | Function-level coding | Pass@k | Full application + NFR evaluation |
| SWE-bench | Issue resolution | %Resolved | Requirements-to-code generation |
| EvalPlus | Test robustness | Enhanced Pass@k | Production readiness metrics |
| MultiPL-E | Multi-language | Cross-language Pass@k | Deployment + operations focus |
| ArchCode/HumanEval-NFR | Design quality | NFR compliance | Comprehensive NFR scoring |

> **Req2Run** evaluates *requirements-to-running-code* with **functional + non-functional (performance/security/quality)** metrics in a **unified containerized environment**, complementing function-level benchmarks (HumanEval/MBPP) and code modification benchmarks (SWE-bench).

## References

- Pass@k metric: [HumanEval](https://github.com/openai/human-eval)
- Test augmentation: [EvalPlus](https://github.com/evalplus/evalplus)
- Performance evaluation: [EvalPerf](https://github.com/evalplus/evalperf)
- Security sandboxing: [nsjail](https://github.com/google/nsjail)
- Static analysis: [Bandit](https://github.com/PyCQA/bandit), [Semgrep](https://semgrep.dev)
- NFR frameworks: [ArchCode](https://arxiv.org/abs/2408.00994), [HumanEval-NFR](https://aclanthology.org/2024.acl-long.730.pdf)
- Requirements syntax: [EARS](https://alistairmavin.com/ears/), [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)