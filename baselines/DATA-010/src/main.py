"""
DATA-010: Real-Time Stream Processing with Windowing and State
Main application entry point
"""
import asyncio
import logging
import signal
from typing import Optional

from stream_processor import StreamProcessor
from config import StreamConfig
from api_server import APIServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StreamProcessingApplication:
    """Main stream processing application"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = StreamConfig.load(config_path)
        self.processor = StreamProcessor(self.config)
        self.api_server = APIServer(self.config, self.processor)
        self._shutdown_event = asyncio.Event()
        
    async def start(self):
        """Start the application"""
        logger.info("Starting Stream Processing Application")
        
        # Start components
        await self.processor.start()
        await self.api_server.start()
        
        logger.info("Stream processor started successfully")
        
    async def stop(self):
        """Stop the application"""
        logger.info("Stopping Stream Processing Application")
        
        # Stop components
        await self.api_server.stop()
        await self.processor.stop()
        
        logger.info("Stream processor stopped")
        
    async def run(self):
        """Run the application"""
        try:
            # Setup signal handlers
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig,
                    lambda: asyncio.create_task(self.shutdown())
                )
            
            # Start application
            await self.start()
            
            # Wait for shutdown
            await self._shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            raise
        finally:
            await self.stop()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Received shutdown signal")
        self._shutdown_event.set()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Real-Time Stream Processing with Windowing"
    )
    parser.add_argument(
        "--config",
        default="config/stream.yaml",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Create and run application
    app = StreamProcessingApplication(config_path=args.config)
    
    # Run event loop
    asyncio.run(app.run())


if __name__ == "__main__":
    main()