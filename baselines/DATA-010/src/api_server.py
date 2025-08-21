"""REST API server for stream processing"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import uvicorn

from stream_processor import StreamProcessor
from models import Pipeline

logger = logging.getLogger(__name__)


class APIServer:
    """REST API for monitoring and controlling stream processing"""
    
    def __init__(self, config, stream_processor: StreamProcessor):
        self.config = config
        self.stream_processor = stream_processor
        self.app = FastAPI(
            title="Stream Processing API",
            description="Monitor and control stream processing pipelines",
            version="1.0.0"
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "processor_running": self.stream_processor.running
            }
        
        @self.app.get("/status")
        async def get_status():
            """Get detailed status"""
            try:
                stats = await self.stream_processor.get_stats()
                return {
                    "status": "running" if self.stream_processor.running else "stopped",
                    "stats": stats,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Status error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/pipelines")
        async def list_pipelines():
            """List all pipelines"""
            try:
                pipelines = []
                for pipeline_id, pipeline in self.stream_processor.pipelines.items():
                    pipelines.append({
                        "id": pipeline_id,
                        "name": pipeline.name,
                        "running": pipeline_id in self.stream_processor.pipeline_tasks,
                        "window_configs": [
                            {
                                "type": wc.window_type.value,
                                "size_ms": wc.size_ms,
                                "slide_ms": wc.slide_ms,
                                "gap_ms": wc.gap_ms
                            }
                            for wc in pipeline.window_configs
                        ]
                    })
                
                return {"pipelines": pipelines}
            except Exception as e:
                logger.error(f"Pipeline list error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/pipelines/{pipeline_id}/start")
        async def start_pipeline(pipeline_id: str):
            """Start a pipeline"""
            try:
                if pipeline_id not in self.stream_processor.pipelines:
                    raise HTTPException(status_code=404, detail="Pipeline not found")
                
                await self.stream_processor.start_pipeline(pipeline_id)
                return {"message": f"Pipeline {pipeline_id} started"}
            except Exception as e:
                logger.error(f"Pipeline start error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/pipelines/{pipeline_id}/stop")
        async def stop_pipeline(pipeline_id: str):
            """Stop a pipeline"""
            try:
                if pipeline_id not in self.stream_processor.pipelines:
                    raise HTTPException(status_code=404, detail="Pipeline not found")
                
                await self.stream_processor.stop_pipeline(pipeline_id)
                return {"message": f"Pipeline {pipeline_id} stopped"}
            except Exception as e:
                logger.error(f"Pipeline stop error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/pipelines/{pipeline_id}/stats")
        async def get_pipeline_stats(pipeline_id: str):
            """Get pipeline statistics"""
            try:
                if pipeline_id not in self.stream_processor.pipelines:
                    raise HTTPException(status_code=404, detail="Pipeline not found")
                
                stats = await self.stream_processor.get_pipeline_stats(pipeline_id)
                return stats
            except Exception as e:
                logger.error(f"Pipeline stats error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/watermarks")
        async def get_watermarks():
            """Get current watermarks"""
            try:
                watermarks = await self.stream_processor.watermark_tracker.get_all_watermarks()
                global_wm = await self.stream_processor.watermark_tracker.get_global_watermark()
                
                return {
                    "watermarks": {
                        k: v.isoformat() for k, v in watermarks.items()
                    },
                    "global_watermark": global_wm.isoformat() if global_wm else None,
                    "stats": self.stream_processor.watermark_tracker.get_stats()
                }
            except Exception as e:
                logger.error(f"Watermarks error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/state")
        async def get_state_info():
            """Get state store information"""
            try:
                stats = self.stream_processor.state_store.get_stats()
                return {"state_store": stats}
            except Exception as e:
                logger.error(f"State info error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/checkpoint")
        async def create_checkpoint():
            """Create a checkpoint"""
            try:
                checkpoint = await self.stream_processor.create_checkpoint()
                return {
                    "message": "Checkpoint created",
                    "timestamp": datetime.utcnow().isoformat(),
                    "checkpoint_size": len(checkpoint)
                }
            except Exception as e:
                logger.error(f"Checkpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/windows")
        async def get_active_windows(
            pipeline_id: str = Query(None, description="Filter by pipeline ID"),
            limit: int = Query(100, description="Maximum number of windows to return")
        ):
            """Get active windows"""
            try:
                windows = []
                
                # Get windows from all or specific pipeline
                pipelines_to_check = (
                    [pipeline_id] if pipeline_id 
                    else list(self.stream_processor.pipelines.keys())
                )
                
                for pid in pipelines_to_check:
                    if pid not in self.stream_processor.pipelines:
                        continue
                    
                    pipeline = self.stream_processor.pipelines[pid]
                    for window_manager in pipeline.window_managers:
                        active_windows = await window_manager.get_active_windows()
                        
                        for window_id, window in active_windows.items():
                            windows.append({
                                "pipeline_id": pid,
                                "window_id": window_id,
                                "start_time": window.start_time.isoformat(),
                                "end_time": window.end_time.isoformat(),
                                "event_count": len(window.events),
                                "state": window.state
                            })
                
                # Sort by start time and limit
                windows.sort(key=lambda w: w["start_time"])
                return {"windows": windows[:limit]}
                
            except Exception as e:
                logger.error(f"Windows error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start(self):
        """Start the API server"""
        config = uvicorn.Config(
            self.app,
            host=self.config.api_host,
            port=self.config.api_port,
            log_level="info"
        )
        
        self.server = uvicorn.Server(config)
        await self.server.serve()
    
    async def stop(self):
        """Stop the API server"""
        if hasattr(self, 'server'):
            self.server.should_exit = True