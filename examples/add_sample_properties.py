import asyncio
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.services.vector_store.pinecone_service import pinecone_service

async def add_sample_properties():
    # Sample properties
    properties = [
        {
            "content": "Luxurious Downtown Penthouse with stunning city views. Modern design meets comfort in this high-rise paradise. Gourmet kitchen, floor-to-ceiling windows, and private terrace.",
            "metadata": {
                "property_id": "DT001",
                "price": 1200000,
                "location": "123 Downtown Ave, City Center",
                "bedrooms": 3,
                "bathrooms": 2.5,
                "area": 2200,
                "amenities": [
                    "Gourmet Kitchen",
                    "Floor-to-ceiling Windows",
                    "Private Terrace",
                    "24/7 Security",
                    "Fitness Center",
                    "Parking Garage"
                ]
            }
        },
        {
            "content": "Charming Suburban Family Home with spacious backyard. Perfect for families, this well-maintained home features an updated kitchen, hardwood floors throughout, and a finished basement.",
            "metadata": {
                "property_id": "SB002",
                "price": 650000,
                "location": "456 Maple Street, Pleasant Valley",
                "bedrooms": 4,
                "bathrooms": 3,
                "area": 2800,
                "amenities": [
                    "Updated Kitchen",
                    "Hardwood Floors",
                    "Finished Basement",
                    "Large Backyard",
                    "Two-car Garage",
                    "Patio"
                ]
            }
        },
        {
            "content": "Modern Beachfront Condo with ocean views. Experience coastal living at its finest in this newly renovated unit. Open concept design, designer finishes, and resort-style amenities.",
            "metadata": {
                "property_id": "BC003",
                "price": 850000,
                "location": "789 Coastal Drive, Oceanview",
                "bedrooms": 2,
                "bathrooms": 2,
                "area": 1500,
                "amenities": [
                    "Ocean Views",
                    "Resort-style Pool",
                    "Private Beach Access",
                    "Balcony",
                    "Covered Parking",
                    "Smart Home Features"
                ]
            }
        }
    ]

    print("Adding sample properties to Pinecone...")
    
    for prop in properties:
        try:
            await pinecone_service.upsert_document(
                content=prop["content"],
                metadata=prop["metadata"],
                index_type="properties"
            )
            print(f"Added property: {prop['metadata']['property_id']}")
        except Exception as e:
            print(f"Error adding property {prop['metadata']['property_id']}: {str(e)}")

    print("\nNow you can try voice queries like:")
    print('- "Show me properties in downtown"')
    print('- "What properties have 3 or more bedrooms?"')
    print('- "Are there any beachfront properties available?"')
    print('- "Tell me about properties with a pool or fitness center"')

if __name__ == "__main__":
    asyncio.run(add_sample_properties())
