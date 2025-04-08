from fastapi import HTTPException
from supabase import create_client, Client
from app.core.config import get_settings
from typing import Optional, Dict, Any
import traceback
from datetime import datetime

settings = get_settings()

def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO format string"""
    return dt.isoformat() if dt else None

class AuthService:
    def __init__(self):
        try:
            print(f"Initializing Supabase clients with URL: {settings.SUPABASE_URL}")
            # Initialize two clients: one with anon key for auth, one with service role for admin ops
            self.auth_client: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            self.admin_client: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            print("Supabase clients initialized successfully")
        except Exception as e:
            print(f"Error initializing Supabase clients: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail="Error initializing auth service")

    async def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        try:
            print(f"Attempting to sign up user with email: {email}")
            data = {
                "email": email,
                "password": password
            }
            response = self.auth_client.auth.sign_up(data)
            print(f"Sign up response received: {response}")
            
            if not response or not response.user:
                raise HTTPException(status_code=400, detail="Invalid response from auth service")
            
            user = response.user
            session = response.session
            
            print(f"User created with ID: {user.id if user else 'None'}")
            print(f"Session created: {session is not None}")
            
            # If email confirmation is required
            if user and not user.email_confirmed_at:
                return {
                    "message": "Please check your email to confirm your account",
                    "requires_confirmation": True,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "email_confirmed_at": None
                    }
                }
            
            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "email_confirmed_at": format_datetime(user.email_confirmed_at)
                },
                "access_token": session.access_token if session else None,
                "token_type": "bearer"
            }
            
        except Exception as e:
            print(f"Error in sign_up: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        try:
            print(f"Attempting to sign in user with email: {email}")
            response = self.auth_client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not response or not response.user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            user = response.user
            session = response.session
            
            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "email_confirmed_at": format_datetime(user.email_confirmed_at)
                },
                "access_token": session.access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            print(f"Error in sign_in: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=401, detail="Invalid credentials")

    async def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            response = self.auth_client.auth.get_user(token)
            if not response or not response.user:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user = response.user
            return {
                "id": user.id,
                "email": user.email,
                "email_confirmed_at": format_datetime(user.email_confirmed_at)
            }
            
        except Exception as e:
            print(f"Error in verify_token: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=401, detail="Invalid token")

    async def sign_out(self, token: str) -> bool:
        try:
            self.auth_client.auth.sign_out(token)
            return True
        except Exception as e:
            print(f"Error in sign_out: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail="Error during sign out")

    async def reset_password(self, email: str) -> bool:
        try:
            self.auth_client.auth.reset_password_email(email)
            return True
        except Exception as e:
            print(f"Error in reset_password: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail="Error sending password reset email")