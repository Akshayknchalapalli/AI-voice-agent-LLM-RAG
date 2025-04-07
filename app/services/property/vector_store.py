import pinecone
from app.core.config import get_settings
from langchain.embeddings import OpenAIEmbeddings
from typing import List, Dict, Optional
import asyncio
import json

settings = get_settings()

class PropertyVectorStore:
    def __init__(self):
        # Initialize Pinecone
        pinecone.init(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        self.index_name = "properties"
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        
        # Create index if it doesn't exist
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.index_name,
                dimension=1536,  # OpenAI embedding dimension
                metric="cosine"
            )
        
        self.index = pinecone.Index(self.index_name)

    async def add_property(self, property_id: int, text: str, metadata: Dict):
        """Add a property to the vector store"""
        try:
            # Generate embedding
            vector = await asyncio.to_thread(
                self.embeddings.embed_query,
                text
            )
            
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
        top_k: int = 5
    ) -> List[Dict]:
        """Search for similar properties"""
        try:
            # Generate query embedding
            query_vector = await asyncio.to_thread(
                self.embeddings.embed_query,
                query
            )
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_vector,
                filter=filter_dict,
                top_k=top_k,
                include_metadata=True
            )
            
            return [
                {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                }
                for match in results.matches
            ]
        except Exception as e:
            print(f"Error searching properties: {e}")
            return []

    def delete_property(self, property_id: int):
        """Delete a property from the vector store"""
        try:
            self.index.delete(ids=[str(property_id)])
            return True
        except Exception as e:
            print(f"Error deleting property: {e}")
            return False

vector_store = PropertyVectorStore()
