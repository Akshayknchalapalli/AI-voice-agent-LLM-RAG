from typing import List, Dict, Optional
from app.core.supabase import get_supabase_client
from app.services.vector_store.pinecone_service import pinecone_service

class PropertyService:
    def __init__(self, auth_token: str):
        self.supabase = get_supabase_client(auth_token)

    async def create_property(self, property_data: Dict) -> Dict:
        """Create a new property listing"""
        try:
            # Create property in database
            response = self.supabase.table('properties').insert([property_data]).execute()
            property_id = response.data[0]['id']
            
            # Add to vector store
            await pinecone_service.upsert_vectors(
                index_name="properties",
                namespace="listings",
                vectors=[{
                    "id": str(property_id),
                    "text": property_data['to_embedding_text'](),
                    "metadata": property_data
                }]
            )
            
            return self.supabase.table('properties').select('*').eq('id', property_id).single().execute().data
        except Exception as e:
            raise Exception(f"Failed to create property: {str(e)}")

    async def get_properties(self, limit: int = 10) -> List[Dict]:
        """Get a list of properties"""
        try:
            response = self.supabase.table('properties')\
                .select('*')\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to fetch properties: {str(e)}")

    async def search_properties(
        self,
        query: str = "",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        property_type: Optional[str] = None,
        listing_type: Optional[str] = None,
        use_semantic: bool = True,
        limit: int = 10
    ) -> List[Dict]:
        """Search for properties with filters"""
        try:
            # Start with base query
            query_builder = self.supabase.table('properties').select('*')
            
            # Apply filters
            if min_price is not None:
                query_builder = query_builder.gte('price', min_price)
            if max_price is not None:
                query_builder = query_builder.lte('price', max_price)
            if bedrooms is not None:
                query_builder = query_builder.eq('bedrooms', bedrooms)
            if bathrooms is not None:
                query_builder = query_builder.eq('bathrooms', bathrooms)
            if property_type:
                query_builder = query_builder.eq('property_type', property_type)
            if listing_type:
                query_builder = query_builder.eq('listing_type', listing_type)
            
            # If semantic search is enabled and we have a query
            if use_semantic and query:
                # Get vector search results
                vector_results = await pinecone_service.query_vectors(
                    index_name="properties",
                    namespace="listings",
                    query=query,
                    top_k=limit
                )
                
                # Get IDs from vector search
                property_ids = [result['id'] for result in vector_results]
                query_builder = query_builder.in_('id', property_ids)
            
            # Execute query with limit
            response = query_builder.limit(limit).execute()
            return response.data
            
        except Exception as e:
            raise Exception(f"Failed to search properties: {str(e)}")

    async def get_property(self, property_id: str) -> Dict:
        """Get a property by ID"""
        try:
            response = self.supabase.table('properties')\
                .select('*')\
                .eq('id', property_id)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            raise Exception(f"Failed to get property: {str(e)}")

    async def update_property(self, property_id: str, property_data: Dict) -> Dict:
        """Update a property listing"""
        try:
            # Update database
            response = self.supabase.table('properties').update([property_data]).eq('id', property_id).execute()
            
            # Update vector store
            await pinecone_service.upsert_vectors(
                index_name="properties",
                namespace="listings",
                vectors=[{
                    "id": str(property_id),
                    "text": property_data['to_embedding_text'](),
                    "metadata": property_data
                }]
            )
            
            return self.supabase.table('properties').select('*').eq('id', property_id).single().execute().data
        except Exception as e:
            raise Exception(f"Failed to update property: {str(e)}")

    async def delete_property(self, property_id: str) -> bool:
        """Delete a property listing"""
        try:
            # Delete from database
            response = self.supabase.table('properties').delete().eq('id', property_id).execute()
            
            # Delete from vector store
            await pinecone_service.delete_vectors(
                index_name="properties",
                namespace="listings",
                ids=[str(property_id)]
            )
            
            return response.status_code == 200
        except Exception as e:
            raise Exception(f"Failed to delete property: {str(e)}")
