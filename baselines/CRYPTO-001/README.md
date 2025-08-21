# CRYPTO-001: AES-256-GCM File Encryption Tool Baseline Implementation

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

This is a reference implementation for the CRYPTO-001 problem: AES-256-GCM File Encryption Tool.

## Problem Requirements

### Functional Requirements (MUST)
- **MUST** implement AES-256-GCM encryption/decryption
- **MUST** use PBKDF2 for key derivation from passwords
- **MUST** generate cryptographically secure random salts and nonces
- **MUST** preserve file metadata (timestamps, permissions)
- **MUST** validate authentication tags to ensure integrity

### Non-Functional Requirements
- **SHOULD** process files in streaming mode for memory efficiency
- **SHOULD** show progress for large files
- **SHOULD** achieve >50 MB/s encryption speed
- **MAY** support batch encryption of multiple files

## Implementation Details

### Technology Stack
- **Language**: Python 3.11
- **Crypto Library**: cryptography
- **CLI Framework**: Click
- **Progress**: tqdm
- **Testing**: pytest

### Project Structure
```
CRYPTO-001/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── crypto/
│   │   ├── __init__.py
│   │   ├── aes_gcm.py       # AES-GCM implementation
│   │   ├── key_derivation.py # PBKDF2 key derivation
│   │   └── utils.py         # Crypto utilities
│   ├── cli/
│   │   ├── __init__.py
│   │   └── commands.py      # CLI commands
│   └── file_handler.py      # File operations
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── Dockerfile
├── requirements.txt
└── README.md
```

### Encryption Format

```
[File Header]
├── Magic Bytes (4 bytes): 0x43525950 ('CRYP')
├── Version (1 byte): 0x01
├── Salt (32 bytes): For PBKDF2
├── Nonce (12 bytes): For AES-GCM
├── Auth Tag (16 bytes): GCM authentication
└── Encrypted Data (variable)
```

## Usage Examples

### Encryption
```bash
# Encrypt a file with password
crypto-tool encrypt input.txt -o output.enc -p "my-secure-password"

# Encrypt with key file
crypto-tool encrypt input.txt -o output.enc -k keyfile.key

# Encrypt directory recursively
crypto-tool encrypt-dir /path/to/dir -o encrypted_dir.tar.enc
```

### Decryption
```bash
# Decrypt a file
crypto-tool decrypt output.enc -o decrypted.txt -p "my-secure-password"

# Decrypt with key file
crypto-tool decrypt output.enc -o decrypted.txt -k keyfile.key

# Verify without decrypting
crypto-tool verify output.enc -p "my-secure-password"
```

### Key Management
```bash
# Generate a secure key
crypto-tool keygen -o mykey.key

# Derive key from password (for testing)
crypto-tool derive-key -p "password" --salt "salt-value"
```

## Security Considerations

1. **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
2. **Random Generation**: Uses `os.urandom()` for cryptographically secure randomness
3. **Memory Safety**: Attempts to clear sensitive data from memory
4. **File Permissions**: Encrypted files are created with restricted permissions (0600)
5. **Authentication**: GCM mode provides authenticated encryption

## Performance Characteristics

- **Encryption Speed**: ~60-80 MB/s on modern hardware
- **Memory Usage**: O(1) - streams data in 64KB chunks
- **Maximum File Size**: Limited only by disk space
- **Concurrent Operations**: Supports parallel encryption of multiple files

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src --cov-report=html

# Run security tests
pytest tests/security/
```

## Docker Deployment

```bash
# Build image
docker build -t crypto-001-baseline .

# Run container
docker run -v $(pwd)/data:/data crypto-001-baseline \
  encrypt /data/input.txt -o /data/output.enc -p "password"
```

## Evaluation Metrics

Expected scores for this baseline:
- Functional Coverage: 100%
- Test Pass Rate: 95%
- Performance: 90%
- Code Quality: 85%
- Security: 95%
- **Total Score: 93%** (Gold)

## Security Warnings

⚠️ **Production Use**: This is a reference implementation for benchmarking. For production use:
- Use hardware security modules (HSM) for key storage
- Implement proper key rotation policies
- Add audit logging
- Consider using envelope encryption for large files
- Implement secure key exchange protocols

## References

- [NIST SP 800-38D](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf) - GCM Specification
- [RFC 8018](https://tools.ietf.org/html/rfc8018) - PBKDF2 Specification
- [cryptography.io](https://cryptography.io/) - Python Cryptography Library

---

<a id="japanese"></a>
## 日本語

## 概要

CRYPTO-001問題のリファレンス実装：AES-256-GCMファイル暗号化ツール。

## 問題要件

### 機能要件 (MUST)
- **MUST** AES-256-GCM暗号化/復号化を実装
- **MUST** パスワードからの鍵導出にPBKDF2を使用
- **MUST** 暗号学的に安全なランダムソルトとnonceを生成
- **MUST** ファイルメタデータ（タイムスタンプ、権限）を保持
- **MUST** 整合性保証のため認証タグを検証

### 非機能要件
- **SHOULD** メモリ効率のためストリーミングモードでファイルを処理
- **SHOULD** 大きなファイルの進行状況を表示
- **SHOULD** >50 MB/sの暗号化速度を達成
- **MAY** 複数ファイルのバッチ暗号化をサポート

## 実装詳細

### 技術スタック
- **言語**: Python 3.11
- **暗号ライブラリ**: cryptography
- **CLIフレームワーク**: Click
- **進行状況**: tqdm
- **テスト**: pytest

### プロジェクト構造
```
CRYPTO-001/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLIエントリーポイント
│   ├── crypto/
│   │   ├── __init__.py
│   │   ├── aes_gcm.py       # AES-GCM実装
│   │   ├── key_derivation.py # PBKDF2鍵導出
│   │   └── utils.py         # 暗号ユーティリティ
│   ├── cli/
│   │   ├── __init__.py
│   │   └── commands.py      # CLIコマンド
│   └── file_handler.py      # ファイル操作
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── Dockerfile
├── requirements.txt
└── README.md
```

### 暗号化フォーマット

```
[ファイルヘッダー]
├── マジックバイト (4バイト): 0x43525950 ('CRYP')
├── バージョン (1バイト): 0x01
├── ソルト (32バイト): PBKDF2用
├── Nonce (12バイト): AES-GCM用
├── 認証タグ (16バイト): GCM認証
└── 暗号化データ (可変長)
```

## 使用例

### 暗号化
```bash
# パスワードでファイルを暗号化
crypto-tool encrypt input.txt -o output.enc -p "my-secure-password"

# 鍵ファイルで暗号化
crypto-tool encrypt input.txt -o output.enc -k keyfile.key

# ディレクトリを再帰的に暗号化
crypto-tool encrypt-dir /path/to/dir -o encrypted_dir.tar.enc
```

### 復号化
```bash
# ファイルを復号化
crypto-tool decrypt output.enc -o decrypted.txt -p "my-secure-password"

# 鍵ファイルで復号化
crypto-tool decrypt output.enc -o decrypted.txt -k keyfile.key

# 復号化せずに検証
crypto-tool verify output.enc -p "my-secure-password"
```

### 鍵管理
```bash
# 安全な鍵を生成
crypto-tool keygen -o mykey.key

# パスワードから鍵を導出（テスト用）
crypto-tool derive-key -p "password" --salt "salt-value"
```

## セキュリティ考慮事項

1. **鍵導出**: PBKDF2-HMAC-SHA256で100,000回反復
2. **ランダム生成**: 暗号学的に安全なランダム性のため`os.urandom()`を使用
3. **メモリ安全性**: メモリから機密データをクリアする試行
4. **ファイル権限**: 暗号化ファイルは制限された権限(0600)で作成
5. **認証**: GCMモードが認証付き暗号化を提供

## パフォーマンス特性

- **暗号化速度**: 現代ハードウェアで~60-80 MB/s
- **メモリ使用量**: O(1) - 64KBチャンクでデータをストリーム
- **最大ファイルサイズ**: ディスク容量による制限のみ
- **同時操作**: 複数ファイルの並列暗号化をサポート

## テスト

```bash
# ユニットテストの実行
pytest tests/unit/

# 統合テストの実行
pytest tests/integration/

# カバレッジ付きで実行
pytest --cov=src --cov-report=html

# セキュリティテストの実行
pytest tests/security/
```

## Dockerデプロイメント

```bash
# イメージのビルド
docker build -t crypto-001-baseline .

# コンテナの実行
docker run -v $(pwd)/data:/data crypto-001-baseline \
  encrypt /data/input.txt -o /data/output.enc -p "password"
```

## 評価指標

このベースラインの期待スコア:
- 機能カバレッジ: 100%
- テスト合格率: 95%
- パフォーマンス: 90%
- コード品質: 85%
- セキュリティ: 95%
- **総合スコア: 93%** (Gold)

## セキュリティ警告

⚠️ **本畫使用**: これはベンチマーク用のリファレンス実装です。本畫使用の場合:
- 鍵ストレージにハードウェアセキュリティモジュール(HSM)を使用
- 適切な鍵ローテーションポリシーを実装
- 監査ログを追加
- 大きなファイルにはエンベロープ暗号化を検討
- 安全な鍵交換プロトコルを実装

## 参考文献

- [NIST SP 800-38D](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf) - GCM仕様
- [RFC 8018](https://tools.ietf.org/html/rfc8018) - PBKDF2仕様
- [cryptography.io](https://cryptography.io/) - Python暗号ライブラリ