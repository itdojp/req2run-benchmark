"""
Event-Driven Webhook System with Retry and DLQ - Main Application

FastAPI application providing webhook management and event delivery.
"""

import asyncio
import json
import os
import yaml
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import logging

from webhook_engine import WebhookEngine, WebhookEndpoint, EventType, WebhookStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
webhook_events_total = Counter('webhook_events_total', 'Total webhook events processed', ['event_type'])
webhook_deliveries_total = Counter('webhook_deliveries_total', 'Total webhook deliveries', ['status'])
webhook_delivery_duration = Histogram('webhook_delivery_duration_seconds', 'Webhook delivery duration')
webhook_queue_size = Gauge('webhook_queue_size', 'Current webhook queue size')
webhook_endpoints_total = Gauge('webhook_endpoints_total', 'Total registered webhook endpoints')

# Global webhook engine instance
webhook_engine: WebhookEngine = None

# Pydantic models for API
class WebhookEndpointCreate(BaseModel):
    url: str = Field(..., description="Webhook endpoint URL")
    secret: str = Field(..., description="Secret for HMAC signing")
    events: List[str] = Field(..., description="List of event types to subscribe to")
    active: bool = Field(True, description="Whether endpoint is active")
    max_retries: int = Field(5, description="Maximum retry attempts")
    timeout: int = Field(30, description="Request timeout in seconds")
    headers: Dict[str, str] = Field(default_factory=dict, description="Additional headers")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Event filters")

class WebhookEndpointUpdate(BaseModel):
    url: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    active: Optional[bool] = None
    max_retries: Optional[int] = None
    timeout: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    filters: Optional[Dict[str, Any]] = None

class EventCreate(BaseModel):
    event_type: str = Field(..., description="Event type identifier")
    payload: Dict[str, Any] = Field(..., description="Event payload data")

class EventBatch(BaseModel):
    events: List[EventCreate] = Field(..., description="Batch of events to process")

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML files"""
    config = {}
    
    config_files = [
        'config/webhooks.yaml',
        'config/queue.yaml',
        'config/retry.yaml'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                config.update(file_config)
    
    # Override with environment variables
    config.update({
        'webhook_engine': {
            'worker_count': int(os.getenv('WEBHOOK_WORKER_COUNT', 4)),
            'max_queue_size': int(os.getenv('WEBHOOK_MAX_QUEUE_SIZE', 10000))
        },
        'retry_policy': {
            'initial_delay': float(os.getenv('RETRY_INITIAL_DELAY', 1.0)),
            'max_delay': float(os.getenv('RETRY_MAX_DELAY', 300.0)),
            'multiplier': float(os.getenv('RETRY_MULTIPLIER', 2.0))
        },
        'dlq': {
            'retention_days': int(os.getenv('DLQ_RETENTION_DAYS', 7))
        }
    })
    
    return config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global webhook_engine
    
    # Load configuration
    config = load_config()
    
    # Initialize webhook engine
    webhook_engine = WebhookEngine(config)
    
    # Start webhook engine
    worker_count = config.get('webhook_engine', {}).get('worker_count', 4)
    await webhook_engine.start(worker_count)
    
    logger.info(f"Webhook engine started with {worker_count} workers")
    
    # Update metrics periodically
    metrics_task = asyncio.create_task(update_metrics_loop())
    
    yield
    
    # Cleanup
    metrics_task.cancel()
    await webhook_engine.stop()
    logger.info("Application shutdown complete")

async def update_metrics_loop():
    """Update Prometheus metrics periodically"""
    while True:
        try:
            if webhook_engine:
                stats = webhook_engine.get_stats()
                webhook_queue_size.set(stats['queue_size'])
                webhook_endpoints_total.set(stats['total_endpoints'])
            
            await asyncio.sleep(10)  # Update every 10 seconds
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            await asyncio.sleep(10)

# FastAPI application
app = FastAPI(
    title="Event-Driven Webhook System",
    description="Reliable webhook delivery system with retry logic and Dead Letter Queue",
    version="1.0.0",
    lifespan=lifespan
)

async def get_webhook_engine() -> WebhookEngine:
    """Dependency to get webhook engine instance"""
    if webhook_engine is None:
        raise HTTPException(status_code=500, detail="Webhook engine not initialized")
    return webhook_engine

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "engine_running": webhook_engine is not None and webhook_engine.running
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/v1/stats")
async def get_stats(engine: WebhookEngine = Depends(get_webhook_engine)):
    """Get webhook engine statistics"""
    stats = engine.get_stats()
    return {
        "stats": stats,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/webhooks", status_code=201)
async def register_webhook(
    endpoint_data: WebhookEndpointCreate,
    engine: WebhookEngine = Depends(get_webhook_engine)
):
    """Register a new webhook endpoint"""
    import uuid
    
    endpoint = WebhookEndpoint(
        id=str(uuid.uuid4()),
        url=endpoint_data.url,
        secret=endpoint_data.secret,
        events=endpoint_data.events,
        active=endpoint_data.active,
        max_retries=endpoint_data.max_retries,
        timeout=endpoint_data.timeout,
        headers=endpoint_data.headers,
        filters=endpoint_data.filters
    )
    
    endpoint_id = await engine.register_endpoint(endpoint)
    
    return {
        "id": endpoint_id,
        "message": "Webhook endpoint registered successfully"
    }

@app.get("/api/v1/webhooks")
async def list_webhooks(engine: WebhookEngine = Depends(get_webhook_engine)):
    """List all registered webhook endpoints"""
    endpoints = []
    for endpoint_id, endpoint in engine.endpoints.items():
        endpoints.append({
            "id": endpoint.id,
            "url": endpoint.url,
            "events": endpoint.events,
            "active": endpoint.active,
            "created_at": endpoint.created_at.isoformat()
        })
    
    return {"endpoints": endpoints}

@app.get("/api/v1/webhooks/{endpoint_id}")
async def get_webhook(
    endpoint_id: str,
    engine: WebhookEngine = Depends(get_webhook_engine)
):
    """Get webhook endpoint details"""
    endpoint = engine.endpoints.get(endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found")
    
    return {
        "id": endpoint.id,
        "url": endpoint.url,
        "events": endpoint.events,
        "active": endpoint.active,
        "max_retries": endpoint.max_retries,
        "timeout": endpoint.timeout,
        "headers": endpoint.headers,
        "filters": endpoint.filters,
        "created_at": endpoint.created_at.isoformat(),
        "updated_at": endpoint.updated_at.isoformat()
    }

@app.put("/api/v1/webhooks/{endpoint_id}")
async def update_webhook(
    endpoint_id: str,
    updates: WebhookEndpointUpdate,
    engine: WebhookEngine = Depends(get_webhook_engine)
):
    """Update webhook endpoint"""
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    success = await engine.update_endpoint(endpoint_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found")
    
    return {"message": "Webhook endpoint updated successfully"}

@app.delete("/api/v1/webhooks/{endpoint_id}")
async def unregister_webhook(
    endpoint_id: str,
    engine: WebhookEngine = Depends(get_webhook_engine)
):
    """Unregister webhook endpoint"""
    await engine.unregister_endpoint(endpoint_id)
    return {"message": "Webhook endpoint unregistered successfully"}

@app.post("/api/v1/events", status_code=202)
async def emit_event(
    event_data: EventCreate,
    background_tasks: BackgroundTasks,
    engine: WebhookEngine = Depends(get_webhook_engine)
):
    """Emit an event for webhook delivery"""
    event_id = await engine.emit_event(event_data.event_type, event_data.payload)
    
    # Update metrics
    webhook_events_total.labels(event_type=event_data.event_type).inc()
    
    return {
        "event_id": event_id,
        "message": "Event queued for delivery"
    }

@app.post("/api/v1/events/batch", status_code=202)
async def emit_events_batch(
    batch_data: EventBatch,
    engine: WebhookEngine = Depends(get_webhook_engine)
):
    """Emit multiple events in batch"""
    event_ids = []
    
    for event_data in batch_data.events:
        event_id = await engine.emit_event(event_data.event_type, event_data.payload)
        event_ids.append(event_id)
        
        # Update metrics
        webhook_events_total.labels(event_type=event_data.event_type).inc()
    
    return {
        "event_ids": event_ids,
        "message": f"{len(event_ids)} events queued for delivery"
    }

@app.get("/api/v1/deliveries/{delivery_id}")
async def get_delivery_status(
    delivery_id: str,
    engine: WebhookEngine = Depends(get_webhook_engine)
):
    """Get delivery status"""
    delivery_info = await engine.get_delivery_status(delivery_id)
    if not delivery_info:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    return delivery_info

@app.get("/api/v1/webhooks/{endpoint_id}/deliveries")
async def get_endpoint_deliveries(
    endpoint_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    engine: WebhookEngine = Depends(get_webhook_engine)
):
    """Get deliveries for an endpoint"""
    deliveries = await engine.get_endpoint_deliveries(endpoint_id, status, limit)
    return {"deliveries": deliveries}

@app.post("/api/v1/deliveries/{delivery_id}/replay")
async def replay_delivery(
    delivery_id: str,
    engine: WebhookEngine = Depends(get_webhook_engine)
):
    """Replay a failed delivery"""
    success = await engine.replay_webhook(delivery_id)
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Cannot replay delivery (not found or not failed)"
        )
    
    return {"message": "Delivery queued for replay"}

@app.get("/api/v1/dlq")
async def get_dlq_messages(
    limit: int = 100,
    engine: WebhookEngine = Depends(get_webhook_engine)
):
    """Get Dead Letter Queue messages"""
    messages = await engine.dlq.get_messages(limit)
    return {"messages": messages}

@app.post("/api/v1/dlq/{message_id}/replay")
async def replay_dlq_message(
    message_id: str,
    engine: WebhookEngine = Depends(get_webhook_engine)
):
    """Replay a DLQ message"""
    success = await engine.dlq.replay_message(message_id)
    if not success:
        raise HTTPException(status_code=404, detail="DLQ message not found")
    
    return {"message": "DLQ message queued for replay"}

@app.get("/api/v1/events/types")
async def get_event_types():
    """Get available event types"""
    return {
        "event_types": [event_type.value for event_type in EventType],
        "custom_supported": True
    }

# Webhook receiver endpoint for testing
@app.post("/test/webhook")
async def test_webhook_receiver(request: Request):
    """Test webhook receiver endpoint"""
    headers = dict(request.headers)
    body = await request.body()
    
    logger.info(f"Received webhook: {headers}")
    
    # Verify signature if present
    signature = headers.get('x-webhook-signature')
    if signature:
        logger.info(f"Webhook signature: {signature}")
    
    return {"status": "received", "timestamp": datetime.utcnow().isoformat()}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )