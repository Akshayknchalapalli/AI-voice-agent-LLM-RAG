from deepgram import DeepgramClient, PrerecordedOptions, LiveOptions, LiveTranscriptionEvents, ClientOptionsFromEnv
from elevenlabs.client import ElevenLabs
from app.core.config import get_settings
import asyncio
import base64
import json

settings = get_settings()

class AudioProcessor:
    def __init__(self):
        self.deepgram = DeepgramClient("", ClientOptionsFromEnv())
        self.elevenlabs = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

    async def speech_to_text(self, audio_data: bytes, mime_type: str = "audio/wav"):
        """Convert speech to text using Deepgram"""
        try:
            options = PrerecordedOptions(
                model="nova-3",
                smart_format=True,
                language="en-US"
            )
            response = await self.deepgram.listen.rest.v("1").transcribe_buffer(audio_data, options)
            return response.results.channels[0].alternatives[0].transcript
        except Exception as e:
            raise Exception(f"Speech-to-text failed: {str(e)}")

    async def text_to_speech(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
        """Convert text to speech using ElevenLabs"""
        try:
            audio = self.elevenlabs.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            return audio
        except Exception as e:
            raise Exception(f"Text-to-speech failed: {str(e)}")

    async def process_realtime_audio(self, websocket):
        """Process real-time audio stream from WebSocket"""
        try:
            options = LiveOptions(
                model="nova-3",
                smart_format=True,
                language="en-US",
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                utterance_end_ms="1000",
                vad_events=True
            )

            dg_connection = self.deepgram.listen.websocket.v("1")

            @dg_connection.on(LiveTranscriptionEvents.Transcript)
            async def on_message(result, **kwargs):
                sentence = result.channel.alternatives[0].transcript
                if len(sentence) > 0:
                    await websocket.send_text(json.dumps({"type": "transcript", "text": sentence}))

            @dg_connection.on(LiveTranscriptionEvents.Error)
            async def on_error(error, **kwargs):
                await websocket.send_text(json.dumps({"type": "error", "error": str(error)}))

            await dg_connection.start(options)

            try:
                while True:
                    data = await websocket.receive_bytes()
                    await dg_connection.send(data)
            except Exception as e:
                print(f"WebSocket error: {str(e)}")
            finally:
                await dg_connection.finish()


        except Exception as e:
            raise Exception(f"Real-time audio processing failed: {str(e)}")

audio_processor = AudioProcessor()
