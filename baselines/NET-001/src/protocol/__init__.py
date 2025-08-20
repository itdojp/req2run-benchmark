"""Binary protocol implementation."""

from .constants import *
from .frame import Frame, FrameEncoder, FrameDecoder
from .messages import Message, MessageType, MessageHandler

__all__ = [
    "Frame",
    "FrameEncoder",
    "FrameDecoder",
    "Message",
    "MessageType",
    "MessageHandler",
    "MAGIC_BYTES",
    "PROTOCOL_VERSION",
]