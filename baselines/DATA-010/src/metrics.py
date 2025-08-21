"""Metrics collection and monitoring for stream processing"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field

try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time"""
    timestamp: datetime
    events_processed: int
    events_per_second: float
    windows_active: int
    windows_completed: int
    processing_latency_ms: float
    memory_usage_mb: float
    pipeline_stats: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and exposes stream processing metrics"""
    
    def __init__(self, config):
        self.config = config
        self.start_time = datetime.utcnow()
        
        # In-memory counters
        self.events_processed = 0
        self.events_failed = 0
        self.windows_created = 0
        self.windows_completed = 0
        self.windows_expired = 0
        
        # Performance tracking
        self.processing_times = deque(maxlen=1000)  # Last 1000 processing times
        self.throughput_history = deque(maxlen=300)  # 5 minutes of throughput data (1 per second)
        
        # Pipeline-specific metrics
        self.pipeline_metrics = defaultdict(lambda: {
            "events_processed": 0,
            "events_failed": 0,
            "windows_active": 0,
            "last_activity": None
        })
        
        # Prometheus metrics (if available)
        self.prometheus_registry = None
        self.prometheus_metrics = {}
        
        if PROMETHEUS_AVAILABLE:
            self._setup_prometheus_metrics()
        
        # Background tasks
        self.running = False
        self.metrics_task = None
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        self.prometheus_registry = CollectorRegistry()
        
        # Counters
        self.prometheus_metrics['events_processed_total'] = Counter(
            'stream_events_processed_total',
            'Total number of events processed',
            ['pipeline_id'],
            registry=self.prometheus_registry
        )
        
        self.prometheus_metrics['events_failed_total'] = Counter(
            'stream_events_failed_total',
            'Total number of events that failed processing',
            ['pipeline_id', 'error_type'],
            registry=self.prometheus_registry
        )
        
        self.prometheus_metrics['windows_created_total'] = Counter(
            'stream_windows_created_total',
            'Total number of windows created',
            ['pipeline_id', 'window_type'],
            registry=self.prometheus_registry
        )
        
        self.prometheus_metrics['windows_completed_total'] = Counter(
            'stream_windows_completed_total',
            'Total number of windows completed',
            ['pipeline_id', 'window_type'],
            registry=self.prometheus_registry
        )
        
        # Histograms
        self.prometheus_metrics['processing_duration_seconds'] = Histogram(
            'stream_processing_duration_seconds',
            'Event processing duration in seconds',
            ['pipeline_id'],
            registry=self.prometheus_registry,
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.prometheus_metrics['window_size_events'] = Histogram(
            'stream_window_size_events',
            'Number of events in completed windows',
            ['pipeline_id', 'window_type'],
            registry=self.prometheus_registry,
            buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
        )
        
        # Gauges
        self.prometheus_metrics['active_windows'] = Gauge(
            'stream_active_windows',
            'Current number of active windows',
            ['pipeline_id'],
            registry=self.prometheus_registry
        )
        
        self.prometheus_metrics['events_per_second'] = Gauge(
            'stream_events_per_second',
            'Current events per second rate',
            ['pipeline_id'],
            registry=self.prometheus_registry
        )
        
        self.prometheus_metrics['watermark_lag_seconds'] = Gauge(
            'stream_watermark_lag_seconds',
            'Current watermark lag in seconds',
            ['partition'],
            registry=self.prometheus_registry
        )
    
    async def start(self):
        """Start metrics collection"""
        self.running = True
        
        # Start Prometheus HTTP server if available
        if PROMETHEUS_AVAILABLE:
            start_http_server(
                self.config.metrics_port,
                registry=self.prometheus_registry
            )
            logger.info(f"Prometheus metrics server started on port {self.config.metrics_port}")
        
        # Start background metrics collection
        self.metrics_task = asyncio.create_task(self._collect_metrics_loop())
        logger.info("Metrics collector started")
    
    async def stop(self):
        """Stop metrics collection"""
        self.running = False
        
        if self.metrics_task:
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Metrics collector stopped")
    
    def record_event_processed(self, pipeline_id: str, processing_time_ms: float):
        """Record an event processing"""
        self.events_processed += 1
        self.pipeline_metrics[pipeline_id]["events_processed"] += 1
        self.pipeline_metrics[pipeline_id]["last_activity"] = datetime.utcnow()
        
        # Track processing time
        self.processing_times.append(processing_time_ms)
        
        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            self.prometheus_metrics['events_processed_total'].labels(
                pipeline_id=pipeline_id
            ).inc()
            
            self.prometheus_metrics['processing_duration_seconds'].labels(
                pipeline_id=pipeline_id
            ).observe(processing_time_ms / 1000.0)
    
    def record_event_failed(self, pipeline_id: str, error_type: str = "unknown"):
        """Record a failed event"""
        self.events_failed += 1
        self.pipeline_metrics[pipeline_id]["events_failed"] += 1
        
        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            self.prometheus_metrics['events_failed_total'].labels(
                pipeline_id=pipeline_id,
                error_type=error_type
            ).inc()
    
    def record_window_created(self, pipeline_id: str, window_type: str):
        """Record window creation"""
        self.windows_created += 1
        
        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            self.prometheus_metrics['windows_created_total'].labels(
                pipeline_id=pipeline_id,
                window_type=window_type
            ).inc()
    
    def record_window_completed(self, pipeline_id: str, window_type: str, event_count: int):
        """Record window completion"""
        self.windows_completed += 1
        
        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            self.prometheus_metrics['windows_completed_total'].labels(
                pipeline_id=pipeline_id,
                window_type=window_type
            ).inc()
            
            self.prometheus_metrics['window_size_events'].labels(
                pipeline_id=pipeline_id,
                window_type=window_type
            ).observe(event_count)
    
    def update_active_windows(self, pipeline_id: str, count: int):
        """Update active window count"""
        self.pipeline_metrics[pipeline_id]["windows_active"] = count
        
        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            self.prometheus_metrics['active_windows'].labels(
                pipeline_id=pipeline_id
            ).set(count)
    
    def update_watermark_lag(self, partition: str, lag_seconds: float):
        """Update watermark lag"""
        if PROMETHEUS_AVAILABLE:
            self.prometheus_metrics['watermark_lag_seconds'].labels(
                partition=partition
            ).set(lag_seconds)
    
    async def _collect_metrics_loop(self):
        """Background loop to collect periodic metrics"""
        last_event_count = 0
        
        try:
            while self.running:
                current_time = datetime.utcnow()
                
                # Calculate throughput
                current_events = self.events_processed
                events_this_second = current_events - last_event_count
                last_event_count = current_events
                
                # Store throughput history
                self.throughput_history.append({
                    "timestamp": current_time,
                    "events_per_second": events_this_second
                })
                
                # Update Prometheus gauges
                if PROMETHEUS_AVAILABLE:
                    for pipeline_id in self.pipeline_metrics:
                        self.prometheus_metrics['events_per_second'].labels(
                            pipeline_id=pipeline_id
                        ).set(events_this_second)
                
                await asyncio.sleep(1.0)
                
        except asyncio.CancelledError:
            logger.info("Metrics collection loop stopped")
    
    def get_snapshot(self) -> MetricSnapshot:
        """Get current metrics snapshot"""
        current_time = datetime.utcnow()
        uptime = (current_time - self.start_time).total_seconds()
        
        # Calculate current events per second
        current_eps = 0
        if self.throughput_history:
            recent_throughput = list(self.throughput_history)[-60:]  # Last minute
            if recent_throughput:
                current_eps = sum(t["events_per_second"] for t in recent_throughput) / len(recent_throughput)
        
        # Calculate average processing latency
        avg_latency = 0
        if self.processing_times:
            avg_latency = sum(self.processing_times) / len(self.processing_times)
        
        # Estimate memory usage (simplified)
        memory_usage = len(self.processing_times) * 8 + len(self.throughput_history) * 64  # bytes
        memory_usage_mb = memory_usage / (1024 * 1024)
        
        return MetricSnapshot(
            timestamp=current_time,
            events_processed=self.events_processed,
            events_per_second=current_eps,
            windows_active=sum(pm["windows_active"] for pm in self.pipeline_metrics.values()),
            windows_completed=self.windows_completed,
            processing_latency_ms=avg_latency,
            memory_usage_mb=memory_usage_mb,
            pipeline_stats=dict(self.pipeline_metrics)
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        snapshot = self.get_snapshot()
        uptime = (snapshot.timestamp - self.start_time).total_seconds()
        
        # Calculate throughput statistics
        throughput_values = [t["events_per_second"] for t in self.throughput_history]
        throughput_stats = {}
        if throughput_values:
            throughput_stats = {
                "min": min(throughput_values),
                "max": max(throughput_values),
                "avg": sum(throughput_values) / len(throughput_values)
            }
        
        # Calculate latency statistics
        latency_stats = {}
        if self.processing_times:
            sorted_times = sorted(self.processing_times)
            latency_stats = {
                "min": min(sorted_times),
                "max": max(sorted_times),
                "avg": sum(sorted_times) / len(sorted_times),
                "p50": sorted_times[len(sorted_times) // 2],
                "p95": sorted_times[int(len(sorted_times) * 0.95)],
                "p99": sorted_times[int(len(sorted_times) * 0.99)]
            }
        
        return {
            "uptime_seconds": uptime,
            "events": {
                "processed": self.events_processed,
                "failed": self.events_failed,
                "success_rate": (
                    (self.events_processed / (self.events_processed + self.events_failed))
                    if (self.events_processed + self.events_failed) > 0 else 0
                )
            },
            "windows": {
                "created": self.windows_created,
                "completed": self.windows_completed,
                "active": snapshot.windows_active,
                "expired": self.windows_expired
            },
            "throughput": throughput_stats,
            "latency_ms": latency_stats,
            "memory_usage_mb": snapshot.memory_usage_mb,
            "pipelines": snapshot.pipeline_stats,
            "prometheus_available": PROMETHEUS_AVAILABLE
        }