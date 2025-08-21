# AUTH-010: OAuth 2.1/OIDC with PKCE Mock IdP Integration - Baseline Implementation

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