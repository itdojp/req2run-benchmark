"""Idempotency manager for exactly-once processing"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Any
from uuid import UUID

from .database import Database
from .models import TransferResponse, IdempotencyRecord
from .config import Settings

logger = logging.getLogger(__name__)


class IdempotencyManager:
    """Manages idempotency keys for exactly-once processing"""
    
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings
        self.ttl_seconds = settings.idempotency_ttl_seconds
    
    async def get_result(
        self,
        idempotency_key: str
    ) -> Optional[TransferResponse]:
        """Get cached result for idempotency key"""
        row = await self.db.fetchone("""
            SELECT transaction_id, result, expires_at
            FROM idempotency_records
            WHERE idempotency_key = $1 AND expires_at > CURRENT_TIMESTAMP
        """, idempotency_key)
        
        if row:
            result_data = json.loads(row['result'])
            return TransferResponse(**result_data)
        
        return None
    
    async def store_result(
        self,
        idempotency_key: str,
        result: TransferResponse
    ):
        """Store result for idempotency key"""
        expires_at = datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
        result_json = result.json()
        
        try:
            await self.db.execute("""
                INSERT INTO idempotency_records (
                    idempotency_key, transaction_id, result, created_at, expires_at
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (idempotency_key) DO UPDATE
                SET result = $3, expires_at = $5
            """, idempotency_key, result.transaction_id, result_json,
                datetime.utcnow(), expires_at)
            
            logger.info(f"Stored idempotency result for key: {idempotency_key}")
        except Exception as e:
            logger.error(f"Failed to store idempotency result: {e}")
            # Don't fail the transaction if idempotency storage fails
    
    async def cleanup_expired(self):
        """Clean up expired idempotency records"""
        try:
            deleted = await self.db.execute("""
                DELETE FROM idempotency_records
                WHERE expires_at < CURRENT_TIMESTAMP
            """)
            
            count = int(deleted.split()[-1])
            if count > 0:
                logger.info(f"Cleaned up {count} expired idempotency records")
        except Exception as e:
            logger.error(f"Failed to cleanup idempotency records: {e}")