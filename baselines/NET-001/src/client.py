#!/usr/bin/env python3
"""Binary protocol TCP client implementation."""

import asyncio
import time
import struct
from typing import Optional

from protocol import (
    Frame,
    FrameEncoder,
    FrameDecoder,
    MessageType,
    create_ping_frame,
    create_echo_frame,
    create_broadcast_frame,
    parse_ping_payload
)
from protocol.messages import ProtocolMessages


class BinaryProtocolClient:
    """Binary protocol TCP client."""
    
    def __init__(self, host: str, port: int):
        """Initialize client.
        
        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port
        
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        
        self.encoder = FrameEncoder()
        self.decoder = FrameDecoder()
        
        self.connected = False
        self.authenticated = False
        self.session_id: Optional[str] = None
        
        # Response tracking
        self.pending_responses = {}
        self.response_event = asyncio.Event()
        
        self.read_task: Optional[asyncio.Task] = None
    
    async def connect(self, timeout: float = 5.0):
        """Connect to server.
        
        Args:
            timeout: Connection timeout in seconds
        """
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port),
            timeout=timeout
        )
        
        self.connected = True
        
        # Start read task
        self.read_task = asyncio.create_task(self._read_loop())
    
    async def _read_loop(self):
        """Read and process server responses."""
        while self.connected:
            try:
                data = await self.reader.read(4096)
                if not data:
                    break
                
                self.decoder.feed(data)
                
                while True:
                    frame = self.decoder.decode_next()
                    if frame is None:
                        break
                    
                    await self._handle_response(frame)
                    
            except Exception as e:
                print(f"Read error: {e}")
                break
    
    async def _handle_response(self, frame: Frame):
        """Handle server response.
        
        Args:
            frame: Response frame
        """
        # Store response for waiting requests
        if frame.message_type in self.pending_responses:
            self.pending_responses[frame.message_type] = frame
            self.response_event.set()
    
    async def _send_and_wait(self, frame: Frame, response_type: MessageType,
                            timeout: float = 5.0) -> Optional[Frame]:
        """Send frame and wait for response.
        
        Args:
            frame: Frame to send
            response_type: Expected response type
            timeout: Response timeout
            
        Returns:
            Response frame or None if timeout
        """
        # Register pending response
        self.pending_responses[response_type] = None
        self.response_event.clear()
        
        # Send frame
        await self.send_frame(frame)
        
        # Wait for response
        try:
            await asyncio.wait_for(self.response_event.wait(), timeout=timeout)
            return self.pending_responses.get(response_type)
        except asyncio.TimeoutError:
            return None
        finally:
            self.pending_responses.pop(response_type, None)
    
    async def send_frame(self, frame: Frame):
        """Send a frame to server.
        
        Args:
            frame: Frame to send
        """
        if not self.connected:
            raise RuntimeError("Not connected")
        
        data = self.encoder.encode(frame)
        self.writer.write(data)
        await self.writer.drain()
    
    async def ping(self) -> float:
        """Send PING and measure latency.
        
        Returns:
            Latency in milliseconds
        """
        timestamp = int(time.time() * 1000)
        ping_frame = create_ping_frame(timestamp)
        
        response = await self._send_and_wait(ping_frame, MessageType.PONG)
        
        if response:
            original_timestamp = parse_ping_payload(response.payload)
            latency = int(time.time() * 1000) - original_timestamp
            return latency
        
        raise TimeoutError("PING timeout")
    
    async def echo(self, data: bytes) -> bytes:
        """Send ECHO request.
        
        Args:
            data: Data to echo
            
        Returns:
            Echoed data
        """
        echo_frame = create_echo_frame(data)
        response = await self._send_and_wait(echo_frame, MessageType.ECHO_REPLY)
        
        if response:
            return response.payload
        
        raise TimeoutError("ECHO timeout")
    
    async def broadcast(self, message: bytes):
        """Send broadcast message.
        
        Args:
            message: Message to broadcast
        """
        broadcast_frame = create_broadcast_frame(message)
        await self.send_frame(broadcast_frame)
    
    async def authenticate(self, username: str, token: str) -> bool:
        """Authenticate with server.
        
        Args:
            username: Username
            token: Authentication token
            
        Returns:
            True if authenticated, False otherwise
        """
        auth_frame = ProtocolMessages.create_auth_message(username, token)
        response = await self._send_and_wait(auth_frame, MessageType.AUTH_REPLY)
        
        if response:
            success, session_id = ProtocolMessages.parse_auth_reply(response.payload)
            if success:
                self.authenticated = True
                self.session_id = session_id
            return success
        
        return False
    
    async def send_data(self, data: bytes, sequence: int = 0) -> bool:
        """Send data message.
        
        Args:
            data: Data to send
            sequence: Sequence number
            
        Returns:
            True if acknowledged
        """
        data_frame = ProtocolMessages.create_data_message(data, sequence)
        response = await self._send_and_wait(data_frame, MessageType.DATA_ACK)
        
        if response:
            ack_seq = ProtocolMessages.parse_data_ack(response.payload)
            return ack_seq == sequence
        
        return False
    
    async def close(self):
        """Close connection."""
        if not self.connected:
            return
        
        # Send CLOSE message
        close_frame = Frame(MessageType.CLOSE, b'')
        await self.send_frame(close_frame)
        
        # Cancel read task
        if self.read_task:
            self.read_task.cancel()
        
        # Close writer
        self.writer.close()
        await self.writer.wait_closed()
        
        self.connected = False


async def main():
    """Example client usage."""
    client = BinaryProtocolClient('localhost', 5000)
    
    try:
        # Connect
        await client.connect()
        print("Connected to server")
        
        # Authenticate
        if await client.authenticate("testuser", "testtoken"):
            print(f"Authenticated with session: {client.session_id}")
        
        # Send PING
        latency = await client.ping()
        print(f"Ping latency: {latency}ms")
        
        # Send ECHO
        echo_data = b"Hello, Server!"
        response = await client.echo(echo_data)
        print(f"Echo response: {response}")
        
        # Send broadcast
        await client.broadcast(b"This is a broadcast message")
        print("Broadcast sent")
        
        # Send data
        if await client.send_data(b"Some important data", sequence=1):
            print("Data acknowledged")
        
    finally:
        await client.close()
        print("Connection closed")


if __name__ == '__main__':
    asyncio.run(main())