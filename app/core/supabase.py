from supabase import create_client
from app.core.config import get_settings
from typing import Optional

def get_supabase_client(auth_token: Optional[str] = None):
    """Get a Supabase client instance with optional auth token"""
    settings = get_settings()
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    
    if auth_token:
        client.auth.set_session(auth_token, auth_token)
    
    return client
