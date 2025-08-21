"""Unit tests for key derivation functions."""

import os
import pytest

from src.crypto.key_derivation import (
    derive_key,
    generate_salt,
    verify_password,
    hmac_compare,
    KeyDerivation
)


class TestKeyDerivation:
    """Test key derivation functions."""
    
    def test_derive_key(self):
        """Test basic key derivation."""
        password = "test_password_123"
        salt = generate_salt()
        
        key = derive_key(password, salt)
        
        # Check key size
        assert len(key) == 32
        
        # Same password and salt should give same key
        key2 = derive_key(password, salt)
        assert key == key2
        
        # Different password should give different key
        key3 = derive_key("different_password", salt)
        assert key != key3
        
        # Different salt should give different key
        salt2 = generate_salt()
        key4 = derive_key(password, salt2)
        assert key != key4
    
    def test_salt_generation(self):
        """Test salt generation."""
        salt1 = generate_salt()
        assert len(salt1) == 32
        
        salt2 = generate_salt(16)
        assert len(salt2) == 16
        
        # Salts should be unique
        salts = set()
        for _ in range(100):
            salt = generate_salt()
            assert salt not in salts
            salts.add(salt)
    
    def test_salt_validation(self):
        """Test salt size validation."""
        password = "test"
        
        # Valid salt sizes
        derive_key(password, os.urandom(16))  # Minimum
        derive_key(password, os.urandom(32))  # Default
        derive_key(password, os.urandom(64))  # Larger
        
        # Invalid salt size
        with pytest.raises(ValueError, match="Salt must be at least 16 bytes"):
            derive_key(password, os.urandom(8))
    
    def test_verify_password(self):
        """Test password verification."""
        password = "correct_password"
        salt = generate_salt()
        key = derive_key(password, salt)
        
        # Correct password
        assert verify_password(password, salt, key)
        
        # Wrong password
        assert not verify_password("wrong_password", salt, key)
        
        # Wrong salt
        wrong_salt = generate_salt()
        assert not verify_password(password, wrong_salt, key)
    
    def test_hmac_compare(self):
        """Test constant-time comparison."""
        # Equal bytes
        a = b"test_data"
        b = b"test_data"
        assert hmac_compare(a, b)
        
        # Different bytes
        a = b"test_data"
        b = b"test_datb"
        assert not hmac_compare(a, b)
        
        # Different lengths
        a = b"short"
        b = b"longer_data"
        assert not hmac_compare(a, b)
    
    def test_key_derivation_class(self):
        """Test KeyDerivation class."""
        kd = KeyDerivation(iterations=50000)
        
        # Derive from password
        password = "test_password"
        key1, salt1 = kd.derive_from_password(password)
        assert len(key1) == 32
        assert len(salt1) == 32
        
        # Same password with same salt gives same key
        key2, _ = kd.derive_from_password(password, salt1)
        assert key1 == key2
    
    def test_keyfile_operations(self, tmp_path):
        """Test keyfile generation and loading."""
        kd = KeyDerivation()
        keyfile_path = str(tmp_path / "test.key")
        
        # Generate keyfile
        key1 = kd.generate_keyfile(keyfile_path)
        assert len(key1) == 32
        assert os.path.exists(keyfile_path)
        
        # Check file permissions (Unix only)
        if hasattr(os, 'chmod'):
            stat = os.stat(keyfile_path)
            assert stat.st_mode & 0o777 == 0o600
        
        # Load keyfile
        key2 = kd.derive_from_keyfile(keyfile_path)
        assert key1 == key2
        
        # Invalid keyfile
        bad_keyfile = str(tmp_path / "bad.key")
        with open(bad_keyfile, 'wb') as f:
            f.write(b"too_short")
        
        with pytest.raises(ValueError, match="Key file must contain exactly 32 bytes"):
            kd.derive_from_keyfile(bad_keyfile)
    
    def test_iteration_count(self):
        """Test different iteration counts."""
        password = "test"
        salt = generate_salt()
        
        # Different iteration counts give different keys
        key1 = derive_key(password, salt, iterations=10000)
        key2 = derive_key(password, salt, iterations=50000)
        key3 = derive_key(password, salt, iterations=100000)
        
        assert key1 != key2
        assert key2 != key3
        assert key1 != key3