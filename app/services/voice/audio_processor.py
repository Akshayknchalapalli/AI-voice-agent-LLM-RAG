import logging
from typing import Dict, Any, List, Optional
import traceback
from deepgram import Deepgram
from elevenlabs.client import ElevenLabs
from app.core.config import get_settings
import asyncio
import io
import json
import tempfile
import os

settings = get_settings()
logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.elevenlabs = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.deepgram = Deepgram(settings.DEEPGRAM_API_KEY)
        logger.info("AudioProcessor initialized with API keys")

    async def process_audio(self, audio_data: bytes) -> Optional[str]:
        """Process audio data to text using Deepgram"""
        try:
            # Log the audio data size for debugging
            logger.info(f"Received audio data of size: {len(audio_data)} bytes")
            
            # Save audio data to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Open the temporary file for Deepgram
                with open(temp_file_path, 'rb') as audio_file:
                    # Create a source from the audio file
                    source = {
                        'buffer': audio_file,
                        'mimetype': 'audio/webm'
                    }
                    
                    # Configure Deepgram options
                    options = {
                        'smart_format': True,
                        'model': 'nova-2',
                        'language': 'en-US',
                        'punctuate': True
                    }
                    
                    # Send to Deepgram for transcription
                    response = await self.deepgram.transcription.prerecorded(source, options)
                    logger.info(f"Deepgram raw response: {json.dumps(response)}")
                    
                    if response and isinstance(response, dict):
                        results = response.get('results', {})
                        channels = results.get('channels', [])
                        
                        if channels and len(channels) > 0:
                            alternatives = channels[0].get('alternatives', [])
                            if alternatives and len(alternatives) > 0:
                                transcript = alternatives[0].get('transcript', '').strip()
                                if transcript:
                                    logger.info(f"Successfully transcribed text: {transcript}")
                                    return transcript
                    
                    logger.error("No valid transcript found in response structure")
                    return None
                    
            except Exception as transcription_error:
                logger.error(f"Deepgram transcription error: {str(transcription_error)}")
                logger.error(traceback.format_exc())
                return None
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.error(f"Error removing temporary file: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech using ElevenLabs"""
        try:
            # Generate audio stream with smaller model
            audio_stream = await asyncio.to_thread(
                lambda: self.elevenlabs.generate(
                    text=text,
                    voice="Adam",  # Using a default voice
                    model="eleven_multilingual_v1",  # Using the multilingual model which uses less credits
                    voice_settings={
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True
                    }
                )
            )
            
            # Convert generator to bytes
            audio_bytes = b''
            try:
                for chunk in audio_stream:
                    if isinstance(chunk, (bytes, bytearray)):
                        audio_bytes += chunk
                
                logger.info(f"Generated speech audio of size: {len(audio_bytes)} bytes")
                return audio_bytes
            except Exception as stream_error:
                if "quota_exceeded" in str(stream_error):
                    error_msg = "ElevenLabs API quota exceeded. Please try again later or upgrade your plan."
                    logger.error(error_msg)
                    raise Exception(error_msg) from stream_error
                raise
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            logger.error(traceback.format_exc())
            # Re-raise with user-friendly message
            if "quota_exceeded" in str(e):
                raise Exception("Voice generation quota exceeded. Please try again later.") from e
            raise Exception("Could not generate speech. Please try again.") from e

audio_processor = AudioProcessor()