"""Unit tests for AES-GCM cipher."""

import os
import pytest
from io import BytesIO

from src.crypto.aes_gcm import AESGCMCipher


class TestAESGCMCipher:
    """Test AES-GCM cipher operations."""
    
    def test_key_validation(self):
        """Test key size validation."""
        # Valid key
        key = os.urandom(32)
        cipher = AESGCMCipher(key)
        assert cipher.key == key
        
        # Invalid key sizes
        with pytest.raises(ValueError, match="Key must be 32 bytes"):
            AESGCMCipher(os.urandom(16))
        
        with pytest.raises(ValueError, match="Key must be 32 bytes"):
            AESGCMCipher(os.urandom(64))
    
    def test_encrypt_decrypt_bytes(self):
        """Test byte encryption and decryption."""
        key = os.urandom(32)
        cipher = AESGCMCipher(key)
        
        # Test data
        plaintext = b"Hello, World! This is a test message."
        
        # Encrypt
        ciphertext, nonce, tag = cipher.encrypt_bytes(plaintext)
        
        # Verify sizes
        assert len(nonce) == 12
        assert len(tag) == 16
        assert len(ciphertext) == len(plaintext)
        
        # Decrypt
        decrypted = cipher.decrypt_bytes(ciphertext, nonce, tag)
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_file(self):
        """Test file encryption and decryption."""
        key = os.urandom(32)
        cipher = AESGCMCipher(key)
        
        # Create test data
        test_data = b"Test file content" * 1000
        
        # Create file-like objects
        input_file = BytesIO(test_data)
        encrypted_file = BytesIO()
        
        # Encrypt
        nonce, tag = cipher.encrypt_file(input_file, encrypted_file)
        
        # Verify nonce and tag
        assert len(nonce) == 12
        assert len(tag) == 16
        
        # Decrypt
        encrypted_file.seek(0)
        decrypted_file = BytesIO()
        cipher.decrypt_file(encrypted_file, decrypted_file, nonce, tag)
        
        # Verify
        decrypted_file.seek(0)
        assert decrypted_file.read() == test_data
    
    def test_authentication_failure(self):
        """Test that tampered data fails authentication."""
        key = os.urandom(32)
        cipher = AESGCMCipher(key)
        
        # Encrypt data
        plaintext = b"Sensitive data"
        ciphertext, nonce, tag = cipher.encrypt_bytes(plaintext)
        
        # Tamper with ciphertext
        tampered = bytearray(ciphertext)
        tampered[0] ^= 1  # Flip one bit
        
        # Decryption should fail
        from cryptography.exceptions import InvalidTag
        with pytest.raises(InvalidTag):
            cipher.decrypt_bytes(bytes(tampered), nonce, tag)
        
        # Wrong tag should also fail
        wrong_tag = os.urandom(16)
        with pytest.raises(InvalidTag):
            cipher.decrypt_bytes(ciphertext, nonce, wrong_tag)
    
    def test_nonce_uniqueness(self):
        """Test that unique nonces are generated."""
        key = os.urandom(32)
        cipher = AESGCMCipher(key)
        
        nonces = set()
        for _ in range(100):
            _, nonce, _ = cipher.encrypt_bytes(b"test")
            assert nonce not in nonces
            nonces.add(nonce)
    
    def test_large_file_streaming(self):
        """Test streaming encryption of large files."""
        key = os.urandom(32)
        cipher = AESGCMCipher(key)
        
        # Create 10MB test data
        chunk = b"x" * 1024  # 1KB
        input_file = BytesIO()
        for _ in range(10 * 1024):  # 10MB
            input_file.write(chunk)
        
        input_file.seek(0)
        encrypted_file = BytesIO()
        
        # Encrypt
        nonce, tag = cipher.encrypt_file(input_file, encrypted_file)
        
        # Decrypt
        encrypted_file.seek(0)
        decrypted_file = BytesIO()
        cipher.decrypt_file(encrypted_file, decrypted_file, nonce, tag)
        
        # Verify size
        input_file.seek(0)
        decrypted_file.seek(0)
        assert len(input_file.read()) == len(decrypted_file.read())