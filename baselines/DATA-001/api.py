#!/usr/bin/env python3
"""
DATA-001: Log Aggregation Pipeline - HTTP API Server
Provides REST API for log submission and queries.
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import time
import re
from app import LogPipeline, LogEntry

# Create FastAPI app
app = FastAPI(
    title="Log Aggregation API",
    description="Real-time log aggregation and query API",
    version="1.0.0"
)

# Initialize pipeline
pipeline = LogPipeline()


class LogSubmission(BaseModel):
    """Log submission model."""
    timestamp: Optional[float] = Field(None, description="Unix timestamp")
    source: Optional[str] = Field("http", description="Log source")
    level: Optional[str] = Field("INFO", description="Log level")
    message: str = Field(..., description="Log message")
    fields: Optional[Dict[str, Any]] = Field({}, description="Additional fields")


class LogQuery(BaseModel):
    """Log query model."""
    start_time: Optional[str] = Field(None, description="Start time (ISO format or relative)")
    end_time: Optional[str] = Field(None, description="End time (ISO format or relative)")
    level: Optional[str] = Field(None, description="Filter by log level")
    source: Optional[str] = Field(None, description="Filter by source")
    search: Optional[str] = Field(None, description="Search in message")
    limit: int = Field(100, ge=1, le=10000, description="Max results")


class AggregationQuery(BaseModel):
    """Aggregation query model."""
    group_by: str = Field(..., description="Field to group by")
    time_range: str = Field("1h", description="Time range (e.g., 1h, 24h, 7d)")
    operation: str = Field("count", description="Aggregation operation")


class AlertRule(BaseModel):
    """Alert rule model."""
    name: str = Field(..., description="Rule name")
    type: str = Field(..., description="Rule type (threshold, pattern, anomaly)")
    field: Optional[str] = Field(None, description="Field to check (for threshold)")
    operator: Optional[str] = Field(None, description="Comparison operator")
    value: Optional[float] = Field(None, description="Threshold value")
    pattern: Optional[str] = Field(None, description="Regex pattern")
    threshold: Optional[float] = Field(None, description="Anomaly threshold")


@app.post("/logs", response_model=Dict[str, str])
async def submit_log(log: LogSubmission):
    """Submit a log entry via HTTP."""
    try:
        # Create log entry
        entry = LogEntry(
            timestamp=log.timestamp or time.time(),
            source=log.source,
            level=log.level.upper(),
            message=log.message,
            fields=log.fields,
            raw=json.dumps(log.dict())
        )
        
        # Process through pipeline
        pipeline.process_log(entry.raw, entry.source)
        
        return {"status": "accepted", "timestamp": str(entry.timestamp)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/logs/batch", response_model=Dict[str, Any])
async def submit_logs_batch(logs: List[LogSubmission]):
    """Submit multiple log entries."""
    try:
        accepted = 0
        errors = []
        
        for log in logs:
            try:
                entry = LogEntry(
                    timestamp=log.timestamp or time.time(),
                    source=log.source,
                    level=log.level.upper(),
                    message=log.message,
                    fields=log.fields,
                    raw=json.dumps(log.dict())
                )
                pipeline.process_log(entry.raw, entry.source)
                accepted += 1
            except Exception as e:
                errors.append(str(e))
        
        return {
            "status": "processed",
            "accepted": accepted,
            "errors": len(errors),
            "error_details": errors[:10]  # Limit error details
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs/query", response_model=List[Dict])
async def query_logs(
    start_time: Optional[str] = Query(None, description="Start time"),
    end_time: Optional[str] = Query(None, description="End time"),
    level: Optional[str] = Query(None, description="Log level filter"),
    source: Optional[str] = Query(None, description="Source filter"),
    search: Optional[str] = Query(None, description="Search text"),
    limit: int = Query(100, ge=1, le=10000, description="Max results")
):
    """Query stored logs."""
    try:
        # Parse time parameters
        start_ts = parse_time(start_time) if start_time else None
        end_ts = parse_time(end_time) if end_time else None
        
        # Query storage
        results = pipeline.storage.query(
            start_time=start_ts,
            end_time=end_ts,
            level=level.upper() if level else None,
            source=source,
            search=search,
            limit=limit
        )
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/logs/aggregate", response_model=Dict[str, Any])
async def aggregate_logs(query: AggregationQuery):
    """Perform aggregation queries on logs."""
    try:
        # Parse time range
        end_time = time.time()
        start_time = end_time - parse_duration(query.time_range)
        
        # Query logs
        logs = pipeline.storage.query(
            start_time=start_time,
            end_time=end_time,
            limit=100000  # Large limit for aggregation
        )
        
        # Perform aggregation
        result = perform_aggregation(logs, query.group_by, query.operation)
        
        return {
            "time_range": {
                "start": datetime.fromtimestamp(start_time).isoformat(),
                "end": datetime.fromtimestamp(end_time).isoformat()
            },
            "group_by": query.group_by,
            "operation": query.operation,
            "results": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts/rules", response_model=Dict[str, str])
async def add_alert_rule(rule: AlertRule):
    """Add a new alert rule."""
    try:
        rule_dict = rule.dict()
        pipeline.alert_manager.add_rule(rule_dict)
        return {"status": "created", "rule": rule.name}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts/recent", response_model=List[Dict])
async def get_recent_alerts(limit: int = Query(100, ge=1, le=1000)):
    """Get recent triggered alerts."""
    try:
        alerts = list(pipeline.alert_manager.alerts)[-limit:]
        return alerts
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=Dict[str, Any])
async def get_statistics():
    """Get pipeline statistics."""
    try:
        stats = pipeline.get_stats()
        
        # Calculate rate
        if stats['total_logs'] > 0:
            runtime = time.time() - pipeline.aggregator.windows.get('1min', {}).get('start_time', time.time())
            stats['logs_per_second'] = stats['total_logs'] / max(runtime, 1)
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


def parse_time(time_str: str) -> float:
    """Parse time string to Unix timestamp."""
    # Try relative time (e.g., "1h", "30m", "7d")
    relative_pattern = re.match(r'^(\d+)([smhd])$', time_str)
    if relative_pattern:
        value = int(relative_pattern.group(1))
        unit = relative_pattern.group(2)
        
        if unit == 's':
            return time.time() - value
        elif unit == 'm':
            return time.time() - (value * 60)
        elif unit == 'h':
            return time.time() - (value * 3600)
        elif unit == 'd':
            return time.time() - (value * 86400)
    
    # Try ISO format
    try:
        dt = datetime.fromisoformat(time_str)
        return dt.timestamp()
    except:
        pass
    
    # Try Unix timestamp
    try:
        return float(time_str)
    except:
        raise ValueError(f"Invalid time format: {time_str}")


def parse_duration(duration_str: str) -> float:
    """Parse duration string to seconds."""
    pattern = re.match(r'^(\d+)([smhd])$', duration_str)
    if not pattern:
        raise ValueError(f"Invalid duration format: {duration_str}")
    
    value = int(pattern.group(1))
    unit = pattern.group(2)
    
    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    elif unit == 'd':
        return value * 86400
    
    raise ValueError(f"Invalid duration unit: {unit}")


def perform_aggregation(logs: List[Dict], group_by: str, operation: str) -> Dict[str, Any]:
    """Perform aggregation on logs."""
    groups = {}
    
    for log in logs:
        # Get grouping key
        if group_by == 'level':
            key = log.get('level', 'UNKNOWN')
        elif group_by == 'source':
            key = log.get('source', 'unknown')
        elif group_by in log.get('fields', {}):
            key = log['fields'][group_by]
        else:
            key = 'other'
        
        if key not in groups:
            groups[key] = []
        groups[key].append(log)
    
    # Perform operation
    results = {}
    for key, group_logs in groups.items():
        if operation == 'count':
            results[key] = len(group_logs)
        elif operation == 'avg_size':
            sizes = [len(log.get('raw', '')) for log in group_logs]
            results[key] = sum(sizes) / len(sizes) if sizes else 0
        elif operation == 'unique_sources':
            sources = set(log.get('source', 'unknown') for log in group_logs)
            results[key] = len(sources)
        else:
            results[key] = len(group_logs)  # Default to count
    
    return results


if __name__ == "__main__":
    import uvicorn
    import threading
    
    # Start pipeline servers in background
    def start_pipeline():
        import asyncio
        
        # Start UDP server
        udp_thread = threading.Thread(
            target=pipeline.start_udp_server,
            args=(514,),
            daemon=True
        )
        udp_thread.start()
        
        # Start TCP server
        asyncio.run(pipeline.start_tcp_server(5514))
    
    # Start pipeline in background
    pipeline_thread = threading.Thread(target=start_pipeline, daemon=True)
    pipeline_thread.start()
    
    # Start API server
    uvicorn.run(app, host="0.0.0.0", port=8000)