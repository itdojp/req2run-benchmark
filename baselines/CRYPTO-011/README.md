# CRYPTO-011: Homomorphic Encryption for Privacy-Preserving Computation

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