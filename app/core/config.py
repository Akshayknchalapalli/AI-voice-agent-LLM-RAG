from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Pinecone
    PINECONE_API_KEY: str
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    
    # Voice Services
    DEEPGRAM_API_KEY: str
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    AGENT_NOTIFICATION_EMAIL: str
    
    # CRM
    CRM_API_URL: str
    CRM_API_KEY: str
    
    class Config:
        env_file = '.env'

@lru_cache()
def get_settings() -> Settings:
    return Settings()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    REDIS_URL: str
    
    # Voice Services
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    
    # AI Services
    OPENAI_API_KEY: str
    ELEVENLABS_API_KEY: str
    DEEPGRAM_API_KEY: str
    
    # Vector Database
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
