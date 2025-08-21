"""Event sources for stream processing"""
import asyncio
import json
import logging
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any

from models import StreamEvent

logger = logging.getLogger(__name__)


class EventSource(ABC):
    """Abstract event source"""
    
    @abstractmethod
    async def read_batch(self, max_events: int = 100) -> List[StreamEvent]:
        """Read a batch of events"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close the source"""
        pass


class MockEventSource(EventSource):
    """Mock event source for testing"""
    
    def __init__(self, config, source_name: str = "mock"):
        self.config = config
        self.source_name = source_name
        self.event_counter = 0
        self.partition_counter = 0
        
    async def read_batch(self, max_events: int = 100) -> List[StreamEvent]:
        """Generate mock events"""
        events = []
        
        # Generate 1-10 events per batch
        batch_size = random.randint(1, min(10, max_events))
        
        for _ in range(batch_size):
            # Simulate some delay between events
            if events:
                await asyncio.sleep(0.01)
            
            event = self._generate_mock_event()
            events.append(event)
        
        return events
    
    def _generate_mock_event(self) -> StreamEvent:
        """Generate a mock event"""
        self.event_counter += 1
        
        # Generate event with some variety
        event_types = ["user_action", "sensor_reading", "transaction", "click"]
        event_type = random.choice(event_types)
        
        # Generate realistic event time (slightly in the past)
        event_time = datetime.utcnow() - timedelta(
            milliseconds=random.randint(0, 1000)
        )
        
        # Create partition key
        partition_key = f"partition_{self.partition_counter % 4}"
        self.partition_counter += 1
        
        # Generate data based on event type
        if event_type == "user_action":
            data = {
                "type": "user_action",
                "user_id": f"user_{random.randint(1, 1000)}",
                "action": random.choice(["login", "logout", "click", "view"]),
                "value": random.randint(1, 100)
            }
        elif event_type == "sensor_reading":
            data = {
                "type": "sensor_reading",
                "sensor_id": f"sensor_{random.randint(1, 50)}",
                "temperature": round(random.uniform(15.0, 35.0), 2),
                "humidity": round(random.uniform(30.0, 80.0), 2),
                "value": round(random.uniform(15.0, 35.0), 2)
            }
        elif event_type == "transaction":
            data = {
                "type": "transaction",
                "account_id": f"account_{random.randint(1, 500)}",
                "amount": round(random.uniform(1.0, 1000.0), 2),
                "currency": random.choice(["USD", "EUR", "GBP"]),
                "value": round(random.uniform(1.0, 1000.0), 2)
            }
        else:  # click
            data = {
                "type": "click",
                "page": random.choice(["/home", "/products", "/about", "/contact"]),
                "session_id": f"session_{random.randint(1, 200)}",
                "value": 1
            }
        
        return StreamEvent(
            data=data,
            event_time=event_time,
            processing_time=datetime.utcnow(),
            partition_key=partition_key,
            source=self.source_name,
            partition=hash(partition_key) % 4,
            offset=self.event_counter,
            headers={"source": self.source_name}
        )
    
    async def close(self):
        """Close mock source"""
        logger.info(f"Mock source {self.source_name} closed")


class FileEventSource(EventSource):
    """File-based event source"""
    
    def __init__(self, config, file_path: str):
        self.config = config
        self.file_path = file_path
        self.offset = 0
        self.events = []
        
    async def _load_events(self):
        """Load events from file"""
        try:
            with open(self.file_path, 'r') as f:
                for line_num, line in enumerate(f):
                    if line.strip():
                        data = json.loads(line)
                        event = StreamEvent(
                            data=data,
                            event_time=datetime.fromisoformat(
                                data.get("event_time", datetime.utcnow().isoformat())
                            ),
                            processing_time=datetime.utcnow(),
                            partition_key=data.get("partition_key", "default"),
                            source="file",
                            partition=0,
                            offset=line_num,
                            headers=data.get("headers", {})
                        )
                        self.events.append(event)
        except Exception as e:
            logger.error(f"Failed to load events from {self.file_path}: {e}")
    
    async def read_batch(self, max_events: int = 100) -> List[StreamEvent]:
        """Read batch from file"""
        if not self.events:
            await self._load_events()
        
        # Return batch from current offset
        start = self.offset
        end = min(start + max_events, len(self.events))
        
        batch = self.events[start:end]
        self.offset = end
        
        # Reset offset when reaching end (for continuous processing)
        if self.offset >= len(self.events):
            self.offset = 0
        
        return batch
    
    async def close(self):
        """Close file source"""
        logger.info(f"File source {self.file_path} closed")