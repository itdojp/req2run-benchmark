# Req2Run System Architecture
# Req2Run システムアーキテクチャ

## System Overview / システム概要

Req2Run is a comprehensive benchmark framework for evaluating AI code generation systems. It transforms detailed requirement specifications into running code and performs automated evaluation across multiple dimensions.

Req2Runは、AIコード生成システムを評価するための包括的なベンチマークフレームワークです。詳細な要件仕様を実行可能なコードに変換し、複数の次元で自動評価を実行します。

## Architecture Diagram / アーキテクチャ図

```mermaid
graph TB
    subgraph "Input Layer / 入力層"
        PS[Problem Specifications<br/>問題仕様]
        RS[Requirements<br/>RFC 2119/EARS]
        TC[Test Cases<br/>テストケース]
    end
    
    subgraph "AI Generation Layer / AI生成層"
        AI[AI/LLM Systems<br/>AIシステム]
        CG[Code Generator<br/>コード生成器]
        TS[Test Suite Generator<br/>テスト生成器]
    end
    
    subgraph "Evaluation Framework / 評価フレームワーク"
        subgraph "Core Components / コアコンポーネント"
            EV[Evaluator<br/>評価エンジン]
            RN[Runner<br/>実行環境]
            MT[Metrics Calculator<br/>メトリクス計算]
            RP[Reporter<br/>レポート生成]
        end
        
        subgraph "Execution Environments / 実行環境"
            DK[Docker Container<br/>Dockerコンテナ]
            K8[Kubernetes Pod<br/>K8s Pod]
            LC[Local Environment<br/>ローカル環境]
        end
        
        subgraph "Security Layer / セキュリティ層"
            SB[Sandbox<br/>サンドボックス]
            NS[nsjail]
            FJ[firejail]
        end
    end
    
    subgraph "Analysis Layer / 分析層"
        subgraph "Metrics / メトリクス"
            FC[Functional Coverage<br/>機能充足率]
            PT[Performance Test<br/>性能テスト]
            SC[Security Scan<br/>セキュリティ]
            QC[Code Quality<br/>コード品質]
        end
        
        subgraph "Tools / ツール"
            PF[Performance Tools<br/>Locust/wrk]
            ST[Security Tools<br/>Bandit/Trivy]
            QT[Quality Tools<br/>Black/Flake8]
        end
    end
    
    subgraph "Output Layer / 出力層"
        SR[Score Results<br/>スコア結果]
        HR[HTML Report<br/>HTMLレポート]
        JR[JSON Results<br/>JSON結果]
        LB[Leaderboard<br/>リーダーボード]
    end
    
    subgraph "Storage Layer / ストレージ層"
        DB[(Results Database<br/>結果DB)]
        FS[File Storage<br/>ファイル保存]
        AR[Artifacts<br/>成果物]
    end
    
    %% Flow connections
    PS --> AI
    RS --> AI
    TC --> EV
    
    AI --> CG
    CG --> EV
    TS --> EV
    
    EV --> RN
    RN --> DK
    RN --> K8
    RN --> LC
    
    DK --> SB
    K8 --> SB
    SB --> NS
    SB --> FJ
    
    RN --> MT
    MT --> FC
    MT --> PT
    MT --> SC
    MT --> QC
    
    FC --> PF
    PT --> PF
    SC --> ST
    QC --> QT
    
    MT --> RP
    RP --> SR
    RP --> HR
    RP --> JR
    
    SR --> DB
    HR --> FS
    JR --> DB
    DB --> LB
    AR --> FS
```

## Component Architecture / コンポーネントアーキテクチャ

```mermaid
classDiagram
    class Evaluator {
        -problem_spec: dict
        -submission_path: Path
        -config: EvaluationConfig
        +evaluate() Result
        +validate_requirements() bool
        +run_tests() TestResult
    }
    
    class Runner {
        <<abstract>>
        +build() bool
        +deploy() bool
        +execute() ExecutionResult
        +cleanup() void
    }
    
    class DockerRunner {
        -container_id: str
        -image_name: str
        +build_image() bool
        +run_container() bool
    }
    
    class KubernetesRunner {
        -namespace: str
        -pod_name: str
        +create_pod() bool
        +get_logs() str
    }
    
    class LocalRunner {
        -process: Process
        -venv_path: Path
        +setup_environment() bool
        +run_process() bool
    }
    
    class MetricsCalculator {
        -results: dict
        -weights: dict
        +calculate_functional() float
        +calculate_performance() float
        +calculate_security() float
        +calculate_quality() float
        +get_total_score() float
    }
    
    class Reporter {
        -results: EvaluationResult
        -format: ReportFormat
        +generate_html() str
        +generate_json() dict
        +generate_markdown() str
        +create_charts() bytes
    }
    
    class SecuritySandbox {
        -backend: str
        -config: dict
        +prepare_environment() Path
        +execute_sandboxed() Result
        +validate_submission() bool
    }
    
    Runner <|-- DockerRunner
    Runner <|-- KubernetesRunner
    Runner <|-- LocalRunner
    
    Evaluator --> Runner
    Evaluator --> MetricsCalculator
    Evaluator --> Reporter
    Runner --> SecuritySandbox
```

## Data Flow / データフロー

```mermaid
sequenceDiagram
    participant User as User/AI System
    participant CLI as CLI Interface
    participant Eval as Evaluator
    participant Runner as Runner
    participant Sandbox as Security Sandbox
    participant Metrics as Metrics
    participant Report as Reporter
    participant DB as Database
    
    User->>CLI: Submit Solution
    CLI->>Eval: Initialize Evaluation
    
    Eval->>Eval: Validate Requirements
    Eval->>Runner: Setup Environment
    
    Runner->>Sandbox: Prepare Sandbox
    Sandbox->>Sandbox: Apply Security Policies
    
    Runner->>Runner: Build Solution
    Runner->>Runner: Deploy Application
    
    Eval->>Runner: Execute Tests
    Runner->>Sandbox: Run in Isolation
    Sandbox-->>Runner: Execution Results
    
    Runner-->>Eval: Test Results
    
    Eval->>Metrics: Calculate Scores
    Metrics->>Metrics: Functional Coverage
    Metrics->>Metrics: Performance Analysis
    Metrics->>Metrics: Security Scan
    Metrics->>Metrics: Code Quality
    Metrics-->>Eval: Total Score
    
    Eval->>Report: Generate Report
    Report->>Report: Create Visualizations
    Report-->>Eval: Report Files
    
    Eval->>DB: Store Results
    DB->>DB: Update Leaderboard
    
    Eval-->>CLI: Final Results
    CLI-->>User: Display Score
```

## System Layers / システムレイヤー

### 1. Input Layer (入力層)

**Components:**
- Problem Specifications (YAML format)
- Requirements (RFC 2119 compliant)
- Test Cases (Unit/Integration/Property)
- Fixtures and Test Data

**Responsibilities:**
- Define evaluation criteria
- Specify functional and non-functional requirements
- Provide test data and expected outputs

### 2. Processing Layer (処理層)

**Components:**
- Evaluator Core Engine
- Execution Runners (Docker/K8s/Local)
- Security Sandbox (nsjail/firejail)
- Metrics Calculators

**Responsibilities:**
- Orchestrate evaluation workflow
- Execute code in isolated environments
- Enforce security policies
- Calculate performance metrics

### 3. Analysis Layer (分析層)

**Components:**
- Performance Analyzers (Locust, wrk, ab)
- Security Scanners (Bandit, Trivy, Safety)
- Code Quality Tools (Black, Flake8, MyPy)
- Test Coverage Tools (pytest-cov)

**Responsibilities:**
- Measure performance characteristics
- Identify security vulnerabilities
- Assess code quality
- Calculate test coverage

### 4. Output Layer (出力層)

**Components:**
- Report Generators (HTML/JSON/Markdown)
- Visualization Tools (matplotlib, charts)
- Leaderboard System
- API Endpoints

**Responsibilities:**
- Generate comprehensive reports
- Create visualizations
- Update leaderboard
- Provide API access to results

## Technology Stack / 技術スタック

```yaml
Core Framework:
  Language: Python 3.11+
  Framework: FastAPI (for API server)
  CLI: Click
  Testing: pytest, hypothesis

Containerization:
  Runtime: Docker 24.0+
  Orchestration: Kubernetes 1.28+
  Registry: Docker Hub / GitHub Container Registry

Security:
  Sandboxing: nsjail, firejail
  Scanning: Bandit, Trivy, Safety
  Policies: Seccomp, AppArmor

Performance:
  Load Testing: Locust, Apache Bench, wrk
  Monitoring: Prometheus, Grafana
  Profiling: cProfile, memory_profiler

Quality:
  Linting: Black, Flake8, Pylint
  Type Checking: MyPy
  Documentation: Sphinx, MkDocs

Storage:
  Database: PostgreSQL 15+ (production), SQLite (development)
  Object Storage: S3-compatible (MinIO, AWS S3)
  Caching: Redis 7.2+

CI/CD:
  Pipeline: GitHub Actions
  Testing: pytest, tox
  Deployment: Helm Charts, ArgoCD
```

## Deployment Architecture / デプロイメントアーキテクチャ

```mermaid
graph TB
    subgraph "Production Environment / 本番環境"
        subgraph "Kubernetes Cluster"
            IG[Ingress Controller<br/>入口制御]
            
            subgraph "API Services"
                API1[API Server Pod 1]
                API2[API Server Pod 2]
                API3[API Server Pod 3]
            end
            
            subgraph "Evaluation Workers"
                W1[Worker Pod 1<br/>評価ワーカー]
                W2[Worker Pod 2<br/>評価ワーカー]
                W3[Worker Pod 3<br/>評価ワーカー]
            end
            
            subgraph "Support Services"
                RD[Redis Cache<br/>キャッシュ]
                PG[PostgreSQL<br/>データベース]
                MQ[Message Queue<br/>メッセージキュー]
            end
        end
        
        subgraph "External Storage"
            S3[S3 Storage<br/>オブジェクトストレージ]
            NFS[NFS Volume<br/>共有ストレージ]
        end
    end
    
    subgraph "Monitoring / 監視"
        PROM[Prometheus<br/>メトリクス収集]
        GRAF[Grafana<br/>可視化]
        ELK[ELK Stack<br/>ログ分析]
    end
    
    Users[Users<br/>ユーザー] --> IG
    IG --> API1
    IG --> API2
    IG --> API3
    
    API1 --> MQ
    API2 --> MQ
    API3 --> MQ
    
    MQ --> W1
    MQ --> W2
    MQ --> W3
    
    W1 --> PG
    W2 --> PG
    W3 --> PG
    
    W1 --> S3
    W2 --> S3
    W3 --> S3
    
    API1 --> RD
    API2 --> RD
    API3 --> RD
    
    API1 --> PROM
    W1 --> PROM
    PROM --> GRAF
    
    API1 --> ELK
    W1 --> ELK
```

## Security Architecture / セキュリティアーキテクチャ

```mermaid
graph LR
    subgraph "Security Layers / セキュリティレイヤー"
        subgraph "Network Security"
            FW[Firewall<br/>ファイアウォール]
            NP[Network Policies<br/>ネットワークポリシー]
            TLS[TLS Encryption<br/>暗号化]
        end
        
        subgraph "Container Security"
            IMG[Image Scanning<br/>イメージスキャン]
            POL[Pod Security Policies<br/>Podセキュリティ]
            ADM[Admission Control<br/>アドミッション制御]
        end
        
        subgraph "Runtime Security"
            SEC[Seccomp Profiles<br/>Seccompプロファイル]
            APP[AppArmor/SELinux]
            CAP[Capabilities<br/>ケーパビリティ]
        end
        
        subgraph "Application Security"
            AUTH[Authentication<br/>認証]
            AUTHZ[Authorization<br/>認可]
            VAL[Input Validation<br/>入力検証]
        end
    end
    
    FW --> NP
    NP --> TLS
    TLS --> IMG
    IMG --> POL
    POL --> ADM
    ADM --> SEC
    SEC --> APP
    APP --> CAP
    CAP --> AUTH
    AUTH --> AUTHZ
    AUTHZ --> VAL
```

## Scalability Design / スケーラビリティ設計

- **Horizontal Scaling**: API servers and workers scale independently
- **Queue-based Processing**: Asynchronous evaluation via message queues
- **Caching Strategy**: Multi-layer caching (Redis, CDN, local)
- **Database Sharding**: Partition by problem_id and timestamp
- **Load Balancing**: Round-robin with health checks
- **Auto-scaling**: HPA based on CPU/memory metrics

## High Availability / 高可用性

- **Multi-zone Deployment**: Spread across availability zones
- **Database Replication**: Primary-secondary with automatic failover
- **Circuit Breakers**: Prevent cascade failures
- **Health Checks**: Liveness and readiness probes
- **Backup Strategy**: Daily snapshots with 30-day retention
- **Disaster Recovery**: RTO < 1 hour, RPO < 15 minutes