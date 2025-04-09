from typing import List, Dict, Any, Optional
import logging
from supabase import create_client, Client
from app.core.config import get_settings
import traceback

logger = logging.getLogger(__name__)
settings = get_settings()

class SupabaseService:
    def __init__(self):
        """Initialize Supabase client"""
        try:
            logger.info(f"Initializing Supabase client with URL: {settings.SUPABASE_URL}")
            self.client: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            # Test connection
            self.client.table('conversations').select('count').execute()
            logger.info("Supabase client initialized and connected successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def save_conversation(self, transcript: str, ai_response: str, audio_url: Optional[str] = None) -> bool:
        """Save a conversation to Supabase"""
        try:
            logger.info("Attempting to save conversation to Supabase")
            logger.info(f"Transcript: {transcript[:100]}...")
            logger.info(f"AI Response: {ai_response[:100]}...")
            
            # Prepare data
            data = {
                'transcript': transcript,
                'ai_response': ai_response,
                'audio_url': audio_url
            }
            
            # Try to get session but don't require it
            try:
                session = self.client.auth.get_session()
                if session and session.user:
                    data['user_id'] = session.user.id
                    logger.info(f"Adding user_id to conversation: {session.user.id}")
                else:
                    logger.info("No authenticated user session found")
            except Exception as e:
                logger.warning(f"Error getting session, saving as anonymous: {str(e)}")

            # Insert conversation into the conversations table
            logger.info("Executing Supabase insert")
            response = self.client.table('conversations').insert(data).execute()
            
            if not response.data:
                logger.error("No data returned from Supabase insert")
                logger.error(f"Response: {response}")
                return False
                
            logger.info(f"Successfully saved conversation with ID: {response.data[0].get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation to Supabase: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    async def get_properties_by_ids(self, property_ids: List[str]) -> List[Dict[str, Any]]:
        """Get property details from Supabase by property IDs"""
        try:
            # Query properties table
            response = self.client.table('properties').select('*').in_('id', property_ids).execute()
            
            if response.data:
                # Sort results to match the order of property_ids
                id_to_property = {prop['id']: prop for prop in response.data}
                sorted_properties = [id_to_property[pid] for pid in property_ids if pid in id_to_property]
                return sorted_properties
            return []
            
        except Exception as e:
            logger.error(f"Error fetching properties from Supabase: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    async def get_properties_by_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get properties from Supabase using filters"""
        try:
            logger.info(f"Searching properties with filters: {filters}")
            query = self.client.table('properties').select('*')
            
            # Apply filters based on actual column names
            if filters.get('city'):
                logger.info(f"Filtering by city: {filters['city']}")
                query = query.ilike('city', f"%{filters['city']}%")
            if filters.get('state'):
                logger.info(f"Filtering by state: {filters['state']}")
                query = query.ilike('state', f"%{filters['state']}%")
            if filters.get('property_type'):
                logger.info(f"Filtering by property_type: {filters['property_type']}")
                # Try both type and property_type fields with OR condition
                query = query.or_(f"type.eq.{filters['property_type']},property_type.eq.{filters['property_type']}")
            if filters.get('listing_type'):
                logger.info(f"Filtering by listing_type: {filters['listing_type']}")
                query = query.eq('listing_type', filters['listing_type'])
            if filters.get('bedrooms'):
                logger.info(f"Filtering by bedrooms: {filters['bedrooms']}")
                # Try both bedrooms and num_bedrooms fields with OR condition
                query = query.or_(f"bedrooms.eq.{filters['bedrooms']},num_bedrooms.eq.{filters['bedrooms']}")
                
            # Execute query
            response = query.execute()
            logger.info(f"Found {len(response.data)} properties")
            
            if response.data:
                logger.info(f"First property: {response.data[0]}")
                return response.data
            return []
            
        except Exception as e:
            logger.error(f"Error fetching properties from Supabase: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    async def get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get a single property by ID"""
        try:
            response = self.client.table('properties').select('*').eq('id', property_id).single().execute()
            return response.data if response.data else None
            
        except Exception as e:
            logger.error(f"Error fetching property from Supabase: {str(e)}")
            logger.error(traceback.format_exc())
            return None

supabase_service = SupabaseService()
