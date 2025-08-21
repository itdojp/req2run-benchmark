"""Database connection and management"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Any, Dict, List
from pathlib import Path

import asyncpg
from asyncpg import Connection, Pool
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_SERIALIZABLE

from .config import Settings

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager with connection pooling"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pool: Optional[Pool] = None
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.settings.database_url,
                min_size=self.settings.pool_min_size,
                max_size=self.settings.pool_max_size,
                command_timeout=self.settings.query_timeout,
                server_settings={
                    'jit': 'off'  # Disable JIT for consistent performance
                }
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a database connection from pool"""
        async with self.pool.acquire() as connection:
            yield connection
    
    @asynccontextmanager
    async def transaction(self, isolation_level: str = "serializable"):
        """Start a database transaction with specified isolation level"""
        async with self.pool.acquire() as connection:
            async with connection.transaction(isolation=isolation_level):
                yield connection
    
    async def execute(self, query: str, *args, timeout: Optional[float] = None):
        """Execute a query without returning results"""
        async with self.acquire() as connection:
            return await connection.execute(query, *args, timeout=timeout)
    
    async def fetchone(self, query: str, *args, timeout: Optional[float] = None):
        """Execute a query and fetch one result"""
        async with self.acquire() as connection:
            return await connection.fetchrow(query, *args, timeout=timeout)
    
    async def fetchall(self, query: str, *args, timeout: Optional[float] = None):
        """Execute a query and fetch all results"""
        async with self.acquire() as connection:
            return await connection.fetch(query, *args, timeout=timeout)
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.acquire() as connection:
                result = await connection.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def run_migrations(self):
        """Run database migrations"""
        migrations_path = Path("migrations")
        
        # Create migrations table if not exists
        await self.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Get applied migrations
        applied = await self.fetchall("SELECT version FROM schema_migrations")
        applied_versions = {row['version'] for row in applied}
        
        # Run pending migrations
        if migrations_path.exists():
            for migration_file in sorted(migrations_path.glob("*.sql")):
                version = int(migration_file.stem.split("_")[0])
                
                if version not in applied_versions:
                    logger.info(f"Running migration {migration_file.name}")
                    
                    with open(migration_file, 'r') as f:
                        migration_sql = f.read()
                    
                    async with self.transaction():
                        await self.execute(migration_sql)
                        await self.execute(
                            "INSERT INTO schema_migrations (version) VALUES ($1)",
                            version
                        )
                    
                    logger.info(f"Migration {migration_file.name} completed")
    
    async def reset(self):
        """Reset database (for testing only)"""
        if not self.settings.debug:
            raise RuntimeError("Database reset is only allowed in debug mode")
        
        # Drop all tables
        await self.execute("""
            DROP TABLE IF EXISTS audit_logs CASCADE;
            DROP TABLE IF EXISTS transactions CASCADE;
            DROP TABLE IF EXISTS accounts CASCADE;
            DROP TABLE IF EXISTS idempotency_records CASCADE;
            DROP TABLE IF EXISTS schema_migrations CASCADE;
        """)
        
        logger.warning("Database reset completed")


class TransactionalConnection:
    """Wrapper for transactional database operations"""
    
    def __init__(self, connection: Connection):
        self.connection = connection
        self.savepoint_counter = 0
    
    async def execute(self, query: str, *args):
        """Execute query within transaction"""
        return await self.connection.execute(query, *args)
    
    async def fetchone(self, query: str, *args):
        """Fetch one row within transaction"""
        return await self.connection.fetchrow(query, *args)
    
    async def fetchall(self, query: str, *args):
        """Fetch all rows within transaction"""
        return await self.connection.fetch(query, *args)
    
    async def savepoint(self, name: Optional[str] = None) -> str:
        """Create a savepoint"""
        if name is None:
            self.savepoint_counter += 1
            name = f"sp_{self.savepoint_counter}"
        
        await self.connection.execute(f"SAVEPOINT {name}")
        return name
    
    async def release_savepoint(self, name: str):
        """Release a savepoint"""
        await self.connection.execute(f"RELEASE SAVEPOINT {name}")
    
    async def rollback_to_savepoint(self, name: str):
        """Rollback to a savepoint"""
        await self.connection.execute(f"ROLLBACK TO SAVEPOINT {name}")