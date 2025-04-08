from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Voice Agent"
    
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
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
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
