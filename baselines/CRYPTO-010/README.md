# CRYPTO-010: Zero-Knowledge Proof Authentication System

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

A comprehensive zero-knowledge proof (ZKP) authentication system implementing multiple ZKP protocols including Schnorr identification, range proofs (Bulletproofs), simplified SNARKs, and various commitment schemes. The system provides cryptographically secure authentication without revealing secret information.

## Key Features

### Zero-Knowledge Protocols
- **Schnorr Identification Protocol**: Interactive and non-interactive variants
- **Range Proofs**: Bulletproof-style and Sigma protocol implementations
- **Simplified SNARKs**: zk-SNARK proof generation and verification
- **Threshold Authentication**: k-of-n threshold secret sharing
- **Multi-round Proofs**: Enhanced security through multiple rounds

### Commitment Schemes
- **Pedersen Commitments**: Homomorphic commitments
- **Hash Commitments**: SHA-256 based commitments
- **Merkle Tree Commitments**: Efficient batch commitments
- **Vector Commitments**: Commit to vectors with selective opening
- **Polynomial Commitments**: KZG-style polynomial commitments

### Security Features
- **No Information Leakage**: True zero-knowledge property
- **Replay Attack Prevention**: Timestamp and nonce-based protection
- **Cryptographically Secure Random**: Using secrets module
- **Session Management**: Secure session handling with expiration
- **Commitment Freshness**: Time-based validity checks

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Client App    │────▶│   ZKP API       │────▶│   Protocol      │
│                 │     │   (FastAPI)     │     │   Engine        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                         │
                                ▼                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Commitment     │     │   Proof         │
                        │   Manager       │     │  Generator      │
                        └─────────────────┘     └─────────────────┘
```

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t zkp-auth .

# Run the container
docker run -p 8000:8000 zkp-auth

# Health check
curl http://localhost:8000/health
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the application:**
```bash
cd src
python main.py
```

## API Endpoints

### Key Management
- `POST /api/v1/keys/generate` - Generate cryptographic key pair

### Authentication
- `POST /api/v1/auth/challenge` - Create authentication challenge
- `POST /api/v1/auth/respond` - Submit authentication response
- `POST /api/v1/auth/verify` - Verify authentication proof
- `POST /api/v1/auth/threshold` - Threshold authentication
- `POST /api/v1/auth/multi-round` - Multi-round authentication

### Range Proofs
- `POST /api/v1/range-proof/create` - Create range proof
- `POST /api/v1/range-proof/verify` - Verify range proof

### SNARKs
- `POST /api/v1/snark/create` - Create SNARK proof
- `POST /api/v1/snark/verify` - Verify SNARK proof

### Commitments
- `POST /api/v1/commitment/create` - Create cryptographic commitment

## Usage Examples

### Generate Keys

```bash
curl -X POST http://localhost:8000/api/v1/keys/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "key_type": "schnorr"
  }'
```

### Interactive Authentication

```bash
# Step 1: Create challenge
curl -X POST http://localhost:8000/api/v1/auth/challenge \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "rounds": 3,
    "challenge_type": "interactive"
  }'

# Step 2: Submit response (client computes response)
curl -X POST http://localhost:8000/api/v1/auth/respond \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_alice_1234567890",
    "response_value": "0x1234567890abcdef..."
  }'

# Step 3: Verify
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_alice_1234567890"
  }'
```

### Non-Interactive Authentication

```bash
curl -X POST http://localhost:8000/api/v1/auth/challenge \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "challenge_type": "non-interactive",
    "message": "Login at 2024-01-21 10:00:00"
  }'
```

### Create Range Proof

```bash
# Prove that a value is in range [0, 1000]
curl -X POST http://localhost:8000/api/v1/range-proof/create \
  -H "Content-Type: application/json" \
  -d '{
    "value": 500,
    "min_value": 0,
    "max_value": 1000,
    "proof_type": "bulletproof"
  }'
```

### Create and Verify SNARK

```bash
# Create SNARK proof
curl -X POST http://localhost:8000/api/v1/snark/create \
  -H "Content-Type: application/json" \
  -d '{
    "statement": "x^2 + y = z",
    "witness": {"x": 3, "y": 7, "z": 16},
    "circuit_type": "arithmetic"
  }'

# Verify SNARK proof
curl -X POST http://localhost:8000/api/v1/snark/verify \
  -H "Content-Type: application/json" \
  -d '{
    "proof": {...},
    "public_inputs": [16],
    "verification_key": "..."
  }'
```

### Threshold Authentication

```bash
curl -X POST http://localhost:8000/api/v1/auth/threshold \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "shares": [
      {"share": 12345, "index": 1},
      {"share": 67890, "index": 2},
      {"share": 11111, "index": 3}
    ],
    "threshold": 2
  }'
```

## Protocol Details

### Schnorr Protocol
1. **Commitment**: Prover generates random r, sends t = g^r
2. **Challenge**: Verifier sends random challenge c
3. **Response**: Prover sends s = r + c*x (where x is private key)
4. **Verification**: Verifier checks g^s = t * y^c (where y is public key)

### Range Proofs
- **Bulletproofs**: Efficient range proofs with logarithmic size
- **Sigma Protocol**: OR-composition for digit range proofs

### SNARKs (Simplified)
- **Setup**: Trusted setup generates proving and verification keys
- **Prove**: Generate proof for satisfiability of arithmetic circuit
- **Verify**: Verify proof using verification key and public inputs

## Security Considerations

1. **Key Storage**: Private keys are stored in memory (use secure storage in production)
2. **Random Generation**: Uses cryptographically secure random from `secrets` module
3. **Session Expiry**: Sessions expire after 5 minutes
4. **Replay Protection**: Challenges are tracked to prevent replay attacks
5. **Commitment Freshness**: Commitments older than 5 minutes are rejected

## Performance

- **Schnorr Proof Generation**: < 50ms
- **Schnorr Verification**: < 10ms
- **Range Proof Generation**: < 100ms
- **Range Proof Verification**: < 20ms
- **SNARK Generation**: < 500ms (simplified)
- **SNARK Verification**: < 50ms (simplified)

## Configuration

Configuration files in `config/` directory:

- `crypto.yaml`: Cryptographic parameters
- `zkp.yaml`: ZKP protocol settings
- `parameters.yaml`: System parameters

## Testing

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Security Tests
```bash
pytest tests/security/ -v
```

## Limitations

This implementation includes simplified versions of some protocols for demonstration:
- SNARKs are simplified (production should use libraries like libsnark/bellman)
- Bulletproofs are simplified (production should use dalek-cryptography)
- No real trusted setup for SNARKs (production requires secure MPC ceremony)

## Production Deployment

For production use:
1. Use hardware security modules (HSM) for key storage
2. Implement proper trusted setup for SNARKs
3. Use production-grade cryptographic libraries
4. Add rate limiting and DDoS protection
5. Implement comprehensive audit logging
6. Use TLS for all communications

## License

MIT

---

<a id="japanese"></a>
## 日本語

## 概要

Schnorr識別、レンジプルーフ（Bulletproofs）、簡易SNARK、および様々なコミットメントスキームを含む複数のZKPプロトコルを実装する包括的なゼロ知識証明（ZKP）認証システム。このシステムは、秘密情報を明かすことなく暗号学的に安全な認証を提供します。

## 主要機能

### ゼロ知識プロトコル
- **Schnorr識別プロトコル**: 対話型および非対話型バリアント
- **レンジプルーフ**: Bulletproofスタイルとシグマプロトコル実装
- **簡易SNARK**: zk-SNARK証明生成と検証
- **閾値認証**: k-of-n閾値秘密分散
- **マルチラウンド証明**: 複数ラウンドによる強化されたセキュリティ

### コミットメントスキーム
- **Pedersenコミットメント**: 準同型コミットメント
- **ハッシュコミットメント**: SHA-256ベースのコミットメント
- **マークルツリーコミットメント**: 効率的なバッチコミットメント
- **ベクトルコミットメント**: 選択的開示を持つベクトルへのコミット
- **多項式コミットメント**: KZGスタイル多項式コミットメント

### セキュリティ機能
- **情報漏洩なし**: 真のゼロ知識特性
- **リプレイ攻撃防止**: タイムスタンプとノンスベースの保護
- **暗号学的に安全な乱数**: secretsモジュールを使用
- **セッション管理**: 有効期限付き安全なセッション処理
- **コミットメントの鮮度**: 時間ベースの有効性チェック

## アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ クライアントアプリ │────▶│   ZKP API       │────▶│ プロトコル      │
│                 │     │   (FastAPI)     │     │ エンジン        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                         │
                                ▼                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │ コミットメント   │     │ 証明            │
                        │ マネージャー     │     │ ジェネレーター  │
                        └─────────────────┘     └─────────────────┘
```

## クイックスタート

### Dockerを使用

```bash
# イメージをビルド
docker build -t zkp-auth .

# コンテナを実行
docker run -p 8000:8000 zkp-auth

# ヘルスチェック
curl http://localhost:8000/health
```

### 手動セットアップ

1. **依存関係のインストール:**
```bash
pip install -r requirements.txt
```

2. **アプリケーションの実行:**
```bash
cd src
python main.py
```

## APIエンドポイント

### 鍵管理
- `POST /api/v1/keys/generate` - 暗号鍵ペアを生成

### 認証
- `POST /api/v1/auth/challenge` - 認証チャレンジを作成
- `POST /api/v1/auth/respond` - 認証レスポンスを送信
- `POST /api/v1/auth/verify` - 認証証明を検証
- `POST /api/v1/auth/threshold` - 閾値認証
- `POST /api/v1/auth/multi-round` - マルチラウンド認証

### レンジプルーフ
- `POST /api/v1/range-proof/create` - レンジプルーフを作成
- `POST /api/v1/range-proof/verify` - レンジプルーフを検証

### SNARK
- `POST /api/v1/snark/create` - SNARK証明を作成
- `POST /api/v1/snark/verify` - SNARK証明を検証

### コミットメント
- `POST /api/v1/commitment/create` - 暗号コミットメントを作成

## 使用例

### 鍵生成

```bash
curl -X POST http://localhost:8000/api/v1/keys/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "key_type": "schnorr"
  }'
```

### 対話型認証

```bash
# ステップ1: チャレンジを作成
curl -X POST http://localhost:8000/api/v1/auth/challenge \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "rounds": 3,
    "challenge_type": "interactive"
  }'

# ステップ2: レスポンスを送信（クライアントがレスポンスを計算）
curl -X POST http://localhost:8000/api/v1/auth/respond \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_alice_1234567890",
    "response_value": "0x1234567890abcdef..."
  }'

# ステップ3: 検証
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_alice_1234567890"
  }'
```

### 非対話型認証

```bash
curl -X POST http://localhost:8000/api/v1/auth/challenge \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "challenge_type": "non-interactive",
    "message": "Login at 2024-01-21 10:00:00"
  }'
```

### レンジプルーフの作成

```bash
# 値が[0, 1000]の範囲にあることを証明
curl -X POST http://localhost:8000/api/v1/range-proof/create \
  -H "Content-Type: application/json" \
  -d '{
    "value": 500,
    "min_value": 0,
    "max_value": 1000,
    "proof_type": "bulletproof"
  }'
```

### SNARKの作成と検証

```bash
# SNARK証明を作成
curl -X POST http://localhost:8000/api/v1/snark/create \
  -H "Content-Type: application/json" \
  -d '{
    "statement": "x^2 + y = z",
    "witness": {"x": 3, "y": 7, "z": 16},
    "circuit_type": "arithmetic"
  }'

# SNARK証明を検証
curl -X POST http://localhost:8000/api/v1/snark/verify \
  -H "Content-Type: application/json" \
  -d '{
    "proof": {...},
    "public_inputs": [16],
    "verification_key": "..."
  }'
```

### 閾値認証

```bash
curl -X POST http://localhost:8000/api/v1/auth/threshold \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "shares": [
      {"share": 12345, "index": 1},
      {"share": 67890, "index": 2},
      {"share": 11111, "index": 3}
    ],
    "threshold": 2
  }'
```

## プロトコル詳細

### Schnorrプロトコル
1. **コミットメント**: 証明者が乱数rを生成し、t = g^rを送信
2. **チャレンジ**: 検証者がランダムなチャレンジcを送信
3. **レスポンス**: 証明者がs = r + c*xを送信（xは秘密鍵）
4. **検証**: 検証者がg^s = t * y^cを確認（yは公開鍵）

### レンジプルーフ
- **Bulletproofs**: 対数サイズの効率的なレンジプルーフ
- **シグマプロトコル**: デジットレンジプルーフのOR合成

### SNARK（簡易版）
- **セットアップ**: 信頼できるセットアップが証明鍵と検証鍵を生成
- **証明**: 算術回路の充足可能性の証明を生成
- **検証**: 検証鍵と公開入力を使用して証明を検証

## セキュリティ考慮事項

1. **鍵ストレージ**: 秘密鍵はメモリに保存（本番環境では安全なストレージを使用）
2. **乱数生成**: `secrets`モジュールから暗号学的に安全な乱数を使用
3. **セッション期限**: セッションは5分後に期限切れ
4. **リプレイ保護**: リプレイ攻撃を防ぐためにチャレンジを追跡
5. **コミットメントの鮮度**: 5分以上古いコミットメントは拒否

## パフォーマンス

- **Schnorr証明生成**: < 50ms
- **Schnorr検証**: < 10ms
- **レンジプルーフ生成**: < 100ms
- **レンジプルーフ検証**: < 20ms
- **SNARK生成**: < 500ms（簡易版）
- **SNARK検証**: < 50ms（簡易版）

## 設定

`config/`ディレクトリの設定ファイル:

- `crypto.yaml`: 暗号パラメータ
- `zkp.yaml`: ZKPプロトコル設定
- `parameters.yaml`: システムパラメータ

## テスト

### ユニットテスト
```bash
pytest tests/unit/ -v
```

### 統合テスト
```bash
pytest tests/integration/ -v
```

### セキュリティテスト
```bash
pytest tests/security/ -v
```

## 制限事項

この実装には、デモンストレーション用にいくつかのプロトコルの簡易版が含まれています:
- SNARKは簡易版（本番環境ではlibsnark/bellmanなどのライブラリを使用すべき）
- Bulletproofsは簡易版（本番環境ではdalek-cryptographyを使用すべき）
- SNARKの実際の信頼できるセットアップなし（本番環境では安全なMPCセレモニーが必要）

## 本番デプロイメント

本番環境での使用:
1. 鍵ストレージにハードウェアセキュリティモジュール（HSM）を使用
2. SNARKの適切な信頼できるセットアップを実装
3. 本番グレードの暗号ライブラリを使用
4. レート制限とDDoS保護を追加
5. 包括的な監査ログを実装
6. すべての通信にTLSを使用

## ライセンス

MIT