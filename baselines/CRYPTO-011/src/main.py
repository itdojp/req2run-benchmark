"""Main API for Homomorphic Encryption System"""
import asyncio
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import structlog
import numpy as np

from paillier_he import (
    PaillierCryptosystem, PartiallyHomomorphicOperations,
    NoiseManager, CKKSApproximateScheme
)
from fhe_operations import (
    SimplifiedBFV, FHEParameters, BatchedOperations,
    ComparisonCircuit, PrivateInformationRetrieval
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

# Global instances
paillier_system: Optional[PaillierCryptosystem] = None
phe_ops: Optional[PartiallyHomomorphicOperations] = None
fhe_system: Optional[SimplifiedBFV] = None
batch_ops: Optional[BatchedOperations] = None
noise_manager: Optional[NoiseManager] = None
ckks_scheme: Optional[CKKSApproximateScheme] = None
pir_system: Optional[PrivateInformationRetrieval] = None

# Storage for keys and ciphertexts
stored_keys: Dict[str, Any] = {}
stored_ciphertexts: Dict[str, Any] = {}


# Pydantic models
class KeyGenerationRequest(BaseModel):
    scheme: str = Field(default="paillier", pattern="^(paillier|bfv|ckks)$")
    key_size: int = Field(default=2048, ge=1024, le=4096)
    user_id: str = Field(..., min_length=1, max_length=100)


class KeyGenerationResponse(BaseModel):
    user_id: str
    scheme: str
    public_key_id: str
    key_size: int
    created_at: float


class EncryptRequest(BaseModel):
    plaintext: Any  # int, float, or list
    user_id: str
    scheme: str = Field(default="paillier")


class EncryptResponse(BaseModel):
    ciphertext_id: str
    scheme: str
    size_bytes: int


class HomomorphicOperationRequest(BaseModel):
    operation: str = Field(..., pattern="^(add|multiply|scalar_multiply|sum|dot_product)$")
    operand1_id: str
    operand2_id: Optional[str] = None
    scalar: Optional[float] = None
    vector: Optional[List[float]] = None


class HomomorphicOperationResponse(BaseModel):
    result_id: str
    operation: str
    noise_level: Optional[int] = None
    needs_bootstrapping: bool = False


class DecryptRequest(BaseModel):
    ciphertext_id: str
    user_id: str


class DecryptResponse(BaseModel):
    plaintext: Any
    scheme: str


class BatchOperationRequest(BaseModel):
    operation: str = Field(..., pattern="^(encrypt|add|multiply|sum)$")
    plaintexts: Optional[List[int]] = None
    ciphertext_ids: Optional[List[str]] = None
    user_id: str


class BatchOperationResponse(BaseModel):
    result_ids: List[str]
    operation: str
    count: int


class BootstrapRequest(BaseModel):
    ciphertext_id: str
    force: bool = False


class BootstrapResponse(BaseModel):
    new_ciphertext_id: str
    noise_before: int
    noise_after: int


class PIRQueryRequest(BaseModel):
    database_id: str
    index: int
    user_id: str


class PIRQueryResponse(BaseModel):
    result_id: str
    encrypted: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global paillier_system, phe_ops, fhe_system, batch_ops, noise_manager, ckks_scheme, pir_system
    
    # Startup
    logger.info("Starting Homomorphic Encryption System")
    
    # Initialize systems
    paillier_system = PaillierCryptosystem()
    phe_ops = PartiallyHomomorphicOperations(paillier_system)
    
    fhe_params = FHEParameters()
    fhe_system = SimplifiedBFV(fhe_params)
    batch_ops = BatchedOperations(fhe_system)
    
    noise_manager = NoiseManager()
    ckks_scheme = CKKSApproximateScheme()
    pir_system = PrivateInformationRetrieval(fhe_system)
    
    # Generate default keys
    logger.info("Generating default keys...")
    paillier_system.generate_keypair()
    fhe_system.generate_keypair()
    ckks_scheme.paillier.generate_keypair()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Homomorphic Encryption System")


# Create FastAPI app
app = FastAPI(
    title="Homomorphic Encryption System",
    description="Privacy-preserving computation with homomorphic encryption",
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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "schemes": {
            "paillier": paillier_system is not None,
            "bfv": fhe_system is not None,
            "ckks": ckks_scheme is not None
        }
    }


@app.post("/api/v1/keys/generate", response_model=KeyGenerationResponse)
async def generate_keys(request: KeyGenerationRequest):
    """Generate homomorphic encryption keys"""
    try:
        start_time = time.time()
        
        if request.scheme == "paillier":
            system = PaillierCryptosystem(request.key_size)
            public_key, private_key = system.generate_keypair()
            
            # Store keys
            key_id = f"{request.user_id}_{request.scheme}_{int(time.time())}"
            stored_keys[key_id] = {
                "public_key": public_key,
                "private_key": private_key,
                "scheme": request.scheme,
                "system": system
            }
            
        elif request.scheme == "bfv":
            params = FHEParameters(dimension=min(4096, request.key_size))
            system = SimplifiedBFV(params)
            public_key, private_key, eval_key = system.generate_keypair()
            
            key_id = f"{request.user_id}_{request.scheme}_{int(time.time())}"
            stored_keys[key_id] = {
                "public_key": public_key,
                "private_key": private_key,
                "eval_key": eval_key,
                "scheme": request.scheme,
                "system": system
            }
            
        else:  # ckks
            system = CKKSApproximateScheme()
            system.paillier.generate_keypair()
            
            key_id = f"{request.user_id}_{request.scheme}_{int(time.time())}"
            stored_keys[key_id] = {
                "scheme": request.scheme,
                "system": system
            }
        
        generation_time = time.time() - start_time
        logger.info(f"Keys generated", scheme=request.scheme, time=generation_time)
        
        return KeyGenerationResponse(
            user_id=request.user_id,
            scheme=request.scheme,
            public_key_id=key_id,
            key_size=request.key_size,
            created_at=time.time()
        )
        
    except Exception as e:
        logger.error(f"Key generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/encrypt", response_model=EncryptResponse)
async def encrypt(request: EncryptRequest):
    """Encrypt plaintext"""
    try:
        # Find user's keys
        key_id = None
        for kid, key_data in stored_keys.items():
            if request.user_id in kid and request.scheme in kid:
                key_id = kid
                break
        
        if not key_id:
            raise HTTPException(status_code=404, detail="Keys not found for user")
        
        key_data = stored_keys[key_id]
        ciphertext_id = f"ct_{request.user_id}_{int(time.time()*1000)}"
        
        if request.scheme == "paillier":
            system = key_data["system"]
            
            if isinstance(request.plaintext, list):
                ciphertexts = system.batch_encrypt(request.plaintext)
                stored_ciphertexts[ciphertext_id] = {
                    "ciphertexts": ciphertexts,
                    "scheme": request.scheme,
                    "batch": True
                }
            else:
                ciphertext = system.encrypt(int(request.plaintext))
                stored_ciphertexts[ciphertext_id] = {
                    "ciphertext": ciphertext,
                    "scheme": request.scheme,
                    "batch": False
                }
                
        elif request.scheme == "bfv":
            system = key_data["system"]
            
            if isinstance(request.plaintext, list):
                ciphertexts = [system.encrypt(int(p)) for p in request.plaintext]
                stored_ciphertexts[ciphertext_id] = {
                    "ciphertexts": ciphertexts,
                    "scheme": request.scheme,
                    "batch": True
                }
            else:
                ciphertext = system.encrypt(int(request.plaintext))
                stored_ciphertexts[ciphertext_id] = {
                    "ciphertext": ciphertext,
                    "scheme": request.scheme,
                    "batch": False
                }
                
        else:  # ckks
            system = key_data["system"]
            
            if isinstance(request.plaintext, list):
                ciphertexts = [system.encrypt_float(float(p)) for p in request.plaintext]
                stored_ciphertexts[ciphertext_id] = {
                    "ciphertexts": ciphertexts,
                    "scheme": request.scheme,
                    "batch": True
                }
            else:
                ciphertext = system.encrypt_float(float(request.plaintext))
                stored_ciphertexts[ciphertext_id] = {
                    "ciphertext": ciphertext,
                    "scheme": request.scheme,
                    "batch": False
                }
        
        # Calculate size
        size_bytes = 256  # Simplified size calculation
        
        return EncryptResponse(
            ciphertext_id=ciphertext_id,
            scheme=request.scheme,
            size_bytes=size_bytes
        )
        
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/compute", response_model=HomomorphicOperationResponse)
async def homomorphic_compute(request: HomomorphicOperationRequest):
    """Perform homomorphic operation"""
    try:
        # Get operands
        if request.operand1_id not in stored_ciphertexts:
            raise HTTPException(status_code=404, detail="Operand 1 not found")
        
        ct1_data = stored_ciphertexts[request.operand1_id]
        scheme = ct1_data["scheme"]
        
        # Find appropriate system
        system = None
        for key_data in stored_keys.values():
            if key_data["scheme"] == scheme:
                system = key_data["system"]
                break
        
        if not system:
            raise HTTPException(status_code=404, detail="System not found")
        
        result_id = f"result_{int(time.time()*1000)}"
        
        # Perform operation
        if request.operation == "add":
            if request.operand2_id not in stored_ciphertexts:
                raise HTTPException(status_code=404, detail="Operand 2 not found")
            
            ct2_data = stored_ciphertexts[request.operand2_id]
            
            if scheme == "paillier":
                result = system.add(ct1_data["ciphertext"], ct2_data["ciphertext"])
            elif scheme == "bfv":
                result = system.add(ct1_data["ciphertext"], ct2_data["ciphertext"])
            else:  # ckks
                result = system.add_floats(ct1_data["ciphertext"], ct2_data["ciphertext"])
            
            stored_ciphertexts[result_id] = {
                "ciphertext": result,
                "scheme": scheme,
                "batch": False
            }
            
        elif request.operation == "multiply":
            if scheme == "paillier":
                raise HTTPException(status_code=400, detail="Paillier doesn't support multiplication")
            
            if request.operand2_id:
                ct2_data = stored_ciphertexts[request.operand2_id]
                result = system.multiply(ct1_data["ciphertext"], ct2_data["ciphertext"])
            else:
                raise HTTPException(status_code=400, detail="Second operand required")
            
            stored_ciphertexts[result_id] = {
                "ciphertext": result,
                "scheme": scheme,
                "batch": False
            }
            
        elif request.operation == "scalar_multiply":
            if not request.scalar:
                raise HTTPException(status_code=400, detail="Scalar value required")
            
            if scheme == "paillier":
                result = system.multiply_by_scalar(ct1_data["ciphertext"], int(request.scalar))
            elif scheme == "ckks":
                result = system.multiply_by_float(ct1_data["ciphertext"], request.scalar)
            else:
                raise HTTPException(status_code=400, detail="Operation not supported for scheme")
            
            stored_ciphertexts[result_id] = {
                "ciphertext": result,
                "scheme": scheme,
                "batch": False
            }
        
        # Check noise level
        noise_level = noise_manager.get_remaining_budget() if noise_manager else 100
        needs_bootstrap = noise_manager.needs_bootstrapping() if noise_manager else False
        
        return HomomorphicOperationResponse(
            result_id=result_id,
            operation=request.operation,
            noise_level=noise_level,
            needs_bootstrapping=needs_bootstrap
        )
        
    except Exception as e:
        logger.error(f"Computation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/decrypt", response_model=DecryptResponse)
async def decrypt(request: DecryptRequest):
    """Decrypt ciphertext"""
    try:
        if request.ciphertext_id not in stored_ciphertexts:
            raise HTTPException(status_code=404, detail="Ciphertext not found")
        
        ct_data = stored_ciphertexts[request.ciphertext_id]
        scheme = ct_data["scheme"]
        
        # Find user's keys
        key_data = None
        for kid, kdata in stored_keys.items():
            if request.user_id in kid and scheme in kid:
                key_data = kdata
                break
        
        if not key_data:
            raise HTTPException(status_code=404, detail="Keys not found")
        
        system = key_data["system"]
        
        if ct_data.get("batch"):
            # Batch decryption
            if scheme == "paillier":
                plaintexts = system.batch_decrypt(ct_data["ciphertexts"])
            elif scheme == "bfv":
                plaintexts = [system.decrypt(ct) for ct in ct_data["ciphertexts"]]
            else:  # ckks
                plaintexts = [system.decrypt_float(ct) for ct in ct_data["ciphertexts"]]
            
            return DecryptResponse(plaintext=plaintexts, scheme=scheme)
        else:
            # Single decryption
            if scheme == "paillier":
                plaintext = system.decrypt(ct_data["ciphertext"])
            elif scheme == "bfv":
                plaintext = system.decrypt(ct_data["ciphertext"])
            else:  # ckks
                plaintext = system.decrypt_float(ct_data["ciphertext"])
            
            return DecryptResponse(plaintext=plaintext, scheme=scheme)
        
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/batch", response_model=BatchOperationResponse)
async def batch_operation(request: BatchOperationRequest):
    """Perform batch operations"""
    try:
        # Find user's keys
        key_data = None
        for kid, kdata in stored_keys.items():
            if request.user_id in kid:
                key_data = kdata
                break
        
        if not key_data:
            raise HTTPException(status_code=404, detail="Keys not found")
        
        system = key_data["system"]
        scheme = key_data["scheme"]
        
        if request.operation == "encrypt":
            if not request.plaintexts:
                raise HTTPException(status_code=400, detail="Plaintexts required")
            
            if scheme == "bfv":
                ciphertexts = batch_ops.batch_encrypt(request.plaintexts)
            else:
                ciphertexts = [system.encrypt(p) for p in request.plaintexts]
            
            result_ids = []
            for i, ct in enumerate(ciphertexts):
                ct_id = f"batch_{request.user_id}_{int(time.time()*1000)}_{i}"
                stored_ciphertexts[ct_id] = {
                    "ciphertext": ct,
                    "scheme": scheme,
                    "batch": False
                }
                result_ids.append(ct_id)
            
            return BatchOperationResponse(
                result_ids=result_ids,
                operation=request.operation,
                count=len(result_ids)
            )
        
        else:
            raise HTTPException(status_code=400, detail="Operation not supported")
        
    except Exception as e:
        logger.error(f"Batch operation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/bootstrap", response_model=BootstrapResponse)
async def bootstrap(request: BootstrapRequest):
    """Bootstrap ciphertext to refresh noise"""
    try:
        if request.ciphertext_id not in stored_ciphertexts:
            raise HTTPException(status_code=404, detail="Ciphertext not found")
        
        ct_data = stored_ciphertexts[request.ciphertext_id]
        
        if ct_data["scheme"] != "bfv":
            raise HTTPException(status_code=400, detail="Bootstrapping only for FHE schemes")
        
        # Get noise level before
        noise_before = noise_manager.current_noise if noise_manager else 50
        
        # Bootstrap
        old_ct = ct_data["ciphertext"]
        new_ct = fhe_system.bootstrap(old_ct)
        
        # Store new ciphertext
        new_id = f"bootstrapped_{int(time.time()*1000)}"
        stored_ciphertexts[new_id] = {
            "ciphertext": new_ct,
            "scheme": "bfv",
            "batch": False
        }
        
        # Reset noise
        if noise_manager:
            noise_manager.reset_noise()
        noise_after = noise_manager.current_noise if noise_manager else 10
        
        return BootstrapResponse(
            new_ciphertext_id=new_id,
            noise_before=noise_before,
            noise_after=noise_after
        )
        
    except Exception as e:
        logger.error(f"Bootstrap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pir/setup")
async def setup_pir_database(data: List[int]):
    """Setup PIR database"""
    try:
        pir_system.setup_database(data)
        
        db_id = f"pir_db_{int(time.time())}"
        stored_ciphertexts[db_id] = {
            "database": pir_system.database,
            "size": len(data),
            "type": "pir"
        }
        
        return {"database_id": db_id, "size": len(data)}
        
    except Exception as e:
        logger.error(f"PIR setup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pir/query", response_model=PIRQueryResponse)
async def pir_query(request: PIRQueryRequest):
    """Query PIR database"""
    try:
        if request.database_id not in stored_ciphertexts:
            raise HTTPException(status_code=404, detail="Database not found")
        
        db_data = stored_ciphertexts[request.database_id]
        
        if db_data.get("type") != "pir":
            raise HTTPException(status_code=400, detail="Not a PIR database")
        
        # Perform private query
        result = pir_system.private_query(request.index)
        
        # Store result
        result_id = f"pir_result_{int(time.time()*1000)}"
        stored_ciphertexts[result_id] = {
            "ciphertext": result,
            "scheme": "bfv",
            "batch": False
        }
        
        return PIRQueryResponse(
            result_id=result_id,
            encrypted=True
        )
        
    except Exception as e:
        logger.error(f"PIR query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )