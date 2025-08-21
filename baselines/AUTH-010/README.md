# AUTH-010: OAuth 2.1/OIDC with PKCE Mock IdP Integration - Baseline Implementation

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

This baseline implementation provides a complete OAuth 2.1 and OpenID Connect provider with PKCE support, token rotation, and comprehensive security features. It demonstrates best practices for implementing secure authentication flows and protecting against common attacks.

## Features Implemented

### Core Features (MUST)
- ✅ OAuth 2.1 authorization code flow with PKCE
- ✅ JWT token validation using JWKs
- ✅ Token refresh with rotation
- ✅ Rejection of tokens with invalid signatures or alg=none
- ✅ Nonce validation to prevent replay attacks
- ✅ Clock skew handling (±60 seconds)
- ✅ Validation of aud, iss, exp, and nbf claims
- ✅ Secure state parameter handling

### Additional Features (SHOULD)
- ✅ Support for multiple IdP configurations
- ✅ Token introspection endpoint

## API Endpoints

### Authorization Flow
- `GET /authorize` - OAuth 2.1 authorization endpoint
- `POST /token` - Token exchange endpoint
- `POST /revoke` - Token revocation endpoint

### OpenID Connect
- `GET /.well-known/openid-configuration` - OIDC discovery
- `GET /.well-known/jwks.json` - JSON Web Key Set
- `GET /userinfo` - User information endpoint

### Token Management
- `POST /introspect` - Token introspection

### Monitoring
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Security Features

### PKCE (Proof Key for Code Exchange)
- Required for all authorization code flows
- Supports S256 challenge method (plain method disabled by default)
- Prevents authorization code interception attacks

### Token Security
- RSA-signed JWTs (RS256)
- Automatic token rotation on refresh
- Token revocation on code reuse detection
- Protection against alg=none attacks

### Replay Attack Prevention
- Nonce validation for ID tokens
- Single-use authorization codes
- State parameter for CSRF protection

## Example Usage

### 1. Authorization Request
```http
GET /authorize?
  response_type=code&
  client_id=test-client-id&
  redirect_uri=http://localhost:3000/callback&
  scope=openid profile email&
  state=random_state_value&
  code_challenge=challenge_value&
  code_challenge_method=S256&
  nonce=random_nonce
```

### 2. Token Exchange
```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=auth_code_from_step_1&
redirect_uri=http://localhost:3000/callback&
client_id=test-client-id&
client_secret=test-client-secret&
code_verifier=verifier_value
```

### 3. Token Refresh
```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=refresh_token_from_step_2&
client_id=test-client-id&
client_secret=test-client-secret
```

### 4. Token Introspection
```http
POST /introspect
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

token=access_token_to_introspect
```

## Performance Characteristics

- **P95 Latency**: < 100ms
- **P99 Latency**: < 300ms
- **Throughput**: 500+ requests/second
- **Token Validation**: < 10ms average

## Running the Baseline

### Docker
```bash
docker build -t auth-010-baseline .
docker run -p 8000:8000 auth-010-baseline
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

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

### Performance Tests
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## Configuration

The application can be configured via environment variables or the `.env` file:

```env
# Security
SECRET_KEY=your-secret-key-here
JWT_PRIVATE_KEY_PATH=config/private_key.pem
JWT_PUBLIC_KEY_PATH=config/public_key.pem

# Token Lifetimes
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
AUTHORIZATION_CODE_EXPIRE_MINUTES=10

# URLs
BASE_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite+aiosqlite:///./oauth.db

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

## Technology Stack

- **Framework**: FastAPI (Python 3.11)
- **JWT Library**: python-jose with cryptography backend
- **OAuth Library**: Authlib
- **State Storage**: Redis (with in-memory fallback)
- **Database**: SQLite (async with aiosqlite)
- **Security**: passlib for password hashing

## Security Considerations

1. **Always use HTTPS in production** - Set `require_https: true` in config
2. **Rotate signing keys regularly** - Update JWT keys periodically
3. **Use strong client secrets** - Generate using cryptographically secure methods
4. **Implement rate limiting** - Enabled by default (100 req/min)
5. **Monitor for suspicious activity** - Check metrics and logs regularly

## Compliance

This implementation follows:
- OAuth 2.1 Draft Specification
- RFC 7636 (PKCE)
- OpenID Connect Core 1.0
- RFC 7662 (Token Introspection)
- RFC 7009 (Token Revocation)

## License

MIT

---

<a id="japanese"></a>
## 日本語

## 概要

このベースライン実装は、PKCE対応、トークンローテーション、包括的なセキュリティ機能を備えた完全なOAuth 2.1およびOpenID Connectプロバイダーを提供します。セキュアな認証フローの実装と一般的な攻撃からの保護のベストプラクティスを示しています。

## 実装済み機能

### コア機能 (MUST)
- ✅ PKCE対応OAuth 2.1認可コードフロー
- ✅ JWKsを使用したJWTトークン検証
- ✅ ローテーション付きトークンリフレッシュ
- ✅ 無効な署名またはalg=noneトークンの拒否
- ✅ リプレイ攻撃防止のためのNonce検証
- ✅ クロックスキュー処理（±60秒）
- ✅ aud、iss、exp、nbfクレームの検証
- ✅ セキュアなstateパラメータ処理

### 追加機能 (SHOULD)
- ✅ 複数IdP設定のサポート
- ✅ トークンイントロスペクションエンドポイント

## APIエンドポイント

### 認可フロー
- `GET /authorize` - OAuth 2.1認可エンドポイント
- `POST /token` - トークン交換エンドポイント
- `POST /revoke` - トークン失効エンドポイント

### OpenID Connect
- `GET /.well-known/openid-configuration` - OIDCディスカバリー
- `GET /.well-known/jwks.json` - JSON Web Key Set
- `GET /userinfo` - ユーザー情報エンドポイント

### トークン管理
- `POST /introspect` - トークンイントロスペクション

### 監視
- `GET /health` - ヘルスチェック
- `GET /metrics` - Prometheusメトリクス

## セキュリティ機能

### PKCE (Proof Key for Code Exchange)
- すべての認可コードフローで必須
- S256チャレンジメソッドをサポート（plainメソッドはデフォルトで無効）
- 認可コード傍受攻撃を防止

### トークンセキュリティ
- RSA署名付きJWT（RS256）
- リフレッシュ時の自動トークンローテーション
- コード再利用検出時のトークン失効
- alg=none攻撃からの保護

### リプレイ攻撃防止
- IDトークンのNonce検証
- 単一使用認可コード
- CSRF保護のためのstateパラメータ

## 使用例

### 1. 認可リクエスト
```http
GET /authorize?
  response_type=code&
  client_id=test-client-id&
  redirect_uri=http://localhost:3000/callback&
  scope=openid profile email&
  state=random_state_value&
  code_challenge=challenge_value&
  code_challenge_method=S256&
  nonce=random_nonce
```

### 2. トークン交換
```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=auth_code_from_step_1&
redirect_uri=http://localhost:3000/callback&
client_id=test-client-id&
client_secret=test-client-secret&
code_verifier=verifier_value
```

### 3. トークンリフレッシュ
```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=refresh_token_from_step_2&
client_id=test-client-id&
client_secret=test-client-secret
```

### 4. トークンイントロスペクション
```http
POST /introspect
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

token=access_token_to_introspect
```

## パフォーマンス特性

- **P95レイテンシ**: < 100ms
- **P99レイテンシ**: < 300ms
- **スループット**: 500+ リクエスト/秒
- **トークン検証**: 平均 < 10ms

## ベースラインの実行

### Docker
```bash
docker build -t auth-010-baseline .
docker run -p 8000:8000 auth-010-baseline
```

### ローカル開発
```bash
# 依存関係のインストール
pip install -r requirements.txt

# アプリケーションの実行
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

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

### パフォーマンステスト
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## 設定

環境変数または`.env`ファイルで設定可能：

```env
# セキュリティ
SECRET_KEY=your-secret-key-here
JWT_PRIVATE_KEY_PATH=config/private_key.pem
JWT_PUBLIC_KEY_PATH=config/public_key.pem

# トークン有効期限
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
AUTHORIZATION_CODE_EXPIRE_MINUTES=10

# URL
BASE_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite+aiosqlite:///./oauth.db

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

## 技術スタック

- **フレームワーク**: FastAPI (Python 3.11)
- **JWTライブラリ**: python-jose with cryptography backend
- **OAuthライブラリ**: Authlib
- **ステート保存**: Redis（インメモリフォールバック付き）
- **データベース**: SQLite（aiosqliteによる非同期）
- **セキュリティ**: passlibによるパスワードハッシュ化

## セキュリティ考慮事項

1. **本番環境では常にHTTPSを使用** - configで`require_https: true`を設定
2. **署名鍵を定期的にローテーション** - JWT鍵を定期的に更新
3. **強力なクライアントシークレットを使用** - 暗号学的に安全な方法で生成
4. **レート制限を実装** - デフォルトで有効（100 req/min）
5. **不審なアクティビティを監視** - メトリクスとログを定期的に確認

## 準拠規格

この実装は以下に準拠：
- OAuth 2.1 Draft Specification
- RFC 7636 (PKCE)
- OpenID Connect Core 1.0
- RFC 7662 (Token Introspection)
- RFC 7009 (Token Revocation)

## ライセンス

MIT