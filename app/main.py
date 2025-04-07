from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api import voice, conversation, property
from app.core.config import get_settings
from app.core.database import engine
from app.models import base, property as property_model

settings = get_settings()

app = FastAPI(
    title="Real Estate AI Voice Agent",
    description="AI-powered voice agent for real estate inquiries and recommendations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
base.Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(voice.router)
app.include_router(conversation.router)
app.include_router(property.router)

@app.get("/")
async def root():
    return {
        "message": "Real Estate AI Voice Agent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "status": "error",
        "code": exc.status_code,
        "message": str(exc.detail)
    }
