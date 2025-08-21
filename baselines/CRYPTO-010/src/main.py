"""Main API for Zero-Knowledge Proof Authentication System"""
import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import structlog
from decouple import config as env_config

from zkp_schnorr import (
    SchnorrProtocol, NonInteractiveSchnorr,
    Commitment, Challenge, Response as ZKResponse, Proof
)
from zkp_range_proof import (
    BulletproofSimplified, SigmaProtocolRange, AggregateRangeProof
)
from zkp_snark import SimplifiedSNARK
from commitment_schemes import (
    PedersenCommitment, HashCommitment, MerkleCommitment
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global protocol instances
schnorr_protocol: Optional[SchnorrProtocol] = None
non_interactive_schnorr: Optional[NonInteractiveSchnorr] = None
bulletproof: Optional[BulletproofSimplified] = None
snark: Optional[SimplifiedSNARK] = None
commitment_manager: Optional[PedersenCommitment] = None

# Storage for keys and sessions
user_keys: Dict[str, Dict[str, Any]] = {}
active_sessions: Dict[str, Dict[str, Any]] = {}


# Pydantic models
class KeyGenerationRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    key_type: str = Field(default="schnorr", pattern="^(schnorr|ecdsa|rsa)$")


class KeyGenerationResponse(BaseModel):
    user_id: str
    public_key: str
    key_type: str
    created_at: float


class AuthenticationRequest(BaseModel):
    user_id: str
    rounds: int = Field(default=3, ge=1, le=10)
    challenge_type: str = Field(default="interactive", pattern="^(interactive|non-interactive)$")
    message: Optional[str] = None


class AuthenticationChallenge(BaseModel):
    session_id: str
    commitment: Dict[str, Any]
    challenge: Dict[str, Any]
    expires_at: float


class AuthenticationResponse(BaseModel):
    session_id: str
    response_value: str


class VerificationResult(BaseModel):
    verified: bool
    session_id: str
    rounds_completed: int
    proof_type: str
    verification_time_ms: float


class RangeProofRequest(BaseModel):
    value: int = Field(..., ge=0)
    min_value: int = Field(default=0, ge=0)
    max_value: int = Field(default=2**32-1, gt=0)
    proof_type: str = Field(default="bulletproof", pattern="^(bulletproof|sigma)$")


class RangeProofResponse(BaseModel):
    proof: Dict[str, Any]
    proof_type: str
    generation_time_ms: float


class SNARKRequest(BaseModel):
    statement: str
    witness: Dict[str, Any]
    circuit_type: str = Field(default="arithmetic", pattern="^(arithmetic|boolean)$")


class SNARKResponse(BaseModel):
    proof: Dict[str, Any]
    public_inputs: List[Any]
    verification_key: str
    generation_time_ms: float


class CommitmentRequest(BaseModel):
    value: Any
    commitment_type: str = Field(default="pedersen", pattern="^(pedersen|hash|merkle)$")
    blinding_factor: Optional[int] = None


class CommitmentResponse(BaseModel):
    commitment: str
    commitment_type: str
    timestamp: float


class ThresholdAuthRequest(BaseModel):
    user_id: str
    shares: List[Dict[str, int]]
    threshold: int = Field(..., ge=1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global schnorr_protocol, non_interactive_schnorr, bulletproof, snark, commitment_manager
    
    # Startup
    logger.info("Starting ZKP Authentication System")
    
    # Initialize protocols
    schnorr_protocol = SchnorrProtocol()
    non_interactive_schnorr = NonInteractiveSchnorr()
    bulletproof = BulletproofSimplified()
    snark = SimplifiedSNARK()
    commitment_manager = PedersenCommitment()
    
    # Start cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    logger.info("Shutting down ZKP Authentication System")
    
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title="Zero-Knowledge Proof Authentication System",
    description="Advanced ZKP authentication with Schnorr, range proofs, and SNARKs",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def periodic_cleanup():
    """Periodic cleanup of expired sessions and challenges"""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            
            current_time = time.time()
            
            # Clean expired sessions
            expired_sessions = [
                sid for sid, session in active_sessions.items()
                if session.get("expires_at", 0) < current_time
            ]
            
            for sid in expired_sessions:
                del active_sessions[sid]
            
            if expired_sessions:
                logger.info(f"Cleaned {len(expired_sessions)} expired sessions")
            
            # Clean old challenges
            schnorr_protocol.clear_used_challenges(older_than_seconds=3600)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "protocols": {
            "schnorr": schnorr_protocol is not None,
            "bulletproof": bulletproof is not None,
            "snark": snark is not None
        }
    }


@app.post("/api/v1/keys/generate", response_model=KeyGenerationResponse)
async def generate_keys(request: KeyGenerationRequest):
    """Generate cryptographic key pair for user"""
    try:
        if request.key_type == "schnorr":
            private_key, public_key = schnorr_protocol.generate_keypair()
            
            # Store keys (in production, store securely)
            user_keys[request.user_id] = {
                "private_key": private_key,
                "public_key": public_key,
                "key_type": request.key_type,
                "created_at": time.time()
            }
            
            return KeyGenerationResponse(
                user_id=request.user_id,
                public_key=hex(public_key),
                key_type=request.key_type,
                created_at=time.time()
            )
        else:
            raise HTTPException(status_code=501, detail=f"Key type {request.key_type} not implemented")
            
    except Exception as e:
        logger.error(f"Key generation error: {e}")
        raise HTTPException(status_code=500, detail="Key generation failed")


@app.post("/api/v1/auth/challenge", response_model=AuthenticationChallenge)
async def create_auth_challenge(request: AuthenticationRequest):
    """Create authentication challenge"""
    if request.user_id not in user_keys:
        raise HTTPException(status_code=404, detail="User keys not found")
    
    user_key_data = user_keys[request.user_id]
    session_id = f"session_{request.user_id}_{int(time.time()*1000)}"
    
    if request.challenge_type == "interactive":
        # Create Schnorr commitment
        r, commitment = schnorr_protocol.create_commitment(user_key_data["private_key"])
        
        # Create challenge
        challenge = schnorr_protocol.create_challenge(commitment)
        
        # Store session
        active_sessions[session_id] = {
            "user_id": request.user_id,
            "r": r,
            "commitment": commitment,
            "challenge": challenge,
            "rounds": request.rounds,
            "rounds_completed": 0,
            "expires_at": time.time() + 300  # 5 minutes
        }
        
        return AuthenticationChallenge(
            session_id=session_id,
            commitment=commitment.to_dict(),
            challenge=challenge.to_dict(),
            expires_at=active_sessions[session_id]["expires_at"]
        )
    else:
        # Non-interactive proof
        proof = non_interactive_schnorr.create_non_interactive_proof(
            user_key_data["private_key"],
            user_key_data["public_key"],
            request.message or f"auth_{request.user_id}"
        )
        
        active_sessions[session_id] = {
            "user_id": request.user_id,
            "proof": proof,
            "type": "non-interactive",
            "expires_at": time.time() + 300
        }
        
        return AuthenticationChallenge(
            session_id=session_id,
            commitment={"value": proof["commitment"]},
            challenge={"value": proof["challenge"]},
            expires_at=active_sessions[session_id]["expires_at"]
        )


@app.post("/api/v1/auth/respond")
async def submit_auth_response(request: AuthenticationResponse):
    """Submit authentication response"""
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    session = active_sessions[request.session_id]
    
    if time.time() > session["expires_at"]:
        del active_sessions[request.session_id]
        raise HTTPException(status_code=410, detail="Session expired")
    
    # Store response for verification
    session["response_value"] = request.response_value
    
    return {"status": "response_received", "session_id": request.session_id}


@app.post("/api/v1/auth/verify", response_model=VerificationResult)
async def verify_authentication(session_id: str):
    """Verify authentication proof"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    start_time = time.time()
    session = active_sessions[session_id]
    user_key_data = user_keys[session["user_id"]]
    
    if session.get("type") == "non-interactive":
        # Verify non-interactive proof
        verified = non_interactive_schnorr.verify_non_interactive_proof(session["proof"])
        
        return VerificationResult(
            verified=verified,
            session_id=session_id,
            rounds_completed=1,
            proof_type="non-interactive",
            verification_time_ms=(time.time() - start_time) * 1000
        )
    else:
        # Verify interactive proof
        response = ZKResponse(
            value=int(session.get("response_value", "0"), 16),
            challenge_hash=schnorr_protocol.hash_value(
                session["challenge"].value,
                session["challenge"].commitment_hash
            )
        )
        
        proof = Proof(
            commitment=session["commitment"],
            challenge=session["challenge"],
            response=response,
            rounds=session["rounds"]
        )
        
        verified = schnorr_protocol.verify_proof(user_key_data["public_key"], proof)
        
        if verified:
            session["rounds_completed"] += 1
        
        return VerificationResult(
            verified=verified,
            session_id=session_id,
            rounds_completed=session["rounds_completed"],
            proof_type="interactive",
            verification_time_ms=(time.time() - start_time) * 1000
        )


@app.post("/api/v1/range-proof/create", response_model=RangeProofResponse)
async def create_range_proof(request: RangeProofRequest):
    """Create range proof"""
    start_time = time.time()
    
    try:
        if request.proof_type == "bulletproof":
            proof = bulletproof.create_range_proof(
                request.value,
                request.min_value,
                request.max_value
            )
        else:
            sigma = SigmaProtocolRange()
            # Create digit proofs for base-4 decomposition
            digits = sigma.decompose_range(request.value - request.min_value, base=4)
            digit_proofs = []
            
            for digit in digits:
                digit_proof = sigma.create_digit_proof(digit, base=4)
                digit_proofs.append(digit_proof)
            
            proof = {
                "digit_proofs": digit_proofs,
                "value_offset": request.min_value,
                "base": 4
            }
        
        return RangeProofResponse(
            proof=proof,
            proof_type=request.proof_type,
            generation_time_ms=(time.time() - start_time) * 1000
        )
        
    except Exception as e:
        logger.error(f"Range proof creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/range-proof/verify")
async def verify_range_proof(proof: Dict[str, Any], proof_type: str = "bulletproof"):
    """Verify range proof"""
    try:
        if proof_type == "bulletproof":
            verified = bulletproof.verify_range_proof(proof)
        else:
            sigma = SigmaProtocolRange()
            # Verify all digit proofs
            verified = all(
                sigma.verify_digit_proof(digit_proof)
                for digit_proof in proof.get("digit_proofs", [])
            )
        
        return {"verified": verified, "proof_type": proof_type}
        
    except Exception as e:
        logger.error(f"Range proof verification error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/snark/create", response_model=SNARKResponse)
async def create_snark_proof(request: SNARKRequest):
    """Create SNARK proof"""
    start_time = time.time()
    
    try:
        # Parse statement and witness
        circuit = snark.create_circuit(
            request.statement,
            request.circuit_type == "arithmetic"
        )
        
        # Generate proof
        proof = snark.prove(circuit, request.witness)
        
        # Get public inputs
        public_inputs = snark.extract_public_inputs(circuit, request.witness)
        
        return SNARKResponse(
            proof=proof,
            public_inputs=public_inputs,
            verification_key=snark.get_verification_key(circuit),
            generation_time_ms=(time.time() - start_time) * 1000
        )
        
    except Exception as e:
        logger.error(f"SNARK creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/snark/verify")
async def verify_snark_proof(
    proof: Dict[str, Any],
    public_inputs: List[Any],
    verification_key: str
):
    """Verify SNARK proof"""
    try:
        verified = snark.verify(proof, public_inputs, verification_key)
        return {"verified": verified}
        
    except Exception as e:
        logger.error(f"SNARK verification error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/commitment/create", response_model=CommitmentResponse)
async def create_commitment(request: CommitmentRequest):
    """Create cryptographic commitment"""
    try:
        if request.commitment_type == "pedersen":
            blinding = request.blinding_factor or commitment_manager.generate_blinding()
            commitment = commitment_manager.commit(
                int(request.value) if isinstance(request.value, (int, str)) else hash(str(request.value)),
                blinding
            )
            commitment_value = hex(commitment)
        elif request.commitment_type == "hash":
            hash_commitment = HashCommitment()
            commitment_value = hash_commitment.commit(request.value)
        else:  # merkle
            merkle = MerkleCommitment()
            if isinstance(request.value, list):
                commitment_value = merkle.create_tree(request.value)
            else:
                commitment_value = merkle.create_tree([request.value])
        
        return CommitmentResponse(
            commitment=commitment_value,
            commitment_type=request.commitment_type,
            timestamp=time.time()
        )
        
    except Exception as e:
        logger.error(f"Commitment creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/auth/threshold")
async def threshold_authentication(request: ThresholdAuthRequest):
    """Perform threshold authentication"""
    if request.user_id not in user_keys:
        raise HTTPException(status_code=404, detail="User keys not found")
    
    user_key_data = user_keys[request.user_id]
    
    # Convert shares to proper format
    shares = [(s["share"], s["index"]) for s in request.shares]
    
    # Perform threshold authentication
    verified = schnorr_protocol.threshold_authentication(
        shares,
        request.threshold,
        user_key_data["public_key"]
    )
    
    return {
        "verified": verified,
        "threshold": request.threshold,
        "shares_provided": len(shares)
    }


@app.post("/api/v1/auth/multi-round")
async def multi_round_authentication(user_id: str, rounds: int = 3):
    """Perform multi-round authentication"""
    if user_id not in user_keys:
        raise HTTPException(status_code=404, detail="User keys not found")
    
    user_key_data = user_keys[user_id]
    
    # Perform multi-round proof
    success, proofs = schnorr_protocol.multi_round_proof(
        user_key_data["private_key"],
        user_key_data["public_key"],
        rounds
    )
    
    return {
        "success": success,
        "rounds": rounds,
        "proofs": [p.to_dict() for p in proofs]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )