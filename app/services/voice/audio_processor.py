import logging
from typing import Dict, Any, List, Optional
import traceback
import google.generativeai as genai
from deepgram import Deepgram
from elevenlabs.client import ElevenLabs
from app.core.config import get_settings
from app.core.supabase import get_supabase_client
from app.services.vector_store.pinecone_service import pinecone_service
from app.services.voice.livekit_service import livekit_service
import asyncio
import aiohttp
import base64
import json
import io

settings = get_settings()
logger = logging.getLogger(__name__)
genai.configure(api_key=settings.GOOGLE_API_KEY)

class AudioProcessor:
    def __init__(self):
        self.elevenlabs = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        self.conversation_history = {}
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.active_rooms: Dict[str, str] = {}  # user_id -> room_name
        logger.info("AudioProcessor initialized with API keys")

    async def load_conversation_history(self, user_id: str, auth_token: str):
        """Load conversation history from Supabase"""
        try:
            # Get last 10 conversations for the user
            supabase = get_supabase_client(auth_token)
            response = await asyncio.to_thread(
                lambda: supabase.table('conversations')
                .select('transcript,ai_response')
                .eq('user_id', user_id)
                .order('created_at', desc=True)
                .limit(10)
                .execute()
            )

            if response.data:
                # Convert to chat format and reverse to get chronological order
                history = []
                for conv in reversed(response.data):
                    if conv.get('transcript'):
                        history.append(conv['transcript'])
                    if conv.get('ai_response'):
                        history.append(conv['ai_response'])
                self.conversation_history[user_id] = history
            else:
                self.conversation_history[user_id] = []

        except Exception as e:
            logger.error(f"Error loading conversation history: {str(e)}")
            # Initialize empty history on error
            self.conversation_history[user_id] = []

    async def save_conversation(self, user_id: str, transcript: str, ai_response: str, auth_token: str):
        """Save conversation to Supabase"""
        try:
            data = {
                'user_id': user_id,
                'transcript': transcript,
                'ai_response': ai_response
            }
            
            supabase = get_supabase_client(auth_token)
            response = await asyncio.to_thread(
                lambda: supabase.table('conversations')
                .insert(data)
                .execute()
            )
            logger.info(f"Saved conversation for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            raise Exception(f"Failed to save conversation: {str(e)}")

    async def create_or_join_room(self, user_id: str, auth_token: str) -> Dict[str, str]:
        """Create or join a LiveKit room for real-time audio"""
        try:
            if user_id not in self.active_rooms:
                room_name = f"voice-chat-{user_id}"
                await livekit_service.create_room(room_name)
                self.active_rooms[user_id] = room_name
                
                # Generate tokens for user and AI agent
                user_token = await livekit_service.generate_token(room_name, f"user-{user_id}", False)
                agent_token = await livekit_service.generate_token(room_name, "ai-agent", True)
                
                return {
                    "room_name": room_name,
                    "user_token": user_token,
                    "agent_token": agent_token
                }
            else:
                room_name = self.active_rooms[user_id]
                user_token = await livekit_service.generate_token(room_name, f"user-{user_id}", False)
                agent_token = await livekit_service.generate_token(room_name, "ai-agent", True)
                
                return {
                    "room_name": room_name,
                    "user_token": user_token,
                    "agent_token": agent_token
                }
        except Exception as e:
            logger.error(f"Error creating/joining room: {str(e)}")
            raise Exception(f"Failed to create/join room: {str(e)}")

    def _enhance_prompt_with_context(self, query: str, relevant_docs: List[Dict[str, Any]]) -> str:
        """Enhance the prompt with relevant real estate knowledge and property listings"""
        context = "\n\nRelevant information:\n"
        
        # Separate real estate knowledge and property listings
        knowledge_docs = [doc for doc in relevant_docs if doc["type"] == "realestate"]
        property_docs = [doc for doc in relevant_docs if doc["type"] == "properties"]
        
        # Add real estate knowledge
        if knowledge_docs:
            context += "\nMarket Information:\n"
            for doc in knowledge_docs:
                context += f"- {doc['content']}\n"
        
        # Add property listings
        if property_docs:
            context += "\nRelevant Properties:\n"
            for doc in property_docs:
                property_info = (
                    f"- {doc['location']}: {doc['bedrooms']} bed, {doc['bathrooms']} bath, "
                    f"{doc['area']} sqft home for ${doc['price']:,}. "
                    f"Features: {', '.join(doc['amenities'][:3])}..."
                )
                context += property_info + "\n"
        
        return f"""You are a helpful real estate AI assistant. Use the following information to provide accurate answers.
        
        {context}
        
        User's question: {query}
        
        Please provide a helpful but concise response suitable for voice conversation. If discussing specific properties, mention key details like price, location, and main features."""

    async def get_ai_response(self, text: str, user_context: Dict[str, Any]) -> str:
        """Get AI response for the transcribed text"""
        try:
            user_id = str(user_context.get('id', 'unknown'))
            auth_token = user_context.get('token')
            if not auth_token:
                raise ValueError("Authentication token is required")

            logger.info(f"Getting AI response for user {user_id}")
            logger.info(f"User message: {text}")
            
            # Initialize conversation history if not exists
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
                await self.load_conversation_history(user_id, auth_token)
            
            # Get relevant information from both indexes
            real_estate_docs = await pinecone_service.query_similar_docs(text, index_type="realestate", top_k=2)
            property_docs = await pinecone_service.query_similar_docs(text, index_type="properties", top_k=3)
            
            # Combine results
            relevant_docs = real_estate_docs + property_docs
            
            # Create enhanced prompt with context
            enhanced_prompt = self._enhance_prompt_with_context(text, relevant_docs)
            
            # Get AI response from Gemini using a separate thread
            logger.info("Sending request to Gemini...")
            ai_response = await asyncio.to_thread(
                self._generate_gemini_response, 
                enhanced_prompt, 
                self.conversation_history[user_id]
            )
            
            # Add messages to history
            if text:
                self.conversation_history[user_id].append(text)
            
            if ai_response:
                self.conversation_history[user_id].append(ai_response)
                
                # Save conversation to Supabase
                await self.save_conversation(user_id, text, ai_response, auth_token)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"AI response error: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get AI response: {str(e)}")

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio data to text using Deepgram"""
        try:
            logger.info(f"Received audio data of size: {len(audio_data)} bytes")
            
            # Initialize Deepgram client
            deepgram = Deepgram(settings.DEEPGRAM_API_KEY)
            
            # Set up request parameters
            source = {
                "buffer": audio_data,
                "mimetype": "audio/webm",
                "encoding": "opus"
            }
            
            # Configure transcription options
            options = {
                "smart_format": True,
                "model": "general",
                "language": "en-US",
                "punctuate": True,
                "diarize": False,
                "channels": 1
            }
            
            logger.info("Sending request to Deepgram API...")
            response = await deepgram.transcription.prerecorded(source, options)
            logger.info("Successfully received response from Deepgram")
            
            if response and 'results' in response:
                transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
                logger.info(f"Successfully transcribed audio to text: {transcript}")
                return transcript.strip() if transcript else ""
            
            logger.warning("No transcript found in Deepgram response")
            return ""
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}", exc_info=True)
            raise Exception(f"Failed to transcribe audio: {str(e)}")

    def _generate_gemini_response(self, prompt: str, history: list) -> str:
        """Generate response using Gemini (synchronous)"""
        try:
            # Start a chat
            chat = self.model.start_chat(history=[])
            
            # Add system prompt
            system_prompt = """You are a helpful real estate AI assistant. You help users find properties, 
            answer questions about listings, and provide relevant information about real estate. 
            Keep responses concise and natural for voice conversation.
            Use the conversation history to maintain context and provide relevant responses."""
            
            # Send system prompt as plain text
            chat.send_message(system_prompt)
            
            # Add conversation history (only non-empty messages)
            for msg in history[-5:]:  # Last 5 messages
                if msg:
                    chat.send_message(msg)
            
            # Send user's message and get response
            if not prompt:
                raise ValueError("User prompt cannot be empty")
                
            response = chat.send_message(prompt)
            return response.text if response and response.text else "I apologize, but I couldn't generate a response at this time."
            
        except Exception as e:
            logger.error(f"Gemini error: {str(e)}\n{traceback.format_exc()}")
            raise Exception(f"Failed to get Gemini response: {str(e)}")

    async def generate_audio_response(self, text: str) -> Optional[bytes]:
        """Convert AI response text to speech"""
        try:
            logger.info(f"Converting text to speech: {text}")
            audio = await asyncio.to_thread(
                self.elevenlabs.text_to_speech.convert,
                text=text,
                voice_id="21m00Tcm4TlvDq8ikWAM",  # Josh voice
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            logger.info("Successfully generated audio response")
            return audio
        except Exception as e:
            logger.error(f"Text-to-speech error: {str(e)}", exc_info=True)
            return None

    def clear_conversation_history(self, user_id: str):
        """Clear conversation history for a user"""
        if user_id in self.conversation_history:
            logger.info(f"Clearing conversation history for user {user_id}")
            del self.conversation_history[user_id]

audio_processor = AudioProcessor()
