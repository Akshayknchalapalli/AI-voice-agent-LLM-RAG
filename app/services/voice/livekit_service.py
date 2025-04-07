from livekit import api
from app.core.config import get_settings
from fastapi import HTTPException
import asyncio
from datetime import datetime, timedelta

settings = get_settings()

class LiveKitService:
    def __init__(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.room_service = api.RoomServiceClient(
            self.api_key,
            self.api_secret
        )

    async def create_room(self, room_name: str):
        """Create a LiveKit room for WebRTC communication"""
        try:
            room = await self.room_service.create_room(
                name=room_name,
                empty_timeout=300,  # 5 minutes
                max_participants=2   # Agent and customer
            )
            return room
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create room: {str(e)}")

    async def generate_token(self, room_name: str, participant_name: str, is_agent: bool = False):
        """Generate access token for a participant"""
        try:
            # Create token with appropriate permissions
            at = api.AccessToken(
                api_key=self.api_key,
                api_secret=self.api_secret,
                identity=participant_name,
                ttl=timedelta(hours=1)
            )
            
            # Grant permissions
            grant = api.VideoGrant(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True
            )
            
            # Add additional permissions for agents
            if is_agent:
                grant.room_admin = True
                grant.can_update_metadata = True
            
            at.add_grant(grant)
            return at.to_jwt()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")

    async def end_room(self, room_name: str):
        """End a LiveKit room"""
        try:
            await self.room_service.delete_room(room_name)
            return {"status": "success", "message": f"Room {room_name} deleted"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to end room: {str(e)}")

livekit_service = LiveKitService()
