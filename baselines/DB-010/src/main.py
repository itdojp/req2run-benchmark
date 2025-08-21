"""
DB-010: Two-Phase Money Transfer with SERIALIZABLE Isolation
Main application entry point
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, List
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from .models import (
    Account,
    TransferRequest,
    TransferResponse,
    TransactionStatus,
    AccountBalance,
    AuditLog
)
from .database import Database
from .transaction_manager import TransactionManager
from .idempotency import IdempotencyManager
from .config import Settings
from .monitoring import (
    transaction_counter,
    transaction_latency,
    failed_transactions,
    balance_gauge
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

# Initialize components
db = Database(settings)
transaction_manager = TransactionManager(db, settings)
idempotency_manager = IdempotencyManager(db, settings)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Financial Transaction System")
    await db.initialize()
    await db.run_migrations()
    yield
    # Shutdown
    logger.info("Shutting down Financial Transaction System")
    await db.close()

# Create FastAPI app
app = FastAPI(
    title="Financial Transaction System",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        await db.health_check()
        return {
            "status": "healthy",
            "service": "transaction-system",
            "version": "1.0.0"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/accounts", response_model=Account)
async def create_account(
    initial_balance: float = 0.0,
    currency: str = "USD"
):
    """Create a new account"""
    try:
        account = await transaction_manager.create_account(
            initial_balance=initial_balance,
            currency=currency
        )
        
        # Update metrics
        balance_gauge.labels(account_id=str(account.id)).set(initial_balance)
        
        return account
    except Exception as e:
        logger.error(f"Failed to create account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/accounts/{account_id}", response_model=Account)
async def get_account(account_id: UUID):
    """Get account details"""
    try:
        account = await transaction_manager.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        return account
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/accounts/{account_id}/balance", response_model=AccountBalance)
async def get_balance(account_id: UUID):
    """Get account balance"""
    try:
        balance = await transaction_manager.get_balance(account_id)
        if balance is None:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return AccountBalance(
            account_id=account_id,
            balance=balance,
            currency="USD"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transfers", response_model=TransferResponse)
async def transfer_money(
    request: TransferRequest,
    background_tasks: BackgroundTasks
):
    """Execute a money transfer between accounts"""
    # Start transaction timer
    with transaction_latency.time():
        try:
            # Check idempotency
            existing_result = await idempotency_manager.get_result(
                request.idempotency_key
            )
            if existing_result:
                logger.info(f"Returning cached result for idempotency key: {request.idempotency_key}")
                return existing_result
            
            # Execute transfer with two-phase commit
            result = await transaction_manager.transfer_money(
                from_account_id=request.from_account_id,
                to_account_id=request.to_account_id,
                amount=request.amount,
                idempotency_key=request.idempotency_key
            )
            
            # Store idempotency result
            await idempotency_manager.store_result(
                request.idempotency_key,
                result
            )
            
            # Update metrics
            transaction_counter.labels(
                status="success",
                type="transfer"
            ).inc()
            
            # Schedule balance update in background
            background_tasks.add_task(
                update_balance_metrics,
                request.from_account_id,
                request.to_account_id
            )
            
            return result
            
        except ValueError as e:
            # Business logic errors (insufficient funds, etc.)
            failed_transactions.labels(reason="validation_error").inc()
            logger.warning(f"Transfer validation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            
        except asyncio.TimeoutError:
            # Transaction timeout
            failed_transactions.labels(reason="timeout").inc()
            logger.error(f"Transfer timeout for idempotency key: {request.idempotency_key}")
            raise HTTPException(status_code=504, detail="Transaction timeout")
            
        except Exception as e:
            # Unexpected errors
            failed_transactions.labels(reason="internal_error").inc()
            logger.error(f"Transfer failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/transfers/{transaction_id}/status", response_model=TransactionStatus)
async def get_transaction_status(transaction_id: UUID):
    """Get transaction status"""
    try:
        status = await transaction_manager.get_transaction_status(transaction_id)
        if not status:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transaction status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    account_id: Optional[UUID] = None,
    transaction_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get audit logs"""
    try:
        logs = await transaction_manager.get_audit_logs(
            account_id=account_id,
            transaction_id=transaction_id,
            limit=limit,
            offset=offset
        )
        return logs
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/reset")
async def reset_database():
    """Reset database (admin endpoint for testing)"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Forbidden in production")
    
    try:
        await db.reset()
        await db.run_migrations()
        return {"status": "success", "message": "Database reset completed"}
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def update_balance_metrics(from_account_id: UUID, to_account_id: UUID):
    """Update balance metrics in background"""
    try:
        from_balance = await transaction_manager.get_balance(from_account_id)
        to_balance = await transaction_manager.get_balance(to_account_id)
        
        if from_balance is not None:
            balance_gauge.labels(account_id=str(from_account_id)).set(from_balance)
        if to_balance is not None:
            balance_gauge.labels(account_id=str(to_account_id)).set(to_balance)
    except Exception as e:
        logger.error(f"Failed to update balance metrics: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )