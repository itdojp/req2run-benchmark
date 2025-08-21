"""Transaction manager for two-phase commit with SERIALIZABLE isolation"""
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import asyncpg

from .database import Database, TransactionalConnection
from .models import (
    Account,
    TransferResponse,
    TransactionState,
    TransactionStatus,
    AuditLog
)
from .config import Settings

logger = logging.getLogger(__name__)


class TransactionManager:
    """Manages financial transactions with strong consistency guarantees"""
    
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings
    
    async def create_account(
        self,
        initial_balance: float = 0.0,
        currency: str = "USD"
    ) -> Account:
        """Create a new account"""
        account_id = uuid4()
        
        async with self.db.transaction():
            await self.db.execute("""
                INSERT INTO accounts (id, balance, currency, version)
                VALUES ($1, $2, $3, 0)
            """, account_id, Decimal(str(initial_balance)), currency)
            
            # Log account creation
            await self._log_audit(
                account_id=account_id,
                action="ACCOUNT_CREATED",
                balance_after=Decimal(str(initial_balance)),
                status="SUCCESS"
            )
        
        return Account(
            id=account_id,
            balance=Decimal(str(initial_balance)),
            currency=currency,
            version=0
        )
    
    async def get_account(self, account_id: UUID) -> Optional[Account]:
        """Get account details"""
        row = await self.db.fetchone("""
            SELECT id, balance, currency, created_at, updated_at, version
            FROM accounts
            WHERE id = $1
        """, account_id)
        
        if row:
            return Account(
                id=row['id'],
                balance=row['balance'],
                currency=row['currency'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                version=row['version']
            )
        return None
    
    async def get_balance(self, account_id: UUID) -> Optional[Decimal]:
        """Get account balance"""
        balance = await self.db.fetchone("""
            SELECT balance FROM accounts WHERE id = $1
        """, account_id)
        
        return balance['balance'] if balance else None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, max=1),
        retry=retry_if_exception_type(asyncpg.SerializationError)
    )
    async def transfer_money(
        self,
        from_account_id: UUID,
        to_account_id: UUID,
        amount: Decimal,
        idempotency_key: str
    ) -> TransferResponse:
        """Execute money transfer with two-phase commit and SERIALIZABLE isolation"""
        transaction_id = uuid4()
        start_time = datetime.utcnow()
        
        try:
            # Use SERIALIZABLE isolation for strongest consistency
            async with self.db.transaction(isolation_level="serializable") as conn:
                # Phase 1: Prepare
                prepared = await self._prepare_transfer(
                    conn,
                    transaction_id,
                    from_account_id,
                    to_account_id,
                    amount
                )
                
                if not prepared:
                    raise ValueError("Failed to prepare transfer")
                
                # Phase 2: Commit
                await self._commit_transfer(
                    conn,
                    transaction_id,
                    from_account_id,
                    to_account_id,
                    amount
                )
                
                # Record successful transaction
                completed_time = datetime.utcnow()
                await conn.execute("""
                    UPDATE transactions
                    SET status = $1, completed_at = $2, updated_at = $2
                    WHERE id = $3
                """, TransactionState.COMMITTED.value, completed_time, transaction_id)
                
                # Log successful transfer
                await self._log_audit_in_transaction(
                    conn,
                    transaction_id=transaction_id,
                    account_id=from_account_id,
                    action="TRANSFER_OUT",
                    amount=amount,
                    status="SUCCESS"
                )
                
                await self._log_audit_in_transaction(
                    conn,
                    transaction_id=transaction_id,
                    account_id=to_account_id,
                    action="TRANSFER_IN",
                    amount=amount,
                    status="SUCCESS"
                )
            
            return TransferResponse(
                transaction_id=transaction_id,
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                amount=amount,
                status=TransactionState.COMMITTED,
                created_at=start_time,
                completed_at=datetime.utcnow()
            )
            
        except asyncpg.SerializationError as e:
            # Serialization error - will be retried
            logger.warning(f"Serialization error for transaction {transaction_id}: {e}")
            await self._rollback_transfer(transaction_id, str(e))
            raise
            
        except ValueError as e:
            # Business logic error (insufficient funds, etc.)
            await self._rollback_transfer(transaction_id, str(e))
            raise
            
        except Exception as e:
            # Unexpected error
            logger.error(f"Transfer failed for transaction {transaction_id}: {e}")
            await self._rollback_transfer(transaction_id, str(e))
            raise
    
    async def _prepare_transfer(
        self,
        conn: asyncpg.Connection,
        transaction_id: UUID,
        from_account_id: UUID,
        to_account_id: UUID,
        amount: Decimal
    ) -> bool:
        """Phase 1: Prepare transfer (check constraints and lock accounts)"""
        # Create transaction record
        await conn.execute("""
            INSERT INTO transactions (
                id, from_account_id, to_account_id, amount, status, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """, transaction_id, from_account_id, to_account_id, amount,
            TransactionState.PENDING.value, datetime.utcnow())
        
        # Lock accounts in a consistent order to prevent deadlocks
        account_ids = sorted([from_account_id, to_account_id])
        
        # Get account balances with row-level locks (SELECT FOR UPDATE)
        accounts = {}
        for account_id in account_ids:
            row = await conn.fetchrow("""
                SELECT id, balance, version
                FROM accounts
                WHERE id = $1
                FOR UPDATE
            """, account_id)
            
            if not row:
                raise ValueError(f"Account {account_id} not found")
            
            accounts[account_id] = row
        
        # Check balance constraint
        from_balance = accounts[from_account_id]['balance']
        if from_balance < amount:
            raise ValueError(f"Insufficient funds: balance={from_balance}, amount={amount}")
        
        # Update status to PREPARED
        await conn.execute("""
            UPDATE transactions
            SET status = $1, updated_at = $2
            WHERE id = $3
        """, TransactionState.PREPARED.value, datetime.utcnow(), transaction_id)
        
        return True
    
    async def _commit_transfer(
        self,
        conn: asyncpg.Connection,
        transaction_id: UUID,
        from_account_id: UUID,
        to_account_id: UUID,
        amount: Decimal
    ):
        """Phase 2: Commit transfer (update balances)"""
        # Update sender balance with optimistic locking
        result = await conn.execute("""
            UPDATE accounts
            SET balance = balance - $1,
                version = version + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2 AND balance >= $1
        """, amount, from_account_id)
        
        if result.split()[-1] == '0':
            raise ValueError("Failed to debit sender account")
        
        # Update receiver balance
        await conn.execute("""
            UPDATE accounts
            SET balance = balance + $1,
                version = version + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, amount, to_account_id)
    
    async def _rollback_transfer(
        self,
        transaction_id: UUID,
        error_message: str
    ):
        """Rollback a failed transfer"""
        try:
            await self.db.execute("""
                UPDATE transactions
                SET status = $1, error_message = $2, updated_at = CURRENT_TIMESTAMP
                WHERE id = $3
            """, TransactionState.ROLLED_BACK.value, error_message, transaction_id)
            
            await self._log_audit(
                transaction_id=transaction_id,
                action="TRANSFER_ROLLBACK",
                status="ROLLED_BACK",
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"Failed to record rollback: {e}")
    
    async def get_transaction_status(
        self,
        transaction_id: UUID
    ) -> Optional[TransactionStatus]:
        """Get transaction status"""
        row = await self.db.fetchone("""
            SELECT id, status, from_account_id, to_account_id, amount,
                   created_at, updated_at, completed_at, error_message, retry_count
            FROM transactions
            WHERE id = $1
        """, transaction_id)
        
        if row:
            return TransactionStatus(
                transaction_id=row['id'],
                status=TransactionState(row['status']),
                from_account_id=row['from_account_id'],
                to_account_id=row['to_account_id'],
                amount=row['amount'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                completed_at=row['completed_at'],
                error_message=row['error_message'],
                retry_count=row['retry_count']
            )
        return None
    
    async def get_audit_logs(
        self,
        account_id: Optional[UUID] = None,
        transaction_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs with optional filtering"""
        query = """
            SELECT id, timestamp, transaction_id, account_id, action,
                   amount, balance_before, balance_after, status,
                   error_message, metadata
            FROM audit_logs
            WHERE 1=1
        """
        params = []
        param_count = 0
        
        if account_id:
            param_count += 1
            query += f" AND account_id = ${param_count}"
            params.append(account_id)
        
        if transaction_id:
            param_count += 1
            query += f" AND transaction_id = ${param_count}"
            params.append(transaction_id)
        
        query += f" ORDER BY timestamp DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])
        
        rows = await self.db.fetchall(query, *params)
        
        return [
            AuditLog(
                id=row['id'],
                timestamp=row['timestamp'],
                transaction_id=row['transaction_id'],
                account_id=row['account_id'],
                action=row['action'],
                amount=row['amount'],
                balance_before=row['balance_before'],
                balance_after=row['balance_after'],
                status=row['status'],
                error_message=row['error_message'],
                metadata=row['metadata'] or {}
            )
            for row in rows
        ]
    
    async def _log_audit(self, **kwargs):
        """Log audit entry"""
        await self.db.execute("""
            INSERT INTO audit_logs (
                id, timestamp, transaction_id, account_id, action,
                amount, balance_before, balance_after, status,
                error_message, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, uuid4(), datetime.utcnow(),
            kwargs.get('transaction_id'),
            kwargs.get('account_id'),
            kwargs.get('action'),
            kwargs.get('amount'),
            kwargs.get('balance_before'),
            kwargs.get('balance_after'),
            kwargs.get('status'),
            kwargs.get('error_message'),
            kwargs.get('metadata', {}))
    
    async def _log_audit_in_transaction(
        self,
        conn: asyncpg.Connection,
        **kwargs
    ):
        """Log audit entry within a transaction"""
        await conn.execute("""
            INSERT INTO audit_logs (
                id, timestamp, transaction_id, account_id, action,
                amount, balance_before, balance_after, status,
                error_message, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, uuid4(), datetime.utcnow(),
            kwargs.get('transaction_id'),
            kwargs.get('account_id'),
            kwargs.get('action'),
            kwargs.get('amount'),
            kwargs.get('balance_before'),
            kwargs.get('balance_after'),
            kwargs.get('status'),
            kwargs.get('error_message'),
            kwargs.get('metadata', {}))