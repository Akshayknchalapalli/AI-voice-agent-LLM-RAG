import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app.core.supabase import get_supabase_client
from app.services.vector_store.pinecone_service import PineconeService
from app.core.config import get_settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_properties_to_pinecone():
    """Load properties from Supabase into Pinecone vector store"""
    try:
        # Initialize services
        settings = get_settings()
        supabase = get_supabase_client()
        pinecone_service = PineconeService()
        
        logger.info("Fetching properties from Supabase...")
        
        # Fetch all properties from Supabase
        response = supabase.table('properties').select('*').execute()
        properties = response.data
        
        logger.info(f"Found {len(properties)} properties in Supabase")
        
        # Process each property
        for property in properties:
            try:
                # Create a rich description for the property
                description = f"""
                Property ID: {property['id']}
                Title: {property['title']}
                Price: ${property.get('price', 'N/A')}
                Location: {property.get('city', '')}, {property.get('state', '')}
                Address: {property.get('address', 'N/A')}
                Type: {property.get('property_type', 'N/A')}
                Bedrooms: {property.get('bedrooms', 'N/A')}
                Bathrooms: {property.get('bathrooms', 'N/A')}
                Square Feet: {property.get('square_feet', 'N/A')}
                Features: {', '.join(property.get('features', []))}
                Description: {property.get('description', '')}
                """
                
                # Create metadata for the property
                metadata = {
                    'id': property['id'],
                    'title': property['title'],
                    'price': property.get('price'),
                    'city': property.get('city'),
                    'state': property.get('state'),
                    'property_type': property.get('property_type'),
                    'bedrooms': property.get('bedrooms'),
                    'bathrooms': property.get('bathrooms'),
                    'square_feet': property.get('square_feet'),
                }
                
                # Upsert the property into Pinecone
                await pinecone_service.upsert_document(
                    content=description,
                    metadata=metadata,
                    index_type="properties"
                )
                logger.info(f"Added property {property['id']} to Pinecone")
                
            except Exception as e:
                logger.error(f"Error processing property {property.get('id')}: {str(e)}")
                continue
        
        logger.info("Finished loading properties into Pinecone")
        
    except Exception as e:
        logger.error(f"Error in load_properties_to_pinecone: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(load_properties_to_pinecone())
