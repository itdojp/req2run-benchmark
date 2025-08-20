# Req2Run Additional Benchmark Problems

## Problem 6: Domain-Specific Language Interpreter

```yaml
problem_id: LANG-001
category: language_processor
difficulty: expert
title: SQL-like Query Language Interpreter
description: |
  SQLサブセットを実装したクエリ言語インタープリタ。
  パーサー、クエリプランナー、実行エンジンを含む。

functional_requirements:
  - id: FR-001
    description: "SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY句のサポート"
    priority: must
  - id: FR-002
    description: "集計関数: COUNT, SUM, AVG, MIN, MAX"
    priority: must
  - id: FR-003
    description: "インデックス構造（B+Tree）による高速検索"
    priority: must
  - id: FR-004
    description: "クエリ実行計画の最適化とEXPLAIN出力"
    priority: must
  - id: FR-005
    description: "CSVファイルからのテーブルロード"
    priority: must
  - id: FR-006
    description: "トランザクション（ACID特性）サポート"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "100万行テーブルでのインデックススキャン < 100ms"
    measurement: "ベンチマークテスト"
  - type: compatibility
    constraint: "ANSI SQL-92基本機能の80%カバー"
    measurement: "コンプライアンステスト"

input_specification:
  format: "SQL-like query string"
  examples:
    - query: "SELECT name, AVG(score) FROM students WHERE age > 20 GROUP BY name ORDER BY AVG(score) DESC"
    - query: "SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.country = 'Japan'"

output_specification:
  format: "Tabular result set or execution plan"
  examples:
    - result:
        columns: ["name", "avg_score"]
        rows: [["Alice", 85.5], ["Bob", 78.2]]
    - explain:
        plan: "IndexScan(customers.country) -> HashJoin -> SeqScan(orders)"

test_cases:
  - input:
      setup: "CREATE TABLE users (id INT, name TEXT, age INT)"
      data: "1000000 rows"
      query: "SELECT * FROM users WHERE id = 12345"
    expected_output:
      execution_time_ms: "< 10"
      rows_returned: 1
    description: "インデックス検索性能"
  
  - input:
      queries:
        - "BEGIN"
        - "INSERT INTO accounts VALUES (1, 1000)"
        - "UPDATE accounts SET balance = balance - 100 WHERE id = 1"
        - "ROLLBACK"
      query: "SELECT balance FROM accounts WHERE id = 1"
    expected_output:
      balance: 1000
    description: "トランザクションロールバック"

deployment_requirements:
  environment: standalone
  dependencies: []
  configuration:
    memory_limit: "1GB"
    data_directory: "/var/lib/querydb"

evaluation_criteria:
  - metric: "SQL機能カバレッジ"
    weight: 0.4
    threshold: 0.8
  - metric: "クエリ実行正確性"
    weight: 0.3
    threshold: 1.0
  - metric: "性能要件達成"
    weight: 0.2
    threshold: 0.9
  - metric: "最適化効果"
    weight: 0.1
    threshold: 0.7
```

## Problem 7: ML Pipeline with Model Serving

```yaml
problem_id: ML-001
category: machine_learning
difficulty: advanced
title: End-to-End ML Pipeline for Time Series Prediction
description: |
  時系列予測モデルの学習・評価・サービング統合パイプライン。
  自動特徴量エンジニアリング、ハイパーパラメータ最適化、A/Bテスト機能を含む。

functional_requirements:
  - id: FR-001
    description: "時系列データの前処理（欠損値補完、正規化、窓関数特徴量）"
    priority: must
  - id: FR-002
    description: "複数アルゴリズム（ARIMA, LSTM, XGBoost）の学習と比較"
    priority: must
  - id: FR-003
    description: "ハイパーパラメータ最適化（Optuna使用）"
    priority: must
  - id: FR-004
    description: "REST APIでのモデルサービング（予測エンドポイント）"
    priority: must
  - id: FR-005
    description: "A/Bテスト機能（トラフィック分割、メトリクス収集）"
    priority: must
  - id: FR-006
    description: "モデルドリフト検出とアラート"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "予測レイテンシ < 100ms（バッチサイズ100）"
    measurement: "負荷テスト"
  - type: scalability
    constraint: "1000 req/secの処理能力"
    measurement: "ベンチマーク"

input_specification:
  format: "CSV time series data"
  examples:
    - columns: ["timestamp", "value", "feature1", "feature2"]
      sample: "2024-01-01T00:00:00,100.5,0.8,12"

output_specification:
  format: "JSON prediction response"
  examples:
    - response:
        predictions: [101.2, 102.8, 99.5]
        confidence_intervals: [[98.1, 104.3], [99.2, 106.4], [95.8, 103.2]]
        model_version: "v2.1"

test_cases:
  - input:
      training_data: "1 year historical data"
      test_data: "1 month future data"
    expected_output:
      mape: "< 5%"
      rmse: "< 10"
    description: "予測精度検証"
  
  - input:
      model_a: "LSTM"
      model_b: "XGBoost"
      traffic_split: [0.5, 0.5]
      duration: "24 hours"
    expected_output:
      metrics_collected: true
      winner_selected: true
    description: "A/Bテスト実行"

deployment_requirements:
  environment: kubernetes
  dependencies: ["mlflow", "postgresql", "redis"]
  configuration:
    gpu_required: true
    model_registry: "s3://models/"

evaluation_criteria:
  - metric: "予測精度（MAPE）"
    weight: 0.3
    threshold: 0.95
  - metric: "パイプライン自動化度"
    weight: 0.3
    threshold: 1.0
  - metric: "サービング性能"
    weight: 0.2
    threshold: 0.9
  - metric: "モニタリング機能"
    weight: 0.2
    threshold: 0.8
```

## Problem 8: WebRTC Video Conferencing Server

```yaml
problem_id: RTC-001
category: real_time_communication
difficulty: expert
title: Scalable WebRTC SFU with Recording
description: |
  WebRTCベースのビデオ会議システム。
  Selective Forwarding Unit (SFU)、録画、画面共有機能を実装。

functional_requirements:
  - id: FR-001
    description: "WebRTC SFU実装（最大50参加者/ルーム）"
    priority: must
  - id: FR-002
    description: "適応的ビットレート制御（network条件に応じた品質調整）"
    priority: must
  - id: FR-003
    description: "サイマルキャスト（複数品質ストリーム同時送信）"
    priority: must
  - id: FR-004
    description: "会議録画（WebM形式、クラウドストレージ保存）"
    priority: must
  - id: FR-005
    description: "画面共有とアノテーション機能"
    priority: must
  - id: FR-006
    description: "エンドツーエンド暗号化（E2EE）"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "エンドツーエンドレイテンシ < 150ms"
    measurement: "ネットワーク測定"
  - type: scalability
    constraint: "1000同時会議室のサポート"
    measurement: "負荷テスト"

input_specification:
  format: "WebRTC signaling messages"
  examples:
    - type: "offer"
      sdp: "v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n..."
    - type: "ice_candidate"
      candidate: "candidate:1 1 UDP 2130706431 192.168.1.1 54321 typ host"

output_specification:
  format: "WebRTC responses and media streams"
  examples:
    - type: "answer"
      sdp: "v=0\r\no=- 0 0 IN IP4 10.0.0.1\r\n..."
    - recording:
        format: "webm"
        resolution: "1280x720"
        bitrate: "2Mbps"

test_cases:
  - input:
      participants: 30
      duration: 60
      network_conditions: "variable (50ms-200ms latency, 1% packet loss)"
    expected_output:
      average_mos_score: "> 3.5"
      successful_connections: "100%"
    description: "大規模会議品質テスト"
  
  - input:
      action: "bandwidth_throttle"
      limit: "500kbps"
    expected_output:
      quality_adapted: true
      no_disconnections: true
      resolution_reduced: true
    description: "適応的品質制御"

deployment_requirements:
  environment: kubernetes
  dependencies: ["coturn", "redis", "minio"]
  configuration:
    turn_server: "turn:turn.example.com:3478"
    storage_backend: "s3-compatible"

evaluation_criteria:
  - metric: "通話品質（MOS）"
    weight: 0.3
    threshold: 3.5
  - metric: "接続成功率"
    weight: 0.3
    threshold: 0.95
  - metric: "録画機能完全性"
    weight: 0.2
    threshold: 1.0
  - metric: "スケーラビリティ"
    weight: 0.2
    threshold: 0.8
```

## Problem 9: Blockchain Smart Contract Platform

```yaml
problem_id: CHAIN-001
category: blockchain
difficulty: expert
title: EVM-Compatible Smart Contract Execution Engine
description: |
  Ethereum Virtual Machine互換のスマートコントラクト実行環境。
  ガス計算、状態管理、コンセンサス統合を含む。

functional_requirements:
  - id: FR-001
    description: "EVM opcodeの完全実装（Constantinople対応）"
    priority: must
  - id: FR-002
    description: "Solidityコントラクトのデプロイと実行"
    priority: must
  - id: FR-003
    description: "ガス計算とガスリミット管理"
    priority: must
  - id: FR-004
    description: "Merkle Patricia Trieによる状態管理"
    priority: must
  - id: FR-005
    description: "JSON-RPC API（eth_call, eth_sendTransaction等）"
    priority: must
  - id: FR-006
    description: "Proof of Authority (PoA)コンセンサス"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "10,000 TPS（単純送金トランザクション）"
    measurement: "ベンチマーク"
  - type: security
    constraint: "reentrancy攻撃、integer overflow対策"
    measurement: "セキュリティ監査"

input_specification:
  format: "Ethereum transaction format"
  examples:
    - transaction:
        from: "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
        to: "0x5aAeb6053f3E94C9b9A09f33669435E7Ef1BeAed"
        value: "1000000000000000000"
        gas: "21000"
        data: "0x"

output_specification:
  format: "Transaction receipt"
  examples:
    - receipt:
        status: "0x1"
        gasUsed: "21000"
        logs: []
        transactionHash: "0xabc..."
        blockNumber: "1234"

test_cases:
  - input:
      contract: "ERC20Token"
      method: "transfer"
      parameters: ["0xrecipient", "1000000"]
      sender_balance: "2000000"
    expected_output:
      success: true
      recipient_balance: "1000000"
      event_emitted: "Transfer"
    description: "ERC20トークン転送"
  
  - input:
      contract: "ReentrancyVulnerable"
      attack_type: "reentrancy"
    expected_output:
      attack_prevented: true
      state_consistent: true
    description: "Reentrancy攻撃防御"

deployment_requirements:
  environment: docker
  dependencies: ["leveldb", "prometheus"]
  configuration:
    chain_id: 31337
    block_time: 5
    validators: ["0xvalidator1", "0xvalidator2", "0xvalidator3"]

evaluation_criteria:
  - metric: "EVM互換性"
    weight: 0.4
    threshold: 0.95
  - metric: "トランザクション処理性能"
    weight: 0.3
    threshold: 0.8
  - metric: "セキュリティテスト合格率"
    weight: 0.2
    threshold: 1.0
  - metric: "API完全性"
    weight: 0.1
    threshold: 0.9
```

## Problem 10: In-Memory Database Engine

```yaml
problem_id: DB-001
category: database
difficulty: expert
title: Redis-Compatible In-Memory Database
description: |
  Redis互換のインメモリデータベース実装。
  レプリケーション、永続化、Luaスクリプティングをサポート。

functional_requirements:
  - id: FR-001
    description: "基本データ型: String, List, Set, Hash, Sorted Set"
    priority: must
  - id: FR-002
    description: "非同期レプリケーション（master-slave）"
    priority: must
  - id: FR-003
    description: "AOF（Append Only File）とRDB永続化"
    priority: must
  - id: FR-004
    description: "トランザクション（MULTI/EXEC）"
    priority: must
  - id: FR-005
    description: "Pub/Subメッセージング"
    priority: must
  - id: FR-006
    description: "Luaスクリプト実行（EVAL/EVALSHA）"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "1M ops/sec（GET/SET、single thread）"
    measurement: "redis-benchmark互換テスト"
  - type: compatibility
    constraint: "Redis 6.0主要コマンドの90%互換"
    measurement: "互換性テストスイート"

input_specification:
  format: "Redis protocol (RESP)"
  examples:
    - command: "*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
      parsed: ["SET", "key", "value"]
    - command: "*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n"
      parsed: ["GET", "key"]

output_specification:
  format: "RESP responses"
  examples:
    - success: "+OK\r\n"
    - bulk_string: "$5\r\nvalue\r\n"
    - array: "*2\r\n$5\r\nvalue1\r\n$5\r\nvalue2\r\n"

test_cases:
  - input:
      commands:
        - "SET counter 0"
        - "MULTI"
        - "INCR counter"
        - "INCR counter"
        - "EXEC"
      query: "GET counter"
    expected_output:
      value: "2"
    description: "トランザクション処理"
  
  - input:
      setup: "Master with 2 slaves"
      action: "Write 1M keys to master"
    expected_output:
      replication_lag_ms: "< 100"
      data_consistency: true
    description: "レプリケーション性能"
  
  - input:
      script: "return redis.call('GET', KEYS[1]) * 2"
      keys: ["number"]
      setup: "SET number 21"
    expected_output:
      result: 42
    description: "Luaスクリプト実行"

deployment_requirements:
  environment: standalone
  dependencies: []
  configuration:
    port: 6379
    maxmemory: "4GB"
    maxmemory_policy: "allkeys-lru"

evaluation_criteria:
  - metric: "コマンド互換性"
    weight: 0.3
    threshold: 0.9
  - metric: "性能ベンチマーク"
    weight: 0.3
    threshold: 0.8
  - metric: "永続化信頼性"
    weight: 0.2
    threshold: 1.0
  - metric: "レプリケーション正確性"
    weight: 0.2
    threshold: 1.0
```

## Problem 11: Container Orchestration Controller

```yaml
problem_id: ORCH-001
category: orchestration
difficulty: expert
title: Kubernetes-like Container Scheduler
description: |
  コンテナオーケストレーション制御プレーン実装。
  スケジューリング、オートスケーリング、ローリングアップデートを含む。

functional_requirements:
  - id: FR-001
    description: "宣言的デプロイメント管理（desired state reconciliation）"
    priority: must
  - id: FR-002
    description: "ビンパッキングアルゴリズムによるスケジューリング"
    priority: must
  - id: FR-003
    description: "水平オートスケーリング（CPU/メモリベース）"
    priority: must
  - id: FR-004
    description: "ローリングアップデートとロールバック"
    priority: must
  - id: FR-005
    description: "ヘルスチェックと自動復旧"
    priority: must
  - id: FR-006
    description: "ネットワークポリシーとサービスディスカバリ"
    priority: should

non_functional_requirements:
  - type: scalability
    constraint: "1000ノード、10000コンテナ管理"
    measurement: "スケールテスト"
  - type: performance
    constraint: "スケジューリング決定 < 100ms"
    measurement: "ベンチマーク"

input_specification:
  format: "YAML manifest"
  examples:
    - manifest: |
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: web-app
        spec:
          replicas: 3
          selector:
            matchLabels:
              app: web
          template:
            metadata:
              labels:
                app: web
            spec:
              containers:
              - name: nginx
                image: nginx:1.21
                resources:
                  requests:
                    memory: "64Mi"
                    cpu: "250m"
                  limits:
                    memory: "128Mi"
                    cpu: "500m"

output_specification:
  format: "Controller status and events"
  examples:
    - status:
        ready_replicas: 3
        available_replicas: 3
        conditions:
          - type: "Progressing"
            status: "True"
            reason: "NewReplicaSetAvailable"

test_cases:
  - input:
      initial_replicas: 3
      cpu_load: "80%"
      hpa_target: "50%"
    expected_output:
      scaled_replicas: 5
      scaling_time_seconds: "< 30"
    description: "オートスケーリング動作"
  
  - input:
      update_strategy: "RollingUpdate"
      max_surge: 1
      max_unavailable: 1
      new_version: "nginx:1.22"
    expected_output:
      zero_downtime: true
      all_pods_updated: true
    description: "ローリングアップデート"
  
  - input:
      node_failure: "node-2"
      affected_pods: 5
    expected_output:
      pods_rescheduled: true
      recovery_time_seconds: "< 60"
    description: "ノード障害時の再スケジューリング"

deployment_requirements:
  environment: kubernetes
  dependencies: ["etcd", "containerd"]
  configuration:
    control_plane_nodes: 3
    worker_nodes: 5

evaluation_criteria:
  - metric: "制御ループ正確性"
    weight: 0.3
    threshold: 1.0
  - metric: "スケジューリング効率"
    weight: 0.3
    threshold: 0.85
  - metric: "障害復旧能力"
    weight: 0.2
    threshold: 0.95
  - metric: "スケーラビリティ"
    weight: 0.2
    threshold: 0.8
```

## Problem 12: GraphQL Federation Gateway

```yaml
problem_id: GQL-001
category: api_gateway
difficulty: advanced
title: GraphQL Federation with Caching and Rate Limiting
description: |
  複数のGraphQLサービスを統合するフェデレーションゲートウェイ。
  スキーマ合成、分散クエリ実行、キャッシング戦略を実装。

functional_requirements:
  - id: FR-001
    description: "Apollo Federation仕様準拠のスキーマ合成"
    priority: must
  - id: FR-002
    description: "クエリプランニングと分散実行"
    priority: must
  - id: FR-003
    description: "DataLoaderパターンによるN+1問題解決"
    priority: must
  - id: FR-004
    description: "クエリ複雑度ベースのレート制限"
    priority: must
  - id: FR-005
    description: "Redis/CDNを使用した多層キャッシュ"
    priority: must
  - id: FR-006
    description: "リアルタイムサブスクリプション（WebSocket）"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "P99レイテンシ < 200ms（10サービス統合時）"
    measurement: "負荷テスト"
  - type: scalability
    constraint: "10,000 concurrent connections"
    measurement: "ストレステスト"

input_specification:
  format: "GraphQL query"
  examples:
    - query: |
        query GetUserWithPosts($userId: ID!) {
          user(id: $userId) {
            name
            email
            posts(limit: 10) {
              title
              content
              comments {
                author {
                  name
                }
                text
              }
            }
          }
        }

output_specification:
  format: "GraphQL response with extensions"
  examples:
    - response:
        data:
          user:
            name: "John Doe"
            posts: [...]
        extensions:
          tracing:
            duration: 145000000
          cacheControl:
            version: 1
            hints: [...]

test_cases:
  - input:
      services: ["users", "posts", "comments"]
      query_depth: 5
      concurrent_requests: 1000
    expected_output:
      all_services_called: true
      response_time_p99_ms: "< 200"
      cache_hit_rate: "> 60%"
    description: "フェデレーション性能テスト"
  
  - input:
      query_complexity: 10000
      rate_limit: 5000
    expected_output:
      request_rejected: true
      error_code: "QUERY_TOO_COMPLEX"
    description: "複雑度制限"

deployment_requirements:
  environment: kubernetes
  dependencies: ["redis", "kafka"]
  configuration:
    replicas: 3
    services:
      - url: "http://users-service/graphql"
      - url: "http://posts-service/graphql"

evaluation_criteria:
  - metric: "Federation仕様準拠"
    weight: 0.3
    threshold: 1.0
  - metric: "クエリ実行性能"
    weight: 0.3
    threshold: 0.9
  - metric: "キャッシュ効率"
    weight: 0.2
    threshold: 0.6
  - metric: "エラーハンドリング"
    weight: 0.2
    threshold: 0.95
```

## Problem 13: Serverless Function Runtime

```yaml
problem_id: SERVERLESS-001
category: runtime_platform
difficulty: advanced
title: Multi-Language Serverless Execution Environment
description: |
  複数言語対応のサーバーレス関数実行環境。
  コールドスタート最適化、リソース制限、分散トレーシングを実装。

functional_requirements:
  - id: FR-001
    description: "Node.js, Python, Go関数の実行サポート"
    priority: must
  - id: FR-002
    description: "コンテナプール管理とウォームスタート最適化"
    priority: must
  - id: FR-003
    description: "CPU/メモリ/実行時間制限の強制"
    priority: must
  - id: FR-004
    description: "非同期呼び出しとイベント駆動実行"
    priority: must
  - id: FR-005
    description: "OpenTelemetry統合の分散トレーシング"
    priority: must
  - id: FR-006
    description: "カスタムランタイムレイヤー"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "コールドスタート < 50ms（Node.js）"
    measurement: "起動時間測定"
  - type: scalability
    constraint: "0から1000インスタンスへの自動スケール < 10秒"
    measurement: "スケールテスト"

input_specification:
  format: "Function invocation request"
  examples:
    - request:
        function_name: "process-image"
        runtime: "python3.9"
        handler: "main.handler"
        payload: {"image_url": "https://example.com/image.jpg"}
        memory: 256
        timeout: 30

output_specification:
  format: "Execution result with metadata"
  examples:
    - result:
        status_code: 200
        body: {"processed": true, "output_url": "..."}
        duration_ms: 1250
        billed_duration_ms: 1300
        memory_used_mb: 128
        init_duration_ms: 45

test_cases:
  - input:
      concurrent_invocations: 500
      function_memory: 128
      expected_duration: 1000
    expected_output:
      all_completed: true
      average_duration_ms: "< 1500"
      error_rate: "< 0.1%"
    description: "高並行実行テスト"
  
  - input:
      function_code: "while(true) {}"
      timeout: 5
    expected_output:
      terminated: true
      error: "Function timeout"
      duration_ms: 5000
    description: "タイムアウト処理"

deployment_requirements:
  environment: kubernetes
  dependencies: ["containerd", "jaeger", "prometheus"]
  configuration:
    container_pool_size: 100
    max_concurrent_executions: 1000

evaluation_criteria:
  - metric: "コールドスタート性能"
    weight: 0.3
    threshold: 0.9
  - metric: "リソース制限精度"
    weight: 0.3
    threshold: 1.0
  - metric: "スケーリング能力"
    weight: 0.2
    threshold: 0.85
  - metric: "トレーシング完全性"
    weight: 0.2
    threshold: 0.95
```

## Problem 14: Time-Series Database

```yaml
problem_id: TSDB-001
category: database
difficulty: expert
title: High-Performance Time-Series Database
description: |
  IoT/監視用途の時系列データベース実装。
  圧縮、ダウンサンプリング、連続集計クエリをサポート。

functional_requirements:
  - id: FR-001
    description: "時系列データの効率的な書き込み（1M points/sec）"
    priority: must
  - id: FR-002
    description: "Gorilla圧縮アルゴリズムによるストレージ最適化"
    priority: must
  - id: FR-003
    description: "自動ダウンサンプリングとデータ保持ポリシー"
    priority: must
  - id: FR-004
    description: "連続クエリとマテリアライズドビュー"
    priority: must
  - id: FR-005
    description: "InfluxQL互換のクエリ言語"
    priority: must
  - id: FR-006
    description: "水平シャーディングとレプリケーション"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "書き込みスループット > 1M points/sec"
    measurement: "ベンチマーク"
  - type: compression
    constraint: "圧縮率 > 10:1（典型的なIoTデータ）"
    measurement: "圧縮テスト"

input_specification:
  format: "Line protocol or JSON"
  examples:
    - line_protocol: "temperature,location=tokyo,sensor=s1 value=25.3 1640995200000000000"
    - json:
        measurement: "temperature"
        tags: {"location": "tokyo", "sensor": "s1"}
        fields: {"value": 25.3}
        timestamp: 1640995200000000000

output_specification:
  format: "Query results"
  examples:
    - query: "SELECT mean(value) FROM temperature WHERE time > now() - 1h GROUP BY time(5m)"
      result:
        series: [{"name": "temperature", "columns": ["time", "mean"], "values": [...]}]

test_cases:
  - input:
      write_rate: 1000000
      duration_seconds: 60
      compression: "enabled"
    expected_output:
      points_written: 60000000
      disk_usage_mb: "< 600"
      compression_ratio: "> 10"
    description: "高速書き込みと圧縮"
  
  - input:
      retention_policy: "7d:5m,30d:1h,1y:1d"
      data_age: "1 year"
    expected_output:
      policies_applied: true
      storage_optimized: true
    description: "保持ポリシーとダウンサンプリング"

deployment_requirements:
  environment: docker
  dependencies: []
  configuration:
    storage_path: "/var/lib/tsdb"
    wal_enabled: true
    cache_size: "2GB"

evaluation_criteria:
  - metric: "書き込み性能"
    weight: 0.3
    threshold: 0.9
  - metric: "圧縮効率"
    weight: 0.3
    threshold: 0.9
  - metric: "クエリ正確性"
    weight: 0.2
    threshold: 1.0
  - metric: "データ保持機能"
    weight: 0.2
    threshold: 1.0
```

## Problem 15: Service Mesh Control Plane

```yaml
problem_id: MESH-001
category: service_mesh
difficulty: expert
title: mTLS Service Mesh with Traffic Management
description: |
  マイクロサービス間通信を管理するサービスメッシュ制御プレーン。
  mTLS、トラフィック管理、可観測性を提供。

functional_requirements:
  - id: FR-001
    description: "自動mTLS証明書管理とローテーション"
    priority: must
  - id: FR-002
    description: "L7トラフィックルーティング（カナリア、A/B、ミラーリング）"
    priority: must
  - id: FR-003
    description: "サーキットブレーカーとリトライ制御"
    priority: must
  - id: FR-004
    description: "分散トレーシングとメトリクス収集"
    priority: must
  - id: FR-005
    description: "Envoyプロキシの動的設定（xDS API）"
    priority: must
  - id: FR-006
    description: "WebAssemblyプラグイン拡張"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "プロキシ追加レイテンシ < 1ms (P99)"
    measurement: "ベンチマーク"
  - type: scalability
    constraint: "10,000サービスエンドポイント管理"
    measurement: "スケールテスト"

input_specification:
  format: "Service mesh configuration"
  examples:
    - traffic_policy:
        destination: "reviews"
        subsets:
          - name: "v1"
            labels: {"version": "v1"}
            weight: 80
          - name: "v2"
            labels: {"version": "v2"}
            weight: 20

output_specification:
  format: "Envoy configuration (xDS)"
  examples:
    - cluster_config:
        name: "reviews"
        type: "EDS"
        lb_policy: "ROUND_ROBIN"
        circuit_breakers:
          thresholds:
            - max_connections: 100
              max_requests: 1000

test_cases:
  - input:
      services: 100
      traffic_pattern: "canary"
      canary_percentage: 10
    expected_output:
      traffic_split_accurate: true
      deviation: "< 1%"
    description: "カナリアデプロイメント精度"
  
  - input:
      failure_rate: 0.5
      circuit_breaker_threshold: 0.3
    expected_output:
      circuit_opened: true
      recovery_successful: true
    description: "サーキットブレーカー動作"
  
  - input:
      certificate_expiry: "1 hour"
    expected_output:
      rotation_completed: true
      zero_downtime: true
    description: "証明書自動ローテーション"

deployment_requirements:
  environment: kubernetes
  dependencies: ["istio", "prometheus", "jaeger"]
  configuration:
    control_plane_replicas: 3
    telemetry_enabled: true

evaluation_criteria:
  - metric: "mTLS実装完全性"
    weight: 0.3
    threshold: 1.0
  - metric: "トラフィック管理精度"
    weight: 0.3
    threshold: 0.95
  - metric: "可観測性機能"
    weight: 0.2
    threshold: 0.9
  - metric: "性能オーバーヘッド"
    weight: 0.2
    threshold: 0.9
```