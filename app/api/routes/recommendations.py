from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List, Dict, Optional
from app.services.property.recommendation_engine import RecommendationEngine
from app.services.property.property_service import PropertyService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/personalized")
async def get_personalized_recommendations(
    limit: int = 10,
    authorization: str = Header(None)
) -> Dict:
    """Get personalized property recommendations for the user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Extract the token from the Authorization header
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        
        # Initialize services with auth token
        property_service = PropertyService(token)
        recommendations = await property_service.get_properties(limit=limit)
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar/{property_id}")
async def get_similar_properties(
    property_id: str,
    limit: int = 5,
    authorization: str = Header(None)
) -> Dict:
    """Get similar properties to a given property"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Extract the token from the Authorization header
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        
        property_service = PropertyService(token)
        similar_properties = await property_service.search_properties(
            query=f"property_id:{property_id}",
            limit=limit
        )
        return {"similar_properties": similar_properties}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
