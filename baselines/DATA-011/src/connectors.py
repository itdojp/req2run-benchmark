"""Connectors for various data sources and sinks"""
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from abc import ABC, abstractmethod
import json

import aiokafka
import structlog

logger = structlog.get_logger()


class SourceConnector(ABC):
    """Base class for source connectors"""
    
    @abstractmethod
    async def connect(self, config: Dict[str, Any]):
        """Connect to source"""
        pass
    
    @abstractmethod
    async def read(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Read data from source"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close connection"""
        pass


class SinkConnector(ABC):
    """Base class for sink connectors"""
    
    @abstractmethod
    async def connect(self, config: Dict[str, Any]):
        """Connect to sink"""
        pass
    
    @abstractmethod
    async def write(self, data: Dict[str, Any]):
        """Write data to sink"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close connection"""
        pass


class KafkaSourceConnector(SourceConnector):
    """Kafka source connector"""
    
    def __init__(self):
        self.consumer = None
        self.topic = None
    
    async def connect(self, config: Dict[str, Any]):
        """Connect to Kafka"""
        self.topic = config.get("topic")
        self.consumer = aiokafka.AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=config.get("bootstrap_servers", "localhost:9092"),
            group_id=config.get("group_id", "etl-pipeline"),
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )
        await self.consumer.start()
        logger.info(f"Connected to Kafka topic", topic=self.topic)
    
    async def read(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Read from Kafka"""
        async for msg in self.consumer:
            yield msg.value
    
    async def close(self):
        """Close Kafka consumer"""
        if self.consumer:
            await self.consumer.stop()


class KafkaSinkConnector(SinkConnector):
    """Kafka sink connector"""
    
    def __init__(self):
        self.producer = None
        self.topic = None
    
    async def connect(self, config: Dict[str, Any]):
        """Connect to Kafka"""
        self.topic = config.get("topic")
        self.producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=config.get("bootstrap_servers", "localhost:9092"),
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        await self.producer.start()
        logger.info(f"Connected to Kafka topic", topic=self.topic)
    
    async def write(self, data: Dict[str, Any]):
        """Write to Kafka"""
        await self.producer.send(self.topic, data)
    
    async def close(self):
        """Close Kafka producer"""
        if self.producer:
            await self.producer.stop()


class FileSourceConnector(SourceConnector):
    """File source connector"""
    
    def __init__(self):
        self.file_path = None
        self.format = None
    
    async def connect(self, config: Dict[str, Any]):
        """Configure file source"""
        self.file_path = config.get("path")
        self.format = config.get("format", "json")
    
    async def read(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Read from file"""
        try:
            if self.format == "json":
                with open(self.file_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            yield item
                    else:
                        yield data
            elif self.format == "jsonl":
                with open(self.file_path, "r") as f:
                    for line in f:
                        yield json.loads(line)
        except Exception as e:
            logger.error(f"Error reading file", error=str(e))
    
    async def close(self):
        """No-op for file connector"""
        pass


class FileSinkConnector(SinkConnector):
    """File sink connector"""
    
    def __init__(self):
        self.file_path = None
        self.format = None
        self.file = None
    
    async def connect(self, config: Dict[str, Any]):
        """Configure file sink"""
        self.file_path = config.get("path")
        self.format = config.get("format", "jsonl")
        
        if self.format == "jsonl":
            self.file = open(self.file_path, "a")
    
    async def write(self, data: Dict[str, Any]):
        """Write to file"""
        if self.format == "jsonl" and self.file:
            self.file.write(json.dumps(data) + "\n")
            self.file.flush()
    
    async def close(self):
        """Close file"""
        if self.file:
            self.file.close()


class ConnectorManager:
    """Manage connectors"""
    
    def __init__(self):
        self.sources: Dict[str, SourceConnector] = {}
        self.sinks: Dict[str, SinkConnector] = {}
    
    def register_source(self, name: str, config: Dict[str, Any]):
        """Register a source connector"""
        connector_type = config.get("type")
        
        if connector_type == "kafka":
            connector = KafkaSourceConnector()
        elif connector_type == "file":
            connector = FileSourceConnector()
        else:
            raise ValueError(f"Unknown source type: {connector_type}")
        
        self.sources[name] = connector
        logger.info(f"Registered source", name=name, type=connector_type)
    
    def register_sink(self, name: str, config: Dict[str, Any]):
        """Register a sink connector"""
        connector_type = config.get("type")
        
        if connector_type == "kafka":
            connector = KafkaSinkConnector()
        elif connector_type == "file":
            connector = FileSinkConnector()
        else:
            raise ValueError(f"Unknown sink type: {connector_type}")
        
        self.sinks[name] = connector
        logger.info(f"Registered sink", name=name, type=connector_type)
    
    def get_source(self, name: str) -> Optional[SourceConnector]:
        """Get source connector"""
        return self.sources.get(name)
    
    def get_sink(self, name: str) -> Optional[SinkConnector]:
        """Get sink connector"""
        return self.sinks.get(name)