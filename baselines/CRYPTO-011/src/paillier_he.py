"""Paillier Homomorphic Encryption Implementation"""
import secrets
import math
from typing import Tuple, Optional, List, Any
from dataclasses import dataclass
import gmpy2
import json


@dataclass
class PaillierPublicKey:
    """Paillier public key"""
    n: int  # n = p * q
    g: int  # generator
    n_sq: int  # n^2
    
    def encrypt(self, plaintext: int, r: Optional[int] = None) -> int:
        """Encrypt plaintext using public key"""
        if plaintext < 0 or plaintext >= self.n:
            raise ValueError(f"Plaintext must be in range [0, {self.n})")
        
        if r is None:
            # Generate random r where gcd(r, n) = 1
            while True:
                r = secrets.randbelow(self.n)
                if math.gcd(r, self.n) == 1:
                    break
        
        # Ciphertext: c = g^m * r^n mod n^2
        gm = pow(self.g, plaintext, self.n_sq)
        rn = pow(r, self.n, self.n_sq)
        ciphertext = (gm * rn) % self.n_sq
        
        return ciphertext
    
    def add_encrypted(self, c1: int, c2: int) -> int:
        """Add two encrypted values (homomorphic addition)"""
        # E(m1 + m2) = E(m1) * E(m2) mod n^2
        return (c1 * c2) % self.n_sq
    
    def multiply_encrypted(self, ciphertext: int, scalar: int) -> int:
        """Multiply encrypted value by scalar (homomorphic scalar multiplication)"""
        # E(m * k) = E(m)^k mod n^2
        return pow(ciphertext, scalar, self.n_sq)


@dataclass
class PaillierPrivateKey:
    """Paillier private key"""
    lambda_n: int  # lcm(p-1, q-1)
    mu: int  # modular multiplicative inverse
    public_key: PaillierPublicKey
    
    def decrypt(self, ciphertext: int) -> int:
        """Decrypt ciphertext using private key"""
        if ciphertext < 0 or ciphertext >= self.public_key.n_sq:
            raise ValueError("Invalid ciphertext")
        
        # L function: L(x) = (x - 1) / n
        def L(x: int) -> int:
            return (x - 1) // self.public_key.n
        
        # Plaintext: m = L(c^lambda mod n^2) * mu mod n
        x = pow(ciphertext, self.lambda_n, self.public_key.n_sq)
        plaintext = (L(x) * self.mu) % self.public_key.n
        
        return plaintext


class PaillierCryptosystem:
    """Paillier homomorphic encryption system"""
    
    def __init__(self, key_size: int = 2048):
        self.key_size = key_size
        self.public_key: Optional[PaillierPublicKey] = None
        self.private_key: Optional[PaillierPrivateKey] = None
    
    def generate_prime(self, bits: int) -> int:
        """Generate a prime number with specified bit length"""
        while True:
            # Generate random odd number
            p = secrets.randbits(bits) | 1
            
            # Miller-Rabin primality test (simplified)
            if self.is_probable_prime(p):
                return p
    
    def is_probable_prime(self, n: int, k: int = 10) -> bool:
        """Miller-Rabin primality test"""
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        if n % 2 == 0:
            return False
        
        # Write n-1 as 2^r * d
        r, d = 0, n - 1
        while d % 2 == 0:
            r += 1
            d //= 2
        
        # Witness loop
        for _ in range(k):
            a = secrets.randbelow(n - 3) + 2
            x = pow(a, d, n)
            
            if x == 1 or x == n - 1:
                continue
            
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        
        return True
    
    def generate_keypair(self) -> Tuple[PaillierPublicKey, PaillierPrivateKey]:
        """Generate Paillier key pair"""
        # Generate two large primes p and q
        p = self.generate_prime(self.key_size // 2)
        q = self.generate_prime(self.key_size // 2)
        
        # Ensure p != q
        while p == q:
            q = self.generate_prime(self.key_size // 2)
        
        n = p * q
        n_sq = n * n
        
        # g = n + 1 (simplified generator choice)
        g = n + 1
        
        # lambda = lcm(p-1, q-1)
        lambda_n = math.lcm(p - 1, q - 1)
        
        # mu = (L(g^lambda mod n^2))^-1 mod n
        def L(x: int) -> int:
            return (x - 1) // n
        
        x = pow(g, lambda_n, n_sq)
        mu = pow(L(x), -1, n)  # Modular inverse
        
        # Create keys
        public_key = PaillierPublicKey(n=n, g=g, n_sq=n_sq)
        private_key = PaillierPrivateKey(
            lambda_n=lambda_n,
            mu=mu,
            public_key=public_key
        )
        
        self.public_key = public_key
        self.private_key = private_key
        
        return public_key, private_key
    
    def encrypt(self, plaintext: int) -> int:
        """Encrypt plaintext"""
        if not self.public_key:
            raise ValueError("Keys not generated")
        return self.public_key.encrypt(plaintext)
    
    def decrypt(self, ciphertext: int) -> int:
        """Decrypt ciphertext"""
        if not self.private_key:
            raise ValueError("Private key not available")
        return self.private_key.decrypt(ciphertext)
    
    def add(self, c1: int, c2: int) -> int:
        """Homomorphic addition"""
        if not self.public_key:
            raise ValueError("Public key not available")
        return self.public_key.add_encrypted(c1, c2)
    
    def multiply_by_scalar(self, ciphertext: int, scalar: int) -> int:
        """Homomorphic scalar multiplication"""
        if not self.public_key:
            raise ValueError("Public key not available")
        return self.public_key.multiply_encrypted(ciphertext, scalar)
    
    def batch_encrypt(self, plaintexts: List[int]) -> List[int]:
        """Batch encryption for efficiency"""
        return [self.encrypt(p) for p in plaintexts]
    
    def batch_decrypt(self, ciphertexts: List[int]) -> List[int]:
        """Batch decryption"""
        return [self.decrypt(c) for c in ciphertexts]
    
    def sum_encrypted(self, ciphertexts: List[int]) -> int:
        """Sum multiple encrypted values"""
        if not ciphertexts:
            return self.encrypt(0)
        
        result = ciphertexts[0]
        for c in ciphertexts[1:]:
            result = self.add(result, c)
        
        return result
    
    def average_encrypted(self, ciphertexts: List[int]) -> int:
        """Compute average of encrypted values (approximate)"""
        if not ciphertexts:
            return self.encrypt(0)
        
        # Sum all encrypted values
        sum_encrypted = self.sum_encrypted(ciphertexts)
        
        # Note: Division is not directly supported in Paillier
        # This returns the sum; actual division would need to be done after decryption
        return sum_encrypted


class PartiallyHomomorphicOperations:
    """Operations for partially homomorphic encryption"""
    
    def __init__(self, cryptosystem: PaillierCryptosystem):
        self.crypto = cryptosystem
    
    def encrypted_dot_product(
        self,
        encrypted_vector: List[int],
        plain_vector: List[int]
    ) -> int:
        """Compute dot product with encrypted and plain vectors"""
        if len(encrypted_vector) != len(plain_vector):
            raise ValueError("Vectors must have same length")
        
        result = self.crypto.encrypt(0)
        
        for enc_val, plain_val in zip(encrypted_vector, plain_vector):
            # Multiply encrypted value by plaintext scalar
            product = self.crypto.multiply_by_scalar(enc_val, plain_val)
            # Add to result
            result = self.crypto.add(result, product)
        
        return result
    
    def encrypted_linear_combination(
        self,
        encrypted_values: List[int],
        coefficients: List[int]
    ) -> int:
        """Compute linear combination of encrypted values"""
        return self.encrypted_dot_product(encrypted_values, coefficients)
    
    def encrypted_polynomial(
        self,
        encrypted_x: int,
        coefficients: List[int]
    ) -> int:
        """Evaluate polynomial on encrypted value (limited degree)"""
        # Note: Only works for degree 1 polynomials in Paillier
        # p(x) = a0 + a1*x
        if len(coefficients) > 2:
            raise ValueError("Paillier only supports degree 1 polynomials")
        
        result = self.crypto.encrypt(coefficients[0]) if coefficients else self.crypto.encrypt(0)
        
        if len(coefficients) > 1:
            term = self.crypto.multiply_by_scalar(encrypted_x, coefficients[1])
            result = self.crypto.add(result, term)
        
        return result


class NoiseManager:
    """Noise management for homomorphic operations"""
    
    def __init__(self, security_parameter: int = 128):
        self.security_parameter = security_parameter
        self.noise_budget = security_parameter * 10  # Simplified noise budget
        self.current_noise = 0
    
    def add_noise(self, operation_type: str) -> bool:
        """Add noise from operation and check if within budget"""
        noise_costs = {
            "encrypt": 1,
            "add": 2,
            "multiply": 5,
            "bootstrap": -self.noise_budget + 10  # Bootstrapping refreshes noise
        }
        
        cost = noise_costs.get(operation_type, 1)
        self.current_noise += cost
        
        return self.current_noise < self.noise_budget
    
    def get_remaining_budget(self) -> int:
        """Get remaining noise budget"""
        return max(0, self.noise_budget - self.current_noise)
    
    def needs_bootstrapping(self) -> bool:
        """Check if bootstrapping is needed"""
        return self.current_noise > self.noise_budget * 0.8
    
    def reset_noise(self):
        """Reset noise after bootstrapping"""
        self.current_noise = 10  # Small residual noise after bootstrapping


class CKKSApproximateScheme:
    """Simplified CKKS scheme for approximate arithmetic"""
    
    def __init__(self, precision: int = 40, scale: float = 2**40):
        self.precision = precision
        self.scale = scale
        self.paillier = PaillierCryptosystem()
    
    def encode(self, value: float) -> int:
        """Encode floating point to integer"""
        return int(value * self.scale)
    
    def decode(self, value: int) -> float:
        """Decode integer to floating point"""
        return value / self.scale
    
    def encrypt_float(self, value: float) -> int:
        """Encrypt floating point value"""
        encoded = self.encode(value)
        return self.paillier.encrypt(encoded)
    
    def decrypt_float(self, ciphertext: int) -> float:
        """Decrypt to floating point value"""
        decrypted = self.paillier.decrypt(ciphertext)
        return self.decode(decrypted)
    
    def add_floats(self, c1: int, c2: int) -> int:
        """Add encrypted floating point values"""
        return self.paillier.add(c1, c2)
    
    def multiply_by_float(self, ciphertext: int, scalar: float) -> int:
        """Multiply encrypted value by floating point scalar"""
        # Convert scalar to integer with scaling
        scalar_int = int(scalar * self.scale)
        
        # Note: This is approximate and may lose precision
        result = self.paillier.multiply_by_scalar(ciphertext, scalar_int)
        
        # Adjust for double scaling
        # In practice, this needs more careful handling
        return result