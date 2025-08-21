"""Main ETL Pipeline with CDC API"""
import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import structlog
import yaml

from cdc_engine import CDCEngine, ChangeEvent, CDCBuffer
from transformation_engine import (
    TransformationEngine, TransformationRule, 
    SchemaEvolution, DataQualityChecker
)
from lineage_tracker import LineageTracker, DataAsset, LineageOperation
from connectors import ConnectorManager, SourceConnector, SinkConnector

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global instances
cdc_engine: Optional[CDCEngine] = None
transformation_engine: Optional[TransformationEngine] = None
lineage_tracker: Optional[LineageTracker] = None
connector_manager: Optional[ConnectorManager] = None
cdc_buffer: Optional[CDCBuffer] = None
schema_evolution: Optional[SchemaEvolution] = None
quality_checker: Optional[DataQualityChecker] = None

# Pipeline state
pipeline_state = {
    "status": "stopped",
    "started_at": None,
    "processed_count": 0,
    "error_count": 0
}


# Pydantic models
class SourceConfig(BaseModel):
    id: str
    type: str = Field(..., pattern="^(postgresql|mysql|mongodb|kafka|file)$")
    connection_string: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class TransformationConfig(BaseModel):
    rule_id: str
    name: str
    rule_type: str = Field(..., pattern="^(map|filter|aggregate|join|custom)$")
    source_fields: List[str]
    target_field: Optional[str] = None
    expression: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None


class PipelineConfig(BaseModel):
    name: str
    sources: List[SourceConfig]
    transformations: List[TransformationConfig]
    sink: Dict[str, Any]
    options: Dict[str, Any] = Field(default_factory=dict)


class CDCEventResponse(BaseModel):
    event_id: str
    timestamp: str
    source_database: str
    source_table: str
    change_type: str
    data: Dict[str, Any]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global cdc_engine, transformation_engine, lineage_tracker, connector_manager
    global cdc_buffer, schema_evolution, quality_checker
    
    # Startup
    logger.info("Starting ETL Pipeline with CDC")
    
    # Initialize components
    cdc_engine = CDCEngine({"poll_interval": 1})
    transformation_engine = TransformationEngine()
    lineage_tracker = LineageTracker()
    connector_manager = ConnectorManager()
    cdc_buffer = CDCBuffer()
    schema_evolution = SchemaEvolution()
    quality_checker = DataQualityChecker()
    
    # Load configuration
    await load_configuration()
    
    # Set up change handlers
    cdc_engine.add_change_handler(handle_change_event)
    
    yield
    
    # Shutdown
    logger.info("Shutting down ETL Pipeline")
    
    # Stop all CDC watchers
    for source_id in list(cdc_engine.watchers.keys()):
        await cdc_engine.stop_capture(source_id)


async def load_configuration():
    """Load configuration from files"""
    try:
        # Load CDC config
        with open("config/cdc.yaml", "r") as f:
            cdc_config = yaml.safe_load(f)
            
            # Configure CDC sources
            for source in cdc_config.get("sources", []):
                await cdc_engine.connect_source(source)
    except FileNotFoundError:
        logger.warning("CDC configuration file not found")
    
    try:
        # Load transformation rules
        with open("config/transformations.yaml", "r") as f:
            transform_config = yaml.safe_load(f)
            
            for rule_data in transform_config.get("rules", []):
                rule = TransformationRule(**rule_data)
                transformation_engine.add_rule(rule)
    except FileNotFoundError:
        logger.warning("Transformation configuration file not found")
    
    try:
        # Load connectors
        with open("config/connectors.yaml", "r") as f:
            connector_config = yaml.safe_load(f)
            
            # Register connectors
            for conn in connector_config.get("sources", []):
                connector_manager.register_source(conn["id"], conn)
            
            for conn in connector_config.get("sinks", []):
                connector_manager.register_sink(conn["id"], conn)
    except FileNotFoundError:
        logger.warning("Connectors configuration file not found")


async def handle_change_event(event: ChangeEvent):
    """Handle CDC change event"""
    try:
        # Add to buffer
        await cdc_buffer.add_event(event)
        
        # Track lineage - register source asset
        source_asset = DataAsset(
            asset_id=f"{event.source_database}_{event.source_table}",
            name=event.source_table,
            asset_type="table",
            location=f"{event.source_database}/{event.source_table}",
            metadata={"database": event.source_database}
        )
        lineage_tracker.register_asset(source_asset)
        
        # Transform data
        data = event.after if event.after else event.before
        if data:
            # Apply transformations
            transformed = await transformation_engine.transform(data)
            
            if transformed:
                # Quality check
                passed, issues = await quality_checker.check(transformed)
                
                if passed:
                    # Send to sink
                    await send_to_sink(transformed, event)
                    
                    # Update pipeline state
                    pipeline_state["processed_count"] += 1
                else:
                    logger.warning("Data quality check failed", issues=issues)
                    pipeline_state["error_count"] += 1
            else:
                # Filtered out
                logger.debug("Event filtered out", event_id=event.event_id)
        
    except Exception as e:
        logger.error(f"Error handling change event", error=str(e))
        pipeline_state["error_count"] += 1


async def send_to_sink(data: Dict[str, Any], event: ChangeEvent):
    """Send transformed data to sink"""
    # Track lineage - register sink asset
    sink_asset = DataAsset(
        asset_id=f"sink_{int(time.time())}",
        name="transformed_output",
        asset_type="stream",
        location="output_sink",
        metadata={"format": "json"}
    )
    sink_asset_id = lineage_tracker.register_asset(sink_asset)
    
    # Track operation
    operation = LineageOperation(
        operation_id=f"transform_{event.event_id}",
        operation_type="transform",
        description=f"Transform and load {event.source_table}",
        inputs=[f"{event.source_database}_{event.source_table}"],
        outputs=[sink_asset_id],
        metadata={"event_id": event.event_id}
    )
    lineage_tracker.track_operation(operation)
    
    # Send to sink (simplified)
    logger.info("Sent to sink", data=data)


# Create FastAPI app
app = FastAPI(
    title="ETL Pipeline with CDC",
    description="Real-time ETL pipeline with Change Data Capture and data lineage",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "cdc_engine": cdc_engine is not None,
            "transformation_engine": transformation_engine is not None,
            "lineage_tracker": lineage_tracker is not None
        }
    }


@app.post("/api/v1/sources/connect")
async def connect_source(config: SourceConfig):
    """Connect a new data source"""
    try:
        source_id = await cdc_engine.connect_source(config.dict())
        return {"source_id": source_id, "status": "connected"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/sources/{source_id}/start")
async def start_cdc(source_id: str, tables: Optional[List[str]] = None):
    """Start CDC for a source"""
    try:
        await cdc_engine.start_capture(source_id, tables)
        return {"source_id": source_id, "status": "capturing"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/sources/{source_id}/stop")
async def stop_cdc(source_id: str):
    """Stop CDC for a source"""
    try:
        await cdc_engine.stop_capture(source_id)
        return {"source_id": source_id, "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/transformations")
async def add_transformation(config: TransformationConfig):
    """Add a transformation rule"""
    try:
        rule = TransformationRule(**config.dict())
        transformation_engine.add_rule(rule)
        return {"rule_id": rule.rule_id, "status": "added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/transformations")
async def list_transformations():
    """List all transformation rules"""
    return {
        "rules": [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "type": rule.rule_type,
                "source_fields": rule.source_fields,
                "target_field": rule.target_field
            }
            for rule in transformation_engine.rules.values()
        ]
    }


@app.post("/api/v1/pipeline/start")
async def start_pipeline(background_tasks: BackgroundTasks):
    """Start the ETL pipeline"""
    if pipeline_state["status"] == "running":
        raise HTTPException(status_code=400, detail="Pipeline already running")
    
    pipeline_state["status"] = "running"
    pipeline_state["started_at"] = datetime.now().isoformat()
    
    # Start all configured sources
    for source_id in cdc_engine.sources.keys():
        background_tasks.add_task(cdc_engine.start_capture, source_id)
    
    return {"status": "started", "timestamp": pipeline_state["started_at"]}


@app.post("/api/v1/pipeline/stop")
async def stop_pipeline():
    """Stop the ETL pipeline"""
    pipeline_state["status"] = "stopped"
    
    # Stop all sources
    for source_id in list(cdc_engine.watchers.keys()):
        await cdc_engine.stop_capture(source_id)
    
    return {"status": "stopped", "processed": pipeline_state["processed_count"]}


@app.get("/api/v1/pipeline/status")
async def get_pipeline_status():
    """Get pipeline status"""
    cdc_stats = await cdc_engine.get_statistics()
    
    return {
        "status": pipeline_state["status"],
        "started_at": pipeline_state["started_at"],
        "processed_count": pipeline_state["processed_count"],
        "error_count": pipeline_state["error_count"],
        "cdc_statistics": cdc_stats,
        "transformation_statistics": transformation_engine.statistics,
        "quality_statistics": quality_checker.statistics
    }


@app.get("/api/v1/events/recent")
async def get_recent_events(count: int = 100):
    """Get recent CDC events"""
    events = await cdc_buffer.get_events(count)
    
    return {
        "count": len(events),
        "events": [
            CDCEventResponse(
                event_id=e.event_id,
                timestamp=e.timestamp.isoformat(),
                source_database=e.source_database,
                source_table=e.source_table,
                change_type=e.change_type.value,
                data=e.after if e.after else e.before
            )
            for e in events
        ]
    }


@app.get("/api/v1/lineage/asset/{asset_id}/downstream")
async def get_downstream_lineage(asset_id: str, max_depth: int = 3):
    """Get downstream lineage for an asset"""
    try:
        lineage = lineage_tracker.get_downstream_lineage(asset_id, max_depth)
        return lineage
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/lineage/asset/{asset_id}/upstream")
async def get_upstream_lineage(asset_id: str, max_depth: int = 3):
    """Get upstream lineage for an asset"""
    try:
        lineage = lineage_tracker.get_upstream_lineage(asset_id, max_depth)
        return lineage
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/lineage/impact/{asset_id}")
async def get_impact_analysis(asset_id: str):
    """Get impact analysis for changes to an asset"""
    try:
        impact = lineage_tracker.get_impact_analysis(asset_id)
        return impact
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/lineage/flow")
async def get_data_flow():
    """Get data flow diagram"""
    return lineage_tracker.get_data_flow_diagram()


@app.get("/api/v1/lineage/statistics")
async def get_lineage_statistics():
    """Get lineage statistics"""
    return lineage_tracker.get_statistics()


@app.post("/api/v1/schema/register")
async def register_schema(name: str, version: int, schema: Dict[str, Any]):
    """Register a schema version"""
    schema_evolution.register_schema(name, version, schema)
    return {"name": name, "version": version, "status": "registered"}


@app.post("/api/v1/schema/check-compatibility")
async def check_schema_compatibility(name: str, schema: Dict[str, Any]):
    """Check schema compatibility"""
    compatible = schema_evolution.check_compatibility(name, schema)
    return {"compatible": compatible, "mode": schema_evolution.compatibility_mode}


@app.post("/api/v1/quality/add-rule")
async def add_quality_rule(rule: Dict[str, Any]):
    """Add data quality rule"""
    quality_checker.add_rule(rule)
    return {"status": "added", "total_rules": len(quality_checker.rules)}


@app.post("/api/v1/quality/check")
async def check_data_quality(data: Dict[str, Any]):
    """Check data quality"""
    passed, issues = await quality_checker.check(data)
    return {"passed": passed, "issues": issues}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )