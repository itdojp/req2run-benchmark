"""Change Data Capture Engine"""
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import hashlib

import structlog
from sqlalchemy import create_engine, MetaData, Table, select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import aiokafka

logger = structlog.get_logger()


class ChangeType(str, Enum):
    """Types of database changes"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    TRUNCATE = "TRUNCATE"
    DDL = "DDL"


@dataclass
class ChangeEvent:
    """Represents a database change event"""
    event_id: str
    timestamp: datetime
    source_database: str
    source_table: str
    change_type: ChangeType
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    primary_key: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source_database": self.source_database,
            "source_table": self.source_table,
            "change_type": self.change_type.value,
            "before": self.before,
            "after": self.after,
            "primary_key": self.primary_key,
            "metadata": self.metadata
        }


class CDCEngine:
    """Change Data Capture Engine"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sources: Dict[str, Any] = {}
        self.watchers: Dict[str, asyncio.Task] = {}
        self.change_handlers: List[Callable] = []
        self.last_positions: Dict[str, Any] = {}
        
    async def connect_source(self, source_config: Dict[str, Any]):
        """Connect to a data source"""
        source_type = source_config.get("type")
        source_id = source_config.get("id", f"source_{len(self.sources)}")
        
        if source_type == "postgresql":
            engine = await self._connect_postgresql(source_config)
        elif source_type == "mysql":
            engine = await self._connect_mysql(source_config)
        elif source_type == "mongodb":
            engine = await self._connect_mongodb(source_config)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        self.sources[source_id] = {
            "engine": engine,
            "config": source_config,
            "type": source_type
        }
        
        logger.info(f"Connected to source", source_id=source_id, type=source_type)
        return source_id
    
    async def _connect_postgresql(self, config: Dict[str, Any]):
        """Connect to PostgreSQL with logical replication"""
        connection_string = config.get("connection_string")
        engine = create_async_engine(connection_string)
        
        # Enable logical replication (simplified)
        async with engine.connect() as conn:
            # Check if logical replication is available
            result = await conn.execute(text("SHOW wal_level"))
            wal_level = result.scalar()
            
            if wal_level != "logical":
                logger.warning("Logical replication not enabled, using polling fallback")
        
        return engine
    
    async def _connect_mysql(self, config: Dict[str, Any]):
        """Connect to MySQL with binlog reading"""
        # Simplified MySQL connection
        import mysql.connector
        
        connection = mysql.connector.connect(
            host=config.get("host", "localhost"),
            port=config.get("port", 3306),
            user=config.get("user"),
            password=config.get("password"),
            database=config.get("database")
        )
        
        return connection
    
    async def _connect_mongodb(self, config: Dict[str, Any]):
        """Connect to MongoDB with change streams"""
        from pymongo import MongoClient
        
        client = MongoClient(config.get("connection_string"))
        db = client[config.get("database")]
        
        return db
    
    async def start_capture(self, source_id: str, tables: Optional[List[str]] = None):
        """Start capturing changes from a source"""
        if source_id not in self.sources:
            raise ValueError(f"Source {source_id} not found")
        
        source = self.sources[source_id]
        source_type = source["type"]
        
        if source_type == "postgresql":
            watcher = asyncio.create_task(
                self._watch_postgresql(source_id, tables)
            )
        elif source_type == "mysql":
            watcher = asyncio.create_task(
                self._watch_mysql(source_id, tables)
            )
        elif source_type == "mongodb":
            watcher = asyncio.create_task(
                self._watch_mongodb(source_id, tables)
            )
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        self.watchers[source_id] = watcher
        logger.info(f"Started CDC for source", source_id=source_id)
    
    async def _watch_postgresql(self, source_id: str, tables: Optional[List[str]] = None):
        """Watch PostgreSQL changes using logical replication or polling"""
        source = self.sources[source_id]
        engine = source["engine"]
        
        # Simplified: Use polling as fallback
        poll_interval = source["config"].get("poll_interval", 1)
        
        while True:
            try:
                async with AsyncSession(engine) as session:
                    # Get tables to watch
                    if not tables:
                        # Get all tables
                        result = await session.execute(
                            text("""
                                SELECT table_name 
                                FROM information_schema.tables 
                                WHERE table_schema = 'public'
                            """)
                        )
                        tables = [row[0] for row in result]
                    
                    for table_name in tables:
                        await self._poll_table_changes(
                            session, source_id, table_name
                        )
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error watching PostgreSQL", error=str(e))
                await asyncio.sleep(5)
    
    async def _poll_table_changes(self, session: AsyncSession, source_id: str, table_name: str):
        """Poll a table for changes (simplified CDC)"""
        # Get last position for this table
        position_key = f"{source_id}:{table_name}"
        last_position = self.last_positions.get(position_key, {})
        
        # Query for changes (simplified - in production use proper CDC)
        # This example assumes tables have updated_at timestamp
        query = f"""
            SELECT * FROM {table_name}
            WHERE updated_at > :last_timestamp
            ORDER BY updated_at
            LIMIT 100
        """
        
        last_timestamp = last_position.get("timestamp", datetime.min)
        
        try:
            result = await session.execute(
                text(query),
                {"last_timestamp": last_timestamp}
            )
            
            rows = result.fetchall()
            
            for row in rows:
                # Create change event
                row_dict = dict(row._mapping)
                
                change_event = ChangeEvent(
                    event_id=self._generate_event_id(),
                    timestamp=row_dict.get("updated_at", datetime.now()),
                    source_database=source_id,
                    source_table=table_name,
                    change_type=ChangeType.UPDATE,  # Simplified
                    before=None,  # Would need to track previous state
                    after=row_dict,
                    primary_key={"id": row_dict.get("id")},
                    metadata={"source_type": "postgresql"}
                )
                
                # Process change event
                await self._process_change_event(change_event)
                
                # Update position
                self.last_positions[position_key] = {
                    "timestamp": row_dict.get("updated_at", datetime.now())
                }
                
        except Exception as e:
            # Table might not have updated_at column
            pass
    
    async def _watch_mysql(self, source_id: str, tables: Optional[List[str]] = None):
        """Watch MySQL changes using binlog"""
        # Simplified implementation
        while True:
            await asyncio.sleep(1)
            # In production, use pymysqlreplication for binlog reading
    
    async def _watch_mongodb(self, source_id: str, collections: Optional[List[str]] = None):
        """Watch MongoDB changes using change streams"""
        source = self.sources[source_id]
        db = source["engine"]
        
        try:
            # Watch all collections or specific ones
            if collections:
                for collection_name in collections:
                    collection = db[collection_name]
                    async with collection.watch() as stream:
                        async for change in stream:
                            await self._process_mongodb_change(
                                source_id, collection_name, change
                            )
            else:
                # Watch entire database
                async with db.watch() as stream:
                    async for change in stream:
                        await self._process_mongodb_change(
                            source_id, change["ns"]["coll"], change
                        )
        except Exception as e:
            logger.error(f"Error watching MongoDB", error=str(e))
    
    async def _process_mongodb_change(self, source_id: str, collection: str, change: Dict[str, Any]):
        """Process MongoDB change stream event"""
        operation_type = change["operationType"]
        
        if operation_type == "insert":
            change_type = ChangeType.INSERT
            after = change["fullDocument"]
            before = None
        elif operation_type == "update":
            change_type = ChangeType.UPDATE
            after = change.get("fullDocument")
            before = None  # Would need to track
        elif operation_type == "delete":
            change_type = ChangeType.DELETE
            after = None
            before = None  # Document already deleted
        else:
            return
        
        change_event = ChangeEvent(
            event_id=str(change["_id"]),
            timestamp=change["clusterTime"].as_datetime(),
            source_database=source_id,
            source_table=collection,
            change_type=change_type,
            before=before,
            after=after,
            primary_key={"_id": str(change.get("documentKey", {}).get("_id"))},
            metadata={"source_type": "mongodb"}
        )
        
        await self._process_change_event(change_event)
    
    async def _process_change_event(self, event: ChangeEvent):
        """Process a change event through handlers"""
        for handler in self.change_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in change handler", error=str(e))
    
    def add_change_handler(self, handler: Callable):
        """Add a handler for change events"""
        self.change_handlers.append(handler)
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = str(time.time()).encode()
        return hashlib.sha256(timestamp).hexdigest()[:16]
    
    async def stop_capture(self, source_id: str):
        """Stop capturing changes from a source"""
        if source_id in self.watchers:
            self.watchers[source_id].cancel()
            del self.watchers[source_id]
            logger.info(f"Stopped CDC for source", source_id=source_id)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get CDC statistics"""
        return {
            "sources": len(self.sources),
            "active_watchers": len(self.watchers),
            "last_positions": self.last_positions
        }


class CDCBuffer:
    """Buffer for CDC events with deduplication"""
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.buffer: List[ChangeEvent] = []
        self.seen_events: Dict[str, datetime] = {}
    
    async def add_event(self, event: ChangeEvent) -> bool:
        """Add event to buffer with deduplication"""
        # Check for duplicate
        if event.event_id in self.seen_events:
            return False
        
        # Add to buffer
        self.buffer.append(event)
        self.seen_events[event.event_id] = event.timestamp
        
        # Trim buffer if needed
        if len(self.buffer) > self.max_size:
            self.buffer = self.buffer[-self.max_size:]
        
        # Clean old seen events
        await self._cleanup_seen_events()
        
        return True
    
    async def _cleanup_seen_events(self):
        """Remove old entries from seen events"""
        cutoff = datetime.now().timestamp() - self.ttl_seconds
        self.seen_events = {
            k: v for k, v in self.seen_events.items()
            if v.timestamp() > cutoff
        }
    
    async def get_events(self, count: int = 100) -> List[ChangeEvent]:
        """Get events from buffer"""
        return self.buffer[-count:]
    
    async def clear(self):
        """Clear buffer"""
        self.buffer.clear()
        self.seen_events.clear()