"""Event sinks for stream processing"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path

from models import ProcessingResult

logger = logging.getLogger(__name__)


class EventSink(ABC):
    """Abstract event sink"""
    
    @abstractmethod
    async def write(self, result: ProcessingResult):
        """Write processing result"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close the sink"""
        pass


class ConsoleSink(EventSink):
    """Console output sink for testing"""
    
    def __init__(self, config):
        self.config = config
        self.write_count = 0
        
    async def write(self, result: ProcessingResult):
        """Write result to console"""
        self.write_count += 1
        
        # Format output nicely
        output = {
            "window_id": result.window_id,
            "window_start": result.window_start.isoformat(),
            "window_end": result.window_end.isoformat(),
            "data": result.data,
            "processing_time": result.processing_time.isoformat()
        }
        
        print(f"RESULT #{self.write_count}: {json.dumps(output, indent=2)}")
    
    async def close(self):
        """Close console sink"""
        logger.info(f"Console sink closed, wrote {self.write_count} results")


class FileSink(EventSink):
    """File output sink"""
    
    def __init__(self, config, file_path: str):
        self.config = config
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.write_count = 0
        self.file_handle = None
        
    async def write(self, result: ProcessingResult):
        """Write result to file"""
        if not self.file_handle:
            self.file_handle = open(self.file_path, 'w')
        
        # Convert result to JSON
        output = {
            "window_id": result.window_id,
            "window_start": result.window_start.isoformat(),
            "window_end": result.window_end.isoformat(),
            "data": result.data,
            "event_time": result.event_time.isoformat(),
            "processing_time": result.processing_time.isoformat(),
            "result_id": str(result.result_id)
        }
        
        # Write as JSON lines
        self.file_handle.write(json.dumps(output) + "\n")
        self.file_handle.flush()
        
        self.write_count += 1
    
    async def close(self):
        """Close file sink"""
        if self.file_handle:
            self.file_handle.close()
        
        logger.info(f"File sink closed, wrote {self.write_count} results to {self.file_path}")


class MetricsSink(EventSink):
    """Metrics collection sink"""
    
    def __init__(self, config):
        self.config = config
        self.write_count = 0
        self.metrics = {
            "total_results": 0,
            "windows_processed": set(),
            "latest_result_time": None
        }
        
    async def write(self, result: ProcessingResult):
        """Collect metrics from result"""
        self.write_count += 1
        self.metrics["total_results"] += 1
        self.metrics["windows_processed"].add(result.window_id)
        self.metrics["latest_result_time"] = result.processing_time
        
        # Log summary periodically
        if self.write_count % 100 == 0:
            logger.info(f"Processed {self.write_count} results, "
                       f"{len(self.metrics['windows_processed'])} unique windows")
    
    async def close(self):
        """Close metrics sink"""
        logger.info(f"Metrics sink closed: {self.get_metrics()}")
    
    def get_metrics(self) -> dict:
        """Get collected metrics"""
        return {
            "total_results": self.metrics["total_results"],
            "unique_windows": len(self.metrics["windows_processed"]),
            "latest_result_time": self.metrics["latest_result_time"].isoformat() 
                if self.metrics["latest_result_time"] else None
        }