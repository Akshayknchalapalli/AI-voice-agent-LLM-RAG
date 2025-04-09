from typing import List, Dict, Any, Optional, Tuple
import logging
from app.services.vector_store.pinecone_service import pinecone_service
from app.services.db.supabase_service import supabase_service
import google.generativeai as genai
from google.generativeai.types import content_types
from dataclasses import dataclass
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class ChatResponse:
    text: str
    properties: List[Dict[str, Any]]

class ConversationManager:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')  # Changed to gemini-pro as it's better for chat
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        # Store last filtered properties for each user
        self.last_properties: Dict[str, List[Dict[str, Any]]] = {}
        
    def _get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a user"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]
        
    def _add_to_history(self, user_id: str, role: str, content: str):
        """Add a message to the conversation history"""
        history = self._get_conversation_history(user_id)
        history.append({"role": role, "content": content})
        
    async def _search_properties(self, filters: Dict[str, Any], user_id: str, is_followup: bool = False) -> List[Dict[str, Any]]:
        """Search for properties using filters"""
        try:
            logger.info(f"Searching properties with filters: {filters}")
            
            # If this is a follow-up query and we have previous results
            if is_followup and user_id in self.last_properties:
                logger.info(f"Filtering from previous results with filters: {filters}")
                previous_properties = self.last_properties[user_id]
                logger.info(f"Previous properties count: {len(previous_properties)}")
                filtered_properties = []
                
                for prop in previous_properties:
                    matches = True
                    for key, value in filters.items():
                        if key == 'property_type':
                            prop_type = str(prop.get('type', '') or prop.get('property_type', '')).lower()
                            filter_type = value.lower()
                            logger.info(f"Comparing property type: {prop_type} with filter: {filter_type}")
                            if not prop_type or prop_type != filter_type:
                                matches = False
                                break
                        elif key in prop and prop[key] != value:
                            matches = False
                            break
                    if matches:
                        filtered_properties.append(prop)
                
                logger.info(f"Filtered properties count: {len(filtered_properties)}")
                if filtered_properties:
                    # Update last properties with filtered results
                    self.last_properties[user_id] = filtered_properties
                return filtered_properties
            
            # First try to get properties directly from Supabase using filters
            properties = await supabase_service.get_properties_by_filters(filters)
            logger.info(f"Direct database search results: {len(properties) if properties else 0} properties")
            
            if properties:
                # Store results for potential follow-up queries
                self.last_properties[user_id] = properties[:6]
                return properties[:6]  # Return top 6 matches
                
            # If no direct matches, try semantic search with Pinecone
            logger.info("No direct matches, trying semantic search")
            query_text = " ".join([f"{k}: {v}" for k, v in filters.items()])
            query_embedding = await pinecone_service.get_embedding(query_text)
            similar_docs = await pinecone_service.search_similar(query_embedding, top_k=6)
            
            if similar_docs:
                logger.info(f"Found {len(similar_docs)} similar properties via semantic search")
                # Get full property details from Supabase
                property_ids = [doc['id'] for doc in similar_docs]
                properties = await supabase_service.get_properties_by_ids(property_ids)
                return properties
            
            logger.info("No properties found in semantic search")    
            return []
            
        except Exception as e:
            logger.error(f"Error searching properties: {str(e)}")
            return []
        
    def _extract_property_filters(self, query: str) -> Tuple[Dict[str, Any], bool]:
        """Extract property filters from user query and determine if it's a follow-up query"""
        # Check if this is a follow-up filter request
        is_followup = any(phrase in query.lower() for phrase in [
            'from these', 'from those', 'filter these', 'filter those',
            'in these', 'in those', 'of these', 'of those', 'now', 'instead',
            'show me', 'i want', 'give me'
        ])
        """Extract property filters from user query"""
        logger.info(f"Extracting filters from query: {query}")
        filters = {
            "location": None,
            "property_type": None,
            "bedrooms": None,
            "category": None,
            "state": None,
            "city": None,
            "listing_type": None
        }
        
        # Extract location (handle variations)
        query_lower = query.lower()
        logger.info(f"Processing query: {query_lower}")
        
        # Location mapping with pronunciation and spelling variations
        location_variants = {
            "bangalore": ["bangalore", "bengaluru", "benguluru", "blr", "banglore", "bangalor"],
            "andhra pradesh": ["andhra pradesh", "andhra", "ap", "andra pradesh", "andra", "andrapradesh"],
            "telangana": ["telangana", "hyderabad", "hyd", "telengana", "telangana", "telungana"],
            "tamil nadu": ["tamil nadu", "chennai", "tamilnadu", "tamil nad", "tamilnad"],
            "kerala": ["kerala", "kochi", "cochin", "trivandrum", "kerela", "karala"],
            "maharashtra": ["maharashtra", "mumbai", "pune", "maharastra", "maharashtra"],
            "dewas": ["dewas", "davos", "divas", "devos", "dewos", "dewaz"],  # Added pronunciation variations
            "orai": ["orai", "oorai", "horai", "orei", "orrai"],  # Added pronunciation variations
            "himachal pradesh": ["himachal pradesh", "himachal", "hp", "himanchal", "himachal pradesh", "himachalpradesh"]
        }

        # Try fuzzy matching for locations
        def get_closest_match(word: str, variants: List[str]) -> Optional[str]:
            # Simple fuzzy matching using character similarity
            word = word.lower()
            max_similarity = 0
            best_match = None
            
            for variant in variants:
                # Calculate character-level similarity
                variant = variant.lower()
                shorter, longer = (word, variant) if len(word) < len(variant) else (variant, word)
                similarity = sum(1 for i in range(len(shorter)) if i < len(longer) and shorter[i] == longer[i])
                similarity = similarity / max(len(word), len(variant))  # Normalize
                
                if similarity > max_similarity and similarity > 0.7:  # 70% similarity threshold
                    max_similarity = similarity
                    best_match = variant
            
            return best_match
        
        # Extract state and city with fuzzy matching
        words = query_lower.split()
        for location, variants in location_variants.items():
            # Check exact matches first
            if any(variant in query_lower for variant in variants):
                if location.lower() in ["andhra pradesh", "telangana", "tamil nadu", "kerala", "maharashtra", "himachal pradesh"]:
                    filters["state"] = location.title()
                else:
                    filters["city"] = location.title()
                break
            
            # If no exact match, try fuzzy matching on individual words
            for word in words:
                if closest_match := get_closest_match(word, variants):
                    logger.info(f"Fuzzy matched '{word}' to '{location}' via variant '{closest_match}'")
                    if location.lower() in ["andhra pradesh", "telangana", "tamil nadu", "kerala", "maharashtra", "himachal pradesh"]:
                        filters["state"] = location.title()
                    else:
                        filters["city"] = location.title()
                    break
        
        # Extract listing type (rent/sale)
        listing_types = {
            "rent": ["rent", "rental", "renting", "lease", "leasing"],
            "sale": ["sale", "buy", "buying", "purchase", "purchasing", "sell", "selling"]
        }
        
        for ltype, variants in listing_types.items():
            if any(variant in query_lower for variant in variants):
                filters["listing_type"] = ltype
                break

        # Extract property type
        property_types = {
            "agricultural": ["agricultural", "farm", "farming"],
            "commercial": ["commercial", "office", "retail", "shop"],
            "residential": ["residential", "house", "home"]
        }
        
        for ptype, variants in property_types.items():
            if any(variant in query_lower for variant in variants):
                filters["property_type"] = ptype
                break
            
        # Extract bedrooms
        bedroom_patterns = {
            "1": ["1bhk", "1 bhk", "one bhk", "1 bedroom"],
            "2": ["2bhk", "2 bhk", "two bhk", "2 bedroom"],
            "3": ["3bhk", "3 bhk", "three bhk", "3 bedroom"],
            "4": ["4bhk", "4 bhk", "four bhk", "4 bedroom"],
            "5": ["5bhk", "5 bhk", "five bhk", "5 bedroom"]
        }
        
        for beds, patterns in bedroom_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                filters["bedrooms"] = int(beds)
                break
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        logger.info(f"Extracted filters: {filters}")
        return filters, is_followup
        
    def _format_property_response(self, properties: List[Dict[str, Any]], filters: Dict[str, Any]) -> str:
        """Format properties into a readable response"""
        if not properties:
            response = "I couldn't find any properties exactly matching your criteria. "
            if filters:
                response += "You were looking for: \n"
                if filters.get('location'):
                    response += f"Location: {filters['location']}\n"
                if filters.get('property_type'):
                    response += f"Type: {filters['property_type']}\n"
                if filters.get('bedrooms'):
                    response += f"{filters['bedrooms']} BHK\n"
                if filters.get('category'):
                    response += f"Category: {filters['category']}\n"
                response += "\nWould you like to try with different criteria?"
            return response
            
        response = f"I found {len(properties)} properties matching your criteria:\n\n"
        for i, prop in enumerate(properties, 1):
            response += f"Property {i}:\n"
            response += f"Title: {prop['title']}\n"
            response += f"Location: {prop.get('city', 'N/A')}, {prop.get('state', 'N/A')}\n"
            response += f"Type: {prop.get('property_type', 'N/A')}\n"
            response += f"Price: ₹{prop.get('price', 0):,}\n"
            if prop.get('bedrooms'):
                response += f"Bedrooms: {prop['bedrooms']}\n"
            if prop.get('bathrooms'):
                response += f"Bathrooms: {prop['bathrooms']}\n"
            response += f"Area: {prop.get('square_feet', 0)} sq ft\n"
            if prop.get('description'):
                response += f"Description: {prop['description']}\n"
            response += "\n"
        
        response += "Would you like more details about any of these properties?"
        return response
        
    async def process_query(self, user_id: str, query: str) -> ChatResponse:
        """Process a user query and return response with properties if applicable"""
        logger.info(f"[User {user_id}] Processing query: {query}")
        history = self._get_conversation_history(user_id)
        self._add_to_history(user_id, "user", query)
        
        try:
            # Extract property filters if query is about properties
            filters, is_followup = self._extract_property_filters(query)
            logger.info(f"[User {user_id}] Extracted filters: {filters}, is_followup: {is_followup}")
            properties = []
            
            # Create initial context for Janaki
            context = (
                "You are Janaki, an AI voice assistant specializing in real estate. "
                "Keep responses concise and natural. Avoid using markdown or special characters. "
                "When mentioning prices, format them in a readable way (e.g., '2 crore' instead of '20000000'). "
                "You can help users find both rental and sale properties. "
                "For commercial properties, focus on location, type, and area. Don't ask about bedrooms or residential features. "
                "For residential properties, you can ask about bedrooms and other residential features. "
                "For general questions, provide helpful answers while staying professional and friendly. "
                "IMPORTANT: Never say you can't filter by rental or sale - you have this capability. "
                "IMPORTANT: If properties are found, always describe them based on the actual filtered results. "
            )
            
            # If query is about properties, search in Pinecone and Supabase
            if filters:
                logger.info(f"[User {user_id}] Searching properties with filters: {filters}")
                properties = await self._search_properties(filters, user_id, is_followup)
                logger.info(f"[User {user_id}] Found {len(properties)} matching properties")
                
                # Add filter information to context
                filter_context = "Current filters: "
                if filters.get('state'): filter_context += f"State: {filters['state']}, "
                if filters.get('listing_type'): filter_context += f"Listing Type: {filters['listing_type']}, "
                if filters.get('property_type'): filter_context += f"Property Type: {filters['property_type']}, "
                if filters.get('bedrooms'): filter_context += f"Bedrooms: {filters['bedrooms']}, "
                context += f"\n{filter_context.rstrip(', ')}"
                
                if properties:
                    logger.info(f"[User {user_id}] Property IDs found: {[p.get('id') for p in properties]}")
                    property_response = self._format_property_response(properties, filters)
                    context += f"\nAvailable properties: {property_response}"
                else:
                    logger.info(f"[User {user_id}] No properties found matching filters")
                    context += "\nNo properties found matching those criteria."
            
            # Format the prompt with context and recent history
            prompt = context + "\n\n"
            for msg in history[-5:]:  # Keep last 5 messages for context
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt += f"{role}: {msg['content']}\n"
            prompt += (
                f"\nUser: {query}\n"
                "Assistant: Remember to respond naturally without using markdown or special characters. "
                "Format the response in a way that's easy to read and speak:"
            )
            
            # If we found properties, use the formatted property response directly
            if filters and properties:
                response_text = self._format_property_response(properties, filters)
            else:
                # Generate response using Gemini only for non-property queries or when no properties found
                response = self.model.generate_content(prompt)
                response_text = response.text
            
            # Return both the response text and the properties
            logger.info(f"[User {user_id}] Returning response with {len(properties)} properties")
            return ChatResponse(text=response_text, properties=properties)
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            logger.error(traceback.format_exc())
            return ChatResponse(
                text="I apologize, but I encountered an error while processing your request. Could you please try again?",
                properties=[]
            )

conversation_manager = ConversationManager()
