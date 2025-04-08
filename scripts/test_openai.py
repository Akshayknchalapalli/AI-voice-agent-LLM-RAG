from openai import OpenAI
import os
from dotenv import load_dotenv

def test_openai_key():
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
            
        print("Testing OpenAI API key...")
        print(f"API Key starts with: {api_key[:8]}...")
        
        client = OpenAI(api_key=api_key)
        
        # Try to create a simple embedding
        response = client.embeddings.create(
            input="Hello, world!",
            model="text-embedding-ada-002"
        )
        
        print("✅ Success! Your OpenAI API key is working.")
        return True
        
    except Exception as e:
        print("❌ Error testing OpenAI API key:")
        print(e)
        return False

if __name__ == "__main__":
    test_openai_key()
