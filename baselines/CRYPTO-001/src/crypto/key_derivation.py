"""Key derivation functions for password-based encryption."""

import os
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend


# PBKDF2 parameters (NIST recommendations)
DEFAULT_ITERATIONS = 100_000
DEFAULT_SALT_SIZE = 32  # 256 bits
KEY_SIZE = 32  # 256 bits for AES-256


def derive_key(password: str, salt: bytes, 
               iterations: int = DEFAULT_ITERATIONS) -> bytes:
    """Derive an encryption key from a password using PBKDF2.
    
    Args:
        password: User password
        salt: Random salt (should be at least 16 bytes)
        iterations: Number of PBKDF2 iterations
        
    Returns:
        32-byte derived key
        
    Raises:
        ValueError: If salt is too short
    """
    if len(salt) < 16:
        raise ValueError("Salt must be at least 16 bytes")
    
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    
    key = kdf.derive(password.encode('utf-8'))
    return key


def generate_salt(size: int = DEFAULT_SALT_SIZE) -> bytes:
    """Generate a cryptographically secure random salt.
    
    Args:
        size: Salt size in bytes
        
    Returns:
        Random salt bytes
    """
    return os.urandom(size)


def verify_password(password: str, salt: bytes, expected_key: bytes,
                   iterations: int = DEFAULT_ITERATIONS) -> bool:
    """Verify a password against a known derived key.
    
    Args:
        password: Password to verify
        salt: Salt used for key derivation
        expected_key: Expected derived key
        iterations: Number of PBKDF2 iterations
        
    Returns:
        True if password is correct, False otherwise
    """
    try:
        derived = derive_key(password, salt, iterations)
        # Constant-time comparison to prevent timing attacks
        return hmac_compare(derived, expected_key)
    except Exception:
        return False


def hmac_compare(a: bytes, b: bytes) -> bool:
    """Constant-time comparison of two byte strings.
    
    Args:
        a: First byte string
        b: Second byte string
        
    Returns:
        True if equal, False otherwise
    """
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    
    return result == 0


class KeyDerivation:
    """High-level key derivation interface."""
    
    def __init__(self, iterations: int = DEFAULT_ITERATIONS):
        """Initialize with specified iteration count.
        
        Args:
            iterations: PBKDF2 iteration count
        """
        self.iterations = iterations
    
    def derive_from_password(self, password: str, 
                            salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """Derive key from password with optional salt.
        
        Args:
            password: User password
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = generate_salt()
        
        key = derive_key(password, salt, self.iterations)
        return key, salt
    
    def derive_from_keyfile(self, keyfile_path: str) -> bytes:
        """Load key from a key file.
        
        Args:
            keyfile_path: Path to key file
            
        Returns:
            32-byte key
            
        Raises:
            ValueError: If key file is invalid
        """
        with open(keyfile_path, 'rb') as f:
            key = f.read()
        
        if len(key) != KEY_SIZE:
            raise ValueError(f"Key file must contain exactly {KEY_SIZE} bytes")
        
        return key
    
    def generate_keyfile(self, keyfile_path: str) -> bytes:
        """Generate a new random key and save to file.
        
        Args:
            keyfile_path: Path to save key file
            
        Returns:
            Generated key
        """
        key = os.urandom(KEY_SIZE)
        
        # Save with restrictive permissions
        with open(keyfile_path, 'wb') as f:
            f.write(key)
        
        # Set file permissions to 0600 (owner read/write only)
        os.chmod(keyfile_path, 0o600)
        
        return key