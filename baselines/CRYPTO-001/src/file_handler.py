"""File handling and encryption/decryption operations."""

import os
import shutil
from pathlib import Path
from typing import Optional, Callable

from .crypto import (
    AESGCMCipher,
    derive_key,
    generate_salt,
    generate_nonce
)
from .crypto.utils import (
    format_file_header,
    parse_file_header,
    validate_magic,
    format_bytes
)


MAGIC_BYTES = b'CRYP'
VERSION = 1
HEADER_SIZE = 65


class FileEncryptor:
    """High-level file encryption/decryption interface."""
    
    def __init__(self, key: Optional[bytes] = None):
        """Initialize with optional key.
        
        Args:
            key: 32-byte encryption key (can be set later)
        """
        self.key = key
    
    def encrypt_file(self, input_path: str, output_path: str,
                    salt: Optional[bytes] = None,
                    password: Optional[str] = None,
                    iterations: int = 100000,
                    progress_callback: Optional[Callable[[int], None]] = None) -> None:
        """Encrypt a file.
        
        Args:
            input_path: Path to input file
            output_path: Path to output encrypted file
            salt: Optional salt for password derivation
            password: Optional password (uses self.key if not provided)
            iterations: PBKDF2 iterations for password derivation
            progress_callback: Optional callback for progress updates
        """
        # Derive key from password if needed
        if password:
            if salt is None:
                salt = generate_salt()
            key = derive_key(password, salt, iterations)
        else:
            key = self.key
            if key is None:
                raise ValueError("No key or password provided")
        
        # Create cipher
        cipher = AESGCMCipher(key)
        
        # Generate nonce
        nonce = generate_nonce()
        
        # Open files
        with open(input_path, 'rb') as infile, \
             open(output_path, 'wb') as outfile:
            
            # Reserve space for header (will write it after encryption)
            outfile.write(b'\x00' * HEADER_SIZE)
            
            # Encrypt file
            nonce, auth_tag = cipher.encrypt_file(infile, outfile, nonce)
            
            # Write header at the beginning
            outfile.seek(0)
            header = format_file_header(
                MAGIC_BYTES,
                VERSION,
                salt if salt else b'\x00' * 32,
                nonce,
                auth_tag
            )
            outfile.write(header)
            
            # Progress callback
            if progress_callback:
                file_size = infile.tell()
                progress_callback(file_size)
        
        # Preserve file metadata
        self._copy_metadata(input_path, output_path)
    
    def decrypt_file(self, input_path: str, output_path: str,
                    password: Optional[str] = None,
                    iterations: int = 100000,
                    progress_callback: Optional[Callable[[int], None]] = None) -> None:
        """Decrypt a file.
        
        Args:
            input_path: Path to encrypted file
            output_path: Path to output decrypted file
            password: Optional password (uses self.key if not provided)
            iterations: PBKDF2 iterations for password derivation
            progress_callback: Optional callback for progress updates
        """
        with open(input_path, 'rb') as infile:
            # Read and parse header
            header_bytes = infile.read(HEADER_SIZE)
            if len(header_bytes) != HEADER_SIZE:
                raise ValueError("Invalid encrypted file - header too short")
            
            header = parse_file_header(header_bytes)
            
            # Validate magic bytes
            if not validate_magic(header['magic'], MAGIC_BYTES):
                raise ValueError("Invalid encrypted file - wrong magic bytes")
            
            # Check version
            if header['version'] != VERSION:
                raise ValueError(f"Unsupported version: {header['version']}")
            
            # Derive key if password provided
            if password:
                salt = header['salt']
                if salt == b'\x00' * 32:
                    raise ValueError("File was encrypted with keyfile, not password")
                key = derive_key(password, salt, iterations)
            else:
                key = self.key
                if key is None:
                    raise ValueError("No key or password provided")
            
            # Create cipher
            cipher = AESGCMCipher(key)
            
            # Decrypt file
            with open(output_path, 'wb') as outfile:
                cipher.decrypt_file(
                    infile,
                    outfile,
                    header['nonce'],
                    header['tag']
                )
            
            # Progress callback
            if progress_callback:
                file_size = os.path.getsize(input_path) - HEADER_SIZE
                progress_callback(file_size)
        
        # Preserve file metadata
        self._copy_metadata(input_path, output_path)
    
    def verify_file(self, file_path: str, 
                   key: Optional[bytes] = None,
                   password: Optional[str] = None,
                   iterations: int = 100000) -> bool:
        """Verify an encrypted file without fully decrypting it.
        
        Args:
            file_path: Path to encrypted file
            key: Optional encryption key
            password: Optional password
            iterations: PBKDF2 iterations
            
        Returns:
            True if file is valid, False otherwise
        """
        try:
            with open(file_path, 'rb') as f:
                # Read header
                header_bytes = f.read(HEADER_SIZE)
                if len(header_bytes) != HEADER_SIZE:
                    return False
                
                header = parse_file_header(header_bytes)
                
                # Validate magic and version
                if not validate_magic(header['magic'], MAGIC_BYTES):
                    return False
                if header['version'] != VERSION:
                    return False
                
                # Derive key if needed
                if password:
                    salt = header['salt']
                    if salt == b'\x00' * 32:
                        return False  # Wrong auth method
                    verify_key = derive_key(password, salt, iterations)
                elif key:
                    verify_key = key
                else:
                    verify_key = self.key
                    if verify_key is None:
                        return False
                
                # Try to decrypt a small portion to verify
                cipher = AESGCMCipher(verify_key)
                
                # Read first chunk
                chunk = f.read(1024)
                if not chunk:
                    # Empty file after header is valid
                    return True
                
                # Create temporary cipher for verification
                from io import BytesIO
                test_input = BytesIO(chunk)
                test_output = BytesIO()
                
                try:
                    cipher.decrypt_file(
                        test_input,
                        test_output,
                        header['nonce'],
                        header['tag']
                    )
                    return True
                except:
                    return False
                    
        except Exception:
            return False
    
    def _copy_metadata(self, source: str, dest: str) -> None:
        """Copy file metadata from source to destination.
        
        Args:
            source: Source file path
            dest: Destination file path
        """
        try:
            # Copy timestamps
            stat = os.stat(source)
            os.utime(dest, (stat.st_atime, stat.st_mtime))
            
            # Copy permissions (Unix-like systems)
            if hasattr(os, 'chmod'):
                os.chmod(dest, stat.st_mode)
        except Exception:
            # Metadata copy is best-effort
            pass
    
    def encrypt_directory(self, input_dir: str, output_file: str,
                         password: Optional[str] = None,
                         compress: bool = True) -> None:
        """Encrypt an entire directory into a single file.
        
        Args:
            input_dir: Directory to encrypt
            output_file: Output encrypted archive
            password: Encryption password
            compress: Whether to compress before encryption
        """
        import tempfile
        import tarfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create tar archive
            tar_path = os.path.join(tmpdir, 'archive.tar')
            if compress:
                tar_path += '.gz'
                mode = 'w:gz'
            else:
                mode = 'w'
            
            with tarfile.open(tar_path, mode) as tar:
                tar.add(input_dir, arcname=os.path.basename(input_dir))
            
            # Encrypt the archive
            self.encrypt_file(tar_path, output_file, password=password)
    
    def decrypt_directory(self, input_file: str, output_dir: str,
                         password: Optional[str] = None) -> None:
        """Decrypt an encrypted directory archive.
        
        Args:
            input_file: Encrypted archive file
            output_dir: Output directory
            password: Decryption password
        """
        import tempfile
        import tarfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Decrypt to temporary file
            tar_path = os.path.join(tmpdir, 'archive.tar')
            self.decrypt_file(input_file, tar_path, password=password)
            
            # Detect compression
            if tar_path.endswith('.gz'):
                mode = 'r:gz'
            else:
                mode = 'r'
            
            # Extract archive
            with tarfile.open(tar_path, mode) as tar:
                tar.extractall(output_dir)