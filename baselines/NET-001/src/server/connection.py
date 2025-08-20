"""Connection management for the TCP server."""

import asyncio
import time
import logging
from enum import Enum
from typing import Optional, Any
from dataclasses import dataclass, field

from ..protocol import (
    Frame,
    FrameDecoder,
    FrameEncoder,
    MessageType,
    ErrorCode,
    HEARTBEAT_INTERVAL,
    CONNECTION_TIMEOUT,
    READ_BUFFER_SIZE
)

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection state enumeration."""
    
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass
class ConnectionStats:
    """Connection statistics."""
    
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    errors: int = 0
    last_activity: float = field(default_factory=time.time)
    connected_at: float = field(default_factory=time.time)


class Connection:
    """Represents a client connection."""
    
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                 connection_id: str, server: Any):
        """Initialize connection.
        
        Args:
            reader: Async stream reader
            writer: Async stream writer
            connection_id: Unique connection ID
            server: Reference to server instance
        """
        self.reader = reader
        self.writer = writer
        self.connection_id = connection_id
        self.server = server
        
        # Connection state
        self.state = ConnectionState.CONNECTING
        self.authenticated = False
        self.username: Optional[str] = None
        self.session_id: Optional[str] = None
        
        # Protocol handling
        self.decoder = FrameDecoder()
        self.encoder = FrameEncoder()
        
        # Statistics
        self.stats = ConnectionStats()
        
        # Tasks
        self.read_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # Rate limiting
        self.message_times: list[float] = []
        
        # Get peer info
        self.peer_address = writer.get_extra_info('peername')
        
    async def start(self):
        """Start connection handling."""
        logger.info(f"Connection {self.connection_id} started from {self.peer_address}")
        
        self.state = ConnectionState.CONNECTED
        
        # Start tasks
        self.read_task = asyncio.create_task(self._read_loop())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Wait for tasks to complete
        try:
            await asyncio.gather(self.read_task, self.heartbeat_task)
        except asyncio.CancelledError:
            pass
        finally:
            await self.close()
    
    async def _read_loop(self):
        """Read and process incoming data."""
        try:
            while self.state in (ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED):
                # Read data
                try:
                    data = await asyncio.wait_for(
                        self.reader.read(READ_BUFFER_SIZE),
                        timeout=CONNECTION_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Connection {self.connection_id} timed out")
                    await self.send_error(ErrorCode.TIMEOUT, "Connection timeout")
                    break
                
                if not data:
                    # Connection closed by client
                    logger.info(f"Connection {self.connection_id} closed by client")
                    break
                
                # Update stats
                self.stats.bytes_received += len(data)
                self.stats.last_activity = time.time()
                
                # Feed data to decoder
                self.decoder.feed(data)
                
                # Process frames
                while True:
                    try:
                        frame = self.decoder.decode_next()
                        if frame is None:
                            break
                        
                        self.stats.messages_received += 1
                        
                        # Handle frame
                        await self._handle_frame(frame)
                        
                    except ValueError as e:
                        logger.error(f"Frame decode error: {e}")
                        self.stats.errors += 1
                        await self.send_error(ErrorCode.CRC_MISMATCH, str(e))
                        # Clear buffer to recover
                        self.decoder.clear()
                        break
                
        except Exception as e:
            logger.error(f"Read loop error for {self.connection_id}: {e}")
            self.stats.errors += 1
        finally:
            self.state = ConnectionState.CLOSING
    
    async def _heartbeat_loop(self):
        """Monitor connection heartbeat."""
        try:
            while self.state in (ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED):
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                
                # Check last activity
                idle_time = time.time() - self.stats.last_activity
                
                if idle_time > CONNECTION_TIMEOUT:
                    logger.warning(f"Connection {self.connection_id} idle timeout")
                    await self.send_error(ErrorCode.TIMEOUT, "Idle timeout")
                    break
                
        except Exception as e:
            logger.error(f"Heartbeat loop error for {self.connection_id}: {e}")
    
    async def _handle_frame(self, frame: Frame):
        """Handle a received frame.
        
        Args:
            frame: Received frame
        """
        # Check rate limit
        if not self._check_rate_limit():
            await self.send_error(ErrorCode.RATE_LIMIT_EXCEEDED, "Rate limit exceeded")
            return
        
        # Route to appropriate handler
        if frame.message_type == MessageType.PING:
            await self._handle_ping(frame)
        elif frame.message_type == MessageType.ECHO:
            await self._handle_echo(frame)
        elif frame.message_type == MessageType.BROADCAST:
            await self._handle_broadcast(frame)
        elif frame.message_type == MessageType.AUTH:
            await self._handle_auth(frame)
        elif frame.message_type == MessageType.DATA:
            await self._handle_data(frame)
        elif frame.message_type == MessageType.CLOSE:
            await self._handle_close(frame)
        else:
            logger.warning(f"Unhandled message type: {frame.message_type}")
    
    async def _handle_ping(self, frame: Frame):
        """Handle PING message."""
        from ..protocol.frame import create_pong_frame, parse_ping_payload
        
        try:
            timestamp = parse_ping_payload(frame.payload)
            pong_frame = create_pong_frame(timestamp)
            await self.send_frame(pong_frame)
        except ValueError as e:
            await self.send_error(ErrorCode.INVALID_MESSAGE_TYPE, str(e))
    
    async def _handle_echo(self, frame: Frame):
        """Handle ECHO message."""
        # Send back ECHO_REPLY with same payload
        reply_frame = Frame(MessageType.ECHO_REPLY, frame.payload)
        await self.send_frame(reply_frame)
    
    async def _handle_broadcast(self, frame: Frame):
        """Handle BROADCAST message."""
        # Broadcast to all other connections
        await self.server.broadcast(frame, exclude=self.connection_id)
    
    async def _handle_auth(self, frame: Frame):
        """Handle AUTH message."""
        from ..protocol.messages import ProtocolMessages
        
        try:
            username, token = ProtocolMessages.parse_auth_message(frame.payload)
            
            # Simple authentication (can be extended)
            if self._authenticate(username, token):
                self.authenticated = True
                self.username = username
                self.session_id = f"{username}_{self.connection_id}"
                self.state = ConnectionState.AUTHENTICATED
                
                # Send success reply
                reply = ProtocolMessages.create_auth_reply(True, self.session_id)
                await self.send_frame(reply)
                
                logger.info(f"Connection {self.connection_id} authenticated as {username}")
            else:
                # Send failure reply
                reply = ProtocolMessages.create_auth_reply(False)
                await self.send_frame(reply)
                
        except ValueError as e:
            await self.send_error(ErrorCode.AUTHENTICATION_FAILED, str(e))
    
    async def _handle_data(self, frame: Frame):
        """Handle DATA message."""
        from ..protocol.messages import ProtocolMessages
        
        try:
            sequence, data = ProtocolMessages.parse_data_message(frame.payload)
            
            # Process data (can be extended)
            logger.debug(f"Received data seq={sequence}, len={len(data)}")
            
            # Send acknowledgment
            ack = ProtocolMessages.create_data_ack(sequence)
            await self.send_frame(ack)
            
        except ValueError as e:
            await self.send_error(ErrorCode.INVALID_MESSAGE_TYPE, str(e))
    
    async def _handle_close(self, frame: Frame):
        """Handle CLOSE message."""
        logger.info(f"Connection {self.connection_id} requested close")
        await self.close()
    
    def _authenticate(self, username: str, token: str) -> bool:
        """Authenticate user.
        
        Args:
            username: Username
            token: Authentication token
            
        Returns:
            True if authenticated, False otherwise
        """
        # Simple authentication - can be extended
        # In production, verify against database or auth service
        return len(username) > 0 and len(token) > 0
    
    def _check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded.
        
        Returns:
            True if within limit, False if exceeded
        """
        now = time.time()
        
        # Remove old timestamps
        self.message_times = [t for t in self.message_times if now - t < 1.0]
        
        # Check limit (1000 messages per second)
        if len(self.message_times) >= 1000:
            return False
        
        self.message_times.append(now)
        return True
    
    async def send_frame(self, frame: Frame):
        """Send a frame to the client.
        
        Args:
            frame: Frame to send
        """
        try:
            data = self.encoder.encode(frame)
            self.writer.write(data)
            await self.writer.drain()
            
            # Update stats
            self.stats.messages_sent += 1
            self.stats.bytes_sent += len(data)
            
        except Exception as e:
            logger.error(f"Failed to send frame to {self.connection_id}: {e}")
            self.stats.errors += 1
            await self.close()
    
    async def send_error(self, error_code: ErrorCode, message: str = ""):
        """Send an error frame.
        
        Args:
            error_code: Error code
            message: Error message
        """
        error_data = self.encoder.encode_error(error_code, message)
        
        try:
            self.writer.write(error_data)
            await self.writer.drain()
            
            self.stats.messages_sent += 1
            self.stats.bytes_sent += len(error_data)
            
        except Exception as e:
            logger.error(f"Failed to send error to {self.connection_id}: {e}")
    
    async def close(self):
        """Close the connection."""
        if self.state == ConnectionState.CLOSED:
            return
        
        self.state = ConnectionState.CLOSING
        
        # Cancel tasks
        if self.read_task and not self.read_task.done():
            self.read_task.cancel()
        
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
        
        # Close writer
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception as e:
            logger.error(f"Error closing connection {self.connection_id}: {e}")
        
        self.state = ConnectionState.CLOSED
        
        # Remove from server
        if self.server:
            await self.server.remove_connection(self.connection_id)
        
        logger.info(f"Connection {self.connection_id} closed. Stats: {self._format_stats()}")
    
    def _format_stats(self) -> str:
        """Format connection statistics."""
        duration = time.time() - self.stats.connected_at
        return (
            f"duration={duration:.1f}s, "
            f"msgs_in={self.stats.messages_received}, "
            f"msgs_out={self.stats.messages_sent}, "
            f"bytes_in={self.stats.bytes_received}, "
            f"bytes_out={self.stats.bytes_sent}, "
            f"errors={self.stats.errors}"
        )