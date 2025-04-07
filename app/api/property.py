from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.property.property_service import PropertyService
from app.core.database import get_db
from typing import List, Dict, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/properties", tags=["properties"])

class PropertyCreate(BaseModel):
    title: str
    description: str
    property_type: str
    listing_type: str
    address: str
    city: str
    state: str
    zip_code: str
    price: int
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    features: List[str] = []
    images: List[str] = []
    virtual_tour_url: Optional[str] = None

@router.post("/")
async def create_property(
    property_data: PropertyCreate,
    db: Session = Depends(get_db)
):
    """Create a new property listing"""
    service = PropertyService(db)
    try:
        property_obj = await service.create_property(property_data.dict())
        return property_obj
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search")
async def search_properties(
    query: str = "",
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None,
    property_type: Optional[str] = None,
    listing_type: Optional[str] = None,
    use_semantic: bool = True,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Search for properties"""
    service = PropertyService(db)
    
    # Build filters
    filters = {}
    if min_price is not None and max_price is not None:
        filters["price_range"] = [min_price, max_price]
    if bedrooms is not None:
        filters["bedrooms"] = bedrooms
    if bathrooms is not None:
        filters["bathrooms"] = bathrooms
    if property_type:
        filters["property_type"] = property_type
    if listing_type:
        filters["listing_type"] = listing_type
    
    try:
        results = await service.search_properties(
            query=query,
            filters=filters,
            use_semantic=use_semantic,
            limit=limit
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{property_id}")
def get_property(
    property_id: int,
    db: Session = Depends(get_db)
):
    """Get a property by ID"""
    service = PropertyService(db)
    try:
        property_obj = service.get_property(property_id)
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        return property_obj
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{property_id}")
async def update_property(
    property_id: int,
    property_data: PropertyCreate,
    db: Session = Depends(get_db)
):
    """Update a property listing"""
    service = PropertyService(db)
    try:
        property_obj = await service.update_property(
            property_id,
            property_data.dict()
        )
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        return property_obj
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{property_id}")
async def delete_property(
    property_id: int,
    db: Session = Depends(get_db)
):
    """Delete a property listing"""
    service = PropertyService(db)
    try:
        success = await service.delete_property(property_id)
        if not success:
            raise HTTPException(status_code=404, detail="Property not found")
        return {"status": "success", "message": "Property deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
