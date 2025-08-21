"""Windowing implementation for stream processing"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

from models import StreamEvent, Window, WindowType, WindowConfig

logger = logging.getLogger(__name__)


class WindowManager:
    """Manages different types of windows for stream processing"""
    
    def __init__(self, config):
        self.config = config
        self.window_configs: List[WindowConfig] = config.window_configs
        self.active_windows: Dict[str, Window] = {}
        self.session_windows: Dict[str, List[Window]] = defaultdict(list)
        
    async def assign_to_windows(self, event: StreamEvent) -> List[Window]:
        """Assign event to appropriate windows"""
        windows = []
        
        for window_config in self.window_configs:
            event_windows = await self._assign_to_window_type(
                event,
                window_config
            )
            windows.extend(event_windows)
        
        return windows
    
    async def _assign_to_window_type(
        self,
        event: StreamEvent,
        config: WindowConfig
    ) -> List[Window]:
        """Assign event to specific window type"""
        if config.window_type == WindowType.TUMBLING:
            return await self._assign_to_tumbling_window(event, config)
        elif config.window_type == WindowType.SLIDING:
            return await self._assign_to_sliding_windows(event, config)
        elif config.window_type == WindowType.SESSION:
            return await self._assign_to_session_window(event, config)
        else:
            raise ValueError(f"Unsupported window type: {config.window_type}")
    
    async def _assign_to_tumbling_window(
        self,
        event: StreamEvent,
        config: WindowConfig
    ) -> List[Window]:
        """Assign event to tumbling window"""
        # Calculate window boundaries
        window_size = timedelta(milliseconds=config.size_ms)
        
        # Align to window boundaries
        event_ts = event.event_time.timestamp() * 1000  # Convert to milliseconds
        window_start_ms = (event_ts // config.size_ms) * config.size_ms
        
        window_start = datetime.fromtimestamp(window_start_ms / 1000)
        window_end = window_start + window_size
        
        window_id = f"tumbling_{event.partition_key}_{window_start_ms}"
        
        window = Window(
            window_id=window_id,
            window_type=WindowType.TUMBLING,
            start_time=window_start,
            end_time=window_end,
            partition_key=event.partition_key
        )
        
        self.active_windows[window_id] = window
        return [window]
    
    async def _assign_to_sliding_windows(
        self,
        event: StreamEvent,
        config: WindowConfig
    ) -> List[Window]:
        """Assign event to sliding windows"""
        windows = []
        
        window_size = timedelta(milliseconds=config.size_ms)
        slide_size = timedelta(milliseconds=config.slide_ms)
        
        event_ts = event.event_time.timestamp() * 1000
        
        # Calculate how many windows this event belongs to
        num_windows = config.size_ms // config.slide_ms
        
        for i in range(num_windows):
            # Calculate window start for this slide
            slide_offset = i * config.slide_ms
            window_start_ms = ((event_ts - slide_offset) // config.slide_ms) * config.slide_ms + slide_offset
            
            window_start = datetime.fromtimestamp(window_start_ms / 1000)
            window_end = window_start + window_size
            
            # Check if event falls within this window
            if window_start <= event.event_time < window_end:
                window_id = f"sliding_{event.partition_key}_{window_start_ms}"
                
                window = Window(
                    window_id=window_id,
                    window_type=WindowType.SLIDING,
                    start_time=window_start,
                    end_time=window_end,
                    partition_key=event.partition_key
                )
                
                self.active_windows[window_id] = window
                windows.append(window)
        
        return windows
    
    async def _assign_to_session_window(
        self,
        event: StreamEvent,
        config: WindowConfig
    ) -> List[Window]:
        """Assign event to session window"""
        partition_sessions = self.session_windows[event.partition_key]
        gap = timedelta(milliseconds=config.gap_ms)
        
        # Find existing session window that this event extends
        for window in partition_sessions:
            # Check if event is within gap of window end
            if event.event_time <= window.end_time + gap:
                # Extend the session window
                window.end_time = max(window.end_time, event.event_time + gap)
                return [window]
        
        # Create new session window
        window_start = event.event_time
        window_end = event.event_time + gap
        window_id = f"session_{event.partition_key}_{int(window_start.timestamp() * 1000)}"
        
        window = Window(
            window_id=window_id,
            window_type=WindowType.SESSION,
            start_time=window_start,
            end_time=window_end,
            partition_key=event.partition_key
        )
        
        partition_sessions.append(window)
        self.active_windows[window_id] = window
        
        return [window]
    
    async def cleanup_expired_windows(self):
        """Remove expired windows to free memory"""
        current_time = datetime.utcnow()
        expired_windows = []
        
        for window_id, window in self.active_windows.items():
            # Consider window expired if it's been closed for some time
            if current_time > window.end_time + timedelta(minutes=5):
                expired_windows.append(window_id)
        
        for window_id in expired_windows:
            del self.active_windows[window_id]
            
            # Also remove from session windows
            for partition_key, sessions in self.session_windows.items():
                self.session_windows[partition_key] = [
                    w for w in sessions if w.window_id != window_id
                ]
        
        if expired_windows:
            logger.debug(f"Cleaned up {len(expired_windows)} expired windows")
    
    def get_active_windows_count(self) -> int:
        """Get count of active windows"""
        return len(self.active_windows)
    
    def get_window_by_id(self, window_id: str) -> Optional[Window]:
        """Get window by ID"""
        return self.active_windows.get(window_id)