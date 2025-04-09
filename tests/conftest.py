import os
import sys
import pytest
import logging

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture(autouse=True)
def check_env_vars():
    """Check if required environment variables are set"""
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        pytest.fail(f"Missing required environment variables: {', '.join(missing_vars)}")
        
    # Log environment variables (masked)
    supabase_url = os.getenv('SUPABASE_URL', '')
    supabase_key = os.getenv('SUPABASE_ANON_KEY', '')
    masked_key = f"{supabase_key[:8]}...{supabase_key[-8:]}" if supabase_key else "None"
    
    logging.info(f"SUPABASE_URL: {supabase_url}")
    logging.info(f"SUPABASE_ANON_KEY (masked): {masked_key}")
