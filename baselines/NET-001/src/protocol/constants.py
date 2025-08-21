"""Protocol constants and configuration."""

from enum import IntEnum

# Protocol constants
MAGIC_BYTES = 0xDEADBEEF
PROTOCOL_VERSION = 0x01
MAX_PAYLOAD_SIZE = 65535  # 2^16 - 1
HEADER_SIZE = 8  # Magic(4) + Version(1) + Type(1) + Length(2)
CRC_SIZE = 4
FRAME_OVERHEAD = HEADER_SIZE + CRC_SIZE

# Connection constants
DEFAULT_PORT = 5000
DEFAULT_BACKLOG = 128
DEFAULT_MAX_CONNECTIONS = 1000
CONNECTION_TIMEOUT = 60  # seconds
HEARTBEAT_INTERVAL = 30  # seconds
READ_BUFFER_SIZE = 4096

# Rate limiting
DEFAULT_RATE_LIMIT_PER_CLIENT = 1000  # messages per second
DEFAULT_GLOBAL_RATE_LIMIT = 50000  # messages per second
RATE_LIMIT_WINDOW = 1  # second


class MessageType(IntEnum):
    """Protocol message types."""
    
    # Heartbeat messages
    PING = 0x01
    PONG = 0x02
    
    # Echo messages
    ECHO = 0x03
    ECHO_REPLY = 0x04
    
    # Broadcast messages
    BROADCAST = 0x05
    
    # Authentication
    AUTH = 0x06
    AUTH_REPLY = 0x07
    
    # Data transfer
    DATA = 0x08
    DATA_ACK = 0x09
    
    # Control messages
    CLOSE = 0x0A
    
    # Error message
    ERROR = 0xFF


class ErrorCode(IntEnum):
    """Protocol error codes."""
    
    UNKNOWN = 0x00
    INVALID_MAGIC = 0x01
    INVALID_VERSION = 0x02
    INVALID_MESSAGE_TYPE = 0x03
    PAYLOAD_TOO_LARGE = 0x04
    CRC_MISMATCH = 0x05
    AUTHENTICATION_FAILED = 0x06
    RATE_LIMIT_EXCEEDED = 0x07
    CONNECTION_LIMIT_EXCEEDED = 0x08
    TIMEOUT = 0x09
    INTERNAL_ERROR = 0xFF


# Error messages
ERROR_MESSAGES = {
    ErrorCode.UNKNOWN: "Unknown error",
    ErrorCode.INVALID_MAGIC: "Invalid magic bytes",
    ErrorCode.INVALID_VERSION: "Unsupported protocol version",
    ErrorCode.INVALID_MESSAGE_TYPE: "Invalid message type",
    ErrorCode.PAYLOAD_TOO_LARGE: "Payload exceeds maximum size",
    ErrorCode.CRC_MISMATCH: "CRC checksum mismatch",
    ErrorCode.AUTHENTICATION_FAILED: "Authentication failed",
    ErrorCode.RATE_LIMIT_EXCEEDED: "Rate limit exceeded",
    ErrorCode.CONNECTION_LIMIT_EXCEEDED: "Connection limit exceeded",
    ErrorCode.TIMEOUT: "Connection timeout",
    ErrorCode.INTERNAL_ERROR: "Internal server error",
}