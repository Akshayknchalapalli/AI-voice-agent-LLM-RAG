from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth.auth_service import AuthService
from app.services.auth.user_service import user_service
from app.api.dependencies.auth import get_auth_service
from app.models.user import UserCreate
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
import traceback
from fastapi.responses import JSONResponse

router = APIRouter()
security = HTTPBearer()

class UserCredentials(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(UserCreate):
    pass

class PasswordResetRequest(BaseModel):
    email: EmailStr

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

@router.post("/login")
async def login(
    credentials: UserCredentials,
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    try:
        print(f"Login attempt for email: {credentials.email}")
        result = await auth_service.sign_in(credentials.email, credentials.password)
        print(f"Login successful for email: {credentials.email}")
        return JSONResponse(content=result)
    except Exception as e:
        print(f"Login error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=401, detail="Invalid credentials")

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