"""Core stream processing engine with windowing"""
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from models import StreamEvent, WindowType, Window, ProcessingResult
from windowing import WindowManager
from state_store import StateStore
from watermark_tracker import WatermarkTracker
from config import StreamConfig
from sources import EventSource
from sinks import EventSink
from metrics import MetricsCollector

logger = logging.getLogger(__name__)


@dataclass
class Pipeline:
    """Stream processing pipeline"""
    source: EventSource
    processors: List[Callable] = field(default_factory=list)
    sink: EventSink = None
    parallelism: int = 1


class StreamProcessor:
    """Real-time stream processor with windowing and state management"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.pipelines: List[Pipeline] = []
        self.window_manager = WindowManager(config)
        self.state_store = StateStore(config)
        self.watermark_tracker = WatermarkTracker(config)
        
        # Processing control
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        # Backpressure control
        self.input_queue = asyncio.Queue(maxsize=config.queue_size)
        self.output_queue = asyncio.Queue(maxsize=config.queue_size)
        
        # State for exactly-once processing
        self.processed_offsets: Dict[str, int] = {}
        self.checkpoint_interval = config.checkpoint_interval
        self.last_checkpoint = time.time()
        
    async def start(self):
        """Start the stream processor"""
        logger.info("Starting stream processor")
        
        # Initialize components
        await self.state_store.initialize()
        await self.watermark_tracker.start()
        
        # Load checkpoints
        await self._load_checkpoint()
        
        # Start processing tasks
        self.running = True
        
        # Start input ingestion
        self.tasks.append(
            asyncio.create_task(self._input_ingestion_loop())
        )
        
        # Start processing workers
        for i in range(self.config.parallelism):
            self.tasks.append(
                asyncio.create_task(self._processing_worker(f"worker-{i}"))
            )
        
        # Start window management
        self.tasks.append(
            asyncio.create_task(self._window_management_loop())
        )
        
        # Start checkpoint task
        self.tasks.append(
            asyncio.create_task(self._checkpoint_loop())
        )
        
        # Start output delivery
        self.tasks.append(
            asyncio.create_task(self._output_delivery_loop())
        )
        
        logger.info(f"Started {len(self.tasks)} processing tasks")
    
    async def stop(self):
        """Stop the stream processor"""
        logger.info("Stopping stream processor")
        
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Final checkpoint
        await self._save_checkpoint()
        
        # Cleanup components
        await self.watermark_tracker.stop()
        await self.state_store.close()
        
        logger.info("Stream processor stopped")
    
    async def _input_ingestion_loop(self):
        """Ingest events from sources"""
        try:
            while self.running:
                for pipeline in self.pipelines:
                    try:
                        # Read batch of events
                        events = await pipeline.source.read_batch()
                        
                        for event in events:
                            # Check for backpressure
                            if self.input_queue.full():
                                backpressure_events.inc()
                                await asyncio.sleep(0.01)  # Brief backoff
                            
                            await self.input_queue.put((pipeline, event))
                            
                    except asyncio.TimeoutError:
                        # No events available, continue
                        continue
                    except Exception as e:
                        logger.error(f"Input ingestion error: {e}")
                
                await asyncio.sleep(0.001)  # Small delay to prevent busy waiting
                
        except asyncio.CancelledError:
            logger.info("Input ingestion stopped")
    
    async def _processing_worker(self, worker_id: str):
        """Process events with windowing and state"""
        try:
            while self.running:
                try:
                    # Get event from input queue
                    pipeline, event = await asyncio.wait_for(
                        self.input_queue.get(),
                        timeout=1.0
                    )
                    
                    start_time = time.time()
                    
                    # Process event
                    result = await self._process_event(pipeline, event)
                    
                    if result:
                        # Put result in output queue
                        await self.output_queue.put(result)
                    
                    # Update metrics
                    processing_time = time.time() - start_time
                    processing_latency.observe(processing_time)
                    events_processed_total.inc()
                    
                    # Update watermark
                    await self.watermark_tracker.update_watermark(
                        event.partition_key,
                        event.event_time
                    )
                    
                except asyncio.TimeoutError:
                    # No events available, continue
                    continue
                    
        except asyncio.CancelledError:
            logger.info(f"Processing worker {worker_id} stopped")
    
    async def _process_event(
        self,
        pipeline: Pipeline,
        event: StreamEvent
    ) -> Optional[ProcessingResult]:
        """Process a single event"""
        try:
            # Check if already processed (exactly-once semantics)
            offset_key = f"{event.source}:{event.partition}:{event.offset}"
            if offset_key in self.processed_offsets:
                return None
            
            # Apply processors in pipeline
            current_data = event.data
            for processor in pipeline.processors:
                current_data = await processor(current_data, event)
                if current_data is None:
                    return None  # Event filtered out
            
            # Apply windowing
            windows = await self.window_manager.assign_to_windows(event)
            
            results = []
            for window in windows:
                # Update window state
                state_key = f"window:{window.window_id}"
                current_state = await self.state_store.get(state_key) or {}
                
                # Apply aggregation
                new_state = await self._apply_aggregation(
                    current_state,
                    current_data,
                    event
                )
                
                # Save updated state
                await self.state_store.put(state_key, new_state)
                
                # Check if window should be emitted
                watermark = await self.watermark_tracker.get_watermark(
                    event.partition_key
                )
                
                if self._should_emit_window(window, watermark):
                    result = ProcessingResult(
                        window_id=window.window_id,
                        window_start=window.start_time,
                        window_end=window.end_time,
                        data=new_state,
                        event_time=event.event_time,
                        processing_time=datetime.utcnow()
                    )
                    results.append(result)
            
            # Mark as processed
            self.processed_offsets[offset_key] = event.offset
            
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Event processing error: {e}")
            return None
    
    async def _apply_aggregation(
        self,
        current_state: Dict[str, Any],
        data: Any,
        event: StreamEvent
    ) -> Dict[str, Any]:
        """Apply aggregation function to window state"""
        # Initialize state if empty
        if not current_state:
            current_state = {
                "count": 0,
                "sum": 0,
                "min": float('inf'),
                "max": float('-inf'),
                "values": []
            }
        
        # Extract numeric value for aggregation
        value = data.get("value", 0) if isinstance(data, dict) else data
        if not isinstance(value, (int, float)):
            value = 1  # Count operation
        
        # Update aggregations
        current_state["count"] += 1
        current_state["sum"] += value
        current_state["min"] = min(current_state["min"], value)
        current_state["max"] = max(current_state["max"], value)
        current_state["values"].append(value)
        
        # Keep only recent values (for memory efficiency)
        if len(current_state["values"]) > 1000:
            current_state["values"] = current_state["values"][-1000:]
        
        # Calculate derived metrics
        current_state["avg"] = current_state["sum"] / current_state["count"]
        current_state["last_updated"] = event.event_time.isoformat()
        
        return current_state
    
    def _should_emit_window(self, window: Window, watermark: datetime) -> bool:
        """Check if window should be emitted based on watermark"""
        if not watermark:
            return False
        
        # Emit window if watermark has passed window end time
        return watermark >= window.end_time
    
    async def _window_management_loop(self):
        """Manage window lifecycle and cleanup"""
        try:
            while self.running:
                # Clean up expired windows
                await self.window_manager.cleanup_expired_windows()
                
                # Update metrics
                current_watermark = await self.watermark_tracker.get_global_watermark()
                if current_watermark:
                    lag = (datetime.utcnow() - current_watermark).total_seconds()
                    watermark_lag.set(lag)
                
                await asyncio.sleep(self.config.window_cleanup_interval)
                
        except asyncio.CancelledError:
            logger.info("Window management stopped")
    
    async def _output_delivery_loop(self):
        """Deliver processed results to sinks"""
        try:
            while self.running:
                try:
                    # Get result from output queue
                    result = await asyncio.wait_for(
                        self.output_queue.get(),
                        timeout=1.0
                    )
                    
                    # Deliver to all sinks
                    for pipeline in self.pipelines:
                        if pipeline.sink:
                            await pipeline.sink.write(result)
                    
                except asyncio.TimeoutError:
                    continue
                    
        except asyncio.CancelledError:
            logger.info("Output delivery stopped")
    
    async def _checkpoint_loop(self):
        """Periodic checkpointing for fault tolerance"""
        try:
            while self.running:
                await asyncio.sleep(self.checkpoint_interval)
                
                if time.time() - self.last_checkpoint >= self.checkpoint_interval:
                    await self._save_checkpoint()
                    
        except asyncio.CancelledError:
            logger.info("Checkpoint loop stopped")
    
    async def _save_checkpoint(self):
        """Save processing state for fault tolerance"""
        try:
            checkpoint_data = {
                "processed_offsets": self.processed_offsets,
                "watermarks": await self.watermark_tracker.get_all_watermarks(),
                "timestamp": time.time()
            }
            
            await self.state_store.put("checkpoint", checkpoint_data)
            self.last_checkpoint = time.time()
            
            logger.debug("Checkpoint saved")
            
        except Exception as e:
            logger.error(f"Checkpoint save error: {e}")
    
    async def _load_checkpoint(self):
        """Load processing state from checkpoint"""
        try:
            checkpoint_data = await self.state_store.get("checkpoint")
            if checkpoint_data:
                self.processed_offsets = checkpoint_data.get("processed_offsets", {})
                
                # Restore watermarks
                watermarks = checkpoint_data.get("watermarks", {})
                await self.watermark_tracker.restore_watermarks(watermarks)
                
                logger.info("Checkpoint loaded successfully")
            else:
                logger.info("No checkpoint found, starting fresh")
                
        except Exception as e:
            logger.error(f"Checkpoint load error: {e}")
    
    def add_pipeline(self, pipeline: Pipeline):
        """Add a processing pipeline"""
        self.pipelines.append(pipeline)
        logger.info(f"Added pipeline with {len(pipeline.processors)} processors")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        watermarks = await self.watermark_tracker.get_all_watermarks()
        
        return {
            "running": self.running,
            "pipelines": len(self.pipelines),
            "input_queue_size": self.input_queue.qsize(),
            "output_queue_size": self.output_queue.qsize(),
            "processed_offsets_count": len(self.processed_offsets),
            "watermarks": watermarks,
            "last_checkpoint": self.last_checkpoint
        }