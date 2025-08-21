"""
Event Store Implementation

Handles event persistence, ordering, and replay capabilities.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import asyncpg
from redis import asyncio as aioredis
import hashlib


@dataclass
class Event:
    """Base event structure"""
    aggregate_id: str
    aggregate_type: str
    event_type: str
    event_version: int
    sequence_number: int
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    event_id: str = None
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class EventStore:
    """Event store for persisting and retrieving events"""
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[aioredis.Redis] = None
        self.event_handlers: Dict[str, List[callable]] = {}
        self.snapshots: Dict[str, Any] = {}
        self.snapshot_frequency = 100
        
    async def initialize(self, db_url: str, redis_url: str = None):
        """Initialize database connections"""
        # PostgreSQL for event storage
        self.db_pool = await asyncpg.create_pool(
            db_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        # Redis for caching and pub/sub
        if redis_url:
            self.redis = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        
        # Create event store table
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id UUID PRIMARY KEY,
                    aggregate_id VARCHAR(255) NOT NULL,
                    aggregate_type VARCHAR(100) NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    event_version INTEGER NOT NULL,
                    sequence_number BIGSERIAL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    data JSONB NOT NULL,
                    metadata JSONB,
                    checksum VARCHAR(64),
                    INDEX idx_aggregate (aggregate_id, sequence_number),
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_event_type (event_type)
                )
            """)
            
            # Create snapshots table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id UUID PRIMARY KEY,
                    aggregate_id VARCHAR(255) NOT NULL,
                    aggregate_type VARCHAR(100) NOT NULL,
                    sequence_number BIGINT NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    state JSONB NOT NULL,
                    INDEX idx_snapshot_aggregate (aggregate_id, sequence_number DESC)
                )
            """)
    
    async def append_event(self, event: Event) -> int:
        """Append event to store"""
        async with self.db_pool.acquire() as conn:
            # Start transaction
            async with conn.transaction():
                # Get next sequence number for aggregate
                sequence = await conn.fetchval("""
                    SELECT COALESCE(MAX(sequence_number), 0) + 1
                    FROM events
                    WHERE aggregate_id = $1
                """, event.aggregate_id)
                
                event.sequence_number = sequence
                
                # Calculate checksum for tamper detection
                checksum = self._calculate_checksum(event)
                
                # Insert event
                await conn.execute("""
                    INSERT INTO events (
                        event_id, aggregate_id, aggregate_type,
                        event_type, event_version, sequence_number,
                        timestamp, data, metadata, checksum
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, event.event_id, event.aggregate_id, event.aggregate_type,
                    event.event_type, event.event_version, sequence,
                    event.timestamp, json.dumps(event.data),
                    json.dumps(event.metadata), checksum)
                
                # Publish event to Redis for real-time subscribers
                if self.redis:
                    await self.redis.publish(
                        f"events:{event.aggregate_type}:{event.event_type}",
                        json.dumps(event.to_dict())
                    )
                
                # Check if snapshot needed
                if sequence % self.snapshot_frequency == 0:
                    await self._create_snapshot(event.aggregate_id, sequence)
                
                return sequence
    
    async def get_events(
        self,
        aggregate_id: str,
        from_sequence: int = 0,
        to_sequence: Optional[int] = None
    ) -> List[Event]:
        """Get events for aggregate"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT * FROM events
                WHERE aggregate_id = $1 AND sequence_number > $2
            """
            params = [aggregate_id, from_sequence]
            
            if to_sequence:
                query += " AND sequence_number <= $3"
                params.append(to_sequence)
            
            query += " ORDER BY sequence_number"
            
            rows = await conn.fetch(query, *params)
            
            events = []
            for row in rows:
                # Verify checksum
                event_dict = dict(row)
                stored_checksum = event_dict.pop('checksum', None)
                
                event = Event(
                    event_id=str(event_dict['event_id']),
                    aggregate_id=event_dict['aggregate_id'],
                    aggregate_type=event_dict['aggregate_type'],
                    event_type=event_dict['event_type'],
                    event_version=event_dict['event_version'],
                    sequence_number=event_dict['sequence_number'],
                    timestamp=event_dict['timestamp'],
                    data=event_dict['data'],
                    metadata=event_dict['metadata']
                )
                
                if stored_checksum:
                    calculated_checksum = self._calculate_checksum(event)
                    if calculated_checksum != stored_checksum:
                        raise ValueError(f"Event tampering detected for {event.event_id}")
                
                events.append(event)
            
            return events
    
    async def get_events_by_time(
        self,
        aggregate_id: str,
        from_time: datetime,
        to_time: Optional[datetime] = None
    ) -> List[Event]:
        """Get events within time range (temporal query)"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT * FROM events
                WHERE aggregate_id = $1 AND timestamp >= $2
            """
            params = [aggregate_id, from_time]
            
            if to_time:
                query += " AND timestamp <= $3"
                params.append(to_time)
            
            query += " ORDER BY sequence_number"
            
            rows = await conn.fetch(query, *params)
            
            return [self._row_to_event(row) for row in rows]
    
    async def replay_events(
        self,
        aggregate_id: str,
        handler: callable,
        from_sequence: int = 0,
        to_sequence: Optional[int] = None,
        use_snapshot: bool = True
    ) -> Any:
        """Replay events to rebuild state"""
        state = None
        start_sequence = from_sequence
        
        # Try to load from snapshot
        if use_snapshot and from_sequence == 0:
            snapshot = await self._get_latest_snapshot(aggregate_id, to_sequence)
            if snapshot:
                state = snapshot['state']
                start_sequence = snapshot['sequence_number']
        
        # Get events after snapshot
        events = await self.get_events(aggregate_id, start_sequence, to_sequence)
        
        # Replay events
        for event in events:
            state = await handler(state, event)
        
        return state
    
    async def _create_snapshot(self, aggregate_id: str, sequence_number: int):
        """Create snapshot for faster replay"""
        # Get aggregate type
        async with self.db_pool.acquire() as conn:
            aggregate_type = await conn.fetchval("""
                SELECT aggregate_type FROM events
                WHERE aggregate_id = $1
                LIMIT 1
            """, aggregate_id)
            
            if not aggregate_type:
                return
            
            # Replay events to build state
            handler = self.event_handlers.get(aggregate_type)
            if not handler:
                return
            
            state = await self.replay_events(
                aggregate_id,
                handler,
                to_sequence=sequence_number,
                use_snapshot=False
            )
            
            # Store snapshot
            snapshot_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO snapshots (
                    snapshot_id, aggregate_id, aggregate_type,
                    sequence_number, timestamp, state
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """, snapshot_id, aggregate_id, aggregate_type,
                sequence_number, datetime.utcnow(), json.dumps(state))
    
    async def _get_latest_snapshot(
        self,
        aggregate_id: str,
        before_sequence: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get latest snapshot before sequence"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT * FROM snapshots
                WHERE aggregate_id = $1
            """
            params = [aggregate_id]
            
            if before_sequence:
                query += " AND sequence_number <= $2"
                params.append(before_sequence)
            
            query += " ORDER BY sequence_number DESC LIMIT 1"
            
            row = await conn.fetchrow(query, *params)
            
            if row:
                return {
                    'state': row['state'],
                    'sequence_number': row['sequence_number']
                }
            
            return None
    
    def _calculate_checksum(self, event: Event) -> str:
        """Calculate event checksum for tamper detection"""
        data = f"{event.aggregate_id}:{event.event_type}:{event.sequence_number}:{json.dumps(event.data)}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _row_to_event(self, row: dict) -> Event:
        """Convert database row to Event"""
        return Event(
            event_id=str(row['event_id']),
            aggregate_id=row['aggregate_id'],
            aggregate_type=row['aggregate_type'],
            event_type=row['event_type'],
            event_version=row['event_version'],
            sequence_number=row['sequence_number'],
            timestamp=row['timestamp'],
            data=row['data'],
            metadata=row['metadata']
        )
    
    def register_handler(self, aggregate_type: str, handler: callable):
        """Register event handler for aggregate type"""
        if aggregate_type not in self.event_handlers:
            self.event_handlers[aggregate_type] = []
        self.event_handlers[aggregate_type].append(handler)
    
    async def close(self):
        """Close connections"""
        if self.db_pool:
            await self.db_pool.close()
        if self.redis:
            await self.redis.close()


class EventMigration:
    """Handle event versioning and migration"""
    
    def __init__(self):
        self.migrations: Dict[Tuple[str, int, int], callable] = {}
    
    def register_migration(
        self,
        event_type: str,
        from_version: int,
        to_version: int,
        migration_func: callable
    ):
        """Register migration function"""
        self.migrations[(event_type, from_version, to_version)] = migration_func
    
    async def migrate_event(self, event: Event, target_version: int) -> Event:
        """Migrate event to target version"""
        current_version = event.event_version
        
        while current_version < target_version:
            next_version = current_version + 1
            migration_key = (event.event_type, current_version, next_version)
            
            if migration_key not in self.migrations:
                raise ValueError(f"No migration found for {migration_key}")
            
            migration_func = self.migrations[migration_key]
            event = await migration_func(event)
            event.event_version = next_version
            current_version = next_version
        
        return event