"""Watermark tracking for handling late data"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class WatermarkTracker:
    """Tracks watermarks for handling late-arriving data"""
    
    def __init__(self, config):
        self.config = config
        self.watermarks: Dict[str, datetime] = {}
        self.partition_watermarks: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        self.watermark_delay = timedelta(seconds=config.watermark_delay_seconds)
        self.running = False
        self.update_task = None
        
    async def start(self):
        """Start watermark tracking"""
        self.running = True
        self.update_task = asyncio.create_task(self._watermark_update_loop())
        logger.info("Watermark tracker started")
    
    async def stop(self):
        """Stop watermark tracking"""
        self.running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        logger.info("Watermark tracker stopped")
    
    async def update_watermark(
        self,
        partition_key: str,
        event_time: datetime,
        source: str = "default"
    ):
        """Update watermark for a partition"""
        # Store per-source watermark
        if source not in self.partition_watermarks[partition_key]:
            self.partition_watermarks[partition_key][source] = event_time
        else:
            # Watermarks can only advance
            current = self.partition_watermarks[partition_key][source]
            self.partition_watermarks[partition_key][source] = max(current, event_time)
    
    async def get_watermark(self, partition_key: str) -> Optional[datetime]:
        """Get current watermark for a partition"""
        return self.watermarks.get(partition_key)
    
    async def get_global_watermark(self) -> Optional[datetime]:
        """Get global watermark (minimum across all partitions)"""
        if not self.watermarks:
            return None
        
        return min(self.watermarks.values())
    
    async def get_all_watermarks(self) -> Dict[str, datetime]:
        """Get all partition watermarks"""
        return self.watermarks.copy()
    
    async def restore_watermarks(self, watermarks: Dict[str, datetime]):
        """Restore watermarks from checkpoint"""
        for partition_key, watermark in watermarks.items():
            if isinstance(watermark, str):
                watermark = datetime.fromisoformat(watermark)
            self.watermarks[partition_key] = watermark
        
        logger.info(f"Restored {len(watermarks)} watermarks")
    
    async def _watermark_update_loop(self):
        """Periodically update watermarks"""
        try:
            while self.running:
                await self._calculate_watermarks()
                await asyncio.sleep(1.0)  # Update every second
                
        except asyncio.CancelledError:
            logger.info("Watermark update loop stopped")
    
    async def _calculate_watermarks(self):
        """Calculate watermarks based on event times and delay"""
        current_time = datetime.utcnow()
        
        for partition_key, source_watermarks in self.partition_watermarks.items():
            if source_watermarks:
                # Get minimum watermark across all sources for this partition
                min_event_time = min(source_watermarks.values())
                
                # Apply watermark delay to handle late data
                watermark = min_event_time - self.watermark_delay
                
                # Watermarks cannot go backwards
                if partition_key in self.watermarks:
                    watermark = max(watermark, self.watermarks[partition_key])
                
                # Don't advance watermark beyond current time
                watermark = min(watermark, current_time)
                
                self.watermarks[partition_key] = watermark
    
    def is_late(self, event_time: datetime, partition_key: str) -> bool:
        """Check if an event is late based on current watermark"""
        watermark = self.watermarks.get(partition_key)
        if not watermark:
            return False
        
        return event_time < watermark
    
    def get_stats(self) -> Dict[str, any]:
        """Get watermark tracking statistics"""
        stats = {
            "partition_count": len(self.watermarks),
            "watermark_delay_seconds": self.watermark_delay.total_seconds(),
            "running": self.running
        }
        
        if self.watermarks:
            current_time = datetime.utcnow()
            lags = [
                (current_time - wm).total_seconds()
                for wm in self.watermarks.values()
            ]
            
            stats.update({
                "min_lag_seconds": min(lags),
                "max_lag_seconds": max(lags),
                "avg_lag_seconds": sum(lags) / len(lags)
            })
        
        return stats