from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.property import Property, PropertyType, ListingType
from app.services.property.vector_store import vector_store
from typing import List, Dict, Optional
import json

class PropertyService:
    def __init__(self, db: Session):
        self.db = db

    async def create_property(self, property_data: Dict) -> Property:
        """Create a new property listing"""
        try:
            # Create property in database
            property_obj = Property(**property_data)
            self.db.add(property_obj)
            self.db.commit()
            self.db.refresh(property_obj)
            
            # Add to vector store
            await vector_store.add_property(
                property_id=property_obj.id,
                text=property_obj.to_embedding_text(),
                metadata=property_obj.to_dict()
            )
            
            return property_obj
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create property: {str(e)}")

    async def search_properties(
        self,
        query: str = "",
        filters: Optional[Dict] = None,
        use_semantic: bool = True,
        limit: int = 10
    ) -> List[Dict]:
        """Search for properties using both vector and traditional search"""
        try:
            if use_semantic and query:
                # Semantic search using vector store
                vector_results = await vector_store.search_properties(
                    query=query,
                    filter_dict=filters,
                    top_k=limit
                )
                
                # Get property IDs from vector search
                property_ids = [int(result["id"]) for result in vector_results]
                
                # Fetch full property objects
                properties = self.db.query(Property).filter(
                    Property.id.in_(property_ids)
                ).all()
                
                # Sort properties to match vector search order
                id_to_property = {p.id: p for p in properties}
                return [
                    id_to_property[int(result["id"])].to_dict()
                    for result in vector_results
                    if int(result["id"]) in id_to_property
                ]
            
            else:
                # Traditional database search
                query_obj = self.db.query(Property)
                
                if filters:
                    conditions = []
                    
                    if "price_range" in filters:
                        min_price, max_price = filters["price_range"]
                        conditions.append(Property.price.between(min_price, max_price))
                    
                    if "bedrooms" in filters:
                        conditions.append(Property.bedrooms >= filters["bedrooms"])
                    
                    if "bathrooms" in filters:
                        conditions.append(Property.bathrooms >= filters["bathrooms"])
                    
                    if "property_type" in filters:
                        conditions.append(Property.property_type == filters["property_type"])
                    
                    if "listing_type" in filters:
                        conditions.append(Property.listing_type == filters["listing_type"])
                    
                    if conditions:
                        query_obj = query_obj.filter(and_(*conditions))
                
                properties = query_obj.limit(limit).all()
                return [p.to_dict() for p in properties]
        
        except Exception as e:
            raise Exception(f"Failed to search properties: {str(e)}")

    def get_property(self, property_id: int) -> Optional[Dict]:
        """Get a property by ID"""
        try:
            property_obj = self.db.query(Property).filter(
                Property.id == property_id
            ).first()
            return property_obj.to_dict() if property_obj else None
        except Exception as e:
            raise Exception(f"Failed to get property: {str(e)}")

    async def update_property(self, property_id: int, property_data: Dict) -> Optional[Dict]:
        """Update a property listing"""
        try:
            property_obj = self.db.query(Property).filter(
                Property.id == property_id
            ).first()
            
            if not property_obj:
                return None
            
            # Update database
            for key, value in property_data.items():
                setattr(property_obj, key, value)
            
            self.db.commit()
            self.db.refresh(property_obj)
            
            # Update vector store
            await vector_store.add_property(
                property_id=property_obj.id,
                text=property_obj.to_embedding_text(),
                metadata=property_obj.to_dict()
            )
            
            return property_obj.to_dict()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update property: {str(e)}")

    async def delete_property(self, property_id: int) -> bool:
        """Delete a property listing"""
        try:
            property_obj = self.db.query(Property).filter(
                Property.id == property_id
            ).first()
            
            if not property_obj:
                return False
            
            # Delete from database
            self.db.delete(property_obj)
            self.db.commit()
            
            # Delete from vector store
            vector_store.delete_property(property_id)
            
            return True
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to delete property: {str(e)}")
