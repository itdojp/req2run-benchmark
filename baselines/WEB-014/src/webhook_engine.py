"""
Webhook Engine with Retry Logic and Dead Letter Queue

Core webhook delivery system with reliability guarantees.
"""

import asyncio
import json
import hmac
import hashlib
import time
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from urllib.parse import urlparse
import aiohttp
import backoff


logger = logging.getLogger(__name__)


class WebhookStatus(Enum):
    PENDING = "pending"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    FAILED = "failed"
    DLQ = "dlq"


class EventType(Enum):
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_CANCELLED = "order.cancelled"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"


@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration"""
    id: str
    url: str
    secret: str
    events: List[str]
    active: bool = True
    max_retries: int = 5
    timeout: int = 30
    headers: Dict[str, str] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WebhookEvent:
    """Webhook event data"""
    id: str
    event_type: str
    payload: Dict[str, Any]
    endpoint_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WebhookDelivery:
    """Webhook delivery attempt"""
    id: str
    event_id: str
    endpoint_id: str
    status: WebhookStatus = WebhookStatus.PENDING
    attempt: int = 0
    max_attempts: int = 5
    next_retry_at: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class WebhookSigner:
    """Webhook payload signing with HMAC-SHA256"""
    
    def __init__(self):
        self.algorithm = hashlib.sha256
    
    def sign_payload(self, payload: str, secret: str) -> str:
        """Sign payload with HMAC-SHA256"""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            self.algorithm
        )
        return f"sha256={signature.hexdigest()}"
    
    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        expected_signature = self.sign_payload(payload, secret)
        return hmac.compare_digest(signature, expected_signature)


class RetryPolicy:
    """Exponential backoff retry policy"""
    
    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 300.0,
        multiplier: float = 2.0,
        jitter: bool = True
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = self.initial_delay * (self.multiplier ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # ±25% jitter
        
        return delay
    
    def get_next_retry_time(self, attempt: int) -> datetime:
        """Get next retry time"""
        delay = self.get_delay(attempt)
        return datetime.utcnow() + timedelta(seconds=delay)


class DeadLetterQueue:
    """Dead Letter Queue for failed webhooks"""
    
    def __init__(self, storage_backend=None):
        self.storage = storage_backend
        self.messages: List[Dict[str, Any]] = []
        self.retention_days = 7
    
    async def send_to_dlq(self, delivery: WebhookDelivery, event: WebhookEvent, endpoint: WebhookEndpoint):
        """Send failed delivery to DLQ"""
        dlq_message = {
            "id": str(uuid.uuid4()),
            "delivery_id": delivery.id,
            "event_id": event.id,
            "endpoint_id": endpoint.id,
            "event_type": event.event_type,
            "payload": event.payload,
            "endpoint_url": endpoint.url,
            "failure_reason": delivery.error_message,
            "attempts": delivery.attempt,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=self.retention_days)).isoformat()
        }
        
        if self.storage:
            await self.storage.store_dlq_message(dlq_message)
        else:
            self.messages.append(dlq_message)
        
        logger.warning(
            f"Webhook delivery {delivery.id} sent to DLQ after {delivery.attempt} attempts"
        )
    
    async def get_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get DLQ messages"""
        if self.storage:
            return await self.storage.get_dlq_messages(limit)
        return self.messages[:limit]
    
    async def replay_message(self, message_id: str) -> bool:
        """Replay a DLQ message"""
        # Find and remove message from DLQ
        message = None
        if self.storage:
            message = await self.storage.get_dlq_message(message_id)
            if message:
                await self.storage.delete_dlq_message(message_id)
        else:
            for i, msg in enumerate(self.messages):
                if msg['id'] == message_id:
                    message = self.messages.pop(i)
                    break
        
        if message:
            logger.info(f"Replaying DLQ message {message_id}")
            return True
        
        return False


class WebhookEngine:
    """Main webhook engine"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.events: Dict[str, WebhookEvent] = {}
        
        self.signer = WebhookSigner()
        self.retry_policy = RetryPolicy()
        self.dlq = DeadLetterQueue()
        
        self.delivery_queue: asyncio.Queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.running = False
        
        # Statistics
        self.stats = {
            'events_received': 0,
            'deliveries_attempted': 0,
            'deliveries_successful': 0,
            'deliveries_failed': 0,
            'messages_in_dlq': 0
        }
    
    async def start(self, worker_count: int = 4):
        """Start webhook engine workers"""
        self.running = True
        
        # Start delivery workers
        for i in range(worker_count):
            worker = asyncio.create_task(self._delivery_worker(f"worker-{i}"))
            self.workers.append(worker)
        
        # Start retry scheduler
        retry_scheduler = asyncio.create_task(self._retry_scheduler())
        self.workers.append(retry_scheduler)
        
        logger.info(f"Webhook engine started with {worker_count} workers")
    
    async def stop(self):
        """Stop webhook engine"""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("Webhook engine stopped")
    
    async def register_endpoint(self, endpoint: WebhookEndpoint) -> str:
        """Register a webhook endpoint"""
        self.endpoints[endpoint.id] = endpoint
        logger.info(f"Registered webhook endpoint {endpoint.id} for events: {endpoint.events}")
        return endpoint.id
    
    async def unregister_endpoint(self, endpoint_id: str):
        """Unregister a webhook endpoint"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            logger.info(f"Unregistered webhook endpoint {endpoint_id}")
    
    async def update_endpoint(self, endpoint_id: str, updates: Dict[str, Any]) -> bool:
        """Update webhook endpoint"""
        if endpoint_id not in self.endpoints:
            return False
        
        endpoint = self.endpoints[endpoint_id]
        for key, value in updates.items():
            if hasattr(endpoint, key):
                setattr(endpoint, key, value)
        
        endpoint.updated_at = datetime.utcnow()
        logger.info(f"Updated webhook endpoint {endpoint_id}")
        return True
    
    async def emit_event(self, event_type: str, payload: Dict[str, Any]) -> str:
        """Emit an event to be delivered via webhooks"""
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            payload=payload,
            endpoint_id=""  # Will be set per endpoint
        )
        
        self.events[event.id] = event
        self.stats['events_received'] += 1
        
        # Find matching endpoints
        matching_endpoints = []
        for endpoint in self.endpoints.values():
            if endpoint.active and self._should_deliver_to_endpoint(event, endpoint):
                matching_endpoints.append(endpoint)
        
        # Create delivery jobs
        for endpoint in matching_endpoints:
            delivery = WebhookDelivery(
                id=str(uuid.uuid4()),
                event_id=event.id,
                endpoint_id=endpoint.id,
                max_attempts=endpoint.max_retries
            )
            
            self.deliveries[delivery.id] = delivery
            
            # Queue for delivery
            await self.delivery_queue.put(delivery.id)
        
        logger.info(f"Event {event.id} queued for delivery to {len(matching_endpoints)} endpoints")
        return event.id
    
    def _should_deliver_to_endpoint(self, event: WebhookEvent, endpoint: WebhookEndpoint) -> bool:
        """Check if event should be delivered to endpoint"""
        # Check event type filter
        if event.event_type not in endpoint.events and "*" not in endpoint.events:
            return False
        
        # Check custom filters
        for filter_key, filter_value in endpoint.filters.items():
            if filter_key in event.payload:
                if event.payload[filter_key] != filter_value:
                    return False
        
        return True
    
    async def _delivery_worker(self, worker_name: str):
        """Worker that processes webhook deliveries"""
        logger.info(f"Delivery worker {worker_name} started")
        
        while self.running:
            try:
                # Get delivery from queue
                delivery_id = await asyncio.wait_for(
                    self.delivery_queue.get(),
                    timeout=1.0
                )
                
                await self._process_delivery(delivery_id)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Delivery worker {worker_name} error: {e}")
    
    async def _process_delivery(self, delivery_id: str):
        """Process a webhook delivery"""
        delivery = self.deliveries.get(delivery_id)
        if not delivery:
            return
        
        event = self.events.get(delivery.event_id)
        endpoint = self.endpoints.get(delivery.endpoint_id)
        
        if not event or not endpoint:
            logger.error(f"Missing event or endpoint for delivery {delivery_id}")
            return
        
        delivery.status = WebhookStatus.DELIVERING
        delivery.attempt += 1
        delivery.updated_at = datetime.utcnow()
        
        self.stats['deliveries_attempted'] += 1
        
        try:
            success = await self._deliver_webhook(delivery, event, endpoint)
            
            if success:
                delivery.status = WebhookStatus.DELIVERED
                delivery.delivered_at = datetime.utcnow()
                self.stats['deliveries_successful'] += 1
                logger.info(f"Webhook delivered successfully: {delivery_id}")
            else:
                await self._handle_delivery_failure(delivery, event, endpoint)
                
        except Exception as e:
            delivery.error_message = str(e)
            await self._handle_delivery_failure(delivery, event, endpoint)
        
        delivery.updated_at = datetime.utcnow()
    
    async def _deliver_webhook(
        self,
        delivery: WebhookDelivery,
        event: WebhookEvent,
        endpoint: WebhookEndpoint
    ) -> bool:
        """Deliver webhook to endpoint"""
        # Prepare payload
        webhook_payload = {
            "id": event.id,
            "event": event.event_type,
            "timestamp": event.created_at.isoformat(),
            "data": event.payload
        }
        
        payload_str = json.dumps(webhook_payload, separators=(',', ':'))
        
        # Sign payload
        signature = self.signer.sign_payload(payload_str, endpoint.secret)
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-ID": event.id,
            "X-Webhook-Timestamp": str(int(event.created_at.timestamp())),
            "User-Agent": "WebhookEngine/1.0"
        }
        headers.update(endpoint.headers)
        
        # Make HTTP request
        timeout = aiohttp.ClientTimeout(total=endpoint.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(
                    endpoint.url,
                    data=payload_str,
                    headers=headers
                ) as response:
                    delivery.response_status = response.status
                    delivery.response_body = await response.text()
                    
                    # Consider 2xx status codes as success
                    success = 200 <= response.status < 300
                    
                    if not success:
                        delivery.error_message = f"HTTP {response.status}: {delivery.response_body}"
                    
                    return success
                    
            except asyncio.TimeoutError:
                delivery.error_message = f"Request timeout after {endpoint.timeout}s"
                return False
            except Exception as e:
                delivery.error_message = f"Request failed: {str(e)}"
                return False
    
    async def _handle_delivery_failure(
        self,
        delivery: WebhookDelivery,
        event: WebhookEvent,
        endpoint: WebhookEndpoint
    ):
        """Handle failed webhook delivery"""
        if delivery.attempt < delivery.max_attempts:
            # Schedule retry
            delivery.status = WebhookStatus.PENDING
            delivery.next_retry_at = self.retry_policy.get_next_retry_time(delivery.attempt)
            logger.info(
                f"Webhook delivery {delivery.id} failed, retry {delivery.attempt}/{delivery.max_attempts} "
                f"scheduled for {delivery.next_retry_at}"
            )
        else:
            # Send to DLQ
            delivery.status = WebhookStatus.DLQ
            await self.dlq.send_to_dlq(delivery, event, endpoint)
            self.stats['deliveries_failed'] += 1
            self.stats['messages_in_dlq'] += 1
    
    async def _retry_scheduler(self):
        """Scheduler that processes retry attempts"""
        logger.info("Retry scheduler started")
        
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Find deliveries ready for retry
                for delivery in self.deliveries.values():
                    if (delivery.status == WebhookStatus.PENDING and 
                        delivery.next_retry_at and 
                        delivery.next_retry_at <= current_time):
                        
                        # Reset retry time and queue for delivery
                        delivery.next_retry_at = None
                        await self.delivery_queue.put(delivery.id)
                
                # Sleep for a short interval
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Retry scheduler error: {e}")
    
    async def get_delivery_status(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        """Get delivery status"""
        delivery = self.deliveries.get(delivery_id)
        if not delivery:
            return None
        
        return {
            "id": delivery.id,
            "event_id": delivery.event_id,
            "endpoint_id": delivery.endpoint_id,
            "status": delivery.status.value,
            "attempt": delivery.attempt,
            "max_attempts": delivery.max_attempts,
            "next_retry_at": delivery.next_retry_at.isoformat() if delivery.next_retry_at else None,
            "response_status": delivery.response_status,
            "error_message": delivery.error_message,
            "delivered_at": delivery.delivered_at.isoformat() if delivery.delivered_at else None,
            "created_at": delivery.created_at.isoformat(),
            "updated_at": delivery.updated_at.isoformat()
        }
    
    async def get_endpoint_deliveries(
        self,
        endpoint_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get deliveries for an endpoint"""
        deliveries = []
        
        for delivery in self.deliveries.values():
            if delivery.endpoint_id == endpoint_id:
                if status is None or delivery.status.value == status:
                    delivery_info = await self.get_delivery_status(delivery.id)
                    if delivery_info:
                        deliveries.append(delivery_info)
        
        # Sort by created_at desc and limit
        deliveries.sort(key=lambda x: x['created_at'], reverse=True)
        return deliveries[:limit]
    
    async def replay_webhook(self, delivery_id: str) -> bool:
        """Replay a failed webhook"""
        delivery = self.deliveries.get(delivery_id)
        if not delivery or delivery.status != WebhookStatus.FAILED:
            return False
        
        # Reset delivery for retry
        delivery.status = WebhookStatus.PENDING
        delivery.attempt = 0
        delivery.next_retry_at = None
        delivery.error_message = None
        delivery.response_status = None
        delivery.response_body = None
        
        # Queue for delivery
        await self.delivery_queue.put(delivery_id)
        
        logger.info(f"Webhook {delivery_id} queued for replay")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get webhook engine statistics"""
        return {
            "events_received": self.stats['events_received'],
            "deliveries_attempted": self.stats['deliveries_attempted'],
            "deliveries_successful": self.stats['deliveries_successful'],
            "deliveries_failed": self.stats['deliveries_failed'],
            "messages_in_dlq": self.stats['messages_in_dlq'],
            "active_endpoints": len([e for e in self.endpoints.values() if e.active]),
            "total_endpoints": len(self.endpoints),
            "pending_deliveries": len([d for d in self.deliveries.values() if d.status == WebhookStatus.PENDING]),
            "queue_size": self.delivery_queue.qsize()
        }