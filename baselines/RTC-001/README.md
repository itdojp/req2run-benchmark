# RTC-001: WebRTC Video Conferencing Server with SFU

**Language / 言語**
- [English](#rtc-001-webrtc-video-conferencing-server-with-sfu)
- [日本語](#rtc-001-sfu機能付きwebrtcビデオ会議サーバー)

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

---

# RTC-001: SFU機能付きWebRTCビデオ会議サーバー

## 概要

Selective Forwarding Unit (SFU)アーキテクチャを実装した本格的なWebRTCビデオ会議サーバー。このシステムは、複数の同時ルーム、適応ビットレートストリーミング、品質適応のためのサイマルキャスト、スクリーン共有、録画機能をサポートします。スケーラビリティとリアルタイムパフォーマンスのために構築されています。

## 主要機能

### SFUアーキテクチャ
- **選択的転送**: トランスコーディングなしで効率的にストリームを転送
- **スケーラブルデザイン**: 1000+の同時ルームをサポート
- **低レイテンシ**: 150ms未満のP95レイテンシ
- **帯域効率**: サーバーサイドの処理を最小限に抑制

### コア機能
- **マルチルームサポート**: 分離された同時会議ルーム
- **適応ビットレート**: ネットワーク状態に基づく動的品質調整
- **サイマルキャスト**: 最適な帯域使用のための複数品質レイヤー
- **スクリーン共有**: ビデオと併用する専用スクリーン共有
- **録画**: 設定可能品質でのルーム録画

### 高度な機能
- **エンドツーエンド暗号化**: オプションのE2EEサポート
- **仮想背景**: クライアントサイド背景処理
- **帯域推定**: Google Congestion Control (GCC)
- **パケット損失復旧**: FECおNACKサポート
- **ジッターバッファ**: スムーズな再生のための適応バッファリング

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    SFU Server                            │
├─────────────────────────────────────────────────────────────┤
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
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │
                    WebRTC Clients
```

## クイックスタート

### Dockerを使用

```bash
# イメージのビルド
docker build -t webrtc-sfu-server .

# サーバーの実行
docker run -p 8080:8080 -p 8443:8443 \
  -v $(pwd)/recordings:/app/recordings \
  webrtc-sfu-server

# サーバーへのアクセス
# WebSocket: ws://localhost:8080/ws
# API: http://localhost:8080/api
# Health: http://localhost:8080/health
```

### 手動セットアップ

1. **システム依存関係のインストール:**
```bash
# Ubuntu/Debian
apt-get install ffmpeg libavformat-dev libavcodec-dev \
  libavdevice-dev libavutil-dev libopus-dev libvpx-dev

# macOS
brew install ffmpeg opus libvpx
```

2. **Python依存関係のインストール:**
```bash
pip install -r requirements.txt
```

3. **サーバーの設定:**
```bash
# 設定の編集
vi config/webrtc.yaml
```

4. **サーバーの実行:**
```bash
python src/main.py
```

## APIドキュメント

### WebSocketシグナリング

シグナリングのために`ws://localhost:8080/ws`に接続。

#### ルームに参加
```json
{
  "type": "join",
  "roomId": "room-123",
  "participantName": "John Doe"
}
```

#### オファーの送信
```json
{
  "type": "offer",
  "roomId": "room-123",
  "sdp": "v=0\r\n..."
}
```

#### ICE候補の送信
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

#### スクリーン共有の開始
```json
{
  "type": "start-screen-share",
  "roomId": "room-123",
  "sdp": "v=0\r\n..."
}
```

#### 品質の更新
```json
{
  "type": "update-quality",
  "roomId": "room-123",
  "quality": "high"
}
```

### REST API

#### ルームの作成
```bash
curl -X POST http://localhost:8080/api/rooms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Conference Room",
    "maxParticipants": 50
  }'
```

#### ルーム一覧
```bash
curl http://localhost:8080/api/rooms
```

#### ルーム詳細取得
```bash
curl http://localhost:8080/api/rooms/room-123
```

#### ルーム統計取得
```bash
curl http://localhost:8080/api/rooms/room-123/stats
```

#### 録画開始
```bash
curl -X POST http://localhost:8080/api/rooms/room-123/recording/start
```

#### 録画停止
```bash
curl -X POST http://localhost:8080/api/rooms/room-123/recording/stop
```

## 設定

### サーバー設定（`config/webrtc.yaml`）

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

### メディア設定（`config/media.yaml`）

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

## サイマルキャスト設定

サーバーは3つの品質レイヤーでサイマルキャストをサポート:

### 低品質
- 解像度: 320x240
- ビットレート: 150 Kbps
- フレームレート: 15 fps

### 中品質
- 解像度: 640x480
- ビットレート: 500 Kbps
- フレームレート: 30 fps

### 高品質
- 解像度: 1280x720
- ビットレート: 2.5 Mbps
- フレームレート: 30 fps

## 適応ビットレート制御

サーバーはGoogle Congestion Control (GCC)アルゴリズムを実装:

1. **帯域推定**: 利用可能帯域の継続監視
2. **パケット損失検出**: パケット損失に基づいたビットレート調整
3. **ジッター分析**: 品質決定でネットワークジッターを考慮
4. **動的調整**: リアルタイムビットレート変更

## 録画

### ローカル録画
```yaml
recording:
  enabled: true
  path: "recordings"
  format: "webm"
  video_bitrate: 2500000
  audio_bitrate: 128000
```

### クラウド録画 (S3)
```yaml
recording:
  s3_upload: true
  s3_bucket: "recordings"
  s3_region: "us-east-1"
```

## クライアント例

```javascript
// ピア接続の作成
const pc = new RTCPeerConnection({
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' }
  ]
});

// シグナリングに接続
const ws = new WebSocket('ws://localhost:8080/ws');

// ルームに参加
ws.send(JSON.stringify({
  type: 'join',
  roomId: 'room-123',
  participantName: 'John Doe'
}));

// シグナリングメッセージの処理
ws.onmessage = async (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'request-offer') {
    // オファーの作成と送信
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    
    ws.send(JSON.stringify({
      type: 'offer',
      roomId: data.roomId,
      sdp: offer.sdp
    }));
  } else if (data.type === 'answer') {
    // リモートディスクリプションの設定
    await pc.setRemoteDescription({
      type: 'answer',
      sdp: data.sdp
    });
  }
};

// ローカルストリームの追加
const stream = await navigator.mediaDevices.getUserMedia({
  video: true,
  audio: true
});

stream.getTracks().forEach(track => {
  pc.addTrack(track, stream);
});
```

## パフォーマンスチューニング

### ネットワーク最適化
```yaml
webrtc:
  jitter_buffer_target: 200  # ms
  jitter_buffer_max: 1000    # ms
  dtx: true  # Discontinuous Transmission
  fec: true  # Forward Error Correction
  nack: true # Negative Acknowledgment
```

### CPU最適化
```yaml
performance:
  worker_threads: 8
  max_cpu_per_room: 25  # percent
  hardware_acceleration: true
```

### メモリ最適化
```yaml
performance:
  max_memory_per_room: 100  # MB
  max_memory_total: 8192     # MB
  garbage_collection_interval: 60  # seconds
```

## 監視

### Prometheusメトリクス
```bash
# メトリクスへのアクセス
curl http://localhost:9090/metrics

# 主要メトリクス
- webrtc_rooms_total
- webrtc_participants_total
- webrtc_video_tracks_total
- webrtc_audio_tracks_total
- webrtc_bandwidth_usage_bytes
- webrtc_packet_loss_rate
- webrtc_jitter_ms
```

### ヘルスチェック
```bash
curl http://localhost:8080/health

# レスポンス
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

## セキュリティ

### DTLS-SRTP
すべてのメディアストリームはデフォルトでDTLS-SRTPを使用して暗号化されます。

### 認証（オプション）
```yaml
security:
  require_auth: true
  auth_token_header: "X-Auth-Token"
```

### レート制限
```yaml
security:
  rate_limit:
    enabled: true
    max_rooms_per_ip: 10
    max_participants_per_ip: 50
```

## トラブルシューティング

### 接続問題
```bash
# ICE候補の確認
webrtc-internals  # Chrome: chrome://webrtc-internals

# STUNサーバーのテスト
stun-client stun.l.google.com:19302
```

### 品質問題
```bash
# ネットワーク統計の確認
curl http://localhost:8080/api/rooms/room-123/stats

# ビットレート制限の調整
vi config/webrtc.yaml
# max_bitrate、min_bitrateを変更
```

### 録画問題
```bash
# 録画パスの権限確認
ls -la recordings/

# ffmpegインストールの確認
ffmpeg -version

# ディスク容量の確認
df -h
```

## 本番デプロイ

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

## スケーリング考慮事項

1. **水平スケーリング**: ロードバランサーの後ろに複数のSFUインスタンスをデプロイ
2. **ルーム分散**: ルーム割り当てに一貫性ハッシュを使用
3. **メディアサーバー**: シグナリングとメディアサーバーを分離
4. **録画オフロード**: 専用録画サーバーを使用
5. **CDN統合**: 録画コンテンツ配信にCDNを使用

## ライセンス

MIT