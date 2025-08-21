# CRYPTO-011: Homomorphic Encryption for Privacy-Preserving Computation

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

A comprehensive homomorphic encryption system implementing both Partially Homomorphic Encryption (PHE) using Paillier cryptosystem and Fully Homomorphic Encryption (FHE) using simplified BFV scheme. The system enables privacy-preserving computation on encrypted data without decryption.

## Key Features

### Encryption Schemes
- **Paillier (PHE)**: Additive homomorphic encryption with scalar multiplication
- **BFV (FHE)**: Fully homomorphic encryption supporting both addition and multiplication
- **CKKS**: Approximate arithmetic on encrypted floating-point numbers

### Homomorphic Operations
- **Addition**: Add encrypted values without decryption
- **Multiplication**: Multiply encrypted values (FHE only)
- **Scalar Multiplication**: Multiply encrypted value by plaintext scalar
- **Batch Operations**: Process multiple ciphertexts efficiently
- **Bootstrapping**: Refresh ciphertexts to reduce noise (FHE)

### Advanced Features
- **Noise Management**: Track and manage noise growth in FHE operations
- **Private Information Retrieval (PIR)**: Query databases privately
- **Comparison Operations**: Simplified comparison circuits
- **Linear Algebra**: Dot products and linear combinations on encrypted vectors
- **Approximate Arithmetic**: CKKS scheme for real number computations

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Client App    │────▶│   HE API        │────▶│  Crypto Engine  │
│                 │     │   (FastAPI)     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                         │
                                ▼                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │    Paillier     │     │      BFV        │
                        │      PHE        │     │      FHE        │
                        └─────────────────┘     └─────────────────┘
```

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t homomorphic-encryption .

# Run the container
docker run -p 8000:8000 homomorphic-encryption

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
- `POST /api/v1/keys/generate` - Generate encryption keys

### Encryption/Decryption
- `POST /api/v1/encrypt` - Encrypt plaintext
- `POST /api/v1/decrypt` - Decrypt ciphertext

### Homomorphic Operations
- `POST /api/v1/compute` - Perform homomorphic computation
- `POST /api/v1/batch` - Batch operations

### FHE Specific
- `POST /api/v1/bootstrap` - Bootstrap ciphertext to refresh noise

### Private Information Retrieval
- `POST /api/v1/pir/setup` - Setup PIR database
- `POST /api/v1/pir/query` - Query database privately

## Usage Examples

### Generate Keys

```bash
# Paillier keys
curl -X POST http://localhost:8000/api/v1/keys/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "scheme": "paillier",
    "key_size": 2048
  }'

# BFV (FHE) keys
curl -X POST http://localhost:8000/api/v1/keys/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "scheme": "bfv",
    "key_size": 4096
  }'
```

### Encrypt Data

```bash
# Encrypt single value
curl -X POST http://localhost:8000/api/v1/encrypt \
  -H "Content-Type: application/json" \
  -d '{
    "plaintext": 42,
    "user_id": "alice",
    "scheme": "paillier"
  }'

# Encrypt batch
curl -X POST http://localhost:8000/api/v1/encrypt \
  -H "Content-Type: application/json" \
  -d '{
    "plaintext": [10, 20, 30, 40],
    "user_id": "alice",
    "scheme": "bfv"
  }'
```

### Homomorphic Addition

```bash
curl -X POST http://localhost:8000/api/v1/compute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "add",
    "operand1_id": "ct_alice_1234567890",
    "operand2_id": "ct_alice_1234567891"
  }'
```

### Homomorphic Multiplication (FHE only)

```bash
curl -X POST http://localhost:8000/api/v1/compute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "multiply",
    "operand1_id": "ct_alice_1234567890",
    "operand2_id": "ct_alice_1234567891"
  }'
```

### Scalar Multiplication

```bash
curl -X POST http://localhost:8000/api/v1/compute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "scalar_multiply",
    "operand1_id": "ct_alice_1234567890",
    "scalar": 5
  }'
```

### Decrypt Result

```bash
curl -X POST http://localhost:8000/api/v1/decrypt \
  -H "Content-Type: application/json" \
  -d '{
    "ciphertext_id": "result_1234567890",
    "user_id": "alice"
  }'
```

### Bootstrap Ciphertext (FHE)

```bash
curl -X POST http://localhost:8000/api/v1/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "ciphertext_id": "ct_alice_1234567890",
    "force": false
  }'
```

### Private Information Retrieval

```bash
# Setup database
curl -X POST http://localhost:8000/api/v1/pir/setup \
  -H "Content-Type: application/json" \
  -d '[100, 200, 300, 400, 500]'

# Query privately
curl -X POST http://localhost:8000/api/v1/pir/query \
  -H "Content-Type: application/json" \
  -d '{
    "database_id": "pir_db_1234567890",
    "index": 2,
    "user_id": "alice"
  }'
```

## Supported Operations

### Paillier (PHE)
- ✅ Homomorphic Addition: E(a) + E(b) = E(a + b)
- ✅ Scalar Multiplication: E(a) * k = E(a * k)
- ❌ Homomorphic Multiplication (not supported)

### BFV (FHE)
- ✅ Homomorphic Addition: E(a) + E(b) = E(a + b)
- ✅ Homomorphic Multiplication: E(a) * E(b) = E(a * b)
- ✅ Bootstrapping for noise refresh
- ⚠️ Limited multiplication depth without bootstrapping

### CKKS (Approximate)
- ✅ Approximate addition and multiplication
- ✅ Real number arithmetic
- ✅ Rescaling operations
- ⚠️ Some precision loss due to approximation

## Noise Management

FHE operations accumulate noise that eventually makes decryption impossible:

- **Addition**: Linear noise growth
- **Multiplication**: Multiplicative noise growth
- **Bootstrapping**: Resets noise to allow more operations

The system automatically tracks noise and recommends bootstrapping when needed.

## Performance Considerations

| Operation | Paillier | BFV | CKKS |
|-----------|----------|-----|------|
| Key Generation | ~100ms | ~500ms | ~300ms |
| Encryption | ~10ms | ~50ms | ~30ms |
| Addition | ~1ms | ~5ms | ~3ms |
| Multiplication | N/A | ~100ms | ~50ms |
| Decryption | ~10ms | ~50ms | ~30ms |
| Bootstrapping | N/A | ~1000ms | ~800ms |

## Security Parameters

- **Paillier**: 2048-bit modulus (112-bit security)
- **BFV**: 128-bit security with 4096 polynomial degree
- **CKKS**: 128-bit security with 40-bit precision

## Applications

### Privacy-Preserving Analytics
- Compute statistics on encrypted data
- Aggregate encrypted values without revealing individual inputs

### Secure Multi-Party Computation
- Multiple parties compute on shared encrypted data
- No party learns the inputs of others

### Private Machine Learning
- Train models on encrypted data (using CKKS)
- Evaluate models on encrypted inputs

### Secure Voting
- Tally encrypted votes without revealing individual choices
- Verifiable and private elections

## Limitations

This is a simplified implementation for demonstration:
- BFV implementation is simplified (production should use SEAL/HElib)
- Limited bootstrapping capabilities
- No GPU acceleration
- Simplified noise management

## Production Deployment

For production use:
1. Use established libraries (SEAL, HElib, TFHE, Concrete)
2. Implement proper parameter selection
3. Add comprehensive benchmarking
4. Use hardware acceleration (GPU/FPGA)
5. Implement secure key management
6. Add audit logging and monitoring

## License

MIT

---

<a id="japanese"></a>
## 日本語

## 概要

Paillier暗号システムを使用した部分準同型暗号（PHE）と簡易BFVスキームを使用した完全準同型暗号（FHE）の両方を実装する包括的な準同型暗号システム。このシステムは、復号化することなく暗号化されたデータに対するプライバシー保護計算を可能にします。

## 主要機能

### 暗号化スキーム
- **Paillier (PHE)**: スカラー乗算を持つ加法準同型暗号
- **BFV (FHE)**: 加算と乗算の両方をサポートする完全準同型暗号
- **CKKS**: 暗号化された浮動小数点数の近似演算

### 準同型演算
- **加算**: 復号化せずに暗号化された値を加算
- **乗算**: 暗号化された値を乗算（FHEのみ）
- **スカラー乗算**: 暗号化された値に平文スカラーを乗算
- **バッチ操作**: 複数の暗号文を効率的に処理
- **ブートストラッピング**: ノイズを削減するために暗号文を更新（FHE）

### 高度な機能
- **ノイズ管理**: FHE演算でのノイズ成長を追跡・管理
- **プライベート情報検索（PIR）**: データベースをプライベートにクエリ
- **比較演算**: 簡易化された比較回路
- **線形代数**: 暗号化ベクトルの内積と線形結合
- **近似演算**: 実数計算のためのCKKSスキーム

## アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ クライアントアプリ │────▶│   HE API        │────▶│ 暗号エンジン    │
│                 │     │   (FastAPI)     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                         │
                                ▼                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │    Paillier     │     │      BFV        │
                        │      PHE        │     │      FHE        │
                        └─────────────────┘     └─────────────────┘
```

## クイックスタート

### Dockerを使用

```bash
# イメージをビルド
docker build -t homomorphic-encryption .

# コンテナを実行
docker run -p 8000:8000 homomorphic-encryption

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
- `POST /api/v1/keys/generate` - 暗号化鍵を生成

### 暗号化/復号化
- `POST /api/v1/encrypt` - 平文を暗号化
- `POST /api/v1/decrypt` - 暗号文を復号化

### 準同型演算
- `POST /api/v1/compute` - 準同型計算を実行
- `POST /api/v1/batch` - バッチ操作

### FHE専用
- `POST /api/v1/bootstrap` - ノイズを更新するために暗号文をブートストラップ

### プライベート情報検索
- `POST /api/v1/pir/setup` - PIRデータベースをセットアップ
- `POST /api/v1/pir/query` - データベースをプライベートにクエリ

## 使用例

### 鍵生成

```bash
# Paillier鍵
curl -X POST http://localhost:8000/api/v1/keys/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "scheme": "paillier",
    "key_size": 2048
  }'

# BFV (FHE) 鍵
curl -X POST http://localhost:8000/api/v1/keys/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "scheme": "bfv",
    "key_size": 4096
  }'
```

### データの暗号化

```bash
# 単一値を暗号化
curl -X POST http://localhost:8000/api/v1/encrypt \
  -H "Content-Type: application/json" \
  -d '{
    "plaintext": 42,
    "user_id": "alice",
    "scheme": "paillier"
  }'

# バッチを暗号化
curl -X POST http://localhost:8000/api/v1/encrypt \
  -H "Content-Type: application/json" \
  -d '{
    "plaintext": [10, 20, 30, 40],
    "user_id": "alice",
    "scheme": "bfv"
  }'
```

### 準同型加算

```bash
curl -X POST http://localhost:8000/api/v1/compute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "add",
    "operand1_id": "ct_alice_1234567890",
    "operand2_id": "ct_alice_1234567891"
  }'
```

### 準同型乗算（FHEのみ）

```bash
curl -X POST http://localhost:8000/api/v1/compute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "multiply",
    "operand1_id": "ct_alice_1234567890",
    "operand2_id": "ct_alice_1234567891"
  }'
```

### スカラー乗算

```bash
curl -X POST http://localhost:8000/api/v1/compute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "scalar_multiply",
    "operand1_id": "ct_alice_1234567890",
    "scalar": 5
  }'
```

### 結果の復号化

```bash
curl -X POST http://localhost:8000/api/v1/decrypt \
  -H "Content-Type: application/json" \
  -d '{
    "ciphertext_id": "result_1234567890",
    "user_id": "alice"
  }'
```

### 暗号文のブートストラップ（FHE）

```bash
curl -X POST http://localhost:8000/api/v1/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "ciphertext_id": "ct_alice_1234567890",
    "force": false
  }'
```

### プライベート情報検索

```bash
# データベースをセットアップ
curl -X POST http://localhost:8000/api/v1/pir/setup \
  -H "Content-Type: application/json" \
  -d '[100, 200, 300, 400, 500]'

# プライベートにクエリ
curl -X POST http://localhost:8000/api/v1/pir/query \
  -H "Content-Type: application/json" \
  -d '{
    "database_id": "pir_db_1234567890",
    "index": 2,
    "user_id": "alice"
  }'
```

## サポートされる演算

### Paillier (PHE)
- ✅ 準同型加算: E(a) + E(b) = E(a + b)
- ✅ スカラー乗算: E(a) * k = E(a * k)
- ❌ 準同型乗算（サポートされていません）

### BFV (FHE)
- ✅ 準同型加算: E(a) + E(b) = E(a + b)
- ✅ 準同型乗算: E(a) * E(b) = E(a * b)
- ✅ ノイズ更新のためのブートストラッピング
- ⚠️ ブートストラッピングなしでは乗算深度に制限

### CKKS（近似）
- ✅ 近似加算と乗算
- ✅ 実数演算
- ✅ リスケーリング操作
- ⚠️ 近似による精度の損失あり

## ノイズ管理

FHE演算はノイズを蓄積し、最終的に復号化を不可能にします：

- **加算**: 線形ノイズ成長
- **乗算**: 乗法的ノイズ成長
- **ブートストラッピング**: より多くの演算を可能にするためにノイズをリセット

システムは自動的にノイズを追跡し、必要に応じてブートストラッピングを推奨します。

## パフォーマンス考慮事項

| 演算 | Paillier | BFV | CKKS |
|-----------|----------|-----|------|
| 鍵生成 | ~100ms | ~500ms | ~300ms |
| 暗号化 | ~10ms | ~50ms | ~30ms |
| 加算 | ~1ms | ~5ms | ~3ms |
| 乗算 | N/A | ~100ms | ~50ms |
| 復号化 | ~10ms | ~50ms | ~30ms |
| ブートストラッピング | N/A | ~1000ms | ~800ms |

## セキュリティパラメータ

- **Paillier**: 2048ビットモジュラス（112ビットセキュリティ）
- **BFV**: 4096多項式次数での128ビットセキュリティ
- **CKKS**: 40ビット精度での128ビットセキュリティ

## アプリケーション

### プライバシー保護分析
- 暗号化データの統計を計算
- 個々の入力を明かさずに暗号化された値を集約

### 安全なマルチパーティ計算
- 複数の当事者が共有暗号化データで計算
- どの当事者も他者の入力を知らない

### プライベート機械学習
- 暗号化データでモデルを訓練（CKKSを使用）
- 暗号化された入力でモデルを評価

### 安全な投票
- 個々の選択を明かさずに暗号化された投票を集計
- 検証可能でプライベートな選挙

## 制限事項

これはデモンストレーション用の簡易実装です：
- BFV実装は簡易版（本番環境ではSEAL/HElibを使用すべき）
- 限定的なブートストラッピング機能
- GPUアクセラレーションなし
- 簡易化されたノイズ管理

## 本番デプロイメント

本番環境での使用：
1. 確立されたライブラリを使用（SEAL、HElib、TFHE、Concrete）
2. 適切なパラメータ選択を実装
3. 包括的なベンチマークを追加
4. ハードウェアアクセラレーションを使用（GPU/FPGA）
5. 安全な鍵管理を実装
6. 監査ログと監視を追加

## ライセンス

MIT