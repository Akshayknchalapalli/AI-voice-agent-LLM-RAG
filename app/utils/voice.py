from typing import Dict, Optional, Tuple
import asyncio
import aiohttp
from app.core.config import settings

class VoiceProcessor:
    def __init__(self):
        self.deepgram_api_key = settings.DEEPGRAM_API_KEY
        self.elevenlabs_api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID

    async def transcribe_audio(self, audio_data: bytes) -> Tuple[str, float]:
        """
        Transcribe audio using Deepgram's API.
        Returns tuple of (transcript, confidence)
        """
        url = "https://api.deepgram.com/v1/listen"
        headers = {
            "Authorization": f"Token {self.deepgram_api_key}",
            "Content-Type": "audio/wav"
        }
        params = {
            "model": "general",
            "language": "en-US",
            "punctuate": True,
            "diarize": True
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, params=params, data=audio_data) as resp:
                    result = await resp.json()
                    
                    if "results" in result:
                        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
                        confidence = result["results"]["channels"][0]["alternatives"][0]["confidence"]
                        return transcript, confidence
                    else:
                        raise ValueError("No transcription results found")
                        
        except Exception as e:
            print(f"Error in transcription: {str(e)}")
            return "", 0.0

    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech using ElevenLabs API."""
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    else:
                        print(f"TTS API error: {resp.status}")
                        return None
                        
        except Exception as e:
            print(f"Error in text-to-speech: {str(e)}")
            return None

    async def enhance_audio(self, audio_data: bytes) -> Optional[bytes]:
        """
        Enhance audio quality by removing background noise
        and improving clarity.
        """
        # TODO: Implement audio enhancement using a service like Krisp or custom ML model
        return audio_data

    async def detect_silence(self, audio_data: bytes, threshold: float = 0.1) -> bool:
        """Detect if audio chunk is silence."""
        # TODO: Implement silence detection
        return False

    async def get_speaker_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of speaker's text."""
        url = "https://api.openai.com/v1/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "text-davinci-003",
            "prompt": f"Analyze the sentiment in this text: '{text}'\nReturn sentiment scores as JSON with keys: positive, negative, neutral. Values should sum to 1.0",
            "max_tokens": 100,
            "temperature": 0.3
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    result = await resp.json()
                    sentiment_text = result["choices"][0]["text"].strip()
                    # Parse the JSON string to dict
                    import json
                    return json.loads(sentiment_text)
        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34}
