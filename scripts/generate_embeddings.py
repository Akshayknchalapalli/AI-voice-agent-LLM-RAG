import asyncio
from supabase import create_client
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

try:
    from app.services.property.vector_store import vector_store
except Exception as e:
    print(f"Error importing vector_store: {str(e)}")
    sys.exit(1)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Initialize Supabase client
try:
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )
except Exception as e:
    print(f"Error initializing Supabase client: {str(e)}")
    sys.exit(1)

async def generate_property_embeddings():
    print("📚 Fetching properties from Supabase...")
    
    try:
        # Fetch all properties
        response = supabase.table('properties').select('*').execute()
        properties = response.data
        
        print(f"🔍 Generating embeddings for {len(properties)} properties...")
        
        for i, property in enumerate(properties):
            try:
                # Create a rich text description for embedding
                description = f"""
                {property['title']}. 
                {property['description']}
                This {property['property_type']} property is located in {property['address']}, {property['city']}, {property['state']}.
                It has {property['bedrooms']} bedrooms and {property['bathrooms']} bathrooms with {property['square_feet']} square feet.
                Features include: {', '.join(property['features'])}.
                The property is {property['furnishing_status']} and {property['possession_status']}.
                """
                
                # Metadata for filtering
                metadata = {
                    "property_id": str(property['id']),
                    "property_type": property['property_type'],
                    "listing_type": property['listing_type'],
                    "city": property['city'],
                    "state": property['state'],
                    "price": property['price'],
                    "bedrooms": property['bedrooms'],
                    "bathrooms": property['bathrooms'],
                    "square_feet": property['square_feet']
                }
                
                # Add to vector store
                success = await vector_store.add_property(
                    property_id=property['id'],
                    text=description.strip(),
                    metadata=metadata
                )
                
                if success:
                    print(f"✅ Generated embedding for property {i+1}/{len(properties)}")
                else:
                    print(f"❌ Failed to generate embedding for property {i+1}/{len(properties)}")
            except Exception as e:
                print(f"Error processing property {i+1}: {str(e)}")
                continue
    except Exception as e:
        print(f"Error fetching properties: {str(e)}")
        return

async def main():
    print("🚀 Starting embedding generation...")
    try:
        await generate_property_embeddings()
        print("✨ Done!")
    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
