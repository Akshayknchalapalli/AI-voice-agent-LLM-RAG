import httpx
from app.core.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        # Initialize ElevenLabs settings
        self.api_key = settings.ELEVENLABS_API_KEY
        self.api_url = "https://api.elevenlabs.io/v1/text-to-speech"
        # Bella voice ID
        self.voice = "EXAVITQu4vr4xnSDxMaL"

    async def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using ElevenLabs"""
        if not self.api_key:
            logger.error("ElevenLabs API key is not set")
            raise ValueError("ElevenLabs API key is not configured")

        if not text or not text.strip():
            logger.error("Empty text provided for TTS conversion")
            raise ValueError("Cannot convert empty text to speech")

        try:
            # Call ElevenLabs API directly
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            url = f"{self.api_url}/{self.voice}"
            logger.info(f"Making TTS request for text: {text[:50]}...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()
                
                if response.headers.get('content-type') != 'audio/mpeg':
                    logger.error(f"Unexpected content type from TTS API: {response.headers.get('content-type')}")
                    raise ValueError("Invalid response from TTS service")
                
                content = response.content
                if not content or len(content) == 0:
                    logger.error("Received empty response from TTS API")
                    raise ValueError("Empty response from TTS service")
                
                logger.info(f"Successfully generated audio of size: {len(content)} bytes")
                return content
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in TTS conversion: {str(e)}")
            if e.response.status_code == 401:
                raise ValueError("Invalid ElevenLabs API key")
            raise ValueError(f"TTS API error: {e.response.status_code}")
            
        except Exception as e:
            logger.error(f"Error in text-to-speech conversion: {str(e)}")
            raise ValueError(f"Failed to convert text to speech: {str(e)}")

tts_service = TTSService()
