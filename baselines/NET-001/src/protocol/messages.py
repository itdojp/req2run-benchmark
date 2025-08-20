"""Message handling for the binary protocol."""

import time
import struct
from typing import Any, Dict, Optional, Callable, Awaitable, List, Tuple
from dataclasses import dataclass

from .constants import MessageType, ErrorCode
from .frame import Frame


@dataclass
class Message:
    """High-level message representation."""
    
    type: MessageType
    data: Any
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class MessageHandler:
    """Handles different message types."""
    
    def __init__(self):
        """Initialize message handler."""
        self.handlers: Dict[MessageType, Callable] = {}
        self.default_handler: Optional[Callable] = None
    
    def register(self, message_type: MessageType):
        """Decorator to register a message handler.
        
        Args:
            message_type: Type of message to handle
        """
        def decorator(func: Callable):
            self.handlers[message_type] = func
            return func
        return decorator
    
    def set_default(self, handler: Callable):
        """Set default handler for unknown message types.
        
        Args:
            handler: Default handler function
        """
        self.default_handler = handler
    
    async def handle(self, frame: Frame, context: Any) -> Optional[Frame]:
        """Handle a received frame.
        
        Args:
            frame: Received frame
            context: Handler context (e.g., connection object)
            
        Returns:
            Optional response frame
        """
        handler = self.handlers.get(frame.message_type, self.default_handler)
        
        if handler is None:
            # No handler registered
            return None
        
        # Call handler
        if asyncio.iscoroutinefunction(handler):
            return await handler(frame, context)
        else:
            return handler(frame, context)


class ProtocolMessages:
    """Protocol message creation and parsing utilities."""
    
    @staticmethod
    def create_auth_message(username: str, token: str) -> Frame:
        """Create authentication message.
        
        Args:
            username: Username
            token: Authentication token
            
        Returns:
            AUTH frame
        """
        # Format: username_len (1 byte) + username + token
        username_bytes = username.encode('utf-8')
        token_bytes = token.encode('utf-8')
        
        if len(username_bytes) > 255:
            raise ValueError("Username too long")
        
        payload = struct.pack('B', len(username_bytes))
        payload += username_bytes
        payload += token_bytes
        
        return Frame(MessageType.AUTH, payload)
    
    @staticmethod
    def parse_auth_message(payload: bytes) -> Tuple[str, str]:
        """Parse authentication message.
        
        Args:
            payload: AUTH payload
            
        Returns:
            Tuple of (username, token)
        """
        if len(payload) < 2:
            raise ValueError("Invalid AUTH payload")
        
        username_len = payload[0]
        if len(payload) < 1 + username_len:
            raise ValueError("Invalid AUTH payload length")
        
        username = payload[1:1+username_len].decode('utf-8')
        token = payload[1+username_len:].decode('utf-8')
        
        return username, token
    
    @staticmethod
    def create_auth_reply(success: bool, session_id: Optional[str] = None) -> Frame:
        """Create authentication reply.
        
        Args:
            success: Whether authentication succeeded
            session_id: Optional session ID if successful
            
        Returns:
            AUTH_REPLY frame
        """
        payload = struct.pack('B', 1 if success else 0)
        
        if success and session_id:
            payload += session_id.encode('utf-8')
        
        return Frame(MessageType.AUTH_REPLY, payload)
    
    @staticmethod
    def parse_auth_reply(payload: bytes) -> Tuple[bool, Optional[str]]:
        """Parse authentication reply.
        
        Args:
            payload: AUTH_REPLY payload
            
        Returns:
            Tuple of (success, session_id)
        """
        if len(payload) < 1:
            raise ValueError("Invalid AUTH_REPLY payload")
        
        success = payload[0] == 1
        session_id = None
        
        if success and len(payload) > 1:
            session_id = payload[1:].decode('utf-8')
        
        return success, session_id
    
    @staticmethod
    def create_data_message(data: bytes, sequence: int = 0) -> Frame:
        """Create data message.
        
        Args:
            data: Data to send
            sequence: Optional sequence number
            
        Returns:
            DATA frame
        """
        # Format: sequence (4 bytes) + data
        payload = struct.pack('>I', sequence) + data
        return Frame(MessageType.DATA, payload)
    
    @staticmethod
    def parse_data_message(payload: bytes) -> Tuple[int, bytes]:
        """Parse data message.
        
        Args:
            payload: DATA payload
            
        Returns:
            Tuple of (sequence, data)
        """
        if len(payload) < 4:
            raise ValueError("Invalid DATA payload")
        
        sequence = struct.unpack('>I', payload[:4])[0]
        data = payload[4:]
        
        return sequence, data
    
    @staticmethod
    def create_data_ack(sequence: int) -> Frame:
        """Create data acknowledgment.
        
        Args:
            sequence: Sequence number to acknowledge
            
        Returns:
            DATA_ACK frame
        """
        payload = struct.pack('>I', sequence)
        return Frame(MessageType.DATA_ACK, payload)
    
    @staticmethod
    def parse_data_ack(payload: bytes) -> int:
        """Parse data acknowledgment.
        
        Args:
            payload: DATA_ACK payload
            
        Returns:
            Acknowledged sequence number
        """
        if len(payload) != 4:
            raise ValueError("Invalid DATA_ACK payload")
        
        return struct.unpack('>I', payload)[0]


import asyncio


class MessageProcessor:
    """Processes messages with rate limiting and validation."""
    
    def __init__(self, rate_limit: int = 1000):
        """Initialize processor.
        
        Args:
            rate_limit: Messages per second limit
        """
        self.rate_limit = rate_limit
        self.message_times: List[float] = []
        self.handler = MessageHandler()
    
    def check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded.
        
        Returns:
            True if within limit, False if exceeded
        """
        now = time.time()
        
        # Remove old timestamps (outside 1-second window)
        self.message_times = [t for t in self.message_times if now - t < 1.0]
        
        # Check limit
        if len(self.message_times) >= self.rate_limit:
            return False
        
        # Add current timestamp
        self.message_times.append(now)
        return True
    
    async def process(self, frame: Frame, context: Any) -> Optional[Frame]:
        """Process a message frame.
        
        Args:
            frame: Message frame
            context: Processing context
            
        Returns:
            Optional response frame
        """
        # Check rate limit
        if not self.check_rate_limit():
            # Rate limit exceeded
            from .frame import FrameEncoder
            return FrameEncoder.encode_error(
                ErrorCode.RATE_LIMIT_EXCEEDED,
                "Message rate limit exceeded"
            )
        
        # Validate frame
        if frame.payload_length > MAX_PAYLOAD_SIZE:
            from .frame import FrameEncoder
            return FrameEncoder.encode_error(
                ErrorCode.PAYLOAD_TOO_LARGE,
                f"Payload size {frame.payload_length} exceeds maximum"
            )
        
        # Process message
        return await self.handler.handle(frame, context)


from .constants import MAX_PAYLOAD_SIZE