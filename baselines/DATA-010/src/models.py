"""Data models for stream processing"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass
from uuid import UUID, uuid4


class WindowType(Enum):
    """Window types for stream processing"""
    TUMBLING = "tumbling"
    SLIDING = "sliding"
    SESSION = "session"


@dataclass
class StreamEvent:
    """Stream event representation"""
    data: Any
    event_time: datetime
    processing_time: datetime
    partition_key: str
    source: str
    partition: int = 0
    offset: int = 0
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class Window:
    """Window representation"""
    window_id: str
    window_type: WindowType
    start_time: datetime
    end_time: datetime
    partition_key: str
    
    def contains(self, event_time: datetime) -> bool:
        """Check if event time falls within window"""
        return self.start_time <= event_time < self.end_time
    
    def is_expired(self, watermark: datetime) -> bool:
        """Check if window is expired based on watermark"""
        return watermark >= self.end_time


@dataclass
class ProcessingResult:
    """Result of stream processing"""
    window_id: str
    window_start: datetime
    window_end: datetime
    data: Any
    event_time: datetime
    processing_time: datetime
    result_id: UUID = None
    
    def __post_init__(self):
        if self.result_id is None:
            self.result_id = uuid4()


@dataclass
class WindowConfig:
    """Window configuration"""
    window_type: WindowType
    size_ms: int
    slide_ms: Optional[int] = None  # For sliding windows
    gap_ms: Optional[int] = None    # For session windows
    allowed_lateness_ms: int = 5000  # 5 seconds default
    
    def __post_init__(self):
        if self.window_type == WindowType.SLIDING and self.slide_ms is None:
            raise ValueError("Sliding windows require slide_ms")
        if self.window_type == WindowType.SESSION and self.gap_ms is None:
            raise ValueError("Session windows require gap_ms")


@dataclass
class Watermark:
    """Watermark for handling late data"""
    timestamp: datetime
    partition_key: str
    source: str