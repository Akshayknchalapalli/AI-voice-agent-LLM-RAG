from fastapi import APIRouter, WebSocket, Depends, HTTPException
from typing import List, Dict, Any
import json
import logging
from app.services.auth.auth_service import AuthService
from app.api.dependencies.auth import get_auth_service
from app.services.voice.audio_processor import AudioProcessor
from app.core.config import Settings

router = APIRouter()
logger = logging.getLogger(__name__)
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/conversation/voice")
async def websocket_endpoint(
    websocket: WebSocket,
    auth_service: AuthService = Depends(get_auth_service),
):
    await websocket.accept()
    user_id = None
    auth_token = None
    audio_processor = AudioProcessor()

    try:
        # Wait for authentication message
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)
        
        if auth_data.get("type") != "auth" or not auth_data.get("token"):
            await websocket.close(code=4001, reason="Authentication required")
            return

        # Verify token
        token = auth_data["token"]
        user = await auth_service.verify_token(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return

        user_id = str(user.get("id", "unknown"))
        auth_token = token  # Store the token for later use
        active_connections[user_id] = websocket

        # Send confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Successfully connected to voice chat"
        })

        # Handle incoming audio data
        while True:
            try:
                # Receive binary audio data
                audio_data = await websocket.receive_bytes()
                
                # Process audio data
                if audio_data:
                    # Transcribe audio to text
                    text = await audio_processor.transcribe_audio(audio_data)
                    
                    if text:
                        logger.info(f"User {user_id} said: {text}")
                        
                        # Send transcript back to client immediately
                        await websocket.send_json({
                            "type": "transcript",
                            "text": text,
                            "status": "processing"
                        })
                        
                        try:
                            # Get AI response with user context including auth token
                            user_context = {
                                "id": user_id,
                                "token": auth_token
                            }
                            ai_response = await audio_processor.get_ai_response(text, user_context)
                            
                            if ai_response:
                                logger.info(f"AI response for user {user_id}: {ai_response}")
                                
                                # Send text response first
                                await websocket.send_json({
                                    "type": "response",
                                    "text": ai_response,
                                    "status": "complete"
                                })
                                
                                # Convert AI response to speech
                                audio_response = await audio_processor.generate_audio_response(ai_response)
                                
                                if audio_response:
                                    # Send audio response back to client
                                    await websocket.send_bytes(audio_response)
                                    
                        except Exception as e:
                            logger.error(f"Error processing AI response: {str(e)}")
                            await websocket.send_json({
                                "type": "error",
                                "message": "Error generating AI response",
                                "status": "error"
                            })

            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                    "status": "error"
                })
                
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        if user_id and user_id in active_connections:
            del active_connections[user_id]
        await websocket.close(code=1011, reason=str(e))
        
    finally:
        if user_id and user_id in active_connections:
            del active_connections[user_id]
        try:
            await websocket.close()
        except:
            pass
