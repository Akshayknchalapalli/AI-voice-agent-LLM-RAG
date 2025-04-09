import aiohttp
from app.core.config import get_settings
from fastapi import HTTPException
import asyncio
from datetime import datetime, timedelta
import logging
import jwt
import json
import time
import re
from urllib.parse import urlparse, urljoin

settings = get_settings()
logger = logging.getLogger(__name__)

class LiveKitService:
    def __init__(self):
        if not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET or not settings.LIVEKIT_WS_URL:
            raise ValueError("LiveKit configuration is missing. Please set LIVEKIT_API_KEY, LIVEKIT_API_SECRET, and LIVEKIT_WS_URL in .env")
            
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.ws_url = settings.LIVEKIT_WS_URL.rstrip('/')  # Remove trailing slash if present
        
        # Parse and validate the WebSocket URL
        parsed_url = urlparse(self.ws_url)
        if not parsed_url.scheme in ['ws', 'wss']:
            raise ValueError(f"Invalid LiveKit WebSocket URL scheme: {self.ws_url}. Must start with ws:// or wss://")
        
        # Convert WebSocket URL to HTTP URL and ensure it has the API path
        http_scheme = 'https' if parsed_url.scheme == 'wss' else 'http'
        self.api_url = f"{http_scheme}://{parsed_url.netloc}"
        
        logger.info(f"Initialized LiveKit service with:")
        logger.info(f"  API URL: {self.api_url}")
        logger.info(f"  WebSocket URL: {self.ws_url}")
        logger.info(f"  API Key: {self.api_key[:4]}...")

    async def create_room_and_token(self, room_name: str, user_id: str) -> str:
        """Create a LiveKit room and generate a token for the user"""
        try:
            # Clean room name (remove special characters)
            room_name = re.sub(r'[^a-zA-Z0-9-]', '-', room_name)
            
            # Create room
            await self.create_room(room_name)
            
            # Generate token with all necessary permissions
            token = self._generate_token(
                room_name,
                identity=f"user-{user_id}",
                is_admin=False,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Failed to create room and token: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create room and token")

    async def create_room(self, room_name: str):
        """Create a LiveKit room using REST API"""
        try:
            logger.info(f"Creating LiveKit room: {room_name}")
            
            # Generate admin token
            token = self._generate_token(room_name, "server", True)
            logger.debug(f"Generated admin token: {token[:20]}...")
            
            # Create room via REST API
            async with aiohttp.ClientSession() as session:
                # Try both API endpoints
                endpoints = [
                    f"{self.api_url}/twirp/livekit.RoomService/CreateRoom",
                    f"{self.api_url}/room/create"
                ]
                
                for endpoint in endpoints:
                    try:
                        async with session.post(
                            endpoint,
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Content-Type": "application/json"
                            },
                            json={"name": room_name}
                        ) as response:
                            if response.status == 200:
                                room_data = await response.json()
                                logger.info(f"Created room successfully: {room_name}")
                                return room_data
                            elif response.status != 404:  # If not 404, break as we got a definitive error
                                response.raise_for_status()
                    except aiohttp.ClientError as e:
                        logger.warning(f"Failed to create room using endpoint {endpoint}: {str(e)}")
                        continue
                
                # If we get here, both endpoints failed
                raise HTTPException(status_code=500, detail="Failed to create room")
                
        except Exception as e:
            logger.error(f"Error creating room: {str(e)}")
            raise

    def _generate_token(
        self,
        room_name: str,
        identity: str,
        is_admin: bool = False,
        can_publish: bool = True,
        can_subscribe: bool = True,
        can_publish_data: bool = True,
        ttl: int = 3600  # 1 hour
    ) -> str:
        """Generate a LiveKit token with specified permissions"""
        try:
            now = int(time.time())
            
            # Define video permissions
            video_grant = {
                "room": room_name,
                "roomJoin": True,
                "canPublish": can_publish,
                "canSubscribe": can_subscribe,
                "canPublishData": can_publish_data,
                "hidden": False
            }
            
            if is_admin:
                video_grant.update({
                    "roomAdmin": True,
                    "roomCreate": True,
                    "roomList": True,
                    "roomRecord": True,
                    "canUpdateOwnMetadata": True,
                    "canAdminMetadata": True
                })
            
            # Create JWT payload
            payload = {
                "iss": self.api_key,  # Issuer
                "nbf": now,  # Not before
                "exp": now + ttl,  # Expiration
                "sub": identity,  # Subject (user identity)
                "video": video_grant
            }
            
            # Generate token
            token = jwt.encode(payload, self.api_secret, algorithm='HS256')
            return token
            
        except Exception as e:
            logger.error(f"Error generating token: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate token")

livekit_service = LiveKitService()
