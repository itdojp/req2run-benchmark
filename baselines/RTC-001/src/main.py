"""
Main WebRTC Video Conferencing Server Application

Integrates SFU server with signaling and HTTP API.
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any
import signal
import sys

from aiohttp import web
import aiohttp_cors

from sfu_server import SFUServer
from signaling_server import SignalingProtocol


class WebRTCApplication:
    """Main WebRTC application"""
    
    def __init__(self, config_path: str = "config/webrtc.yaml"):
        self.sfu_server = SFUServer(config_path)
        self.signaling = SignalingProtocol(self.sfu_server)
        self.app = web.Application()
        self.logger = logging.getLogger(__name__)
        self.config = self.sfu_server.config
        
        # Setup routes
        self._setup_routes()
        
        # Setup CORS
        self._setup_cors()
    
    def _setup_routes(self):
        """Setup HTTP and WebSocket routes"""
        # WebSocket endpoint for signaling
        self.app.router.add_get('/ws', self.signaling.handle_websocket)
        
        # REST API endpoints
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/api/rooms', self.handle_list_rooms)
        self.app.router.add_post('/api/rooms', self.handle_create_room)
        self.app.router.add_get('/api/rooms/{room_id}', self.handle_get_room)
        self.app.router.add_delete('/api/rooms/{room_id}', self.handle_delete_room)
        self.app.router.add_get('/api/rooms/{room_id}/stats', self.handle_get_room_stats)
        self.app.router.add_post('/api/rooms/{room_id}/recording/start', self.handle_start_recording)
        self.app.router.add_post('/api/rooms/{room_id}/recording/stop', self.handle_stop_recording)
        
        # Static files (for demo client)
        if os.path.exists('static'):
            self.app.router.add_static('/', path='static', name='static')
    
    def _setup_cors(self):
        """Setup CORS for cross-origin requests"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Configure CORS on all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "rooms": len(self.sfu_server.rooms),
            "participants": len(self.sfu_server.participants),
            "config": {
                "max_rooms": 1000,
                "max_participants_per_room": self.config["rooms"]["max_participants"],
                "recording_enabled": self.config["recording"]["enabled"],
                "simulcast_enabled": self.config["webrtc"].get("simulcast", True)
            }
        })
    
    async def handle_list_rooms(self, request: web.Request) -> web.Response:
        """List all active rooms"""
        rooms = []
        for room_id, room in self.sfu_server.rooms.items():
            rooms.append({
                "id": room_id,
                "name": room.name,
                "created_at": room.created_at.isoformat(),
                "participant_count": len(room.participants),
                "max_participants": room.max_participants,
                "is_recording": room.is_recording
            })
        
        return web.json_response({
            "rooms": rooms,
            "total": len(rooms)
        })
    
    async def handle_create_room(self, request: web.Request) -> web.Response:
        """Create a new room"""
        try:
            data = await request.json()
            room_id = data.get("id") or str(uuid.uuid4())
            room_name = data.get("name")
            
            room = await self.sfu_server.create_room(room_id, room_name)
            
            return web.json_response({
                "id": room.id,
                "name": room.name,
                "created_at": room.created_at.isoformat(),
                "max_participants": room.max_participants
            }, status=201)
            
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            self.logger.error(f"Error creating room: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def handle_get_room(self, request: web.Request) -> web.Response:
        """Get room details"""
        room_id = request.match_info['room_id']
        
        if room_id not in self.sfu_server.rooms:
            return web.json_response({"error": "Room not found"}, status=404)
        
        room = self.sfu_server.rooms[room_id]
        
        participants = []
        for participant in room.participants.values():
            participants.append({
                "id": participant.id,
                "name": participant.name,
                "joined_at": participant.joined_at.isoformat(),
                "is_publisher": participant.is_publisher,
                "has_video": len(participant.video_tracks) > 0,
                "has_audio": len(participant.audio_tracks) > 0,
                "has_screen_share": participant.screen_track is not None
            })
        
        return web.json_response({
            "id": room.id,
            "name": room.name,
            "created_at": room.created_at.isoformat(),
            "participant_count": len(room.participants),
            "max_participants": room.max_participants,
            "is_recording": room.is_recording,
            "recording_path": room.recording_path,
            "participants": participants
        })
    
    async def handle_delete_room(self, request: web.Request) -> web.Response:
        """Delete a room"""
        room_id = request.match_info['room_id']
        
        if room_id not in self.sfu_server.rooms:
            return web.json_response({"error": "Room not found"}, status=404)
        
        try:
            await self.sfu_server.delete_room(room_id)
            return web.json_response({"message": "Room deleted"}, status=200)
        except Exception as e:
            self.logger.error(f"Error deleting room: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def handle_get_room_stats(self, request: web.Request) -> web.Response:
        """Get room statistics"""
        room_id = request.match_info['room_id']
        
        try:
            stats = await self.sfu_server.get_room_stats(room_id)
            return web.json_response(stats)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)
        except Exception as e:
            self.logger.error(f"Error getting room stats: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def handle_start_recording(self, request: web.Request) -> web.Response:
        """Start recording a room"""
        room_id = request.match_info['room_id']
        
        try:
            recording_path = await self.sfu_server.start_recording(room_id)
            return web.json_response({
                "message": "Recording started",
                "recording_path": recording_path
            })
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)
        except Exception as e:
            self.logger.error(f"Error starting recording: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def handle_stop_recording(self, request: web.Request) -> web.Response:
        """Stop recording a room"""
        room_id = request.match_info['room_id']
        
        try:
            recording_path = await self.sfu_server.stop_recording(room_id)
            return web.json_response({
                "message": "Recording stopped",
                "recording_path": recording_path
            })
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
            return web.json_response({"error": "Internal server error"}, status=500)
    
    async def start(self):
        """Start the application"""
        host = self.config["server"].get("host", "0.0.0.0")
        port = self.config["server"].get("port", 8080)
        
        self.logger.info(f"Starting WebRTC server on {host}:{port}")
        
        # Start background tasks
        asyncio.create_task(self._monitor_rooms())
        asyncio.create_task(self._collect_metrics())
        
        # Run web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        self.logger.info(f"WebRTC server started successfully")
        self.logger.info(f"WebSocket endpoint: ws://{host}:{port}/ws")
        self.logger.info(f"API endpoint: http://{host}:{port}/api")
        
        # Keep running
        await asyncio.Event().wait()
    
    async def _monitor_rooms(self):
        """Monitor and clean up idle rooms"""
        idle_timeout = self.config["rooms"].get("idle_timeout", 3600)
        
        while True:
            try:
                current_time = datetime.utcnow()
                rooms_to_delete = []
                
                for room_id, room in self.sfu_server.rooms.items():
                    if not room.participants:
                        # Check if room has been empty for too long
                        idle_time = (current_time - room.created_at).total_seconds()
                        if idle_time > idle_timeout:
                            rooms_to_delete.append(room_id)
                
                # Delete idle rooms
                for room_id in rooms_to_delete:
                    self.logger.info(f"Deleting idle room {room_id}")
                    await self.sfu_server.delete_room(room_id)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Room monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _collect_metrics(self):
        """Collect and log metrics"""
        while True:
            try:
                metrics = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "rooms": len(self.sfu_server.rooms),
                    "participants": len(self.sfu_server.participants),
                    "connections": len(self.sfu_server.peer_connections),
                    "websockets": len(self.signaling.websockets)
                }
                
                # Calculate room statistics
                total_video_tracks = 0
                total_audio_tracks = 0
                recording_rooms = 0
                
                for room in self.sfu_server.rooms.values():
                    if room.is_recording:
                        recording_rooms += 1
                    
                    for participant in room.participants.values():
                        total_video_tracks += len(participant.video_tracks)
                        total_audio_tracks += len(participant.audio_tracks)
                
                metrics["total_video_tracks"] = total_video_tracks
                metrics["total_audio_tracks"] = total_audio_tracks
                metrics["recording_rooms"] = recording_rooms
                
                self.logger.info(f"Metrics: {json.dumps(metrics)}")
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(30)


async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create application
    config_path = os.getenv("CONFIG_PATH", "config/webrtc.yaml")
    app = WebRTCApplication(config_path)
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    
    async def shutdown(sig):
        logging.info(f"Received signal {sig.name}")
        # Cleanup
        for room_id in list(app.sfu_server.rooms.keys()):
            await app.sfu_server.delete_room(room_id)
        loop.stop()
    
    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(shutdown(s))
        )
    
    # Start application
    try:
        await app.start()
    except KeyboardInterrupt:
        pass
    finally:
        logging.info("WebRTC server stopped")


if __name__ == "__main__":
    # Add missing import
    import uuid
    asyncio.run(main())