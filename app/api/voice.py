from fastapi import APIRouter, WebSocket, HTTPException, Depends
from app.services.voice.twilio_service import twilio_service
from app.services.voice.livekit_service import livekit_service
from app.services.voice.audio_processor import audio_processor
from app.core.config import get_settings
from typing import Optional
import uuid

router = APIRouter(prefix="/voice", tags=["voice"])
settings = get_settings()

@router.post("/call/outbound")
async def initiate_outbound_call(to_number: str, from_number: str, webhook_url: str):
    """Initiate an outbound call using Twilio"""
    call_sid = await twilio_service.start_outbound_call(to_number, from_number, webhook_url)
    return {"call_sid": call_sid}

@router.get("/call/{call_sid}")
async def get_call_status(call_sid: str):
    """Get status of a Twilio call"""
    return await twilio_service.get_call_status(call_sid)

@router.post("/room")
async def create_webrtc_room(customer_name: str):
    """Create a LiveKit room for WebRTC communication"""
    room_name = f"room_{uuid.uuid4().hex[:8]}"
    room = await livekit_service.create_room(room_name)
    
    # Generate tokens for both participants
    customer_token = await livekit_service.generate_token(room_name, customer_name)
    agent_token = await livekit_service.generate_token(room_name, "agent", is_agent=True)
    
    return {
        "room_name": room_name,
        "customer_token": customer_token,
        "agent_token": agent_token
    }

@router.delete("/room/{room_name}")
async def end_webrtc_room(room_name: str):
    """End a LiveKit room"""
    return await livekit_service.end_room(room_name)

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming"""
    await websocket.accept()
    try:
        await audio_processor.process_realtime_audio(websocket)
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))
    finally:
        await websocket.close()
