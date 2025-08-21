"""Commitment schemes for zero-knowledge proofs"""
import hashlib
import secrets
from typing import Any, List, Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class CommitmentParams:
    """Parameters for commitment schemes"""
    modulus: int = 2**256 - 189  # Large prime
    generator_g: int = 3
    generator_h: int = 5
    hash_function: str = "sha256"


class PedersenCommitment:
    """Pedersen commitment scheme"""
    
    def __init__(self, params: Optional[CommitmentParams] = None):
        self.params = params or CommitmentParams()
        self.commitments: Dict[str, Tuple[int, int]] = {}
        
    def generate_blinding(self) -> int:
        """Generate random blinding factor"""
        return secrets.randbelow(self.params.modulus - 1) + 1
    
    def commit(self, value: int, blinding: Optional[int] = None) -> int:
        """Create Pedersen commitment C = g^m * h^r mod p"""
        if blinding is None:
            blinding = self.generate_blinding()
        
        g_m = pow(self.params.generator_g, value, self.params.modulus)
        h_r = pow(self.params.generator_h, blinding, self.params.modulus)
        
        commitment = (g_m * h_r) % self.params.modulus
        
        # Store for opening later
        commitment_id = hex(commitment)
        self.commitments[commitment_id] = (value, blinding)
        
        return commitment
    
    def open(self, commitment: int) -> Optional[Tuple[int, int]]:
        """Open commitment to reveal value and blinding factor"""
        commitment_id = hex(commitment)
        return self.commitments.get(commitment_id)
    
    def verify(self, commitment: int, value: int, blinding: int) -> bool:
        """Verify that commitment opens to given value and blinding"""
        expected = self.commit(value, blinding)
        return commitment == expected
    
    def add_commitments(self, c1: int, c2: int) -> int:
        """Homomorphic addition: C(m1+m2, r1+r2) = C(m1,r1) * C(m2,r2)"""
        return (c1 * c2) % self.params.modulus
    
    def scalar_multiply(self, commitment: int, scalar: int) -> int:
        """Scalar multiplication: C(k*m, k*r) = C(m,r)^k"""
        return pow(commitment, scalar, self.params.modulus)


class HashCommitment:
    """Hash-based commitment scheme"""
    
    def __init__(self, hash_function: str = "sha256"):
        self.hash_function = hash_function
        self.commitments: Dict[str, Tuple[Any, str]] = {}
        
    def generate_nonce(self) -> str:
        """Generate random nonce"""
        return secrets.token_hex(32)
    
    def commit(self, value: Any, nonce: Optional[str] = None) -> str:
        """Create hash commitment H(value || nonce)"""
        if nonce is None:
            nonce = self.generate_nonce()
        
        # Serialize value
        if isinstance(value, (int, float)):
            value_str = str(value)
        elif isinstance(value, bytes):
            value_str = value.hex()
        else:
            value_str = str(value)
        
        # Compute hash
        hasher = hashlib.new(self.hash_function)
        hasher.update(value_str.encode())
        hasher.update(nonce.encode())
        
        commitment = hasher.hexdigest()
        
        # Store for opening
        self.commitments[commitment] = (value, nonce)
        
        return commitment
    
    def open(self, commitment: str) -> Optional[Tuple[Any, str]]:
        """Open commitment to reveal value and nonce"""
        return self.commitments.get(commitment)
    
    def verify(self, commitment: str, value: Any, nonce: str) -> bool:
        """Verify that commitment opens to given value and nonce"""
        expected = self.commit(value, nonce)
        return commitment == expected


class MerkleCommitment:
    """Merkle tree commitment scheme"""
    
    def __init__(self, hash_function: str = "sha256"):
        self.hash_function = hash_function
        self.tree: List[List[str]] = []
        self.leaves: List[Any] = []
        
    def hash_leaf(self, value: Any) -> str:
        """Hash a leaf value"""
        hasher = hashlib.new(self.hash_function)
        
        if isinstance(value, (int, float)):
            hasher.update(str(value).encode())
        elif isinstance(value, bytes):
            hasher.update(value)
        else:
            hasher.update(str(value).encode())
        
        return hasher.hexdigest()
    
    def hash_nodes(self, left: str, right: str) -> str:
        """Hash two nodes together"""
        hasher = hashlib.new(self.hash_function)
        hasher.update(left.encode())
        hasher.update(right.encode())
        return hasher.hexdigest()
    
    def create_tree(self, values: List[Any]) -> str:
        """Create Merkle tree and return root"""
        if not values:
            return ""
        
        self.leaves = values
        
        # Hash all leaves
        current_level = [self.hash_leaf(v) for v in values]
        self.tree = [current_level]
        
        # Build tree levels
        while len(current_level) > 1:
            next_level = []
            
            # Pair up nodes
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    # Hash pair
                    node_hash = self.hash_nodes(current_level[i], current_level[i + 1])
                else:
                    # Odd number of nodes, promote last one
                    node_hash = current_level[i]
                
                next_level.append(node_hash)
            
            self.tree.append(next_level)
            current_level = next_level
        
        return current_level[0] if current_level else ""
    
    def get_proof(self, index: int) -> List[Tuple[str, bool]]:
        """Get Merkle proof for leaf at index"""
        if index < 0 or index >= len(self.leaves):
            raise ValueError("Index out of range")
        
        proof = []
        current_index = index
        
        for level in range(len(self.tree) - 1):
            level_nodes = self.tree[level]
            
            # Determine sibling
            if current_index % 2 == 0:
                # Current is left, sibling is right
                sibling_index = current_index + 1
                is_left = False
            else:
                # Current is right, sibling is left
                sibling_index = current_index - 1
                is_left = True
            
            # Add sibling to proof if it exists
            if sibling_index < len(level_nodes):
                proof.append((level_nodes[sibling_index], is_left))
            
            # Move to parent index
            current_index //= 2
        
        return proof
    
    def verify_proof(
        self,
        leaf_value: Any,
        proof: List[Tuple[str, bool]],
        root: str
    ) -> bool:
        """Verify Merkle proof"""
        # Start with leaf hash
        current_hash = self.hash_leaf(leaf_value)
        
        # Apply proof
        for sibling_hash, is_sibling_left in proof:
            if is_sibling_left:
                current_hash = self.hash_nodes(sibling_hash, current_hash)
            else:
                current_hash = self.hash_nodes(current_hash, sibling_hash)
        
        return current_hash == root


class VectorCommitment:
    """Vector commitment scheme (simplified)"""
    
    def __init__(self):
        self.pedersen = PedersenCommitment()
        self.commitments: Dict[str, Tuple[List[int], List[int]]] = {}
        
    def commit_vector(self, vector: List[int]) -> int:
        """Commit to a vector of values"""
        # Generate blinding factors for each element
        blindings = [self.pedersen.generate_blinding() for _ in vector]
        
        # Commit to each element
        element_commitments = [
            self.pedersen.commit(v, r)
            for v, r in zip(vector, blindings)
        ]
        
        # Combine commitments (simplified - in practice use more sophisticated method)
        combined = element_commitments[0]
        for c in element_commitments[1:]:
            combined = self.pedersen.add_commitments(combined, c)
        
        # Store for opening
        commitment_id = hex(combined)
        self.commitments[commitment_id] = (vector, blindings)
        
        return combined
    
    def open_at_index(self, commitment: int, index: int) -> Optional[Tuple[int, int]]:
        """Open commitment at specific index"""
        commitment_id = hex(commitment)
        
        if commitment_id not in self.commitments:
            return None
        
        vector, blindings = self.commitments[commitment_id]
        
        if index < 0 or index >= len(vector):
            return None
        
        return vector[index], blindings[index]
    
    def update_at_index(
        self,
        commitment: int,
        index: int,
        old_value: int,
        new_value: int,
        old_blinding: int,
        new_blinding: int
    ) -> int:
        """Update commitment at specific index"""
        # Remove old commitment
        old_element_commitment = self.pedersen.commit(old_value, old_blinding)
        inverse_old = pow(old_element_commitment, self.pedersen.params.modulus - 2, 
                         self.pedersen.params.modulus)
        
        # Add new commitment
        new_element_commitment = self.pedersen.commit(new_value, new_blinding)
        
        # Update combined commitment
        updated = (commitment * inverse_old * new_element_commitment) % self.pedersen.params.modulus
        
        return updated


class PolynomialCommitment:
    """Polynomial commitment scheme (simplified KZG-style)"""
    
    def __init__(self):
        self.params = CommitmentParams()
        self.commitments: Dict[str, List[int]] = {}
        
    def commit_polynomial(self, coefficients: List[int]) -> int:
        """Commit to polynomial with given coefficients"""
        # Simplified commitment: C = g^(a0) * g^(a1*tau) * ... * g^(an*tau^n)
        # where tau is from trusted setup (we use a fixed value for simplicity)
        tau = 12345  # In practice, from trusted setup
        
        commitment = 1
        tau_power = 1
        
        for coeff in coefficients:
            # g^(ai * tau^i)
            term = pow(self.params.generator_g, (coeff * tau_power) % self.params.modulus, 
                      self.params.modulus)
            commitment = (commitment * term) % self.params.modulus
            tau_power = (tau_power * tau) % self.params.modulus
        
        # Store coefficients
        commitment_id = hex(commitment)
        self.commitments[commitment_id] = coefficients
        
        return commitment
    
    def evaluate_polynomial(self, coefficients: List[int], x: int) -> int:
        """Evaluate polynomial at point x"""
        result = 0
        x_power = 1
        
        for coeff in coefficients:
            result = (result + coeff * x_power) % self.params.modulus
            x_power = (x_power * x) % self.params.modulus
        
        return result
    
    def create_opening_proof(self, commitment: int, x: int) -> Tuple[int, int]:
        """Create proof that polynomial evaluates to y at point x"""
        commitment_id = hex(commitment)
        
        if commitment_id not in self.commitments:
            raise ValueError("Commitment not found")
        
        coefficients = self.commitments[commitment_id]
        y = self.evaluate_polynomial(coefficients, x)
        
        # Simplified proof (in practice, use polynomial division)
        proof = hashlib.sha256(f"{commitment}|{x}|{y}".encode()).hexdigest()
        proof_value = int(proof, 16) % self.params.modulus
        
        return y, proof_value
    
    def verify_opening(self, commitment: int, x: int, y: int, proof: int) -> bool:
        """Verify polynomial opening proof"""
        # Simplified verification
        expected_proof = hashlib.sha256(f"{commitment}|{x}|{y}".encode()).hexdigest()
        expected_value = int(expected_proof, 16) % self.params.modulus
        
        return proof == expected_value