import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.property import Property, PropertyType, ListingType
from app.services.property.property_service import PropertyService

# Test properties data
test_properties = [
    {
        "title": "Modern Downtown Apartment",
        "description": "Beautiful 2-bed apartment with stunning city views and modern amenities",
        "property_type": "APARTMENT",
        "listing_type": "SALE",
        "address": "123 Downtown St",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
        "price": 250000,
        "bedrooms": 2,
        "bathrooms": 2.0,
        "square_feet": 1200,
        "features": ["parking", "pool", "gym"],
        "images": ["https://placehold.co/600x400/png?text=Modern+Apartment"]
    },
    {
        "title": "Suburban Family Home",
        "description": "Spacious 4 bedroom house with large backyard and updated kitchen",
        "property_type": "HOUSE",
        "listing_type": "SALE",
        "address": "456 Suburban Ave",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "90001",
        "price": 450000,
        "bedrooms": 4,
        "bathrooms": 3.0,
        "square_feet": 2500,
        "features": ["garage", "backyard", "updated_kitchen"],
        "images": ["https://placehold.co/600x400/png?text=Family+Home"]
    },
    {
        "title": "Luxury Penthouse",
        "description": "Exclusive penthouse with panoramic views and high-end finishes",
        "property_type": "PENTHOUSE",
        "listing_type": "SALE",
        "address": "789 Luxury Blvd",
        "city": "Miami",
        "state": "FL",
        "zip_code": "33101",
        "price": 850000,
        "bedrooms": 3,
        "bathrooms": 3.5,
        "square_feet": 3000,
        "features": ["views", "luxury_finishes", "private_elevator"],
        "images": ["https://placehold.co/600x400/png?text=Luxury+Penthouse"]
    }
]

async def add_test_properties():
    db = SessionLocal()
    try:
        property_service = PropertyService(db)
        for prop_data in test_properties:
            await property_service.create_property(prop_data)
        print("Test properties added successfully!")
    except Exception as e:
        print(f"Error adding test properties: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(add_test_properties())
