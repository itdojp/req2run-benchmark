# RTC-001: WebRTC Video Conferencing Server with SFU

## Overview

A production-grade WebRTC video conferencing server implementing Selective Forwarding Unit (SFU) architecture. The system supports multiple concurrent rooms, adaptive bitrate streaming, simulcast for quality adaptation, screen sharing, and recording capabilities. Built for scalability and real-time performance.

## Key Features

### SFU Architecture
- **Selective Forwarding**: Efficiently forwards streams without transcoding
- **Scalable Design**: Supports 1000+ concurrent rooms
- **Low Latency**: Sub-150ms P95 latency
- **Bandwidth Efficient**: Minimal server-side processing

### Core Capabilities
- **Multi-Room Support**: Concurrent conference rooms with isolation
- **Adaptive Bitrate**: Dynamic quality adjustment based on network conditions
- **Simulcast**: Multiple quality layers for optimal bandwidth usage
- **Screen Sharing**: Dedicated screen share alongside video
- **Recording**: Room recording with configurable quality

### Advanced Features
- **End-to-End Encryption**: Optional E2EE support
- **Virtual Backgrounds**: Client-side background processing
- **Bandwidth Estimation**: Google Congestion Control (GCC)
- **Packet Loss Recovery**: FEC and NACK support
- **Jitter Buffer**: Adaptive buffering for smooth playback

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SFU Server                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │              │         │              │             │
│  │  Signaling   │◄────────│   Room       │             │
│  │  WebSocket   │         │  Manager     │             │
│  │              │         │              │             │
│  └──────────────┘         └──────────────┘             │
│         ▲                        │                      │
│         │                        ▼                      │
│  ┌──────────────┐         ┌──────────────┐             │
│  │              │         │              │             │
│  │   WebRTC     │◄────────│   Media      │             │
│  │   Engine     │         │   Router     │             │
│  │              │         │              │             │
│  └──────────────┘         └──────────────┘             │
│         ▲                        │                      │
│         │                        ▼                      │
│  ┌──────────────┐         ┌──────────────┐             │
│  │              │         │              │             │
│  │  Adaptive    │◄────────│  Recording   │             │
│  │   Bitrate    │         │   Engine     │             │
│  │              │         │              │             │
│  └──────────────┘         └──────────────┘             │
│                                                          │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
                    WebRTC Clients
```

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t webrtc-sfu-server .

# Run the server
docker run -p 8080:8080 -p 8443:8443 \
  -v $(pwd)/recordings:/app/recordings \
  webrtc-sfu-server

# Access the server
# WebSocket: ws://localhost:8080/ws
# API: http://localhost:8080/api
# Health: http://localhost:8080/health
```

### Manual Setup

1. **Install system dependencies:**
```bash
# Ubuntu/Debian
apt-get install ffmpeg libavformat-dev libavcodec-dev \
  libavdevice-dev libavutil-dev libopus-dev libvpx-dev

# macOS
brew install ffmpeg opus libvpx
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure the server:**
```bash
# Edit configuration
vi config/webrtc.yaml
```

4. **Run the server:**
```bash
python src/main.py
```

## API Documentation

### WebSocket Signaling

Connect to `ws://localhost:8080/ws` for signaling.

#### Join Room
```json
{
  "type": "join",
  "roomId": "room-123",
  "participantName": "John Doe"
}
```

#### Send Offer
```json
{
  "type": "offer",
  "roomId": "room-123",
  "sdp": "v=0\r\n..."
}
```

#### Send ICE Candidate
```json
{
  "type": "ice-candidate",
  "candidate": {
    "candidate": "candidate:...",
    "sdpMLineIndex": 0,
    "sdpMid": "0"
  }
}
```

#### Start Screen Share
```json
{
  "type": "start-screen-share",
  "roomId": "room-123",
  "sdp": "v=0\r\n..."
}
```

#### Update Quality
```json
{
  "type": "update-quality",
  "roomId": "room-123",
  "quality": "high"
}
```

### REST API

#### Create Room
```bash
curl -X POST http://localhost:8080/api/rooms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Conference Room",
    "maxParticipants": 50
  }'
```

#### List Rooms
```bash
curl http://localhost:8080/api/rooms
```

#### Get Room Details
```bash
curl http://localhost:8080/api/rooms/room-123
```

#### Get Room Statistics
```bash
curl http://localhost:8080/api/rooms/room-123/stats
```

#### Start Recording
```bash
curl -X POST http://localhost:8080/api/rooms/room-123/recording/start
```

#### Stop Recording
```bash
curl -X POST http://localhost:8080/api/rooms/room-123/recording/stop
```

## Configuration

### Server Configuration (`config/webrtc.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8080

webrtc:
  ice_servers:
    - urls: ["stun:stun.l.google.com:19302"]
  max_bitrate: 5000000
  simulcast: true

rooms:
  max_participants: 100
  auto_create: true
  idle_timeout: 3600

recording:
  enabled: true
  path: "recordings"
  format: "webm"
```

### Media Configuration (`config/media.yaml`)

```yaml
video:
  codecs:
    - name: "VP8"
      priority: 100
    - name: "H264"
      priority: 80
  
  resolutions:
    preferred:
      width: 1280
      height: 720

audio:
  codecs:
    - name: "opus"
      priority: 100
  
  processing:
    echo_cancellation: true
    noise_suppression: true
```

## Simulcast Configuration

The server supports simulcast with three quality layers:

### Low Quality
- Resolution: 320x240
- Bitrate: 150 Kbps
- Framerate: 15 fps

### Medium Quality
- Resolution: 640x480
- Bitrate: 500 Kbps
- Framerate: 30 fps

### High Quality
- Resolution: 1280x720
- Bitrate: 2.5 Mbps
- Framerate: 30 fps

## Adaptive Bitrate Control

The server implements Google Congestion Control (GCC) algorithm:

1. **Bandwidth Estimation**: Continuous monitoring of available bandwidth
2. **Packet Loss Detection**: Adjusts bitrate based on packet loss
3. **Jitter Analysis**: Considers network jitter in quality decisions
4. **Dynamic Adjustment**: Real-time bitrate modification

## Recording

### Local Recording
```yaml
recording:
  enabled: true
  path: "recordings"
  format: "webm"
  video_bitrate: 2500000
  audio_bitrate: 128000
```

### Cloud Recording (S3)
```yaml
recording:
  s3_upload: true
  s3_bucket: "recordings"
  s3_region: "us-east-1"
```

## Client Example

```javascript
// Create peer connection
const pc = new RTCPeerConnection({
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' }
  ]
});

// Connect to signaling
const ws = new WebSocket('ws://localhost:8080/ws');

// Join room
ws.send(JSON.stringify({
  type: 'join',
  roomId: 'room-123',
  participantName: 'John Doe'
}));

// Handle signaling messages
ws.onmessage = async (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'request-offer') {
    // Create and send offer
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    
    ws.send(JSON.stringify({
      type: 'offer',
      roomId: data.roomId,
      sdp: offer.sdp
    }));
  } else if (data.type === 'answer') {
    // Set remote description
    await pc.setRemoteDescription({
      type: 'answer',
      sdp: data.sdp
    });
  }
};

// Add local stream
const stream = await navigator.mediaDevices.getUserMedia({
  video: true,
  audio: true
});

stream.getTracks().forEach(track => {
  pc.addTrack(track, stream);
});
```

## Performance Tuning

### Network Optimization
```yaml
webrtc:
  jitter_buffer_target: 200  # ms
  jitter_buffer_max: 1000    # ms
  dtx: true  # Discontinuous Transmission
  fec: true  # Forward Error Correction
  nack: true # Negative Acknowledgment
```

### CPU Optimization
```yaml
performance:
  worker_threads: 8
  max_cpu_per_room: 25  # percent
  hardware_acceleration: true
```

### Memory Optimization
```yaml
performance:
  max_memory_per_room: 100  # MB
  max_memory_total: 8192     # MB
  garbage_collection_interval: 60  # seconds
```

## Monitoring

### Prometheus Metrics
```bash
# Access metrics
curl http://localhost:9090/metrics

# Key metrics
- webrtc_rooms_total
- webrtc_participants_total
- webrtc_video_tracks_total
- webrtc_audio_tracks_total
- webrtc_bandwidth_usage_bytes
- webrtc_packet_loss_rate
- webrtc_jitter_ms
```

### Health Check
```bash
curl http://localhost:8080/health

# Response
{
  "status": "healthy",
  "rooms": 5,
  "participants": 23,
  "config": {
    "max_rooms": 1000,
    "max_participants_per_room": 100
  }
}
```

## Security

### DTLS-SRTP
All media streams are encrypted using DTLS-SRTP by default.

### Authentication (Optional)
```yaml
security:
  require_auth: true
  auth_token_header: "X-Auth-Token"
```

### Rate Limiting
```yaml
security:
  rate_limit:
    enabled: true
    max_rooms_per_ip: 10
    max_participants_per_ip: 50
```

## Troubleshooting

### Connection Issues
```bash
# Check ICE candidates
webrtc-internals  # Chrome: chrome://webrtc-internals

# Test STUN server
stun-client stun.l.google.com:19302
```

### Quality Issues
```bash
# Check network stats
curl http://localhost:8080/api/rooms/room-123/stats

# Adjust bitrate limits
vi config/webrtc.yaml
# Modify max_bitrate, min_bitrate
```

### Recording Issues
```bash
# Check recording path permissions
ls -la recordings/

# Verify ffmpeg installation
ffmpeg -version

# Check disk space
df -h
```

## Production Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  webrtc-sfu:
    image: webrtc-sfu-server
    ports:
      - "8080:8080"
      - "8443:8443"
    volumes:
      - ./recordings:/app/recordings
      - ./config:/app/config
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webrtc-sfu
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: sfu
        image: webrtc-sfu-server
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "2Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "8"
```

## Scaling Considerations

1. **Horizontal Scaling**: Deploy multiple SFU instances behind a load balancer
2. **Room Distribution**: Use consistent hashing for room assignment
3. **Media Servers**: Separate signaling from media servers
4. **Recording Offload**: Use dedicated recording servers
5. **CDN Integration**: Use CDN for recorded content delivery

## License

MIT