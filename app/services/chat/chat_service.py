from typing import List, Dict, Any
import logging
from app.services.vector_store.pinecone_service import pinecone_service
import google.generativeai as genai
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ChatService:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
    async def get_response(self, user_query: str) -> str:
        """Get AI response for user query using RAG with Pinecone"""
        try:
            # Search for relevant properties in Pinecone
            similar_properties = await pinecone_service.query_similar_docs(
                query=user_query,
                index_type="properties",
                top_k=3
            )
            
            # Format property information for context
            property_context = ""
            if similar_properties:
                property_context = "Here are some relevant properties:\n\n"
                for idx, prop in enumerate(similar_properties, 1):
                    metadata = prop.get('metadata', {})
                    property_context += f"""
                    Property {idx}:
                    - Title: {metadata.get('title', 'N/A')}
                    - Price: ${metadata.get('price', 'N/A')}
                    - Location: {metadata.get('city', '')}, {metadata.get('state', '')}
                    - Bedrooms: {metadata.get('bedrooms', 'N/A')}
                    - Bathrooms: {metadata.get('bathrooms', 'N/A')}
                    - Square Feet: {metadata.get('square_feet', 'N/A')}
                    - Type: {metadata.get('property_type', 'N/A')}
                    """
            
            # Create a prompt that includes property context
            prompt = f"""
            You are an AI real estate assistant. Use the following property information to answer the user's question.
            If the question is not about properties, provide a helpful response based on your general knowledge.
            
            Property Information:
            {property_context if property_context else "No specific properties found for this query."}
            
            User Question: {user_query}
            
            Please provide a natural, conversational response that directly addresses the user's question.
            If discussing properties, mention specific details from the provided information.
            """
            
            # Get response from Gemini
            response = await self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request at the moment. Could you please try again?"

chat_service = ChatService()
