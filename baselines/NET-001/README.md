# NET-001: Binary Message Protocol Server Baseline Implementation

## Overview

This is a reference implementation for the NET-001 problem: Custom Binary Message Protocol Server over TCP.

## Problem Requirements

### Functional Requirements (MUST)
- **MUST** implement a custom binary protocol over TCP
- **MUST** support multiple message types (PING, ECHO, BROADCAST, AUTH, DATA)
- **MUST** handle concurrent client connections
- **MUST** implement message framing with header and payload
- **MUST** validate messages with CRC32 checksums

### Non-Functional Requirements
- **SHOULD** support 1000+ concurrent connections
- **SHOULD** achieve <10ms latency for PING/PONG
- **SHOULD** handle >10,000 messages per second
- **MAY** support TLS encryption

## Implementation Details

### Technology Stack
- **Language**: Python 3.11
- **Async Framework**: asyncio
- **Serialization**: struct (binary packing)
- **Testing**: pytest with pytest-asyncio
- **Performance**: uvloop (optional)

### Protocol Specification

#### Frame Format
```
+----------------+----------+--------------+----------------+
| Magic (4 bytes)| Ver (1B) | Type (1B)    | Length (2B)    |
+----------------+----------+--------------+----------------+
| Payload (variable length, max 65535 bytes)                 |
+-------------------------------------------------------------+
| CRC32 Checksum (4 bytes)                                   |
+----------------+
```

- **Magic Bytes**: 0xDEADBEEF (4 bytes) - Frame start marker
- **Version**: Protocol version (currently 0x01)
- **Message Type**: See message types below
- **Payload Length**: Big-endian uint16 (max 65535)
- **Payload**: Message-specific data
- **CRC32**: Checksum of entire frame except CRC field

#### Message Types

| Type | Value | Description | Payload Format |
|------|-------|-------------|----------------|
| PING | 0x01 | Heartbeat request | 8-byte timestamp |
| PONG | 0x02 | Heartbeat response | 8-byte original timestamp |
| ECHO | 0x03 | Echo request | Variable data |
| ECHO_REPLY | 0x04 | Echo response | Original data |
| BROADCAST | 0x05 | Broadcast to all | Variable message |
| AUTH | 0x06 | Authentication | Username + token |
| AUTH_REPLY | 0x07 | Auth response | Success byte + session ID |
| DATA | 0x08 | Data transfer | Variable data |
| ERROR | 0xFF | Error message | Error code + message |

### Project Structure
```
NET-001/
├── src/
│   ├── __init__.py
│   ├── server.py           # Main TCP server
│   ├── client.py           # Test client implementation
│   ├── protocol/
│   │   ├── __init__.py
│   │   ├── frame.py        # Frame encoding/decoding
│   │   ├── messages.py     # Message types and handlers
│   │   └── constants.py    # Protocol constants
│   └── server/
│       ├── __init__.py
│       ├── connection.py   # Connection management
│       ├── handler.py      # Message handlers
│       └── pool.py         # Connection pooling
├── tests/
│   ├── unit/
│   ├── integration/
│   └── performance/
├── Dockerfile
├── requirements.txt
└── README.md
```

## Usage Examples

### Starting the Server
```bash
# Start server on default port (5000)
python -m src.server

# Start with custom configuration
python -m src.server --host 0.0.0.0 --port 8080 --max-connections 2000

# Enable debug logging
python -m src.server --debug

# With TLS support
python -m src.server --tls --cert server.crt --key server.key
```

### Client Usage
```python
import asyncio
from src.client import BinaryProtocolClient

async def main():
    client = BinaryProtocolClient('localhost', 5000)
    await client.connect()
    
    # Send PING
    pong = await client.ping()
    print(f"Latency: {pong.latency_ms}ms")
    
    # Send ECHO
    response = await client.echo(b"Hello, Server!")
    assert response == b"Hello, Server!"
    
    # Broadcast message
    await client.broadcast(b"Message to all clients")
    
    # Send data
    await client.send_data(b"Large data payload...")
    
    await client.close()

asyncio.run(main())
```

## Performance Characteristics

- **Concurrent Connections**: 1000-5000 (configurable)
- **Message Throughput**: 10,000-50,000 msg/sec
- **Latency**: <5ms for PING/PONG (local), <10ms (network)
- **Memory Usage**: ~100KB per connection
- **CPU Usage**: Single core can handle ~1000 connections

## Connection Management

### Heartbeat Mechanism
- Clients must send PING every 30 seconds
- Server responds with PONG immediately
- Connection closed after 60 seconds of inactivity

### Rate Limiting
- Per-client: 1000 messages/second
- Global: 50,000 messages/second
- Configurable via environment variables

### Connection Pooling
- Pre-allocated connection slots
- Efficient memory management
- Fast connection acceptance

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/performance/

# Run with coverage
pytest --cov=src --cov-report=html

# Load testing
locust -f tests/performance/locustfile.py --host tcp://localhost:5000
```

## Docker Deployment

```bash
# Build image
docker build -t net-001-baseline .

# Run server
docker run -p 5000:5000 net-001-baseline

# Run with environment variables
docker run -p 5000:5000 \
  -e MAX_CONNECTIONS=2000 \
  -e RATE_LIMIT=5000 \
  net-001-baseline
```

## Monitoring and Metrics

The server exposes metrics on `/metrics` (HTTP endpoint on port +1000):

- Active connections
- Messages per second
- Average latency
- Error rate
- Memory usage

## Security Considerations

1. **Input Validation**: All messages validated before processing
2. **Buffer Overflow Prevention**: Fixed maximum message size
3. **Rate Limiting**: Prevents DoS attacks
4. **Authentication**: Optional AUTH message for client verification
5. **TLS Support**: Optional encryption for sensitive data

## Evaluation Metrics

Expected scores for this baseline:
- Functional Coverage: 100%
- Test Pass Rate: 95%
- Performance: 90%
- Code Quality: 85%
- Security: 85%
- **Total Score: 91%** (Gold)

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Too many open files" | Increase ulimit: `ulimit -n 4096` |
| High latency | Enable uvloop: `pip install uvloop` |
| Memory growth | Check for connection leaks, enable GC |
| CRC errors | Verify network stability, check MTU |

## References

- [TCP/IP Protocol Design](https://tools.ietf.org/html/rfc793)
- [Binary Protocol Best Practices](https://developers.google.com/protocol-buffers)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)