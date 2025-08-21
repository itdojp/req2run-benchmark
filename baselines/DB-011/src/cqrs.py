"""
CQRS Implementation

Separates read and write models with command and query handlers.
"""

import asyncio
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
from datetime import datetime
import uuid
from abc import ABC, abstractmethod

from event_store import Event, EventStore


@dataclass
class Command:
    """Base command structure"""
    command_id: str
    aggregate_id: str
    command_type: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.command_id:
            self.command_id = str(uuid.uuid4())
        if not self.metadata:
            self.metadata = {}


@dataclass
class Query:
    """Base query structure"""
    query_id: str
    query_type: str
    timestamp: datetime
    filters: Dict[str, Any]
    projection: Optional[str] = None
    
    def __post_init__(self):
        if not self.query_id:
            self.query_id = str(uuid.uuid4())


class CommandHandler(ABC):
    """Abstract command handler"""
    
    @abstractmethod
    async def handle(self, command: Command) -> List[Event]:
        """Handle command and return events"""
        pass
    
    @abstractmethod
    def can_handle(self, command_type: str) -> bool:
        """Check if handler can handle command type"""
        pass


class QueryHandler(ABC):
    """Abstract query handler"""
    
    @abstractmethod
    async def handle(self, query: Query) -> Any:
        """Handle query and return result"""
        pass
    
    @abstractmethod
    def can_handle(self, query_type: str) -> bool:
        """Check if handler can handle query type"""
        pass


class Aggregate(ABC):
    """Base aggregate root"""
    
    def __init__(self, aggregate_id: str = None):
        self.aggregate_id = aggregate_id or str(uuid.uuid4())
        self.version = 0
        self.uncommitted_events: List[Event] = []
    
    @abstractmethod
    def apply_event(self, event: Event):
        """Apply event to aggregate"""
        pass
    
    def add_event(self, event_type: str, data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Add new event to uncommitted events"""
        event = Event(
            aggregate_id=self.aggregate_id,
            aggregate_type=self.__class__.__name__,
            event_type=event_type,
            event_version=1,
            sequence_number=0,  # Will be set by event store
            timestamp=datetime.utcnow(),
            data=data,
            metadata=metadata or {}
        )
        
        self.uncommitted_events.append(event)
        self.apply_event(event)
        self.version += 1
    
    def mark_events_committed(self):
        """Mark all events as committed"""
        self.uncommitted_events.clear()
    
    @classmethod
    async def load_from_events(cls, aggregate_id: str, events: List[Event]) -> 'Aggregate':
        """Load aggregate from events"""
        aggregate = cls(aggregate_id)
        for event in events:
            aggregate.apply_event(event)
            aggregate.version += 1
        return aggregate


class CommandBus:
    """Command bus for routing commands to handlers"""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.handlers: List[CommandHandler] = []
        self.middleware: List[callable] = []
    
    def register_handler(self, handler: CommandHandler):
        """Register command handler"""
        self.handlers.append(handler)
    
    def add_middleware(self, middleware: callable):
        """Add middleware for command processing"""
        self.middleware.append(middleware)
    
    async def send(self, command: Command) -> List[Event]:
        """Send command to appropriate handler"""
        # Apply middleware
        for mw in self.middleware:
            command = await mw(command)
        
        # Find handler
        handler = None
        for h in self.handlers:
            if h.can_handle(command.command_type):
                handler = h
                break
        
        if not handler:
            raise ValueError(f"No handler found for command type: {command.command_type}")
        
        # Handle command and get events
        events = await handler.handle(command)
        
        # Store events
        for event in events:
            await self.event_store.append_event(event)
        
        return events


class QueryBus:
    """Query bus for routing queries to handlers"""
    
    def __init__(self):
        self.handlers: List[QueryHandler] = []
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 60  # seconds
    
    def register_handler(self, handler: QueryHandler):
        """Register query handler"""
        self.handlers.append(handler)
    
    async def send(self, query: Query) -> Any:
        """Send query to appropriate handler"""
        # Check cache
        cache_key = f"{query.query_type}:{str(query.filters)}"
        if cache_key in self.cache:
            cached_result, cached_time = self.cache[cache_key]
            if (datetime.utcnow() - cached_time).seconds < self.cache_ttl:
                return cached_result
        
        # Find handler
        handler = None
        for h in self.handlers:
            if h.can_handle(query.query_type):
                handler = h
                break
        
        if not handler:
            raise ValueError(f"No handler found for query type: {query.query_type}")
        
        # Handle query
        result = await handler.handle(query)
        
        # Cache result
        self.cache[cache_key] = (result, datetime.utcnow())
        
        return result


class ReadModel:
    """Base read model for queries"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
    
    async def project(self, event: Event):
        """Project event to read model"""
        pass
    
    async def query(self, filters: Dict[str, Any]) -> Any:
        """Query read model"""
        pass


class Projection:
    """Manages projections from events to read models"""
    
    def __init__(self, name: str, event_store: EventStore):
        self.name = name
        self.event_store = event_store
        self.read_models: Dict[str, ReadModel] = {}
        self.position = 0
        self.running = False
    
    def register_read_model(self, model_name: str, read_model: ReadModel):
        """Register read model"""
        self.read_models[model_name] = read_model
    
    async def start(self):
        """Start projection"""
        self.running = True
        
        while self.running:
            try:
                # Get new events
                events = await self._get_new_events()
                
                if events:
                    # Project events to read models
                    for event in events:
                        for read_model in self.read_models.values():
                            await read_model.project(event)
                        
                        self.position = event.sequence_number
                
                # Short delay before next check
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Projection error: {e}")
                await asyncio.sleep(1)
    
    async def stop(self):
        """Stop projection"""
        self.running = False
    
    async def _get_new_events(self) -> List[Event]:
        """Get new events since last position"""
        # This would query all aggregates in production
        # For simplicity, we'll return empty list
        return []
    
    async def rebuild(self):
        """Rebuild projection from beginning"""
        self.position = 0
        
        # Clear read models
        for read_model in self.read_models.values():
            read_model.data.clear()
        
        # Restart projection
        await self.start()


class SagaOrchestrator:
    """Orchestrates sagas (long-running transactions)"""
    
    def __init__(self, command_bus: CommandBus):
        self.command_bus = command_bus
        self.sagas: Dict[str, 'Saga'] = {}
        self.active_sagas: Dict[str, 'Saga'] = {}
    
    def register_saga(self, saga_type: str, saga_class: Type['Saga']):
        """Register saga type"""
        self.sagas[saga_type] = saga_class
    
    async def start_saga(self, saga_type: str, initial_data: Dict[str, Any]) -> str:
        """Start new saga"""
        if saga_type not in self.sagas:
            raise ValueError(f"Unknown saga type: {saga_type}")
        
        saga_class = self.sagas[saga_type]
        saga = saga_class(initial_data)
        saga_id = saga.saga_id
        
        self.active_sagas[saga_id] = saga
        
        # Start saga
        await saga.start(self.command_bus)
        
        return saga_id
    
    async def handle_event(self, event: Event):
        """Handle event for active sagas"""
        for saga in self.active_sagas.values():
            if await saga.can_handle(event):
                await saga.handle_event(event, self.command_bus)
                
                if saga.is_completed():
                    del self.active_sagas[saga.saga_id]


class Saga(ABC):
    """Base saga for long-running transactions"""
    
    def __init__(self, initial_data: Dict[str, Any]):
        self.saga_id = str(uuid.uuid4())
        self.state = "started"
        self.data = initial_data
    
    @abstractmethod
    async def start(self, command_bus: CommandBus):
        """Start saga"""
        pass
    
    @abstractmethod
    async def can_handle(self, event: Event) -> bool:
        """Check if saga can handle event"""
        pass
    
    @abstractmethod
    async def handle_event(self, event: Event, command_bus: CommandBus):
        """Handle event"""
        pass
    
    def is_completed(self) -> bool:
        """Check if saga is completed"""
        return self.state in ["completed", "failed", "compensated"]