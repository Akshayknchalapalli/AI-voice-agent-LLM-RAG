from deepgram import Deepgram
from elevenlabs import generate, set_api_key
from app.core.config import get_settings
import asyncio
import base64
import json

settings = get_settings()

class AudioProcessor:
    def __init__(self):
        self.deepgram = Deepgram(settings.DEEPGRAM_API_KEY)
        set_api_key(settings.ELEVENLABS_API_KEY)

    async def speech_to_text(self, audio_data: bytes, mime_type: str = "audio/wav"):
        """Convert speech to text using Deepgram"""
        try:
            source = {"buffer": audio_data, "mimetype": mime_type}
            response = await self.deepgram.transcription.prerecorded(
                source,
                {
                    "smart_format": True,
                    "model": "general",
                    "language": "en-US"
                }
            )
            return response["results"]["channels"][0]["alternatives"][0]["transcript"]
        except Exception as e:
            raise Exception(f"Speech-to-text failed: {str(e)}")

    async def text_to_speech(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
        """Convert text to speech using ElevenLabs"""
        try:
            audio = generate(
                text=text,
                voice=voice_id,
                model="eleven_monolingual_v1"
            )
            return audio
        except Exception as e:
            raise Exception(f"Text-to-speech failed: {str(e)}")

    async def process_realtime_audio(self, websocket):
        """Process real-time audio stream from WebSocket"""
        try:
            deepgram_socket = await self.deepgram.transcription.live({
                'punctuate': True,
                'interim_results': False,
                'language': 'en-US',
                'model': 'general',
            })

            async def send_to_deepgram(websocket, deepgram_socket):
                try:
                    while True:
                        audio_data = await websocket.receive_bytes()
                        await deepgram_socket.send(audio_data)
                except Exception as e:
                    print(f"Error sending to Deepgram: {e}")
                    await deepgram_socket.finish()

            async def receive_from_deepgram(websocket, deepgram_socket):
                try:
                    while True:
                        result = await deepgram_socket.recv()
                        transcript = json.loads(result)["channel"]["alternatives"][0]["transcript"]
                        if transcript:
                            await websocket.send_text(transcript)
                except Exception as e:
                    print(f"Error receiving from Deepgram: {e}")

            await asyncio.gather(
                send_to_deepgram(websocket, deepgram_socket),
                receive_from_deepgram(websocket, deepgram_socket)
            )

        except Exception as e:
            raise Exception(f"Real-time audio processing failed: {str(e)}")

audio_processor = AudioProcessor()
