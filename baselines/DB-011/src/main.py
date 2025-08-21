"""
Main application for Event Sourcing with CQRS

FastAPI application exposing event sourcing and CQRS functionality.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import yaml
import os
import uuid

from event_store import EventStore, Event, EventMigration
from cqrs import (
    Command, Query, CommandBus, QueryBus,
    CommandHandler, QueryHandler, Aggregate,
    Projection, SagaOrchestrator
)
from projections import (
    AccountBalanceProjection,
    OrderSummaryProjection,
    InventoryProjection,
    UserActivityProjection,
    EventStreamBranching
)


# FastAPI app
app = FastAPI(title="Event Sourcing with CQRS", version="1.0.0")

# Global instances
event_store = EventStore()
command_bus = None
query_bus = QueryBus()
projections: Dict[str, Projection] = {}
saga_orchestrator = None
event_branching = EventStreamBranching()


# Pydantic models for API
class CommandRequest(BaseModel):
    command_type: str
    aggregate_id: Optional[str] = None
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = {}


class QueryRequest(BaseModel):
    query_type: str
    filters: Dict[str, Any]
    projection: Optional[str] = None


class EventRequest(BaseModel):
    aggregate_id: str
    aggregate_type: str
    event_type: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = {}


class ReplayRequest(BaseModel):
    aggregate_id: str
    from_sequence: Optional[int] = 0
    to_sequence: Optional[int] = None
    use_snapshot: Optional[bool] = True


class TemporalQueryRequest(BaseModel):
    aggregate_id: str
    from_time: str
    to_time: Optional[str] = None


class SagaRequest(BaseModel):
    saga_type: str
    initial_data: Dict[str, Any]


# Sample command handlers
class AccountCommandHandler(CommandHandler):
    """Handle account-related commands"""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    async def handle(self, command: Command) -> List[Event]:
        """Handle account commands"""
        events = []
        
        if command.command_type == "CreateAccount":
            event = Event(
                aggregate_id=command.aggregate_id,
                aggregate_type="Account",
                event_type="AccountCreated",
                event_version=1,
                sequence_number=0,
                timestamp=datetime.utcnow(),
                data=command.data,
                metadata=command.metadata
            )
            events.append(event)
            
        elif command.command_type == "DepositMoney":
            event = Event(
                aggregate_id=command.aggregate_id,
                aggregate_type="Account",
                event_type="MoneyDeposited",
                event_version=1,
                sequence_number=0,
                timestamp=datetime.utcnow(),
                data=command.data,
                metadata=command.metadata
            )
            events.append(event)
            
        elif command.command_type == "WithdrawMoney":
            # Check balance before withdrawal
            balance_projection = projections.get("account_balance")
            if balance_projection:
                balance_data = await balance_projection.read_models["balance"].query({
                    "account_id": command.aggregate_id
                })
                if balance_data and balance_data.get("balance", 0) < command.data.get("amount", 0):
                    raise ValueError("Insufficient funds")
            
            event = Event(
                aggregate_id=command.aggregate_id,
                aggregate_type="Account",
                event_type="MoneyWithdrawn",
                event_version=1,
                sequence_number=0,
                timestamp=datetime.utcnow(),
                data=command.data,
                metadata=command.metadata
            )
            events.append(event)
        
        return events
    
    def can_handle(self, command_type: str) -> bool:
        """Check if can handle command"""
        return command_type in ["CreateAccount", "DepositMoney", "WithdrawMoney", "Transfer"]


class OrderCommandHandler(CommandHandler):
    """Handle order-related commands"""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    async def handle(self, command: Command) -> List[Event]:
        """Handle order commands"""
        events = []
        
        if command.command_type == "CreateOrder":
            event = Event(
                aggregate_id=command.aggregate_id,
                aggregate_type="Order",
                event_type="OrderCreated",
                event_version=1,
                sequence_number=0,
                timestamp=datetime.utcnow(),
                data=command.data,
                metadata=command.metadata
            )
            events.append(event)
            
        elif command.command_type == "AddItem":
            event = Event(
                aggregate_id=command.aggregate_id,
                aggregate_type="Order",
                event_type="ItemAdded",
                event_version=1,
                sequence_number=0,
                timestamp=datetime.utcnow(),
                data=command.data,
                metadata=command.metadata
            )
            events.append(event)
            
        elif command.command_type == "ConfirmOrder":
            event = Event(
                aggregate_id=command.aggregate_id,
                aggregate_type="Order",
                event_type="OrderConfirmed",
                event_version=1,
                sequence_number=0,
                timestamp=datetime.utcnow(),
                data=command.data,
                metadata=command.metadata
            )
            events.append(event)
        
        return events
    
    def can_handle(self, command_type: str) -> bool:
        """Check if can handle command"""
        return command_type in ["CreateOrder", "AddItem", "ConfirmOrder", "ShipOrder", "CancelOrder"]


# Sample query handlers
class ProjectionQueryHandler(QueryHandler):
    """Handle queries against projections"""
    
    def __init__(self, projections: Dict[str, Projection]):
        self.projections = projections
    
    async def handle(self, query: Query) -> Any:
        """Handle projection queries"""
        projection_name = query.projection or self._get_projection_for_query(query.query_type)
        
        if projection_name not in self.projections:
            raise ValueError(f"Projection {projection_name} not found")
        
        projection = self.projections[projection_name]
        
        # Get read model from projection
        for read_model in projection.read_models.values():
            result = await read_model.query(query.filters)
            if result:
                return result
        
        return None
    
    def can_handle(self, query_type: str) -> bool:
        """Check if can handle query"""
        return True  # Can handle all queries
    
    def _get_projection_for_query(self, query_type: str) -> str:
        """Map query type to projection"""
        mapping = {
            "GetAccountBalance": "account_balance",
            "GetOrderSummary": "order_summary",
            "GetInventory": "inventory",
            "GetUserActivity": "user_activity"
        }
        return mapping.get(query_type, "default")


@app.on_event("startup")
async def startup():
    """Initialize application"""
    global command_bus, saga_orchestrator
    
    # Load configuration
    config_path = os.getenv("CONFIG_PATH", "config")
    
    # Initialize event store
    db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/eventstore")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    await event_store.initialize(db_url, redis_url)
    
    # Initialize command bus
    command_bus = CommandBus(event_store)
    
    # Register command handlers
    command_bus.register_handler(AccountCommandHandler(event_store))
    command_bus.register_handler(OrderCommandHandler(event_store))
    
    # Initialize projections
    projections["account_balance"] = Projection("account_balance", event_store)
    projections["account_balance"].register_read_model("balance", AccountBalanceProjection())
    
    projections["order_summary"] = Projection("order_summary", event_store)
    projections["order_summary"].register_read_model("summary", OrderSummaryProjection())
    
    projections["inventory"] = Projection("inventory", event_store)
    projections["inventory"].register_read_model("stock", InventoryProjection())
    
    projections["user_activity"] = Projection("user_activity", event_store)
    projections["user_activity"].register_read_model("activity", UserActivityProjection())
    
    # Start projections
    for projection in projections.values():
        asyncio.create_task(projection.start())
    
    # Register query handlers
    query_bus.register_handler(ProjectionQueryHandler(projections))
    
    # Initialize saga orchestrator
    saga_orchestrator = SagaOrchestrator(command_bus)


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    # Stop projections
    for projection in projections.values():
        await projection.stop()
    
    # Close event store
    await event_store.close()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "event_store": "up",
            "projections": len(projections),
            "command_handlers": len(command_bus.handlers) if command_bus else 0,
            "query_handlers": len(query_bus.handlers)
        }
    }


@app.post("/api/v1/commands")
async def send_command(request: CommandRequest):
    """Send command to command bus"""
    if not command_bus:
        raise HTTPException(status_code=503, detail="Command bus not initialized")
    
    try:
        command = Command(
            command_id=None,
            aggregate_id=request.aggregate_id or str(uuid.uuid4()),
            command_type=request.command_type,
            timestamp=datetime.utcnow(),
            data=request.data,
            metadata=request.metadata
        )
        
        events = await command_bus.send(command)
        
        return {
            "success": True,
            "command_id": command.command_id,
            "aggregate_id": command.aggregate_id,
            "events_created": len(events),
            "events": [e.to_dict() for e in events]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/queries")
async def send_query(request: QueryRequest):
    """Send query to query bus"""
    try:
        query = Query(
            query_id=None,
            query_type=request.query_type,
            timestamp=datetime.utcnow(),
            filters=request.filters,
            projection=request.projection
        )
        
        result = await query_bus.send(query)
        
        return {
            "success": True,
            "query_id": query.query_id,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/events")
async def append_event(request: EventRequest):
    """Append event directly to event store"""
    try:
        event = Event(
            aggregate_id=request.aggregate_id,
            aggregate_type=request.aggregate_type,
            event_type=request.event_type,
            event_version=1,
            sequence_number=0,
            timestamp=datetime.utcnow(),
            data=request.data,
            metadata=request.metadata
        )
        
        sequence = await event_store.append_event(event)
        
        return {
            "success": True,
            "event_id": event.event_id,
            "sequence_number": sequence
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/events/{aggregate_id}")
async def get_events(
    aggregate_id: str,
    from_sequence: int = 0,
    to_sequence: Optional[int] = None
):
    """Get events for aggregate"""
    try:
        events = await event_store.get_events(aggregate_id, from_sequence, to_sequence)
        
        return {
            "aggregate_id": aggregate_id,
            "event_count": len(events),
            "events": [e.to_dict() for e in events]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/replay")
async def replay_events(request: ReplayRequest):
    """Replay events to rebuild state"""
    try:
        # Simple handler that builds state dict
        async def state_builder(state, event):
            if state is None:
                state = {}
            state[event.event_type] = event.data
            return state
        
        state = await event_store.replay_events(
            request.aggregate_id,
            state_builder,
            request.from_sequence,
            request.to_sequence,
            request.use_snapshot
        )
        
        return {
            "success": True,
            "aggregate_id": request.aggregate_id,
            "state": state
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/temporal-query")
async def temporal_query(request: TemporalQueryRequest):
    """Query events by time range"""
    try:
        from_time = datetime.fromisoformat(request.from_time)
        to_time = datetime.fromisoformat(request.to_time) if request.to_time else None
        
        events = await event_store.get_events_by_time(
            request.aggregate_id,
            from_time,
            to_time
        )
        
        return {
            "aggregate_id": request.aggregate_id,
            "from_time": from_time.isoformat(),
            "to_time": to_time.isoformat() if to_time else None,
            "event_count": len(events),
            "events": [e.to_dict() for e in events]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/projections/{projection_name}/rebuild")
async def rebuild_projection(projection_name: str, background_tasks: BackgroundTasks):
    """Rebuild projection from events"""
    if projection_name not in projections:
        raise HTTPException(status_code=404, detail=f"Projection {projection_name} not found")
    
    try:
        projection = projections[projection_name]
        background_tasks.add_task(projection.rebuild)
        
        return {
            "success": True,
            "projection": projection_name,
            "status": "rebuilding"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/sagas")
async def start_saga(request: SagaRequest):
    """Start new saga"""
    if not saga_orchestrator:
        raise HTTPException(status_code=503, detail="Saga orchestrator not initialized")
    
    try:
        saga_id = await saga_orchestrator.start_saga(
            request.saga_type,
            request.initial_data
        )
        
        return {
            "success": True,
            "saga_id": saga_id,
            "saga_type": request.saga_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/branches")
async def create_branch(
    branch_name: str,
    aggregate_id: str,
    branch_point: int
):
    """Create event stream branch"""
    try:
        events = await event_store.get_events(aggregate_id)
        branch_id = await event_branching.create_branch(
            branch_name,
            events,
            branch_point
        )
        
        return {
            "success": True,
            "branch_id": branch_id,
            "branch_name": branch_name,
            "branch_point": branch_point
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)