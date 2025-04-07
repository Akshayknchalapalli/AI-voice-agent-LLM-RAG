from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.callbacks import AsyncCallbackManager
from app.services.llm.prompts import (
    REAL_ESTATE_AGENT_PROMPT,
    PROPERTY_FILTER_PROMPT,
    CONVERSATION_SUMMARY_PROMPT
)
from app.core.config import get_settings
from typing import Dict, List, Optional
import json
import asyncio

settings = get_settings()

class ConversationManager:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0.7,
            model_name="gpt-4",
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.memory = ConversationBufferMemory()
        self.conversation_chain = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=REAL_ESTATE_AGENT_PROMPT,
            verbose=True
        )
        
    async def process_user_input(
        self,
        user_input: str,
        property_context: Optional[Dict] = None
    ) -> Dict:
        """Process user input and generate appropriate response"""
        try:
            # Extract property requirements if present
            requirements = await self._extract_property_requirements(user_input)
            
            # Get response from LLM
            response = await self.conversation_chain.apredict(
                conversation_history=self.memory.buffer,
                current_query=user_input,
                property_context=property_context or {}
            )
            
            return {
                "response": response,
                "extracted_requirements": requirements
            }
        except Exception as e:
            return {
                "error": f"Failed to process input: {str(e)}",
                "response": "I apologize, but I'm having trouble processing your request. Could you please rephrase it?"
            }

    async def _extract_property_requirements(self, user_input: str) -> Optional[Dict]:
        """Extract structured property requirements from user input"""
        try:
            result = await self.llm.apredict(
                PROPERTY_FILTER_PROMPT.format(user_requirements=user_input)
            )
            return json.loads(result)
        except:
            return None

    async def get_conversation_summary(self) -> str:
        """Generate a summary of the current conversation"""
        try:
            summary = await self.llm.apredict(
                CONVERSATION_SUMMARY_PROMPT.format(
                    conversation=self.memory.buffer
                )
            )
            return summary
        except Exception as e:
            return f"Failed to generate summary: {str(e)}"

    def clear_conversation(self):
        """Clear the conversation history"""
        self.memory.clear()

class ConversationPool:
    def __init__(self):
        self.conversations: Dict[str, ConversationManager] = {}
        
    def get_conversation(self, session_id: str) -> ConversationManager:
        """Get or create a conversation manager for a session"""
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationManager()
        return self.conversations[session_id]
    
    def end_conversation(self, session_id: str):
        """End and cleanup a conversation session"""
        if session_id in self.conversations:
            del self.conversations[session_id]

# Global conversation pool
conversation_pool = ConversationPool()
