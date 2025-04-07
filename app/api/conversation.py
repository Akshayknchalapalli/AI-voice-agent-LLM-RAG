from fastapi import APIRouter, HTTPException, WebSocket, Depends
from app.services.llm.conversation_manager import conversation_pool
from app.services.voice.audio_processor import audio_processor
from typing import Dict, Optional
import json
import uuid

router = APIRouter(prefix="/conversation", tags=["conversation"])

@router.post("/{session_id}/message")
async def process_message(
    session_id: str,
    message: str,
    property_context: Optional[Dict] = None
):
    """Process a text message in a conversation"""
    conversation = conversation_pool.get_conversation(session_id)
    result = await conversation.process_user_input(message, property_context)
    return result

@router.get("/{session_id}/summary")
async def get_summary(session_id: str):
    """Get a summary of the conversation"""
    conversation = conversation_pool.get_conversation(session_id)
    summary = await conversation.get_conversation_summary()
    return {"summary": summary}

@router.delete("/{session_id}")
async def end_conversation(session_id: str):
    """End a conversation session"""
    conversation_pool.end_conversation(session_id)
    return {"status": "success", "message": "Conversation ended"}

@router.websocket("/voice/{session_id}")
async def voice_conversation(websocket: WebSocket, session_id: str):
    """Handle real-time voice conversation"""
    await websocket.accept()
    conversation = conversation_pool.get_conversation(session_id)
    
    try:
        while True:
            # Receive audio data
            audio_data = await websocket.receive_bytes()
            
            # Convert speech to text
            text = await audio_processor.speech_to_text(audio_data)
            
            if text.strip():
                # Process the text through conversation manager
                result = await conversation.process_user_input(text)
                
                # Convert response to speech
                audio_response = await audio_processor.text_to_speech(result["response"])
                
                # Send both text and audio response
                await websocket.send_json({
                    "type": "response",
                    "text": result["response"],
                    "requirements": result.get("extracted_requirements")
                })
                await websocket.send_bytes(audio_response)
    
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))
    finally:
        # Cleanup
        conversation_pool.end_conversation(session_id)
