# CRYPTO-010: Zero-Knowledge Proof Authentication System

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