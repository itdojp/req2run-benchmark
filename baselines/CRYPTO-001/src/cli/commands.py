"""CLI commands for the encryption tool."""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from tqdm import tqdm

from ..crypto import AESGCMCipher, KeyDerivation, generate_salt
from ..file_handler import FileEncryptor


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """AES-256-GCM File Encryption Tool."""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), required=True,
              help='Output file path')
@click.option('-p', '--password', help='Encryption password')
@click.option('-k', '--keyfile', type=click.Path(exists=True),
              help='Key file to use instead of password')
@click.option('--iterations', default=100000, help='PBKDF2 iterations')
@click.option('--no-progress', is_flag=True, help='Disable progress bar')
def encrypt(input_file: str, output: str, password: Optional[str],
           keyfile: Optional[str], iterations: int, no_progress: bool):
    """Encrypt a file using AES-256-GCM."""
    
    # Validate input
    if not password and not keyfile:
        password = click.prompt('Enter password', hide_input=True,
                               confirmation_prompt=True)
    elif password and keyfile:
        click.echo("Error: Specify either password or keyfile, not both", err=True)
        sys.exit(1)
    
    try:
        # Get encryption key
        key_derivation = KeyDerivation(iterations=iterations)
        
        if keyfile:
            key = key_derivation.derive_from_keyfile(keyfile)
            salt = None  # Not needed for keyfile
        else:
            key, salt = key_derivation.derive_from_password(password)
        
        # Create encryptor
        encryptor = FileEncryptor(key)
        
        # Get file size for progress bar
        file_size = os.path.getsize(input_file)
        
        # Encrypt file with progress
        with tqdm(total=file_size, unit='B', unit_scale=True,
                 disable=no_progress, desc='Encrypting') as pbar:
            
            def progress_callback(bytes_processed):
                pbar.update(bytes_processed)
            
            encryptor.encrypt_file(
                input_file, 
                output,
                salt=salt,
                progress_callback=progress_callback if not no_progress else None
            )
        
        click.echo(f"✓ File encrypted successfully: {output}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), required=True,
              help='Output file path')
@click.option('-p', '--password', help='Decryption password')
@click.option('-k', '--keyfile', type=click.Path(exists=True),
              help='Key file to use instead of password')
@click.option('--iterations', default=100000, help='PBKDF2 iterations')
@click.option('--no-progress', is_flag=True, help='Disable progress bar')
def decrypt(input_file: str, output: str, password: Optional[str],
           keyfile: Optional[str], iterations: int, no_progress: bool):
    """Decrypt a file encrypted with AES-256-GCM."""
    
    # Validate input
    if not password and not keyfile:
        password = click.prompt('Enter password', hide_input=True)
    elif password and keyfile:
        click.echo("Error: Specify either password or keyfile, not both", err=True)
        sys.exit(1)
    
    try:
        # Create decryptor
        key_derivation = KeyDerivation(iterations=iterations)
        encryptor = FileEncryptor(None)  # Key will be set later
        
        # Get file size for progress bar
        file_size = os.path.getsize(input_file)
        
        # Decrypt file with progress
        with tqdm(total=file_size, unit='B', unit_scale=True,
                 disable=no_progress, desc='Decrypting') as pbar:
            
            def progress_callback(bytes_processed):
                pbar.update(bytes_processed)
            
            if keyfile:
                key = key_derivation.derive_from_keyfile(keyfile)
                encryptor.key = key
                encryptor.decrypt_file(
                    input_file,
                    output,
                    password=None,
                    progress_callback=progress_callback if not no_progress else None
                )
            else:
                encryptor.decrypt_file(
                    input_file,
                    output,
                    password=password,
                    iterations=iterations,
                    progress_callback=progress_callback if not no_progress else None
                )
        
        click.echo(f"✓ File decrypted successfully: {output}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-p', '--password', help='Password to verify')
@click.option('-k', '--keyfile', type=click.Path(exists=True),
              help='Key file to verify')
@click.option('--iterations', default=100000, help='PBKDF2 iterations')
def verify(input_file: str, password: Optional[str], 
          keyfile: Optional[str], iterations: int):
    """Verify an encrypted file without decrypting."""
    
    # Validate input
    if not password and not keyfile:
        password = click.prompt('Enter password', hide_input=True)
    elif password and keyfile:
        click.echo("Error: Specify either password or keyfile, not both", err=True)
        sys.exit(1)
    
    try:
        key_derivation = KeyDerivation(iterations=iterations)
        encryptor = FileEncryptor(None)
        
        if keyfile:
            key = key_derivation.derive_from_keyfile(keyfile)
            is_valid = encryptor.verify_file(input_file, key=key)
        else:
            is_valid = encryptor.verify_file(
                input_file, 
                password=password,
                iterations=iterations
            )
        
        if is_valid:
            click.echo("✓ File verification successful - integrity intact")
        else:
            click.echo("✗ File verification failed - corrupted or wrong password", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('-o', '--output', type=click.Path(), required=True,
              help='Output key file path')
def keygen(output: str):
    """Generate a new encryption key file."""
    try:
        key_derivation = KeyDerivation()
        key = key_derivation.generate_keyfile(output)
        
        click.echo(f"✓ Key file generated: {output}")
        click.echo(f"  Key size: 256 bits")
        click.echo(f"  Permissions: 0600 (owner read/write only)")
        click.echo("\n⚠️  Keep this file secure and backed up!")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('-p', '--password', required=True, help='Password to derive from')
@click.option('-s', '--salt', help='Salt value (hex encoded)')
@click.option('--iterations', default=100000, help='PBKDF2 iterations')
def derive_key(password: str, salt: Optional[str], iterations: int):
    """Derive a key from a password (for testing/debugging)."""
    try:
        if salt:
            salt_bytes = bytes.fromhex(salt)
        else:
            salt_bytes = generate_salt()
            click.echo(f"Generated salt: {salt_bytes.hex()}")
        
        key_derivation = KeyDerivation(iterations=iterations)
        key, _ = key_derivation.derive_from_password(password, salt_bytes)
        
        click.echo(f"Derived key: {key.hex()}")
        click.echo(f"Iterations: {iterations}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()