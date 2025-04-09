from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from app.services.auth.auth_service import AuthService
from app.services.auth.user_service import user_service
from app.api.dependencies.auth import get_auth_service
from app.models.user import UserCreate
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
import traceback
from app.services.voice.livekit_service import livekit_service
from app.core.config import get_settings

router = APIRouter()
security = HTTPBearer(auto_error=False)  # Make bearer token optional for OPTIONS requests

class UserCredentials(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(UserCreate):
    pass

class PasswordResetRequest(BaseModel):
    email: EmailStr

@router.options("/login")
async def login_options():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@router.post("/login")
async def login(
    credentials: UserCredentials,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    try:
        print(f"Login attempt for email: {credentials.email}")
        result = await auth_service.sign_in(credentials.email, credentials.password)
        print(f"Login successful for email: {credentials.email}")
        return JSONResponse(
            content=result,
            headers={
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    except Exception as e:
        print(f"Login error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/verify")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    try:
        print("Attempting to verify token")
        user = await auth_service.verify_token(credentials.credentials)
        return JSONResponse(content=user)
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/signup")
async def signup(
    user_data: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    try:
        print(f"Received signup request for email: {user_data.email}")
        
        # First create the user profile
        user = await user_service.register_user(user_data)
        if not user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        # Then sign them in to get the access token
        auth_result = await auth_service.sign_in(user_data.email, user_data.password)
        print(f"Signup successful for email: {user_data.email}")
        
        return JSONResponse(content={
            "user": user,
            "access_token": auth_result["access_token"],
            "token_type": "bearer"
        })
        
    except HTTPException as e:
        print(f"HTTP error during signup: {str(e.detail)}")
        raise e
    except Exception as e:
        print(f"Unexpected error in signup route: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    try:
        print("Processing logout request")
        success = await auth_service.sign_out(credentials.credentials)
        return JSONResponse(content={"success": success})
    except Exception as e:
        print(f"Logout error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Error during logout")

@router.post("/reset-password")
async def reset_password(
    request: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    try:
        print(f"Processing password reset for email: {request.email}")
        success = await auth_service.reset_password(request.email)
        return JSONResponse(content={"success": success})
    except Exception as e:
        print(f"Password reset error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Error sending password reset email")

@router.get("/livekit-token")
async def get_livekit_token(
    userId: str,
    roomName: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Generate a LiveKit token for a user to join a room"""
    try:
        # Verify the user's token
        user = await verify_token(credentials, auth_service)
        
        # Generate LiveKit token
        token = await livekit_service.generate_token(roomName, userId, False)
        
        # Get settings for LiveKit WebSocket URL
        settings = get_settings()
        
        return {
            "token": token,
            "ws_url": settings.LIVEKIT_WS_URL
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))