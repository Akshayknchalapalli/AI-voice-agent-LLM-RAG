from app.core.config import get_settings
from app.models.user import UserCreate, User
from supabase import create_client
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
from postgrest.exceptions import APIError
from gotrue.errors import AuthApiError

logger = logging.getLogger(__name__)
settings = get_settings()

def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO format string"""
    return dt.isoformat() if dt else None

class UserService:
    def __init__(self):
        # Initialize two clients: one with anon key for auth, one with service role for admin ops
        self.auth_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        self.admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    async def wait_for_user(self, user_id: str, max_retries: int = 5) -> bool:
        """Wait for user to be available in auth system"""
        for attempt in range(max_retries):
            try:
                # Try to get user data through auth API instead of admin API
                response = self.admin_client.auth.get_user(user_id)
                if response and response.user:
                    logger.info(f"User {user_id} found in auth system")
                    return True
                
                logger.warning(f"User {user_id} not found in auth system, attempt {attempt + 1}/{max_retries}")
                await asyncio.sleep(2)  # Wait 2 seconds before retrying
            except Exception as e:
                logger.error(f"Error checking user existence: {str(e)}")
                await asyncio.sleep(2)
        return False
    
    async def register_user(self, user_data: UserCreate) -> Dict[str, Any]:
        try:
            logger.info(f"Registering user with email: {user_data.email}")
            
            # Create user in Supabase auth using anon client
            auth_response = self.auth_client.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password
            })
            
            if not auth_response or not auth_response.user:
                logger.error("Failed to create user in Supabase auth")
                return None
            
            user = auth_response.user
            created_at = format_datetime(user.created_at) if hasattr(user, 'created_at') else None
            
            # Store additional user data in profiles table using admin client
            profile_data = {
                'id': user.id,
                'email': user_data.email,
                'full_name': user_data.full_name,
                'created_at': created_at,
                'updated_at': created_at
            }
            
            logger.debug(f"Inserting profile data: {profile_data}")
            max_retries = 3
            last_error = None
            
            # Retry profile creation a few times
            for attempt in range(max_retries):
                try:
                    # Check if profile already exists
                    existing_profile = self.admin_client.from_('profiles').select('*').eq('id', user.id).execute()
                    if existing_profile.data and len(existing_profile.data) > 0:
                        logger.info(f"Profile already exists for user: {user.id}")
                        break
                    
                    profile_response = self.admin_client.from_('profiles').insert(profile_data).execute()
                    if profile_response.data:
                        logger.info(f"Successfully created profile for user: {user.id}")
                        break
                except APIError as e:
                    last_error = e
                    logger.warning(f"Profile creation attempt {attempt + 1}/{max_retries} failed: {e}")
                    await asyncio.sleep(2)  # Wait 2 seconds before retrying
            else:
                logger.error(f"Failed to create profile after {max_retries} attempts: {last_error}")
                return None
            
            logger.info(f"Successfully registered user: {user_data.email}")
            return {
                "id": user.id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "created_at": created_at
            }
            
        except AuthApiError as e:
            logger.error(f"Auth API error during signup: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during signup: {e}")
            return None

user_service = UserService()
