"""Schnorr Zero-Knowledge Proof Implementation"""
import hashlib
import secrets
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
import json
import time

# Using standard Python for elliptic curve operations
# In production, use specialized libraries like py_ecc or petlib

@dataclass
class SchnorrParams:
    """Parameters for Schnorr protocol"""
    # Using secp256k1 parameters as example
    p: int = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F  # Field prime
    n: int = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141  # Group order
    g: int = 0x0279BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798  # Generator point (compressed)
    
    def __post_init__(self):
        # Simplified - in production use proper elliptic curve library
        self.curve_name = "secp256k1"


@dataclass
class Commitment:
    """Commitment in Schnorr protocol"""
    value: int
    timestamp: float
    nonce: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": hex(self.value),
            "timestamp": self.timestamp,
            "nonce": self.nonce
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Commitment':
        return cls(
            value=int(data["value"], 16),
            timestamp=data["timestamp"],
            nonce=data["nonce"]
        )


@dataclass
class Challenge:
    """Challenge in Schnorr protocol"""
    value: int
    commitment_hash: str
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": hex(self.value),
            "commitment_hash": self.commitment_hash,
            "timestamp": self.timestamp
        }


@dataclass
class Response:
    """Response in Schnorr protocol"""
    value: int
    challenge_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": hex(self.value),
            "challenge_hash": self.challenge_hash
        }


@dataclass
class Proof:
    """Complete zero-knowledge proof"""
    commitment: Commitment
    challenge: Challenge
    response: Response
    verified: Optional[bool] = None
    rounds: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "commitment": self.commitment.to_dict(),
            "challenge": self.challenge.to_dict(),
            "response": self.response.to_dict(),
            "verified": self.verified,
            "rounds": self.rounds
        }


class SchnorrProtocol:
    """Schnorr identification protocol implementation"""
    
    def __init__(self, params: Optional[SchnorrParams] = None):
        self.params = params or SchnorrParams()
        self.commitment_store: Dict[str, Commitment] = {}
        self.used_challenges: set = set()
        
    def modular_exp(self, base: int, exp: int, mod: int) -> int:
        """Modular exponentiation"""
        return pow(base, exp, mod)
    
    def generate_random(self, max_val: Optional[int] = None) -> int:
        """Generate cryptographically secure random number"""
        if max_val is None:
            max_val = self.params.n - 1
        return secrets.randbelow(max_val) + 1
    
    def hash_value(self, *values) -> str:
        """Hash multiple values together"""
        hasher = hashlib.sha256()
        for v in values:
            if isinstance(v, int):
                hasher.update(str(v).encode())
            elif isinstance(v, str):
                hasher.update(v.encode())
            else:
                hasher.update(json.dumps(v).encode())
        return hasher.hexdigest()
    
    def generate_keypair(self) -> Tuple[int, int]:
        """Generate public/private key pair"""
        # Private key: random number in [1, n-1]
        private_key = self.generate_random(self.params.n - 1)
        
        # Public key: g^private_key mod p
        public_key = self.modular_exp(self.params.g, private_key, self.params.p)
        
        return private_key, public_key
    
    def create_commitment(self, private_key: int) -> Tuple[int, Commitment]:
        """Create commitment (first step of prover)"""
        # Generate random r
        r = self.generate_random(self.params.n - 1)
        
        # Compute commitment: t = g^r mod p
        t = self.modular_exp(self.params.g, r, self.params.p)
        
        # Create commitment object
        nonce = secrets.token_hex(16)
        commitment = Commitment(
            value=t,
            timestamp=time.time(),
            nonce=nonce
        )
        
        # Store commitment for later verification
        commitment_id = self.hash_value(commitment.value, commitment.nonce)
        self.commitment_store[commitment_id] = commitment
        
        return r, commitment
    
    def create_challenge(self, commitment: Commitment) -> Challenge:
        """Create challenge (verifier's step)"""
        # Generate random challenge c in [0, 2^t - 1] where t is security parameter
        # Using 128-bit challenges for security
        c = self.generate_random(2**128)
        
        # Prevent replay attacks
        challenge_id = self.hash_value(c, commitment.value, time.time())
        if challenge_id in self.used_challenges:
            raise ValueError("Challenge replay detected")
        self.used_challenges.add(challenge_id)
        
        return Challenge(
            value=c,
            commitment_hash=self.hash_value(commitment.value, commitment.nonce),
            timestamp=time.time()
        )
    
    def create_response(self, r: int, private_key: int, challenge: Challenge) -> Response:
        """Create response (second step of prover)"""
        # Compute response: s = r + c * private_key mod n
        s = (r + challenge.value * private_key) % self.params.n
        
        return Response(
            value=s,
            challenge_hash=self.hash_value(challenge.value, challenge.commitment_hash)
        )
    
    def verify_proof(self, public_key: int, proof: Proof) -> bool:
        """Verify the zero-knowledge proof"""
        try:
            # Verify commitment freshness (prevent old commitments)
            if time.time() - proof.commitment.timestamp > 300:  # 5 minutes
                return False
            
            # Verify challenge corresponds to commitment
            expected_hash = self.hash_value(proof.commitment.value, proof.commitment.nonce)
            if proof.challenge.commitment_hash != expected_hash:
                return False
            
            # Verify response corresponds to challenge
            expected_challenge_hash = self.hash_value(
                proof.challenge.value, 
                proof.challenge.commitment_hash
            )
            if proof.response.challenge_hash != expected_challenge_hash:
                return False
            
            # Schnorr verification equation:
            # g^s = t * y^c (mod p)
            # where s is response, t is commitment, y is public key, c is challenge
            
            left_side = self.modular_exp(self.params.g, proof.response.value, self.params.p)
            
            # Right side: t * y^c mod p
            y_c = self.modular_exp(public_key, proof.challenge.value, self.params.p)
            right_side = (proof.commitment.value * y_c) % self.params.p
            
            return left_side == right_side
            
        except Exception as e:
            print(f"Verification error: {e}")
            return False
    
    def multi_round_proof(self, private_key: int, public_key: int, rounds: int = 3) -> Tuple[bool, List[Proof]]:
        """Perform multi-round proof for increased security"""
        proofs = []
        
        for round_num in range(rounds):
            # Prover creates commitment
            r, commitment = self.create_commitment(private_key)
            
            # Verifier creates challenge
            challenge = self.create_challenge(commitment)
            
            # Prover creates response
            response = self.create_response(r, private_key, challenge)
            
            # Create proof object
            proof = Proof(
                commitment=commitment,
                challenge=challenge,
                response=response,
                rounds=rounds
            )
            
            # Verify proof
            proof.verified = self.verify_proof(public_key, proof)
            proofs.append(proof)
            
            if not proof.verified:
                return False, proofs
        
        return True, proofs
    
    def threshold_authentication(
        self, 
        shares: List[Tuple[int, int]], 
        threshold: int,
        public_key: int
    ) -> bool:
        """Threshold authentication using Shamir's secret sharing"""
        if len(shares) < threshold:
            return False
        
        # Simplified threshold verification
        # In production, use proper threshold cryptography
        successful_proofs = 0
        
        for private_share, share_index in shares[:threshold]:
            r, commitment = self.create_commitment(private_share)
            challenge = self.create_challenge(commitment)
            response = self.create_response(r, private_share, challenge)
            
            proof = Proof(
                commitment=commitment,
                challenge=challenge,
                response=response
            )
            
            # Modified verification for threshold
            # This is simplified - real implementation needs proper threshold crypto
            if self.verify_proof(public_key, proof):
                successful_proofs += 1
        
        return successful_proofs >= threshold
    
    def clear_used_challenges(self, older_than_seconds: int = 3600):
        """Clear old used challenges to prevent memory growth"""
        # In production, store these in a database with TTL
        current_size = len(self.used_challenges)
        if current_size > 10000:  # Arbitrary limit
            self.used_challenges.clear()


class NonInteractiveSchnorr(SchnorrProtocol):
    """Non-interactive Schnorr using Fiat-Shamir heuristic"""
    
    def create_non_interactive_proof(self, private_key: int, public_key: int, message: str) -> Dict[str, Any]:
        """Create non-interactive proof using Fiat-Shamir transform"""
        # Generate random r
        r = self.generate_random(self.params.n - 1)
        
        # Compute commitment: t = g^r mod p
        t = self.modular_exp(self.params.g, r, self.params.p)
        
        # Create challenge using hash (Fiat-Shamir)
        # c = H(g || y || t || m)
        challenge_input = f"{self.params.g}|{public_key}|{t}|{message}"
        c = int(hashlib.sha256(challenge_input.encode()).hexdigest(), 16) % self.params.n
        
        # Compute response: s = r + c * private_key mod n
        s = (r + c * private_key) % self.params.n
        
        return {
            "commitment": hex(t),
            "challenge": hex(c),
            "response": hex(s),
            "message": message,
            "public_key": hex(public_key)
        }
    
    def verify_non_interactive_proof(self, proof: Dict[str, Any]) -> bool:
        """Verify non-interactive proof"""
        try:
            t = int(proof["commitment"], 16)
            c = int(proof["challenge"], 16)
            s = int(proof["response"], 16)
            y = int(proof["public_key"], 16)
            message = proof["message"]
            
            # Recompute challenge
            challenge_input = f"{self.params.g}|{y}|{t}|{message}"
            expected_c = int(hashlib.sha256(challenge_input.encode()).hexdigest(), 16) % self.params.n
            
            if c != expected_c:
                return False
            
            # Verify equation: g^s = t * y^c (mod p)
            left_side = self.modular_exp(self.params.g, s, self.params.p)
            y_c = self.modular_exp(y, c, self.params.p)
            right_side = (t * y_c) % self.params.p
            
            return left_side == right_side
            
        except Exception:
            return False