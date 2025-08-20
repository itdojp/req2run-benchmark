"""Frame encoding and decoding for the binary protocol."""

import struct
import zlib
from typing import Optional, Tuple, List
from dataclasses import dataclass

from .constants import (
    MAGIC_BYTES,
    PROTOCOL_VERSION,
    MAX_PAYLOAD_SIZE,
    HEADER_SIZE,
    CRC_SIZE,
    MessageType,
    ErrorCode
)


@dataclass
class Frame:
    """Represents a protocol frame."""
    
    message_type: MessageType
    payload: bytes
    version: int = PROTOCOL_VERSION
    
    def __post_init__(self):
        """Validate frame after initialization."""
        if len(self.payload) > MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload size {len(self.payload)} exceeds maximum {MAX_PAYLOAD_SIZE}")
        
        if not isinstance(self.message_type, MessageType):
            try:
                self.message_type = MessageType(self.message_type)
            except ValueError:
                raise ValueError(f"Invalid message type: {self.message_type}")
    
    @property
    def payload_length(self) -> int:
        """Get payload length."""
        return len(self.payload)
    
    def calculate_crc(self) -> int:
        """Calculate CRC32 for the frame."""
        # Pack header without CRC
        header = struct.pack(
            '>IBBH',  # Big-endian: uint32, uint8, uint8, uint16
            MAGIC_BYTES,
            self.version,
            self.message_type.value,
            self.payload_length
        )
        # Calculate CRC of header + payload
        return zlib.crc32(header + self.payload) & 0xFFFFFFFF


class FrameEncoder:
    """Encodes frames to binary format."""
    
    @staticmethod
    def encode(frame: Frame) -> bytes:
        """Encode a frame to binary format.
        
        Args:
            frame: Frame to encode
            
        Returns:
            Encoded frame bytes
            
        Raises:
            ValueError: If frame is invalid
        """
        # Validate frame
        if not isinstance(frame, Frame):
            raise ValueError("Invalid frame object")
        
        # Pack header
        header = struct.pack(
            '>IBBH',  # Big-endian: uint32, uint8, uint8, uint16
            MAGIC_BYTES,
            frame.version,
            frame.message_type.value,
            frame.payload_length
        )
        
        # Calculate CRC
        crc = frame.calculate_crc()
        
        # Pack CRC
        crc_bytes = struct.pack('>I', crc)
        
        # Combine header + payload + CRC
        return header + frame.payload + crc_bytes
    
    @staticmethod
    def encode_error(error_code: ErrorCode, message: str = "") -> bytes:
        """Encode an error frame.
        
        Args:
            error_code: Error code
            message: Optional error message
            
        Returns:
            Encoded error frame
        """
        # Pack error payload: code (1 byte) + message (UTF-8)
        payload = struct.pack('B', error_code.value)
        if message:
            payload += message.encode('utf-8')
        
        frame = Frame(
            message_type=MessageType.ERROR,
            payload=payload
        )
        
        return FrameEncoder.encode(frame)


class FrameDecoder:
    """Decodes frames from binary format."""
    
    def __init__(self):
        """Initialize decoder with buffer."""
        self.buffer = bytearray()
    
    def feed(self, data: bytes) -> None:
        """Feed data to the decoder buffer.
        
        Args:
            data: Raw bytes to add to buffer
        """
        self.buffer.extend(data)
    
    def decode_next(self) -> Optional[Frame]:
        """Decode the next frame from buffer.
        
        Returns:
            Decoded frame or None if insufficient data
            
        Raises:
            ValueError: If frame is malformed
        """
        # Need at least header + CRC
        if len(self.buffer) < HEADER_SIZE + CRC_SIZE:
            return None
        
        # Unpack header
        try:
            magic, version, msg_type, payload_length = struct.unpack(
                '>IBBH',
                self.buffer[:HEADER_SIZE]
            )
        except struct.error:
            raise ValueError("Failed to unpack header")
        
        # Validate magic bytes
        if magic != MAGIC_BYTES:
            raise ValueError(f"Invalid magic bytes: {magic:#x}")
        
        # Validate version
        if version != PROTOCOL_VERSION:
            raise ValueError(f"Unsupported protocol version: {version}")
        
        # Validate message type
        try:
            message_type = MessageType(msg_type)
        except ValueError:
            raise ValueError(f"Invalid message type: {msg_type}")
        
        # Check if we have complete frame
        frame_size = HEADER_SIZE + payload_length + CRC_SIZE
        if len(self.buffer) < frame_size:
            return None
        
        # Extract payload
        payload_start = HEADER_SIZE
        payload_end = payload_start + payload_length
        payload = bytes(self.buffer[payload_start:payload_end])
        
        # Extract and verify CRC
        crc_start = payload_end
        crc_end = crc_start + CRC_SIZE
        received_crc = struct.unpack('>I', self.buffer[crc_start:crc_end])[0]
        
        # Calculate expected CRC
        frame_data = self.buffer[:payload_end]
        expected_crc = zlib.crc32(frame_data) & 0xFFFFFFFF
        
        if received_crc != expected_crc:
            raise ValueError(f"CRC mismatch: expected {expected_crc:#x}, got {received_crc:#x}")
        
        # Remove frame from buffer
        del self.buffer[:frame_size]
        
        # Create and return frame
        return Frame(
            message_type=message_type,
            payload=payload,
            version=version
        )
    
    def decode_all(self) -> List[Frame]:
        """Decode all available frames from buffer.
        
        Returns:
            List of decoded frames
        """
        frames = []
        while True:
            frame = self.decode_next()
            if frame is None:
                break
            frames.append(frame)
        return frames
    
    def clear(self) -> None:
        """Clear the decoder buffer."""
        self.buffer.clear()
    
    @property
    def buffer_size(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)


def create_ping_frame(timestamp: int) -> Frame:
    """Create a PING frame.
    
    Args:
        timestamp: Unix timestamp in milliseconds
        
    Returns:
        PING frame
    """
    payload = struct.pack('>Q', timestamp)  # 8-byte unsigned long
    return Frame(MessageType.PING, payload)


def create_pong_frame(timestamp: int) -> Frame:
    """Create a PONG frame.
    
    Args:
        timestamp: Original timestamp from PING
        
    Returns:
        PONG frame
    """
    payload = struct.pack('>Q', timestamp)
    return Frame(MessageType.PONG, payload)


def create_echo_frame(data: bytes) -> Frame:
    """Create an ECHO frame.
    
    Args:
        data: Data to echo
        
    Returns:
        ECHO frame
    """
    return Frame(MessageType.ECHO, data)


def create_broadcast_frame(message: bytes) -> Frame:
    """Create a BROADCAST frame.
    
    Args:
        message: Message to broadcast
        
    Returns:
        BROADCAST frame
    """
    return Frame(MessageType.BROADCAST, message)


def parse_ping_payload(payload: bytes) -> int:
    """Parse PING payload to get timestamp.
    
    Args:
        payload: PING payload
        
    Returns:
        Timestamp in milliseconds
    """
    if len(payload) != 8:
        raise ValueError(f"Invalid PING payload size: {len(payload)}")
    return struct.unpack('>Q', payload)[0]


def parse_error_payload(payload: bytes) -> Tuple[ErrorCode, str]:
    """Parse ERROR payload.
    
    Args:
        payload: ERROR payload
        
    Returns:
        Tuple of (error_code, message)
    """
    if len(payload) < 1:
        raise ValueError("Empty error payload")
    
    error_code = ErrorCode(payload[0])
    message = payload[1:].decode('utf-8') if len(payload) > 1 else ""
    
    return error_code, message