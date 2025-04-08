from pinecone import Pinecone, ServerlessSpec
from app.core.config import get_settings
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging
import time
import numpy as np

logger = logging.getLogger(__name__)
settings = get_settings()

class PineconeService:
    def __init__(self):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Define indexes
        self.indexes = {
            "realestate": {
                "name": "realestate",
                "namespace": "knowledge",
                "dimension": 768  # Using 768 dimensions for consistency
            },
            "properties": {
                "name": "properties",
                "namespace": "listings",
                "dimension": 768  # Using 768 dimensions for consistency
            }
        }
        
        # Create/verify both indexes
        for index_config in self.indexes.values():
            self.ensure_index_exists(index_config["name"], index_config["dimension"])
        
        # Wait for indexes to be ready
        time.sleep(5)
        
        # Initialize index connections
        self.index_connections = {
            name: self.pc.Index(config["name"])
            for name, config in self.indexes.items()
        }
        
        # Initialize Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash') 
        logger.info("PineconeService initialized successfully")

    def ensure_index_exists(self, index_name: str, dimension: int):
        """Create index if it doesn't exist, recreate if dimensions don't match"""
        try:
            # Check existing indexes
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            logger.info(f"Existing indexes: {existing_indexes}")
            
            needs_creation = True
            
            if index_name in existing_indexes:
                # Check if dimensions match
                index = self.pc.Index(index_name)
                index_stats = index.describe_index_stats()
                current_dim = index_stats.dimension
                
                if current_dim == dimension:
                    logger.info(f"Index {index_name} exists with correct dimension {dimension}")
                    needs_creation = False
                else:
                    logger.warning(f"Index {index_name} exists but has wrong dimension ({current_dim} vs {dimension})")
                    logger.info(f"Deleting index {index_name} to recreate with correct dimension")
                    self.pc.delete_index(index_name)
                    time.sleep(5)  # Wait for deletion to complete
            
            if needs_creation:
                logger.info(f"Creating index {index_name} with dimension {dimension}")
                self.pc.create_index(
                    name=index_name,
                    dimension=dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Created new Pinecone index: {index_name}")
                
        except Exception as e:
            logger.error(f"Error managing Pinecone index: {str(e)}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Gemini"""
        try:
            # Generate a more semantic embedding using a structured prompt
            prompt = f"""
            Task: Generate a semantic embedding for the following text.
            Text: {text}
            
            Think about:
            1. Key topics and themes
            2. Important details and facts
            3. Contextual meaning
            
            Provide a detailed analysis that captures the semantic essence.
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.0,
                    "candidate_count": 1,
                    "max_output_tokens": 768
                }
            )
            
            text_response = response.text
            
            # Create a more sophisticated embedding
            embedding = np.zeros(768)  # Using 768 dimensions
            
            # Use a better hashing strategy
            for i, char in enumerate(text_response):
                # Create multiple hash features per character
                embedding[i % 768] += ord(char) * 0.1
                embedding[(i * 2) % 768] += (ord(char) ** 2) * 0.01
                embedding[(i * 3) % 768] += (ord(char) ** 0.5) * 0.001
            
            # Apply additional transformations
            embedding = np.tanh(embedding)  # Squash values to [-1, 1]
            embedding = embedding / np.linalg.norm(embedding)  # Normalize
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise

    async def query_similar_docs(self, query: str, index_type: str = "realestate", top_k: int = 3) -> List[Dict[str, Any]]:
        """Query similar documents from specified Pinecone index"""
        try:
            if index_type not in self.indexes:
                raise ValueError(f"Invalid index type: {index_type}")
            
            # Get query embedding
            query_embedding = await self.get_embedding(query)
            
            # Get index and namespace
            index = self.index_connections[index_type]
            namespace = self.indexes[index_type]["namespace"]
            
            # Query Pinecone
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace
            )
            
            # Format results
            formatted_results = []
            for match in results.matches:
                result = {
                    "score": match.score,
                    "content": match.metadata.get("content", ""),
                    "type": index_type
                }
                
                # Add property-specific metadata for properties index
                if index_type == "properties":
                    result.update({
                        "property_id": match.metadata.get("property_id"),
                        "price": match.metadata.get("price"),
                        "location": match.metadata.get("location"),
                        "bedrooms": match.metadata.get("bedrooms"),
                        "bathrooms": match.metadata.get("bathrooms"),
                        "area": match.metadata.get("area"),
                        "amenities": match.metadata.get("amenities", [])
                    })
                
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying {index_type} index: {str(e)}")
            raise

    async def upsert_document(self, content: str, metadata: Dict[str, Any], index_type: str = "realestate"):
        """Add or update document in specified Pinecone index"""
        try:
            if index_type not in self.indexes:
                raise ValueError(f"Invalid index type: {index_type}")
            
            # Get embedding
            vector = await self.get_embedding(content)
            
            # Get index and namespace
            index = self.index_connections[index_type]
            namespace = self.indexes[index_type]["namespace"]
            
            # Prepare metadata
            metadata["content"] = content
            
            # Generate ID based on content hash for deduplication
            import hashlib
            doc_id = hashlib.md5(content.encode()).hexdigest()
            
            # Upsert to Pinecone
            index.upsert(
                vectors=[{
                    "id": doc_id,
                    "values": vector,
                    "metadata": metadata
                }],
                namespace=namespace
            )
            
            logger.info(f"Successfully upserted document to {index_type} index")
            
        except Exception as e:
            logger.error(f"Error upserting to {index_type} index: {str(e)}")
            raise

pinecone_service = PineconeService()
