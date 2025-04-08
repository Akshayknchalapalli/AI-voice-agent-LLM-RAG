import asyncio
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_store.pinecone_service import pinecone_service

# Sample real estate knowledge
REAL_ESTATE_KNOWLEDGE = [
    {
        "content": "When buying a first home, key factors to consider include: location, budget, down payment requirements, mortgage rates, property condition, and future resale value. Get pre-approved for a mortgage before house hunting.",
        "source": "First-time Buyer Guide",
        "id": "guide-001"
    },
    {
        "content": "Property inspection checklist: foundation integrity, roof condition, electrical systems, plumbing, HVAC system, insulation, windows and doors, signs of water damage or mold, and pest infestation.",
        "source": "Home Inspection Guide",
        "id": "inspect-001"
    },
    {
        "content": "Real estate market indicators include: median home prices, days on market, inventory levels, price per square foot, and absorption rate. These help determine if it's a buyer's or seller's market.",
        "source": "Market Analysis",
        "id": "market-001"
    },
    {
        "content": "Common types of mortgages: Conventional (fixed-rate or adjustable), FHA loans (lower down payment), VA loans (for veterans), and jumbo loans (for high-value properties). Each has different requirements and terms.",
        "source": "Mortgage Guide",
        "id": "mortgage-001"
    },
    {
        "content": "Property value factors: location quality (schools, crime rate, amenities), lot size, house size, age and condition, recent renovations, comparable sales in the area, and local market trends.",
        "source": "Property Valuation",
        "id": "value-001"
    },
    {
        "content": "Real estate negotiation tips: research comparable sales, know your maximum budget, get a home inspection, request repairs or credits, and be prepared to walk away if terms aren't favorable.",
        "source": "Negotiation Guide",
        "id": "nego-001"
    },
    {
        "content": "Closing costs typically include: loan origination fees, appraisal fees, title insurance, property taxes, homeowners insurance, and various other processing fees. Usually 2-5% of purchase price.",
        "source": "Closing Guide",
        "id": "close-001"
    }
]

# Sample property listings
PROPERTY_LISTINGS = [
    {
        "content": "Luxurious Downtown Penthouse with stunning city views. Modern design meets comfort in this high-rise paradise. Gourmet kitchen, floor-to-ceiling windows, and private terrace.",
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
    },
    {
        "content": "Charming Suburban Family Home with spacious backyard. Perfect for families, this well-maintained home features an updated kitchen, hardwood floors throughout, and a finished basement.",
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
    },
    {
        "content": "Modern Beachfront Condo with ocean views. Experience coastal living at its finest in this newly renovated unit. Open concept design, designer finishes, and resort-style amenities.",
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
    },
    {
        "content": "Historic Victorian Gem in prime location. This beautifully restored home combines period charm with modern conveniences. Features original hardwood floors, crown molding, and a chef's kitchen.",
        "property_id": "HV004",
        "price": 950000,
        "location": "321 Heritage Lane, Historic District",
        "bedrooms": 4,
        "bathrooms": 3.5,
        "area": 3200,
        "amenities": [
            "Chef's Kitchen",
            "Original Hardwood",
            "Crown Molding",
            "Wine Cellar",
            "Garden",
            "Period Features"
        ]
    }
]

async def populate_pinecone():
    """Populate Pinecone with real estate knowledge and property listings"""
    logger.info("Starting to populate Pinecone...")
    
    try:
        # Upload real estate knowledge
        logger.info("Uploading real estate knowledge...")
        for doc in REAL_ESTATE_KNOWLEDGE:
            logger.info(f"Processing knowledge document: {doc['id']}")
            try:
                await pinecone_service.upsert_document(
                    content=doc['content'],
                    metadata={
                        'id': doc['id'],
                        'source': doc['source']
                    },
                    index_type="realestate"
                )
                logger.info(f"Successfully uploaded knowledge document: {doc['id']}")
            except Exception as e:
                logger.error(f"Error uploading knowledge document {doc['id']}: {str(e)}")
        
        # Upload property listings
        logger.info("\nUploading property listings...")
        for prop in PROPERTY_LISTINGS:
            logger.info(f"Processing property: {prop['property_id']}")
            try:
                await pinecone_service.upsert_document(
                    content=prop['content'],
                    metadata={
                        'property_id': prop['property_id'],
                        'price': prop['price'],
                        'location': prop['location'],
                        'bedrooms': prop['bedrooms'],
                        'bathrooms': prop['bathrooms'],
                        'area': prop['area'],
                        'amenities': prop['amenities']
                    },
                    index_type="properties"
                )
                logger.info(f"Successfully uploaded property: {prop['property_id']}")
            except Exception as e:
                logger.error(f"Error uploading property {prop['property_id']}: {str(e)}")
        
        logger.info("\nFinished populating Pinecone!")
        logger.info("\nYou can now try voice queries like:")
        logger.info('- "Tell me about buying a first home"')
        logger.info('- "What should I check during a home inspection?"')
        logger.info('- "Show me properties in downtown"')
        logger.info('- "Are there any beachfront properties?"')
        logger.info('- "What properties have 3 or more bedrooms?"')
        
    except Exception as e:
        logger.error(f"Fatal error during population: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(populate_pinecone())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
