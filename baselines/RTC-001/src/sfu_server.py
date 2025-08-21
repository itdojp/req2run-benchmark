"""
WebRTC SFU (Selective Forwarding Unit) Server

Implements WebRTC video conferencing with SFU architecture.
"""

import asyncio
import json
import logging
import uuid
import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import os

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaPlayer, MediaRecorder, MediaBlackhole
from aiortc.rtcrtpsender import RTCRtpSender
from aiortc.mediastreams import MediaStreamTrack, VideoStreamTrack, AudioStreamTrack
import aiohttp
from aiohttp import web
import av


@dataclass
class Participant:
    """Represents a participant in a room"""
    id: str
    name: str
    room_id: str
    peer_connection: RTCPeerConnection
    video_tracks: Dict[str, MediaStreamTrack]
    audio_tracks: Dict[str, MediaStreamTrack]
    screen_track: Optional[MediaStreamTrack] = None
    joined_at: datetime = None
    is_publisher: bool = True
    simulcast_layers: Dict[str, List[str]] = None
    selected_quality: str = "high"
    
    def __post_init__(self):
        if not self.joined_at:
            self.joined_at = datetime.utcnow()
        if not self.simulcast_layers:
            self.simulcast_layers = {}


@dataclass
class Room:
    """Represents a conference room"""
    id: str
    name: str
    created_at: datetime
    participants: Dict[str, Participant]
    max_participants: int = 100
    is_recording: bool = False
    recorder: Optional[MediaRecorder] = None
    recording_path: Optional[str] = None
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.config:
            self.config = {}


class SimulcastLayer:
    """Manages simulcast layers for adaptive bitrate"""
    
    def __init__(self):
        self.layers = {
            "low": {"width": 320, "height": 240, "bitrate": 150000},
            "medium": {"width": 640, "height": 480, "bitrate": 500000},
            "high": {"width": 1280, "height": 720, "bitrate": 2500000}
        }
    
    def get_layer(self, quality: str) -> Dict[str, int]:
        """Get simulcast layer configuration"""
        return self.layers.get(quality, self.layers["medium"])
    
    def select_quality(self, available_bandwidth: int) -> str:
        """Select quality based on available bandwidth"""
        if available_bandwidth < 200000:
            return "low"
        elif available_bandwidth < 1000000:
            return "medium"
        else:
            return "high"


class AdaptiveBitrateController:
    """Controls adaptive bitrate based on network conditions"""
    
    def __init__(self):
        self.bandwidth_history: Dict[str, List[int]] = defaultdict(list)
        self.packet_loss_history: Dict[str, List[float]] = defaultdict(list)
        self.jitter_history: Dict[str, List[float]] = defaultdict(list)
        self.current_bitrates: Dict[str, int] = {}
        
    def update_stats(
        self,
        participant_id: str,
        bandwidth: int,
        packet_loss: float,
        jitter: float
    ):
        """Update network statistics"""
        self.bandwidth_history[participant_id].append(bandwidth)
        self.packet_loss_history[participant_id].append(packet_loss)
        self.jitter_history[participant_id].append(jitter)
        
        # Keep only recent history
        max_history = 100
        if len(self.bandwidth_history[participant_id]) > max_history:
            self.bandwidth_history[participant_id] = self.bandwidth_history[participant_id][-50:]
            self.packet_loss_history[participant_id] = self.packet_loss_history[participant_id][-50:]
            self.jitter_history[participant_id] = self.jitter_history[participant_id][-50:]
    
    def calculate_target_bitrate(self, participant_id: str) -> int:
        """Calculate target bitrate based on network conditions"""
        if participant_id not in self.bandwidth_history:
            return 2500000  # Default high bitrate
        
        # Get recent averages
        recent_bandwidth = self.bandwidth_history[participant_id][-10:]
        recent_loss = self.packet_loss_history[participant_id][-10:]
        
        if not recent_bandwidth:
            return 2500000
        
        avg_bandwidth = sum(recent_bandwidth) / len(recent_bandwidth)
        avg_loss = sum(recent_loss) / len(recent_loss) if recent_loss else 0
        
        # Adjust based on packet loss
        if avg_loss > 0.05:  # >5% loss
            target_bitrate = int(avg_bandwidth * 0.5)
        elif avg_loss > 0.02:  # >2% loss
            target_bitrate = int(avg_bandwidth * 0.7)
        else:
            target_bitrate = int(avg_bandwidth * 0.9)
        
        # Clamp to reasonable limits
        target_bitrate = max(50000, min(target_bitrate, 5000000))
        
        self.current_bitrates[participant_id] = target_bitrate
        return target_bitrate


class SFUServer:
    """WebRTC SFU Server implementation"""
    
    def __init__(self, config_path: str = "config/webrtc.yaml"):
        self.rooms: Dict[str, Room] = {}
        self.participants: Dict[str, Participant] = {}
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.simulcast = SimulcastLayer()
        self.bitrate_controller = AdaptiveBitrateController()
        self.recording_enabled = self.config.get("recording", {}).get("enabled", False)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load server configuration"""
        if os.path.exists(config_path):
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "ssl": False
            },
            "webrtc": {
                "ice_servers": [
                    {"urls": ["stun:stun.l.google.com:19302"]},
                ],
                "max_bitrate": 5000000,
                "simulcast": True,
                "dtx": True,
                "fec": True
            },
            "rooms": {
                "max_participants": 100,
                "auto_create": True,
                "idle_timeout": 3600
            },
            "recording": {
                "enabled": False,
                "path": "recordings",
                "format": "webm"
            }
        }
    
    async def create_room(self, room_id: str, name: str = None) -> Room:
        """Create a new room"""
        if room_id in self.rooms:
            raise ValueError(f"Room {room_id} already exists")
        
        room = Room(
            id=room_id,
            name=name or f"Room {room_id}",
            created_at=datetime.utcnow(),
            participants={},
            max_participants=self.config["rooms"]["max_participants"],
            config=self.config
        )
        
        self.rooms[room_id] = room
        self.logger.info(f"Created room {room_id}")
        
        return room
    
    async def join_room(
        self,
        room_id: str,
        participant_id: str,
        participant_name: str,
        sdp_offer: str
    ) -> Dict[str, Any]:
        """Join a room with WebRTC offer"""
        # Create room if it doesn't exist and auto-create is enabled
        if room_id not in self.rooms:
            if self.config["rooms"]["auto_create"]:
                await self.create_room(room_id)
            else:
                raise ValueError(f"Room {room_id} does not exist")
        
        room = self.rooms[room_id]
        
        # Check room capacity
        if len(room.participants) >= room.max_participants:
            raise ValueError(f"Room {room_id} is full")
        
        # Create peer connection
        pc = RTCPeerConnection(
            configuration={
                "iceServers": self.config["webrtc"]["ice_servers"]
            }
        )
        
        # Create participant
        participant = Participant(
            id=participant_id,
            name=participant_name,
            room_id=room_id,
            peer_connection=pc,
            video_tracks={},
            audio_tracks={}
        )
        
        # Handle incoming tracks
        @pc.on("track")
        async def on_track(track):
            self.logger.info(f"Received {track.kind} track from {participant_id}")
            
            if track.kind == "video":
                participant.video_tracks[track.id] = track
                # Forward to other participants
                await self._forward_track_to_room(room_id, participant_id, track)
            elif track.kind == "audio":
                participant.audio_tracks[track.id] = track
                # Forward to other participants
                await self._forward_track_to_room(room_id, participant_id, track)
            
            # Start recording if enabled
            if room.is_recording and room.recorder:
                room.recorder.addTrack(track)
        
        # Handle ICE connection state changes
        @pc.on("iceconnectionstatechange")
        async def on_ice_state_change():
            self.logger.info(f"ICE state for {participant_id}: {pc.iceConnectionState}")
            
            if pc.iceConnectionState == "failed":
                await self.leave_room(room_id, participant_id)
        
        # Set remote description (offer)
        await pc.setRemoteDescription(
            RTCSessionDescription(sdp=sdp_offer, type="offer")
        )
        
        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        # Add participant to room
        room.participants[participant_id] = participant
        self.participants[participant_id] = participant
        self.peer_connections[participant_id] = pc
        
        self.logger.info(f"Participant {participant_id} joined room {room_id}")
        
        # Notify other participants
        await self._notify_participant_joined(room_id, participant_id)
        
        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type,
            "room_id": room_id,
            "participant_id": participant_id
        }
    
    async def leave_room(self, room_id: str, participant_id: str):
        """Leave a room"""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        
        if participant_id in room.participants:
            participant = room.participants[participant_id]
            
            # Close peer connection
            if participant.peer_connection:
                await participant.peer_connection.close()
            
            # Remove from room
            del room.participants[participant_id]
            del self.participants[participant_id]
            
            if participant_id in self.peer_connections:
                del self.peer_connections[participant_id]
            
            self.logger.info(f"Participant {participant_id} left room {room_id}")
            
            # Notify other participants
            await self._notify_participant_left(room_id, participant_id)
            
            # Delete room if empty
            if not room.participants:
                await self.delete_room(room_id)
    
    async def delete_room(self, room_id: str):
        """Delete a room"""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        
        # Stop recording if active
        if room.recorder:
            await room.recorder.stop()
        
        # Close all peer connections
        for participant in room.participants.values():
            if participant.peer_connection:
                await participant.peer_connection.close()
        
        del self.rooms[room_id]
        self.logger.info(f"Deleted room {room_id}")
    
    async def add_ice_candidate(
        self,
        participant_id: str,
        candidate: Dict[str, Any]
    ):
        """Add ICE candidate"""
        if participant_id not in self.peer_connections:
            raise ValueError(f"Participant {participant_id} not found")
        
        pc = self.peer_connections[participant_id]
        
        ice_candidate = RTCIceCandidate(
            sdpMLineIndex=candidate.get("sdpMLineIndex"),
            sdpMid=candidate.get("sdpMid"),
            candidate=candidate.get("candidate")
        )
        
        await pc.addIceCandidate(ice_candidate)
        self.logger.debug(f"Added ICE candidate for {participant_id}")
    
    async def start_screen_share(
        self,
        room_id: str,
        participant_id: str,
        sdp_offer: str
    ) -> Dict[str, Any]:
        """Start screen sharing"""
        if room_id not in self.rooms:
            raise ValueError(f"Room {room_id} not found")
        
        if participant_id not in self.participants:
            raise ValueError(f"Participant {participant_id} not found")
        
        participant = self.participants[participant_id]
        
        # Handle screen share track
        # This would be added to the existing peer connection
        # or create a new one specifically for screen share
        
        return {
            "status": "screen_share_started",
            "participant_id": participant_id
        }
    
    async def update_simulcast_layer(
        self,
        room_id: str,
        participant_id: str,
        quality: str
    ):
        """Update simulcast layer for a participant"""
        if participant_id not in self.participants:
            return
        
        participant = self.participants[participant_id]
        participant.selected_quality = quality
        
        # Update forwarding quality
        layer_config = self.simulcast.get_layer(quality)
        
        self.logger.info(
            f"Updated simulcast layer for {participant_id} to {quality}: {layer_config}"
        )
    
    async def start_recording(self, room_id: str) -> str:
        """Start recording a room"""
        if room_id not in self.rooms:
            raise ValueError(f"Room {room_id} not found")
        
        room = self.rooms[room_id]
        
        if room.is_recording:
            return room.recording_path
        
        # Create recording path
        recording_dir = self.config["recording"]["path"]
        os.makedirs(recording_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"room_{room_id}_{timestamp}.{self.config['recording']['format']}"
        recording_path = os.path.join(recording_dir, filename)
        
        # Create media recorder
        room.recorder = MediaRecorder(recording_path)
        room.recording_path = recording_path
        room.is_recording = True
        
        # Add existing tracks to recorder
        for participant in room.participants.values():
            for track in participant.video_tracks.values():
                room.recorder.addTrack(track)
            for track in participant.audio_tracks.values():
                room.recorder.addTrack(track)
        
        await room.recorder.start()
        
        self.logger.info(f"Started recording room {room_id} to {recording_path}")
        
        return recording_path
    
    async def stop_recording(self, room_id: str) -> str:
        """Stop recording a room"""
        if room_id not in self.rooms:
            raise ValueError(f"Room {room_id} not found")
        
        room = self.rooms[room_id]
        
        if not room.is_recording:
            return None
        
        await room.recorder.stop()
        
        room.is_recording = False
        recording_path = room.recording_path
        room.recorder = None
        room.recording_path = None
        
        self.logger.info(f"Stopped recording room {room_id}")
        
        return recording_path
    
    async def _forward_track_to_room(
        self,
        room_id: str,
        sender_id: str,
        track: MediaStreamTrack
    ):
        """Forward track to all other participants in room"""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        
        for participant_id, participant in room.participants.items():
            if participant_id == sender_id:
                continue  # Don't send back to sender
            
            try:
                # Add track to peer connection
                participant.peer_connection.addTrack(track)
                
                self.logger.debug(
                    f"Forwarded {track.kind} track from {sender_id} to {participant_id}"
                )
            except Exception as e:
                self.logger.error(f"Error forwarding track: {e}")
    
    async def _notify_participant_joined(self, room_id: str, participant_id: str):
        """Notify room participants about new participant"""
        # This would send WebSocket notifications in a real implementation
        self.logger.info(f"Notifying room {room_id} about {participant_id} joining")
    
    async def _notify_participant_left(self, room_id: str, participant_id: str):
        """Notify room participants about participant leaving"""
        # This would send WebSocket notifications in a real implementation
        self.logger.info(f"Notifying room {room_id} about {participant_id} leaving")
    
    async def get_room_stats(self, room_id: str) -> Dict[str, Any]:
        """Get room statistics"""
        if room_id not in self.rooms:
            raise ValueError(f"Room {room_id} not found")
        
        room = self.rooms[room_id]
        
        participants_stats = []
        for participant in room.participants.values():
            stats = {
                "id": participant.id,
                "name": participant.name,
                "joined_at": participant.joined_at.isoformat(),
                "video_tracks": len(participant.video_tracks),
                "audio_tracks": len(participant.audio_tracks),
                "has_screen_share": participant.screen_track is not None,
                "selected_quality": participant.selected_quality
            }
            
            # Get connection stats
            if participant.peer_connection:
                pc_stats = await participant.peer_connection.getStats()
                # Process stats...
                stats["connection_state"] = participant.peer_connection.connectionState
            
            participants_stats.append(stats)
        
        return {
            "room_id": room_id,
            "room_name": room.name,
            "created_at": room.created_at.isoformat(),
            "participant_count": len(room.participants),
            "max_participants": room.max_participants,
            "is_recording": room.is_recording,
            "recording_path": room.recording_path,
            "participants": participants_stats
        }
    
    async def update_bitrate(self, participant_id: str, stats: Dict[str, Any]):
        """Update adaptive bitrate based on network stats"""
        bandwidth = stats.get("availableOutgoingBitrate", 2500000)
        packet_loss = stats.get("packetLossRate", 0.0)
        jitter = stats.get("jitter", 0.0)
        
        self.bitrate_controller.update_stats(
            participant_id,
            bandwidth,
            packet_loss,
            jitter
        )
        
        target_bitrate = self.bitrate_controller.calculate_target_bitrate(participant_id)
        
        # Apply bitrate limit
        if participant_id in self.peer_connections:
            pc = self.peer_connections[participant_id]
            # This would apply the bitrate limit to the peer connection
            # In practice, this involves SDP manipulation or REMB messages
            
        self.logger.debug(f"Updated bitrate for {participant_id}: {target_bitrate}")
        
        return target_bitrate