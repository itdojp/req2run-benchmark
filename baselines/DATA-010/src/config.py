"""Configuration for stream processing"""
import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
import yaml

from models import WindowConfig, WindowType


@dataclass
class StreamConfig:
    """Stream processing configuration"""
    # Application settings
    app_name: str = "Stream Processor"
    debug: bool = False
    
    # Processing settings
    parallelism: int = 4
    queue_size: int = 10000
    checkpoint_interval: float = 30.0  # seconds
    
    # State storage
    state_path: str = "./state"
    
    # Windowing
    window_configs: List[WindowConfig] = field(default_factory=list)
    window_cleanup_interval: float = 60.0  # seconds
    
    # Watermarks
    watermark_delay_seconds: float = 5.0
    
    # Sources and sinks
    input_topics: List[str] = field(default_factory=list)
    output_topics: List[str] = field(default_factory=list)
    
    # Kafka settings (if using Kafka)
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "stream-processor"
    kafka_auto_offset_reset: str = "latest"
    
    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    metrics_port: int = 9090
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "StreamConfig":
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = "config/stream.yaml"
        
        config_file = Path(config_path)
        if not config_file.exists():
            return cls.default()
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict) -> "StreamConfig":
        """Create configuration from dictionary"""
        config = cls()
        
        # Basic settings
        config.app_name = data.get("app_name", config.app_name)
        config.debug = data.get("debug", config.debug)
        
        # Processing settings
        if "processing" in data:
            proc = data["processing"]
            config.parallelism = proc.get("parallelism", config.parallelism)
            config.queue_size = proc.get("queue_size", config.queue_size)
            config.checkpoint_interval = proc.get("checkpoint_interval", config.checkpoint_interval)
        
        # State storage
        if "state" in data:
            state = data["state"]
            config.state_path = state.get("path", config.state_path)
        
        # Windowing
        if "windowing" in data:
            windowing = data["windowing"]
            config.window_cleanup_interval = windowing.get("cleanup_interval", config.window_cleanup_interval)
            
            # Parse window configurations
            if "windows" in windowing:
                for window_data in windowing["windows"]:
                    window_type = WindowType(window_data["type"])
                    window_config = WindowConfig(
                        window_type=window_type,
                        size_ms=window_data["size_ms"],
                        slide_ms=window_data.get("slide_ms"),
                        gap_ms=window_data.get("gap_ms"),
                        allowed_lateness_ms=window_data.get("allowed_lateness_ms", 5000)
                    )
                    config.window_configs.append(window_config)
        
        # Watermarks
        if "watermarks" in data:
            wm = data["watermarks"]
            config.watermark_delay_seconds = wm.get("delay_seconds", config.watermark_delay_seconds)
        
        # Sources and sinks
        if "sources" in data:
            config.input_topics = data["sources"].get("topics", config.input_topics)
        
        if "sinks" in data:
            config.output_topics = data["sinks"].get("topics", config.output_topics)
        
        # Kafka settings
        if "kafka" in data:
            kafka = data["kafka"]
            config.kafka_bootstrap_servers = kafka.get("bootstrap_servers", config.kafka_bootstrap_servers)
            config.kafka_group_id = kafka.get("group_id", config.kafka_group_id)
            config.kafka_auto_offset_reset = kafka.get("auto_offset_reset", config.kafka_auto_offset_reset)
        
        # API settings
        if "api" in data:
            api = data["api"]
            config.api_host = api.get("host", config.api_host)
            config.api_port = api.get("port", config.api_port)
            config.metrics_port = api.get("metrics_port", config.metrics_port)
        
        return config
    
    @classmethod
    def default(cls) -> "StreamConfig":
        """Create default configuration"""
        return cls(
            window_configs=[
                WindowConfig(
                    window_type=WindowType.TUMBLING,
                    size_ms=60000,  # 1 minute
                    allowed_lateness_ms=5000
                )
            ],
            input_topics=["input-stream"],
            output_topics=["output-stream"]
        )