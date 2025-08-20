"""AES-256-GCM encryption/decryption implementation."""

import os
from typing import BinaryIO, Optional, Tuple

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag


class AESGCMCipher:
    """AES-256-GCM cipher for file encryption/decryption."""
    
    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits (recommended for GCM)
    TAG_SIZE = 16  # 128 bits
    CHUNK_SIZE = 64 * 1024  # 64KB chunks for streaming
    
    def __init__(self, key: bytes):
        """Initialize cipher with a 256-bit key.
        
        Args:
            key: 32-byte encryption key
            
        Raises:
            ValueError: If key size is incorrect
        """
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"Key must be {self.KEY_SIZE} bytes, got {len(key)}")
        self.key = key
    
    def encrypt_file(self, input_file: BinaryIO, output_file: BinaryIO, 
                    nonce: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Encrypt a file using AES-256-GCM.
        
        Args:
            input_file: Input file object opened in binary mode
            output_file: Output file object opened in binary mode
            nonce: Optional 12-byte nonce (generated if not provided)
            
        Returns:
            Tuple of (nonce, auth_tag)
            
        Raises:
            ValueError: If nonce size is incorrect
        """
        if nonce is None:
            nonce = os.urandom(self.NONCE_SIZE)
        elif len(nonce) != self.NONCE_SIZE:
            raise ValueError(f"Nonce must be {self.NONCE_SIZE} bytes")
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Process file in chunks
        while True:
            chunk = input_file.read(self.CHUNK_SIZE)
            if not chunk:
                break
            encrypted_chunk = encryptor.update(chunk)
            output_file.write(encrypted_chunk)
        
        # Finalize and get authentication tag
        encryptor.finalize()
        auth_tag = encryptor.tag
        
        return nonce, auth_tag
    
    def decrypt_file(self, input_file: BinaryIO, output_file: BinaryIO,
                    nonce: bytes, auth_tag: bytes) -> None:
        """Decrypt a file using AES-256-GCM.
        
        Args:
            input_file: Encrypted input file object
            output_file: Decrypted output file object
            nonce: 12-byte nonce used for encryption
            auth_tag: 16-byte authentication tag
            
        Raises:
            ValueError: If nonce or tag size is incorrect
            InvalidTag: If authentication fails (data corrupted/tampered)
        """
        if len(nonce) != self.NONCE_SIZE:
            raise ValueError(f"Nonce must be {self.NONCE_SIZE} bytes")
        if len(auth_tag) != self.TAG_SIZE:
            raise ValueError(f"Auth tag must be {self.TAG_SIZE} bytes")
        
        # Create cipher with tag
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(nonce, auth_tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Process file in chunks
        while True:
            chunk = input_file.read(self.CHUNK_SIZE)
            if not chunk:
                break
            decrypted_chunk = decryptor.update(chunk)
            output_file.write(decrypted_chunk)
        
        # Verify authentication tag
        try:
            decryptor.finalize()
        except InvalidTag:
            raise InvalidTag("Authentication failed - file may be corrupted or tampered")
    
    def encrypt_bytes(self, data: bytes, nonce: Optional[bytes] = None) -> Tuple[bytes, bytes, bytes]:
        """Encrypt bytes using AES-256-GCM.
        
        Args:
            data: Data to encrypt
            nonce: Optional 12-byte nonce
            
        Returns:
            Tuple of (encrypted_data, nonce, auth_tag)
        """
        if nonce is None:
            nonce = os.urandom(self.NONCE_SIZE)
        elif len(nonce) != self.NONCE_SIZE:
            raise ValueError(f"Nonce must be {self.NONCE_SIZE} bytes")
        
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return ciphertext, nonce, encryptor.tag
    
    def decrypt_bytes(self, ciphertext: bytes, nonce: bytes, auth_tag: bytes) -> bytes:
        """Decrypt bytes using AES-256-GCM.
        
        Args:
            ciphertext: Encrypted data
            nonce: 12-byte nonce
            auth_tag: 16-byte authentication tag
            
        Returns:
            Decrypted data
            
        Raises:
            InvalidTag: If authentication fails
        """
        if len(nonce) != self.NONCE_SIZE:
            raise ValueError(f"Nonce must be {self.NONCE_SIZE} bytes")
        if len(auth_tag) != self.TAG_SIZE:
            raise ValueError(f"Auth tag must be {self.TAG_SIZE} bytes")
        
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.GCM(nonce, auth_tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext