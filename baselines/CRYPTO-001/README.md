# CRYPTO-001: AES-256-GCM File Encryption Tool Baseline Implementation

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