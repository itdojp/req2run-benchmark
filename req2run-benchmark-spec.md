# Req2Run Benchmark Specification v1.0

## 要求記述フォーマット

### 基本構造

```yaml
problem_id: string
category: enum[web_api, cli_tool, network_protocol, cryptography, data_processing, system_utility]
difficulty: enum[basic, intermediate, advanced, expert]
title: string
description: string
functional_requirements:
  - id: string
    description: string
    priority: enum[must, should, nice_to_have]
non_functional_requirements:
  - type: enum[performance, security, scalability, compatibility]
    constraint: string
    measurement: string
input_specification:
  format: string
  examples: array
output_specification:
  format: string
  examples: array
test_cases:
  - input: any
    expected_output: any
    description: string
deployment_requirements:
  environment: enum[docker, kubernetes, standalone, lambda]
  dependencies: array
  configuration: object
evaluation_criteria:
  - metric: string
    weight: float
    threshold: float
```

## ベンチマーク問題サンプル

### Problem 1: REST API with Rate Limiting

```yaml
problem_id: WEB-001
category: web_api
difficulty: intermediate
title: Task Management API with Rate Limiting
description: |
  RESTful APIを実装し、タスク管理機能を提供する。
  認証、レート制限、データ永続化を含む。

functional_requirements:
  - id: FR-001
    description: "POST /tasks: 新規タスク作成（title, description, due_date）"
    priority: must
  - id: FR-002
    description: "GET /tasks: タスク一覧取得（ページネーション対応）"
    priority: must
  - id: FR-003
    description: "PUT /tasks/{id}: タスク更新"
    priority: must
  - id: FR-004
    description: "DELETE /tasks/{id}: タスク削除"
    priority: must
  - id: FR-005
    description: "JWTベース認証の実装"
    priority: must
  - id: FR-006
    description: "IPベースのレート制限（100req/min per IP）"
    priority: must

non_functional_requirements:
  - type: performance
    constraint: "95パーセンタイルレスポンス時間 < 200ms"
    measurement: "負荷テストツールによる測定"
  - type: security
    constraint: "SQLインジェクション、XSS対策実装"
    measurement: "セキュリティスキャナによる検証"

input_specification:
  format: "JSON REST API requests"
  examples:
    - method: POST
      endpoint: /tasks
      body: {"title": "Deploy v2", "description": "Production deployment", "due_date": "2024-12-31"}

output_specification:
  format: "JSON responses with appropriate HTTP status codes"
  examples:
    - status: 201
      body: {"id": "uuid", "title": "Deploy v2", "created_at": "2024-01-01T00:00:00Z"}

test_cases:
  - input: 
      method: POST
      endpoint: /tasks
      headers: {"Authorization": "Bearer valid_token"}
      body: {"title": "Test Task"}
    expected_output:
      status: 201
      body_contains: {"title": "Test Task"}
    description: "正常なタスク作成"
  
  - input:
      method: GET
      endpoint: /tasks
      headers: {"Authorization": "Bearer invalid_token"}
    expected_output:
      status: 401
    description: "無効なトークンでのアクセス拒否"

deployment_requirements:
  environment: docker
  dependencies: ["postgres:14", "redis:7"]
  configuration:
    env_vars: ["DATABASE_URL", "REDIS_URL", "JWT_SECRET"]

evaluation_criteria:
  - metric: "機能要件充足率"
    weight: 0.4
    threshold: 1.0
  - metric: "テストケース通過率"
    weight: 0.3
    threshold: 0.95
  - metric: "性能要件達成率"
    weight: 0.2
    threshold: 0.9
  - metric: "セキュリティスキャン通過"
    weight: 0.1
    threshold: 1.0
```

### Problem 2: AES File Encryption CLI

```yaml
problem_id: CRYPTO-001
category: cryptography
difficulty: intermediate
title: AES-256-GCM File Encryption Tool
description: |
  AES-256-GCMを使用したファイル暗号化/復号化CLIツール。
  パスワード導出にはArgon2idを使用。

functional_requirements:
  - id: FR-001
    description: "encrypt サブコマンド: ファイルをAES-256-GCMで暗号化"
    priority: must
  - id: FR-002
    description: "decrypt サブコマンド: 暗号化ファイルの復号化"
    priority: must
  - id: FR-003
    description: "パスワードからArgon2idでキー導出（salt: 16bytes, iterations: 3, memory: 64MB）"
    priority: must
  - id: FR-004
    description: "暗号化ファイルヘッダーにsalt, nonce, tagを含める"
    priority: must
  - id: FR-005
    description: "大容量ファイル対応（ストリーミング処理）"
    priority: should

non_functional_requirements:
  - type: security
    constraint: "NIST SP 800-38D準拠のGCM実装"
    measurement: "テストベクトルによる検証"
  - type: performance
    constraint: "1GBファイルの暗号化時間 < 10秒（SSD環境）"
    measurement: "ベンチマークテスト"

input_specification:
  format: "CLI arguments"
  examples:
    - "encrypt --input data.txt --output data.enc --password mypass"
    - "decrypt --input data.enc --output data.txt --password mypass"

output_specification:
  format: "Encrypted file with header structure"
  examples:
    - header: "[magic_bytes(4)][version(1)][salt(16)][nonce(12)][tag(16)][encrypted_data]"

test_cases:
  - input:
      command: "encrypt --input test.txt --output test.enc --password TestPass123"
      file_content: "Hello, World!"
    expected_output:
      exit_code: 0
      file_exists: "test.enc"
      file_header_valid: true
    description: "基本的な暗号化"
  
  - input:
      command: "decrypt --input test.enc --output decrypted.txt --password TestPass123"
    expected_output:
      exit_code: 0
      file_content: "Hello, World!"
    description: "正常な復号化"
  
  - input:
      command: "decrypt --input test.enc --output fail.txt --password WrongPass"
    expected_output:
      exit_code: 1
      error_contains: "authentication failed"
    description: "不正なパスワードでの復号化失敗"

deployment_requirements:
  environment: standalone
  dependencies: []
  configuration:
    binary_name: "cryptool"

evaluation_criteria:
  - metric: "暗号化仕様準拠"
    weight: 0.5
    threshold: 1.0
  - metric: "テストケース通過率"
    weight: 0.3
    threshold: 1.0
  - metric: "性能要件達成"
    weight: 0.2
    threshold: 0.9
```

### Problem 3: Custom TCP Protocol Implementation

```yaml
problem_id: NET-001
category: network_protocol
difficulty: advanced
title: Binary Message Protocol Server
description: |
  カスタムバイナリプロトコルを実装したTCPサーバー。
  メッセージフレーミング、ハートビート、再送制御を含む。

functional_requirements:
  - id: FR-001
    description: "TCP port 9000でリッスン"
    priority: must
  - id: FR-002
    description: |
      メッセージフレーム構造:
      [length(4bytes, big-endian)][type(1byte)][seq(4bytes)][payload][crc32(4bytes)]
    priority: must
  - id: FR-003
    description: "メッセージタイプ: 0x01=DATA, 0x02=ACK, 0x03=HEARTBEAT"
    priority: must
  - id: FR-004
    description: "30秒ごとのハートビート送信、60秒タイムアウトで切断"
    priority: must
  - id: FR-005
    description: "シーケンス番号による順序保証と再送制御（タイムアウト: 5秒）"
    priority: must
  - id: FR-006
    description: "最大100同時接続のサポート"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "メッセージ処理レイテンシ < 10ms（ローカル環境）"
    measurement: "ロードテスト"
  - type: scalability
    constraint: "1000 msg/secの処理能力"
    measurement: "ベンチマークツール"

input_specification:
  format: "Binary TCP stream"
  examples:
    - description: "DATA message"
      hex: "0000000F01000000010548656C6C6F1234ABCD"
      parsed: {length: 15, type: DATA, seq: 1, payload: "Hello", crc: "1234ABCD"}

output_specification:
  format: "Binary TCP response"
  examples:
    - description: "ACK message"
      hex: "0000000902000000015678DCBA"
      parsed: {length: 9, type: ACK, seq: 1, crc: "5678DCBA"}

test_cases:
  - input:
      action: "send_data_message"
      payload: "TestData"
      sequence: 1
    expected_output:
      message_type: "ACK"
      sequence: 1
    description: "データメッセージ送信とACK受信"
  
  - input:
      action: "wait_without_heartbeat"
      duration: 65
    expected_output:
      connection_state: "closed"
    description: "ハートビートタイムアウトによる切断"
  
  - input:
      action: "send_corrupted_crc"
      payload: "BadData"
    expected_output:
      error_response: true
      connection_state: "open"
    description: "CRCエラー処理"

deployment_requirements:
  environment: docker
  dependencies: []
  configuration:
    ports: ["9000:9000/tcp"]
    env_vars: ["LOG_LEVEL=info"]

evaluation_criteria:
  - metric: "プロトコル仕様準拠"
    weight: 0.4
    threshold: 1.0
  - metric: "エラー処理正確性"
    weight: 0.3
    threshold: 1.0
  - metric: "並行接続処理"
    weight: 0.2
    threshold: 0.9
  - metric: "性能要件達成"
    weight: 0.1
    threshold: 0.8
```

### Problem 4: Stream Processing Pipeline

```yaml
problem_id: DATA-001
category: data_processing
difficulty: advanced
title: Real-time Log Aggregation Pipeline
description: |
  複数ソースからのログをリアルタイム集計し、異常検知を行うパイプライン。
  ウィンドウ集計とアラート機能を含む。

functional_requirements:
  - id: FR-001
    description: "複数のログソース（HTTP, TCP, File）からの並行入力受付"
    priority: must
  - id: FR-002
    description: "1分間のスライディングウィンドウでエラー率計算"
    priority: must
  - id: FR-003
    description: "エラー率が閾値（5%）を超えた場合のWebhookアラート"
    priority: must
  - id: FR-004
    description: "ログパース: JSON, Apache Common Log, Syslog形式対応"
    priority: must
  - id: FR-005
    description: "集計結果のPrometheusメトリクスエクスポート"
    priority: should
  - id: FR-006
    description: "バックプレッシャー制御（メモリ使用量ベース）"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "10,000 logs/secの処理能力"
    measurement: "負荷テスト"
  - type: scalability
    constraint: "水平スケーリング対応（Kafka経由）"
    measurement: "クラスタテスト"

input_specification:
  format: "Multiple log formats"
  examples:
    - format: "JSON"
      content: '{"timestamp":"2024-01-01T00:00:00Z","level":"ERROR","message":"Database connection failed"}'
    - format: "Apache"
      content: '127.0.0.1 - - [01/Jan/2024:00:00:00 +0000] "GET /api/users HTTP/1.1" 500 1234'

output_specification:
  format: "Metrics and alerts"
  examples:
    - metrics: 
        error_rate: 0.06
        total_processed: 10000
        errors_count: 600
    - alert:
        type: "webhook"
        payload: {"threshold_exceeded": true, "current_rate": 0.06}

test_cases:
  - input:
      log_count: 1000
      error_count: 100
      time_window: 60
    expected_output:
      calculated_error_rate: 0.10
      alert_triggered: true
    description: "エラー率閾値超過によるアラート"
  
  - input:
      logs_per_second: 15000
      duration: 10
    expected_output:
      dropped_logs: 0
      backpressure_activated: true
    description: "高負荷時のバックプレッシャー動作"

deployment_requirements:
  environment: kubernetes
  dependencies: ["kafka", "prometheus"]
  configuration:
    replicas: 3
    resources:
      memory: "2Gi"
      cpu: "1000m"

evaluation_criteria:
  - metric: "機能要件充足率"
    weight: 0.3
    threshold: 1.0
  - metric: "処理性能"
    weight: 0.3
    threshold: 0.9
  - metric: "異常検知精度"
    weight: 0.2
    threshold: 0.95
  - metric: "リソース効率"
    weight: 0.2
    threshold: 0.8
```

### Problem 5: Distributed Lock Service

```yaml
problem_id: SYS-001
category: system_utility
difficulty: expert
title: Distributed Lock Coordinator
description: |
  分散システム向けのロックサービス実装。
  Raftコンセンサスアルゴリズムベースの強一貫性保証。

functional_requirements:
  - id: FR-001
    description: "gRPCインターフェースでのロック取得/解放API"
    priority: must
  - id: FR-002
    description: "Raftアルゴリズムによるレプリケーション（3ノード以上）"
    priority: must
  - id: FR-003
    description: "ロックのTTL（Time To Live）サポート"
    priority: must
  - id: FR-004
    description: "リーダー選出とフェイルオーバー（< 5秒）"
    priority: must
  - id: FR-005
    description: "分散トレーシング対応（OpenTelemetry）"
    priority: should
  - id: FR-006
    description: "ロック待機キューと公平性保証"
    priority: should

non_functional_requirements:
  - type: performance
    constraint: "ロック取得レイテンシ < 50ms（同一DC内）"
    measurement: "ベンチマーク"
  - type: scalability
    constraint: "10,000同時ロックの管理"
    measurement: "負荷テスト"

input_specification:
  format: "gRPC requests"
  examples:
    - method: "AcquireLock"
      request: {resource_id: "user:123", ttl_seconds: 30, client_id: "service-a"}
    - method: "ReleaseLock"
      request: {resource_id: "user:123", lock_token: "uuid-token"}

output_specification:
  format: "gRPC responses"
  examples:
    - response: {success: true, lock_token: "uuid-token", expires_at: "2024-01-01T00:00:30Z"}

test_cases:
  - input:
      scenario: "leader_failure"
      action: "kill_leader_node"
    expected_output:
      new_leader_elected: true
      election_time_ms: "< 5000"
      locks_preserved: true
    description: "リーダー障害時のフェイルオーバー"
  
  - input:
      scenario: "concurrent_lock_requests"
      clients: 100
      resource: "shared_resource"
    expected_output:
      exactly_one_holder: true
      queue_ordering_preserved: true
    description: "並行ロック要求の処理"
  
  - input:
      scenario: "network_partition"
      partition: "minority"
    expected_output:
      minority_requests_rejected: true
      majority_operational: true
    description: "ネットワーク分断時の一貫性保持"

deployment_requirements:
  environment: kubernetes
  dependencies: []
  configuration:
    replicas: 5
    pod_anti_affinity: true
    persistent_volume: "10Gi"

evaluation_criteria:
  - metric: "Raftプロトコル準拠"
    weight: 0.4
    threshold: 1.0
  - metric: "フェイルオーバー時間"
    weight: 0.3
    threshold: 1.0
  - metric: "並行性制御正確性"
    weight: 0.2
    threshold: 1.0
  - metric: "性能要件達成"
    weight: 0.1
    threshold: 0.9
```

## 評価方法

### 自動評価パイプライン

1. **要求解析**: YAMLパースと要求抽出
2. **実装生成**: AI/LLMによるコード生成
3. **ビルド・デプロイ**: 指定環境での自動構築
4. **テスト実行**: 定義済みテストケースの実行
5. **メトリクス計算**: 各評価基準に基づくスコアリング
6. **総合評価**: 重み付けスコアの算出

### スコア計算式

```
総合スコア = Σ(metric_score × weight)
合格判定 = すべてのmetric_score >= threshold
```

## 拡張性

- 新カテゴリの追加が容易な構造
- 評価基準のカスタマイズ可能
- 外部ツール連携（セキュリティスキャナ、性能測定ツール等）