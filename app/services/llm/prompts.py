from langchain.prompts import PromptTemplate

REAL_ESTATE_AGENT_PROMPT = PromptTemplate(
    input_variables=["conversation_history", "current_query", "property_context"],
    template="""You are an AI-powered real estate agent assistant. Be professional, friendly, and helpful.
Use the property context provided to answer questions accurately. If you don't know something, say so politely.

Conversation History:
{conversation_history}

Property Context:
{property_context}

Current Query: {current_query}

Assistant Response:"""
)

PROPERTY_FILTER_PROMPT = PromptTemplate(
    input_variables=["user_requirements"],
    template="""Extract key property requirements from the user's query.
Return a JSON object with the following fields (if mentioned):
- price_range: [min, max]
- bedrooms: number or range
- bathrooms: number or range
- location: area or neighborhood
- property_type: (house, apartment, condo, etc.)
- special_features: [list of features]

User Requirements: {user_requirements}

JSON Output:"""
)

CONVERSATION_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["conversation"],
    template="""Summarize the key points from this real estate conversation.
Focus on:
1. Property requirements mentioned
2. Areas of interest
3. Budget constraints
4. Timeline for purchase/rent
5. Any specific concerns raised

Conversation:
{conversation}

Summary:"""
)
