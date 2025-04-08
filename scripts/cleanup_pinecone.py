import pinecone
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Initialize Pinecone
pinecone.init(
    api_key=os.getenv('PINECONE_API_KEY'),
    environment=os.getenv('PINECONE_ENVIRONMENT')
)

# List all indexes
print("📚 Current Pinecone indexes:")
indexes = pinecone.list_indexes()
print(indexes)

# Delete all indexes
for index_name in indexes:
    print(f"🗑️ Deleting index: {index_name}")
    pinecone.delete_index(index_name)

print("✨ Cleanup complete!")
