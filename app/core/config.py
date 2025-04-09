from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
import logging

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Voice Agent"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered voice agent for real estate inquiries and recommendations"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Database
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_JWT_SECRET: str
    
    # AI Services
    GOOGLE_API_KEY: str | None = None  # For Gemini
    ELEVENLABS_API_KEY: str | None = None
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID
    DEEPGRAM_API_KEY: str | None = None
    
    # CORS Settings
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "ws://localhost:3000",
        "ws://localhost:3001",
        "ws://localhost:5173",
        "ws://127.0.0.1:3000",
        "ws://127.0.0.1:3001",
        "ws://127.0.0.1:5173",
        "ws://127.0.0.1:8000"
    ]
    
    # Other Settings (Optional)
    FRONTEND_URL: str = "http://localhost:3000"
    TWILIO_NUMBER: str | None = None
    LIVEKIT_API_KEY: str | None = None
    LIVEKIT_API_SECRET: str | None = None
    LIVEKIT_WS_URL: str | None = None  # WebSocket URL for LiveKit
    PINECONE_API_KEY: str | None = None
    PINECONE_ENVIRONMENT: str | None = None
    SMTP_HOST: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    try:
        settings = Settings()
        print("Settings loaded successfully")
        return settings
    except Exception as e:
        print(f"Error loading settings: {e}")
        raise
