from faker import Faker
import random
import json
from supabase import create_client
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

fake = Faker('en_IN')

property_types = {
    "Residential": ["Flat", "Villa", "Plot", "Independent House"],
    "Commercial": ["Office Space", "Showroom", "Godown", "Industrial Space", "Hotel Space", "Restaurant", "Cafe", "Shop"],
    "Agricultural": ["Agricultural Land", "Farm House"]
}

enquiry_types = ["None", "Buy", "Sale", "Rent"]
sale_types = ["None", "New", "Resale"]
statuses = ["Available", "Sold", "Pending"]
bhk_types = ["1 RK", "1 BHK", "2 BHK", "3 BHK", "4 BHK", "Studio"]
furnishing_status = ["Unfurnished", "Semi-furnished", "Fully-furnished"]
availability = ["Immediate", "Within 1 Month", "Within 3 Months"]
ownerships = ["Freehold", "Leasehold", "Co-operative Society"]
possession_statuses = ["Ready to move", "Under construction"]

def generate_property():
    main_type = random.choice(list(property_types.keys()))
    sub_type = random.choice(property_types[main_type])
    bhk_type = random.choice(bhk_types) if main_type == "Residential" else None
    no_of_bhks = int(bhk_type[0]) if bhk_type and bhk_type[0].isdigit() else None
    
    # Generate fake coordinates near major Indian cities
    city = fake.city()
    latitude = random.uniform(8.4, 28.7)  # India's latitude range
    longitude = random.uniform(68.7, 97.3)  # India's longitude range
    
    amenities = random.sample([
        "Lift", "Parking", "Power Backup", "Security", "Park", "Gym", "Swimming Pool", "Club House"
    ], k=random.randint(2, 6))

    # Generate fake images
    images = [
        f"https://picsum.photos/seed/{random.randint(1, 1000)}/800/600"
        for _ in range(random.randint(3, 8))
    ]

    return {
        "title": fake.catch_phrase(),
        "description": fake.paragraph(nb_sentences=3),
        "property_type": main_type.lower(),
        "listing_type": random.choice(["sale", "rent"]),
        "address": fake.street_address(),
        "city": city,
        "state": fake.state(),
        "zip_code": fake.postcode(),
        "latitude": latitude,
        "longitude": longitude,
        "price": fake.random_int(min=1000000, max=100000000),
        "bedrooms": no_of_bhks if no_of_bhks else random.randint(1, 5),
        "bathrooms": float(random.randint(1, 4)),
        "square_feet": fake.random_int(min=500, max=10000),
        "lot_size": round(random.uniform(0.1, 2.0), 2),
        "year_built": random.randint(1990, 2023),
        "features": amenities,
        "images": images,
        "virtual_tour_url": "https://my.matterport.com/show/?m=example" if random.random() > 0.7 else None,
        "is_active": True,
        "is_featured": random.random() > 0.8,
        "furnishing_status": random.choice(furnishing_status),
        "availability": random.choice(availability),
        "ownership": random.choice(ownerships),
        "possession_status": random.choice(possession_statuses)
    }

def main():
    # Generate properties
    print("🏗️ Generating fake properties...")
    properties = [generate_property() for _ in range(100)]  # Start with 100 properties

    # Insert properties in batches
    batch_size = 20
    total_properties = len(properties)
    
    print(f"📤 Uploading {total_properties} properties to Supabase...")
    
    for i in range(0, total_properties, batch_size):
        batch = properties[i:i + batch_size]
        try:
            result = supabase.table('properties').insert(batch).execute()
            print(f"✅ Uploaded batch {i//batch_size + 1}/{(total_properties + batch_size - 1)//batch_size}")
        except Exception as e:
            print(f"❌ Error uploading batch {i//batch_size + 1}: {str(e)}")
            continue

    print("✨ Done!")

if __name__ == "__main__":
    main()
