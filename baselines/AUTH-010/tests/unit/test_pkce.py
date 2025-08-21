"""Unit tests for PKCE implementation"""
import hashlib
import base64
import secrets


def generate_code_verifier() -> str:
    """Generate a code verifier for PKCE"""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")


def generate_code_challenge(verifier: str, method: str = "S256") -> str:
    """Generate code challenge from verifier"""
    if method == "plain":
        return verifier
    elif method == "S256":
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")
    raise ValueError(f"Unsupported method: {method}")


def test_pkce_s256():
    """Test PKCE with S256 method"""
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier, "S256")
    
    # Verify challenge generation
    assert len(verifier) >= 43  # Min length per spec
    assert len(verifier) <= 128  # Max length per spec
    assert len(challenge) > 0
    
    # Verify challenge verification
    calculated = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")
    assert challenge == calculated


def test_pkce_plain():
    """Test PKCE with plain method"""
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier, "plain")
    
    # In plain method, challenge equals verifier
    assert challenge == verifier


def test_pkce_verifier_length():
    """Test code verifier length requirements"""
    # Generate multiple verifiers and check length
    for _ in range(10):
        verifier = generate_code_verifier()
        assert 43 <= len(verifier) <= 128


def test_pkce_challenge_format():
    """Test code challenge format"""
    verifier = "test_verifier_123456789_abcdefghijk_ABCDEFGHIJK"
    challenge = generate_code_challenge(verifier, "S256")
    
    # Challenge should be base64url without padding
    assert "=" not in challenge
    assert "+" not in challenge
    assert "/" not in challenge
    
    # Should only contain base64url characters
    import re
    assert re.match(r'^[A-Za-z0-9_-]+$', challenge)