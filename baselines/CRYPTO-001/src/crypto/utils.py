"""Cryptographic utility functions."""

import os
import secrets
from typing import Optional


def generate_nonce(size: int = 12) -> bytes:
    """Generate a cryptographically secure nonce.
    
    Args:
        size: Nonce size in bytes (default 12 for GCM)
        
    Returns:
        Random nonce bytes
    """
    return os.urandom(size)


def secure_random_bytes(size: int) -> bytes:
    """Generate cryptographically secure random bytes.
    
    Args:
        size: Number of bytes to generate
        
    Returns:
        Random bytes
    """
    return secrets.token_bytes(size)


def clear_bytes(data: bytearray) -> None:
    """Attempt to clear sensitive data from memory.
    
    Note: This is best-effort and may not work on all platforms.
    
    Args:
        data: Mutable byte array to clear
    """
    if isinstance(data, bytearray):
        for i in range(len(data)):
            data[i] = 0


def format_file_header(magic: bytes, version: int, salt: bytes, 
                      nonce: bytes, tag: bytes) -> bytes:
    """Format encryption file header.
    
    Header format:
    - Magic bytes (4 bytes)
    - Version (1 byte)
    - Salt (32 bytes)
    - Nonce (12 bytes)
    - Auth tag (16 bytes)
    Total: 65 bytes
    
    Args:
        magic: 4-byte magic identifier
        version: Protocol version (0-255)
        salt: 32-byte salt
        nonce: 12-byte nonce
        tag: 16-byte authentication tag
        
    Returns:
        Formatted header bytes
    """
    if len(magic) != 4:
        raise ValueError("Magic must be 4 bytes")
    if not 0 <= version <= 255:
        raise ValueError("Version must be 0-255")
    if len(salt) != 32:
        raise ValueError("Salt must be 32 bytes")
    if len(nonce) != 12:
        raise ValueError("Nonce must be 12 bytes")
    if len(tag) != 16:
        raise ValueError("Tag must be 16 bytes")
    
    header = bytearray()
    header.extend(magic)
    header.append(version)
    header.extend(salt)
    header.extend(nonce)
    header.extend(tag)
    
    return bytes(header)


def parse_file_header(header: bytes) -> dict:
    """Parse encryption file header.
    
    Args:
        header: 65-byte header
        
    Returns:
        Dictionary with header fields
        
    Raises:
        ValueError: If header format is invalid
    """
    if len(header) != 65:
        raise ValueError(f"Header must be 65 bytes, got {len(header)}")
    
    return {
        'magic': header[0:4],
        'version': header[4],
        'salt': header[5:37],
        'nonce': header[37:49],
        'tag': header[49:65]
    }


def validate_magic(magic: bytes, expected: bytes = b'CRYP') -> bool:
    """Validate file magic bytes.
    
    Args:
        magic: Magic bytes to check
        expected: Expected magic bytes
        
    Returns:
        True if magic matches, False otherwise
    """
    return magic == expected


def calculate_file_size_after_encryption(original_size: int) -> int:
    """Calculate encrypted file size including header.
    
    Args:
        original_size: Original file size in bytes
        
    Returns:
        Expected encrypted file size
    """
    header_size = 65  # Fixed header size
    # GCM doesn't add padding, ciphertext is same size as plaintext
    return header_size + original_size


def format_bytes(size: int) -> str:
    """Format byte size in human-readable format.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"