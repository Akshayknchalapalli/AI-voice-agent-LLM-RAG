from pinecone import Pinecone
from app.core.config import get_settings
from openai import OpenAI
from typing import List, Dict, Optional
import asyncio
import json

settings = get_settings()

class PropertyVectorStore:
    def __init__(self):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = "properties"  # Use existing index
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Connect to existing index
        self.index = self.pc.Index(self.index_name)

    async def add_property(self, property_id: str, text: str, metadata: Dict):
        """Add a property to the vector store"""
        try:
            # Generate embedding
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                input=text,
                model="text-embedding-ada-002"  # Using older model with higher rate limits
            )
            vector = response.data[0].embedding
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[(str(property_id), vector, metadata)]
            )
            return True
        except Exception as e:
            print(f"Error adding property to vector store: {e}")
            return False

    async def search_properties(
        self,
        query: str,
        filter_dict: Optional[Dict] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """Search for properties using semantic similarity"""
        try:
            # Generate query embedding
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                input=query,
                model="text-embedding-ada-002"
            )
            query_vector = response.data[0].embedding
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_vector,
                filter=filter_dict,
                top_k=top_k,
                include_metadata=True
            )
            
            return results.matches
        except Exception as e:
            print(f"Error searching properties: {e}")
            return []

vector_store = PropertyVectorStore()
