from typing import List, Dict, Optional
from app.services.property.property_service import PropertyService
from app.services.vector_store.pinecone_service import pinecone_service

class RecommendationEngine:
    def __init__(self, auth_token: str):
        self.property_service = PropertyService(auth_token)

    async def get_personalized_recommendations(
        self,
        user_preferences: Optional[Dict] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get personalized property recommendations based on user preferences"""
        try:
            # If no preferences, return latest properties
            if not user_preferences:
                return await self.property_service.get_properties(limit=limit)
            
            # Build search filters based on preferences
            filters = {}
            if "min_price" in user_preferences:
                filters["min_price"] = user_preferences["min_price"]
            if "max_price" in user_preferences:
                filters["max_price"] = user_preferences["max_price"]
            if "min_bedrooms" in user_preferences:
                filters["bedrooms"] = user_preferences["min_bedrooms"]
            if "min_bathrooms" in user_preferences:
                filters["bathrooms"] = user_preferences["min_bathrooms"]
            if "property_types" in user_preferences:
                filters["property_type"] = user_preferences["property_types"][0] if user_preferences["property_types"] else None
            
            # Get properties matching filters
            properties = await self.property_service.search_properties(
                filters=filters,
                limit=limit
            )
            
            return properties
            
        except Exception as e:
            raise Exception(f"Failed to get personalized recommendations: {str(e)}")

    async def find_similar_properties(
        self,
        property_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """Find properties similar to a given property"""
        try:
            # Get the source property
            source_property = await self.property_service.get_property(property_id)
            if not source_property:
                raise Exception("Property not found")
            
            # Use vector search to find similar properties
            similar_properties = await self.property_service.search_properties(
                query=f"property:{property_id}",
                limit=limit
            )
            
            return similar_properties
            
        except Exception as e:
            raise Exception(f"Failed to find similar properties: {str(e)}")
