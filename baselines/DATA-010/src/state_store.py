"""State storage for stream processing"""
import asyncio
import json
import logging
import pickle
from typing import Any, Optional, Dict
from pathlib import Path

try:
    import rocksdict
    ROCKSDB_AVAILABLE = True
except ImportError:
    ROCKSDB_AVAILABLE = False
    import diskcache

logger = logging.getLogger(__name__)


class StateStore:
    """Persistent state storage for stream processing"""
    
    def __init__(self, config):
        self.config = config
        self.state_path = Path(config.state_path)
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        if ROCKSDB_AVAILABLE:
            self.store = None  # Will be initialized in initialize()
            self.backend = "rocksdb"
        else:
            self.backend = "diskcache"
            self.store = diskcache.Cache(str(self.state_path / "cache"))
        
        logger.info(f"Using {self.backend} for state storage")
    
    async def initialize(self):
        """Initialize the state store"""
        if self.backend == "rocksdb":
            # Initialize RocksDB
            db_path = str(self.state_path / "rocksdb")
            self.store = rocksdict.Rdict(
                db_path,
                options={
                    "create_if_missing": True,
                    "compression": "lz4",
                    "max_open_files": 1000,
                }
            )
        
        logger.info("State store initialized")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from state store"""
        try:
            if self.backend == "rocksdb":
                data = self.store.get(key.encode())
                if data:
                    return pickle.loads(data)
            else:
                return self.store.get(key)
        except Exception as e:
            logger.error(f"State get error for key {key}: {e}")
        
        return None
    
    async def put(self, key: str, value: Any):
        """Put value into state store"""
        try:
            if self.backend == "rocksdb":
                serialized = pickle.dumps(value)
                self.store[key.encode()] = serialized
            else:
                self.store[key] = value
        except Exception as e:
            logger.error(f"State put error for key {key}: {e}")
    
    async def delete(self, key: str):
        """Delete key from state store"""
        try:
            if self.backend == "rocksdb":
                del self.store[key.encode()]
            else:
                del self.store[key]
        except KeyError:
            # Key doesn't exist, ignore
            pass
        except Exception as e:
            logger.error(f"State delete error for key {key}: {e}")
    
    async def scan_prefix(self, prefix: str) -> Dict[str, Any]:
        """Scan all keys with given prefix"""
        result = {}
        
        try:
            if self.backend == "rocksdb":
                # RocksDB prefix scan
                for key, value in self.store.items():
                    key_str = key.decode()
                    if key_str.startswith(prefix):
                        result[key_str] = pickle.loads(value)
            else:
                # DiskCache doesn't have efficient prefix scan
                # Would need to iterate all keys
                for key in self.store:
                    if key.startswith(prefix):
                        result[key] = self.store[key]
        except Exception as e:
            logger.error(f"State scan error for prefix {prefix}: {e}")
        
        return result
    
    async def checkpoint(self) -> Dict[str, Any]:
        """Create a checkpoint of current state"""
        try:
            checkpoint_data = {}
            
            if self.backend == "rocksdb":
                for key, value in self.store.items():
                    checkpoint_data[key.decode()] = pickle.loads(value)
            else:
                for key in self.store:
                    checkpoint_data[key] = self.store[key]
            
            return checkpoint_data
            
        except Exception as e:
            logger.error(f"Checkpoint creation error: {e}")
            return {}
    
    async def restore_from_checkpoint(self, checkpoint_data: Dict[str, Any]):
        """Restore state from checkpoint"""
        try:
            for key, value in checkpoint_data.items():
                await self.put(key, value)
            
            logger.info(f"Restored {len(checkpoint_data)} keys from checkpoint")
            
        except Exception as e:
            logger.error(f"Checkpoint restore error: {e}")
    
    async def close(self):
        """Close the state store"""
        try:
            if self.backend == "rocksdb" and self.store:
                self.store.close()
            elif self.backend == "diskcache":
                self.store.close()
            
            logger.info("State store closed")
            
        except Exception as e:
            logger.error(f"State store close error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get state store statistics"""
        stats = {
            "backend": self.backend,
            "path": str(self.state_path)
        }
        
        try:
            if self.backend == "rocksdb" and self.store:
                stats["approximate_size"] = len(self.store)
            elif self.backend == "diskcache":
                stats["size"] = len(self.store)
                stats["disk_usage"] = self.store.volume()
        except Exception as e:
            logger.error(f"Stats error: {e}")
            stats["error"] = str(e)
        
        return stats