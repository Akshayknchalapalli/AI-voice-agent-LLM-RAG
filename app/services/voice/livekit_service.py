from livekit import rtc
from app.core.config import get_settings
from fastapi import HTTPException
import asyncio
from datetime import datetime, timedelta

settings = get_settings()

class LiveKitService:
    def __init__(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.ws_url = settings.LIVEKIT_WS_URL
        self.room = rtc.Room()

    async def create_room(self, room_name: str):
        """Create a LiveKit room for WebRTC communication"""
        try:
            await self.room.connect(self.ws_url, room_name)
            return self.room
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create room: {str(e)}")

    async def generate_token(self, room_name: str, participant_name: str, is_agent: bool = False):
        """Generate access token for a participant"""
        try:
            # Create token with appropriate permissions
            token = rtc.Token(
                api_key=self.api_key,
                api_secret=self.api_secret,
                identity=participant_name,
                ttl=timedelta(hours=1)
            )
            
            # Grant permissions
            token.grant = rtc.VideoGrant(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True
            )
            
            # Add additional permissions for agents
            if is_agent:
                token.grant.can_admin_room = True
                token.grant.can_admin_tracks = True
            
            return token.to_jwt()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")

    async def close_room(self, room_name: str):
        """Close a LiveKit room"""
        try:
            if self.room.name == room_name and self.room.connected:
                await self.room.disconnect()
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to close room: {str(e)}")

    def setup_event_handlers(self):
        """Set up event handlers for the room"""
        @self.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            print(f"Participant connected: {participant.identity}")

        @self.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            print(f"Participant disconnected: {participant.identity}")

        @self.room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            print(f"Track subscribed: {track.kind} from {participant.identity}")

        @self.room.on("track_unsubscribed")
        def on_track_unsubscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            print(f"Track unsubscribed: {track.kind} from {participant.identity}")



livekit_service = LiveKitService()
