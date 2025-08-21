"""
WebRTC Signaling Server

Handles WebRTC signaling via WebSocket connections.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Set, Optional, Any
from datetime import datetime
import aiohttp
from aiohttp import web
import weakref

from sfu_server import SFUServer


class SignalingProtocol:
    """WebSocket signaling protocol handler"""
    
    def __init__(self, sfu_server: SFUServer):
        self.sfu_server = sfu_server
        self.websockets: Dict[str, web.WebSocketResponse] = {}
        self.participant_sockets: Dict[str, str] = {}  # participant_id -> socket_id
        self.socket_participants: Dict[str, str] = {}  # socket_id -> participant_id
        self.logger = logging.getLogger(__name__)
    
    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connection"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        socket_id = str(uuid.uuid4())
        self.websockets[socket_id] = ws
        
        self.logger.info(f"WebSocket connected: {socket_id}")
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self.handle_message(socket_id, msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")
                    
        except Exception as e:
            self.logger.error(f"WebSocket handler error: {e}")
            
        finally:
            await self.disconnect_socket(socket_id)
        
        return ws
    
    async def handle_message(self, socket_id: str, message: str):
        """Handle signaling message"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            self.logger.debug(f"Received {msg_type} from {socket_id}")
            
            if msg_type == "join":
                await self.handle_join(socket_id, data)
            elif msg_type == "offer":
                await self.handle_offer(socket_id, data)
            elif msg_type == "answer":
                await self.handle_answer(socket_id, data)
            elif msg_type == "ice-candidate":
                await self.handle_ice_candidate(socket_id, data)
            elif msg_type == "leave":
                await self.handle_leave(socket_id, data)
            elif msg_type == "start-screen-share":
                await self.handle_start_screen_share(socket_id, data)
            elif msg_type == "stop-screen-share":
                await self.handle_stop_screen_share(socket_id, data)
            elif msg_type == "update-quality":
                await self.handle_update_quality(socket_id, data)
            elif msg_type == "start-recording":
                await self.handle_start_recording(socket_id, data)
            elif msg_type == "stop-recording":
                await self.handle_stop_recording(socket_id, data)
            elif msg_type == "get-room-stats":
                await self.handle_get_room_stats(socket_id, data)
            elif msg_type == "network-stats":
                await self.handle_network_stats(socket_id, data)
            else:
                await self.send_error(socket_id, f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError:
            await self.send_error(socket_id, "Invalid JSON")
        except Exception as e:
            self.logger.error(f"Message handling error: {e}")
            await self.send_error(socket_id, str(e))
    
    async def handle_join(self, socket_id: str, data: Dict[str, Any]):
        """Handle room join request"""
        room_id = data.get("roomId")
        participant_id = data.get("participantId") or str(uuid.uuid4())
        participant_name = data.get("participantName", "Anonymous")
        
        # Associate socket with participant
        self.participant_sockets[participant_id] = socket_id
        self.socket_participants[socket_id] = participant_id
        
        # Send join confirmation
        await self.send_message(socket_id, {
            "type": "joined",
            "roomId": room_id,
            "participantId": participant_id
        })
        
        # Request offer from client
        await self.send_message(socket_id, {
            "type": "request-offer",
            "roomId": room_id,
            "participantId": participant_id
        })
        
        self.logger.info(f"Participant {participant_id} preparing to join room {room_id}")
    
    async def handle_offer(self, socket_id: str, data: Dict[str, Any]):
        """Handle SDP offer"""
        participant_id = self.socket_participants.get(socket_id)
        if not participant_id:
            await self.send_error(socket_id, "Not registered")
            return
        
        room_id = data.get("roomId")
        sdp = data.get("sdp")
        participant_name = data.get("participantName", "Anonymous")
        
        try:
            # Join room with offer
            response = await self.sfu_server.join_room(
                room_id,
                participant_id,
                participant_name,
                sdp
            )
            
            # Send answer back
            await self.send_message(socket_id, {
                "type": "answer",
                "sdp": response["sdp"],
                "roomId": room_id,
                "participantId": participant_id
            })
            
            # Notify other participants
            await self.broadcast_to_room(room_id, {
                "type": "participant-joined",
                "participantId": participant_id,
                "participantName": participant_name
            }, exclude=participant_id)
            
        except Exception as e:
            await self.send_error(socket_id, f"Failed to join room: {e}")
    
    async def handle_answer(self, socket_id: str, data: Dict[str, Any]):
        """Handle SDP answer"""
        # This would be used in mesh topology, not typically in SFU
        pass
    
    async def handle_ice_candidate(self, socket_id: str, data: Dict[str, Any]):
        """Handle ICE candidate"""
        participant_id = self.socket_participants.get(socket_id)
        if not participant_id:
            await self.send_error(socket_id, "Not registered")
            return
        
        candidate = data.get("candidate")
        
        try:
            await self.sfu_server.add_ice_candidate(participant_id, candidate)
            
            await self.send_message(socket_id, {
                "type": "ice-candidate-added",
                "participantId": participant_id
            })
            
        except Exception as e:
            await self.send_error(socket_id, f"Failed to add ICE candidate: {e}")
    
    async def handle_leave(self, socket_id: str, data: Dict[str, Any]):
        """Handle leave request"""
        participant_id = self.socket_participants.get(socket_id)
        if not participant_id:
            return
        
        room_id = data.get("roomId")
        
        try:
            await self.sfu_server.leave_room(room_id, participant_id)
            
            # Notify other participants
            await self.broadcast_to_room(room_id, {
                "type": "participant-left",
                "participantId": participant_id
            }, exclude=participant_id)
            
        except Exception as e:
            self.logger.error(f"Error leaving room: {e}")
    
    async def handle_start_screen_share(self, socket_id: str, data: Dict[str, Any]):
        """Handle screen share start"""
        participant_id = self.socket_participants.get(socket_id)
        if not participant_id:
            await self.send_error(socket_id, "Not registered")
            return
        
        room_id = data.get("roomId")
        sdp = data.get("sdp")
        
        try:
            response = await self.sfu_server.start_screen_share(
                room_id,
                participant_id,
                sdp
            )
            
            await self.send_message(socket_id, {
                "type": "screen-share-started",
                "participantId": participant_id
            })
            
            # Notify other participants
            await self.broadcast_to_room(room_id, {
                "type": "screen-share-started",
                "participantId": participant_id
            }, exclude=participant_id)
            
        except Exception as e:
            await self.send_error(socket_id, f"Failed to start screen share: {e}")
    
    async def handle_stop_screen_share(self, socket_id: str, data: Dict[str, Any]):
        """Handle screen share stop"""
        participant_id = self.socket_participants.get(socket_id)
        if not participant_id:
            return
        
        room_id = data.get("roomId")
        
        # Notify other participants
        await self.broadcast_to_room(room_id, {
            "type": "screen-share-stopped",
            "participantId": participant_id
        }, exclude=participant_id)
    
    async def handle_update_quality(self, socket_id: str, data: Dict[str, Any]):
        """Handle quality update request"""
        participant_id = self.socket_participants.get(socket_id)
        if not participant_id:
            return
        
        room_id = data.get("roomId")
        quality = data.get("quality", "medium")
        
        try:
            await self.sfu_server.update_simulcast_layer(
                room_id,
                participant_id,
                quality
            )
            
            await self.send_message(socket_id, {
                "type": "quality-updated",
                "quality": quality
            })
            
        except Exception as e:
            await self.send_error(socket_id, f"Failed to update quality: {e}")
    
    async def handle_start_recording(self, socket_id: str, data: Dict[str, Any]):
        """Handle recording start request"""
        room_id = data.get("roomId")
        
        try:
            recording_path = await self.sfu_server.start_recording(room_id)
            
            await self.broadcast_to_room(room_id, {
                "type": "recording-started",
                "recordingPath": recording_path
            })
            
        except Exception as e:
            await self.send_error(socket_id, f"Failed to start recording: {e}")
    
    async def handle_stop_recording(self, socket_id: str, data: Dict[str, Any]):
        """Handle recording stop request"""
        room_id = data.get("roomId")
        
        try:
            recording_path = await self.sfu_server.stop_recording(room_id)
            
            await self.broadcast_to_room(room_id, {
                "type": "recording-stopped",
                "recordingPath": recording_path
            })
            
        except Exception as e:
            await self.send_error(socket_id, f"Failed to stop recording: {e}")
    
    async def handle_get_room_stats(self, socket_id: str, data: Dict[str, Any]):
        """Handle room stats request"""
        room_id = data.get("roomId")
        
        try:
            stats = await self.sfu_server.get_room_stats(room_id)
            
            await self.send_message(socket_id, {
                "type": "room-stats",
                "stats": stats
            })
            
        except Exception as e:
            await self.send_error(socket_id, f"Failed to get room stats: {e}")
    
    async def handle_network_stats(self, socket_id: str, data: Dict[str, Any]):
        """Handle network statistics update"""
        participant_id = self.socket_participants.get(socket_id)
        if not participant_id:
            return
        
        stats = data.get("stats", {})
        
        try:
            target_bitrate = await self.sfu_server.update_bitrate(participant_id, stats)
            
            await self.send_message(socket_id, {
                "type": "bitrate-updated",
                "targetBitrate": target_bitrate
            })
            
        except Exception as e:
            self.logger.error(f"Failed to update bitrate: {e}")
    
    async def send_message(self, socket_id: str, message: Dict[str, Any]):
        """Send message to specific socket"""
        if socket_id in self.websockets:
            ws = self.websockets[socket_id]
            try:
                await ws.send_str(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Failed to send message: {e}")
    
    async def send_error(self, socket_id: str, error: str):
        """Send error message"""
        await self.send_message(socket_id, {
            "type": "error",
            "error": error
        })
    
    async def broadcast_to_room(
        self,
        room_id: str,
        message: Dict[str, Any],
        exclude: Optional[str] = None
    ):
        """Broadcast message to all participants in room"""
        if room_id not in self.sfu_server.rooms:
            return
        
        room = self.sfu_server.rooms[room_id]
        
        for participant_id in room.participants:
            if participant_id == exclude:
                continue
            
            if participant_id in self.participant_sockets:
                socket_id = self.participant_sockets[participant_id]
                await self.send_message(socket_id, message)
    
    async def disconnect_socket(self, socket_id: str):
        """Handle socket disconnection"""
        self.logger.info(f"WebSocket disconnected: {socket_id}")
        
        # Get participant ID
        participant_id = self.socket_participants.get(socket_id)
        
        if participant_id:
            # Find and leave all rooms
            for room_id, room in self.sfu_server.rooms.items():
                if participant_id in room.participants:
                    await self.sfu_server.leave_room(room_id, participant_id)
                    
                    # Notify other participants
                    await self.broadcast_to_room(room_id, {
                        "type": "participant-disconnected",
                        "participantId": participant_id
                    }, exclude=participant_id)
            
            # Clean up mappings
            if participant_id in self.participant_sockets:
                del self.participant_sockets[participant_id]
        
        if socket_id in self.socket_participants:
            del self.socket_participants[socket_id]
        
        if socket_id in self.websockets:
            del self.websockets[socket_id]