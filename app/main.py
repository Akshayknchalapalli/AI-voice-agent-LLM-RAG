from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.api.routes import auth, voice
from app.core.config import get_settings
from app.core.database import engine
from app.models import base

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered voice agent for real estate inquiries and recommendations",
    version="1.0.0"
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    # Add WebSocket origins
    "ws://localhost:3000",
    "ws://127.0.0.1:3000",
    "ws://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # In production, specify your actual domain
)

# Create database tables
base.Base.metadata.create_all(bind=engine)

# Include routers with prefix
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])

@app.get("/")
async def root() -> dict:
    return {"message": "Welcome to the AI Voice Agent API"}

@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)}
    )
