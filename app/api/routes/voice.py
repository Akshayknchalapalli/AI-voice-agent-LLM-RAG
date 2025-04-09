from fastapi import APIRouter, WebSocket, Depends, HTTPException, WebSocketDisconnect, Header, Query
from typing import List, Dict, Any, Optional
import json
import logging
from app.services.auth.auth_service import AuthService
from app.api.dependencies.auth import get_auth_service
from app.services.voice.audio_processor import AudioProcessor
from app.services.voice.tts_service import tts_service
from app.services.voice.livekit_service import livekit_service
from app.services.chat.conversation_manager import conversation_manager
from app.core.config import get_settings
import traceback
from pydantic import BaseModel
from starlette.websockets import WebSocketState

class RoomRequest(BaseModel):
    user_id: str

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()
active_connections: Dict[str, WebSocket] = {}

@router.post("/conversation/room")
async def create_room(
    request: RoomRequest,
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Create a LiveKit room for a user"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="No authorization token provided")
        
        # Extract token from Bearer header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = authorization.split(" ")[1]
        
        # Verify token and get user ID
        try:
            verified_user = await auth_service.verify_token(token)
            logger.info(f"Verified user: {verified_user}")
            logger.info(f"Request user_id: {request.user_id}")
            
            if verified_user['id'] != request.user_id:
                logger.error(f"User ID mismatch: token user {verified_user['id']} != request user {request.user_id}")
                raise HTTPException(status_code=403, detail="User ID mismatch")
                
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid authorization token")
            
        # Create LiveKit room
        try:
            room_name = f"voice-{request.user_id}"
            token = await livekit_service.create_room_and_token(room_name, request.user_id)
            return {
                "token": token,
                "room": room_name,
                "livekit_ws_url": settings.LIVEKIT_WS_URL
            }
        except Exception as e:
            logger.error(f"Failed to create LiveKit room: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create room")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.websocket("/conversation/voice")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    auth_service: AuthService = Depends(get_auth_service),
):
    user_id = None
    try:
        # Verify token before accepting connection
        user = await auth_service.verify_token(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid authentication token")
            return
            
        # Accept the connection after successful authentication
        await websocket.accept()
        
        user_id = user.get("id")
        audio_processor = AudioProcessor()

        try:
            # Store the connection
            if user_id in active_connections:
                # Close existing connection
                try:
                    await active_connections[user_id].close()
                except:
                    pass
                    
            active_connections[user_id] = websocket
            
            # Send success message
            await websocket.send_json({
                "type": "connected",
                "message": "Connected successfully"
            })
            
            # Handle incoming messages
            while True:
                try:
                    # Receive binary audio data
                    data = await websocket.receive_bytes()
                    
                    # Process audio to text
                    text = await audio_processor.process_audio(data)
                    if not text:
                        continue
                        
                    await websocket.send_json({
                        "type": "transcription",
                        "text": text
                    })
                    
                    # Get AI response
                    response = await conversation_manager.process_query(user_id, text)
                    
                    # Send text response
                    await websocket.send_json({
                        "type": "response",
                        "text": response.text,
                        "properties": response.properties if hasattr(response, 'properties') else None
                    })

                    # Convert response to speech and send audio
                    try:
                        audio_data = await tts_service.text_to_speech(response.text)
                        if audio_data and len(audio_data) > 0:
                            logger.info(f"Sending audio response of size: {len(audio_data)} bytes")
                            await websocket.send_bytes(audio_data)
                        else:
                            logger.error("TTS service returned empty audio data")
                            await websocket.send_json({
                                "type": "error",
                                "message": "Failed to generate audio response"
                            })
                    except ValueError as ve:
                        logger.error(f"TTS error: {str(ve)}")
                        await websocket.send_json({
                            "type": "error",
                            "message": str(ve)
                        })
                    except Exception as e:
                        logger.error(f"Unexpected TTS error: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to generate audio response"
                        })
                    
                except WebSocketDisconnect:
                    logger.info(f"Client disconnected: {user_id}")
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Error processing message"
                    })
                    
        except WebSocketDisconnect:
            logger.info(f"Client disconnected during auth: {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.close()
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket connection: {str(e)}")
        await websocket.close(code=4000, reason="Connection initialization failed")
    finally:
        if user_id and user_id in active_connections:
            del active_connections[user_id]
        logger.info(f"Connection closed for user: {user_id}")
