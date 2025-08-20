#!/usr/bin/env python3
"""Binary protocol TCP server implementation."""

import asyncio
import logging
import signal
import sys
import uuid
from typing import Dict, Optional, Set

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass  # uvloop is optional

from protocol import (
    Frame,
    MessageType,
    DEFAULT_PORT,
    DEFAULT_MAX_CONNECTIONS,
    DEFAULT_BACKLOG
)
from server.connection import Connection, ConnectionState

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BinaryProtocolServer:
    """Binary protocol TCP server."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = DEFAULT_PORT,
                 max_connections: int = DEFAULT_MAX_CONNECTIONS):
        """Initialize server.
        
        Args:
            host: Host to bind to
            port: Port to listen on
            max_connections: Maximum concurrent connections
        """
        self.host = host
        self.port = port
        self.max_connections = max_connections
        
        # Connection management
        self.connections: Dict[str, Connection] = {}
        self.connection_lock = asyncio.Lock()
        
        # Server state
        self.server: Optional[asyncio.Server] = None
        self.running = False
        
        # Statistics
        self.total_connections = 0
        self.total_messages = 0
        
    async def start(self):
        """Start the server."""
        logger.info(f"Starting server on {self.host}:{self.port}")
        
        self.server = await asyncio.start_server(
            self._handle_connection,
            self.host,
            self.port,
            backlog=DEFAULT_BACKLOG
        )
        
        self.running = True
        
        addrs = ', '.join(str(sock.getsockname()) for sock in self.server.sockets)
        logger.info(f"Server listening on {addrs}")
        logger.info(f"Max connections: {self.max_connections}")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self):
        """Stop the server."""
        logger.info("Stopping server...")
        self.running = False
        
        # Close all connections
        async with self.connection_lock:
            for conn_id in list(self.connections.keys()):
                conn = self.connections.get(conn_id)
                if conn:
                    await conn.close()
        
        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("Server stopped")
    
    async def _handle_connection(self, reader: asyncio.StreamReader,
                                writer: asyncio.StreamWriter):
        """Handle a new connection.
        
        Args:
            reader: Stream reader
            writer: Stream writer
        """
        # Generate connection ID
        conn_id = str(uuid.uuid4())
        peer = writer.get_extra_info('peername')
        
        logger.info(f"New connection from {peer} (ID: {conn_id})")
        
        # Check connection limit
        async with self.connection_lock:
            if len(self.connections) >= self.max_connections:
                logger.warning(f"Connection limit exceeded, rejecting {peer}")
                writer.close()
                await writer.wait_closed()
                return
            
            # Create connection
            connection = Connection(reader, writer, conn_id, self)
            self.connections[conn_id] = connection
            self.total_connections += 1
        
        # Handle connection
        try:
            await connection.start()
        except Exception as e:
            logger.error(f"Connection {conn_id} error: {e}")
        finally:
            await self.remove_connection(conn_id)
    
    async def remove_connection(self, conn_id: str):
        """Remove a connection.
        
        Args:
            conn_id: Connection ID
        """
        async with self.connection_lock:
            if conn_id in self.connections:
                del self.connections[conn_id]
                logger.info(f"Removed connection {conn_id}. Active: {len(self.connections)}")
    
    async def broadcast(self, frame: Frame, exclude: Optional[str] = None):
        """Broadcast a frame to all connections.
        
        Args:
            frame: Frame to broadcast
            exclude: Optional connection ID to exclude
        """
        async with self.connection_lock:
            tasks = []
            for conn_id, conn in self.connections.items():
                if conn_id != exclude and conn.state == ConnectionState.AUTHENTICATED:
                    tasks.append(conn.send_frame(frame))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_stats(self) -> dict:
        """Get server statistics.
        
        Returns:
            Server statistics dictionary
        """
        return {
            'active_connections': len(self.connections),
            'total_connections': self.total_connections,
            'total_messages': self.total_messages,
            'max_connections': self.max_connections,
            'running': self.running
        }


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Binary Protocol TCP Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Port to listen on')
    parser.add_argument('--max-connections', type=int, default=DEFAULT_MAX_CONNECTIONS,
                       help='Maximum concurrent connections')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create server
    server = BinaryProtocolServer(
        host=args.host,
        port=args.port,
        max_connections=args.max_connections
    )
    
    # Handle signals
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received signal, shutting down...")
        asyncio.create_task(server.stop())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    # Start server
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await server.stop()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)