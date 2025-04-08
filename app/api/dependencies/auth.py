from fastapi import Depends, HTTPException
from app.services.auth.auth_service import AuthService
from typing import Optional, Dict, Any

def get_auth_service() -> AuthService:
    """Dependency to get an instance of AuthService"""
    try:
        return AuthService()
    except Exception as e:
        print(f"Error creating AuthService: {str(e)}")
        raise HTTPException(status_code=500, detail="Error initializing auth service")

async def get_current_user(
    auth_service: AuthService = Depends(get_auth_service),
    token: str = None
) -> Optional[Dict[str, Any]]:
    """Dependency to get the current authenticated user"""
    if not token:
        return None
    
    try:
        return await auth_service.verify_token(token)
    except HTTPException:
        return None