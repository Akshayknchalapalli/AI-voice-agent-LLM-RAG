import pytest
from app.services.db.supabase_service import supabase_service
import logging
import uuid
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture(autouse=True)
async def verify_supabase_connection():
    """Verify Supabase connection before running tests"""
    try:
        # Log Supabase configuration
        logger.info(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
        anon_key = os.getenv('SUPABASE_ANON_KEY', '')
        masked_key = f"{anon_key[:8]}...{anon_key[-8:]}" if anon_key else "Not set"
        logger.info(f"SUPABASE_ANON_KEY (masked): {masked_key}")

        # Check if we can connect to Supabase
        logger.info("Verifying Supabase connection...")
        response = supabase_service.client.table('conversations').select('count').execute()
        logger.info(f"Connection test response: {response}")
        logger.info("Successfully connected to Supabase")
        yield
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

@pytest.fixture
async def cleanup_test_data():
    """Clean up test data after tests"""
    yield
    try:
        # Delete test conversations after tests
        logger.info("Cleaning up test conversations...")
        response = supabase_service.client.table('conversations').delete().execute()
        logger.info(f"Cleanup response: {response}")
        logger.info("Successfully cleaned up test data")
    except Exception as e:
        logger.error(f"Error cleaning up test data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

@pytest.mark.asyncio
async def test_save_conversation(cleanup_test_data):
    """Test saving conversations to Supabase"""
    # Test data
    test_transcript = f"Test user query {uuid.uuid4()}"
    test_response = "Test AI response"
    test_audio_url = "https://example.com/audio.mp3"

    try:
        # Test saving conversation
        logger.info(f"Testing save_conversation with transcript: {test_transcript}")
        result = await supabase_service.save_conversation(
            transcript=test_transcript,
            ai_response=test_response,
            audio_url=test_audio_url
        )
        
        if not result:
            logger.error("save_conversation returned False")
            raise AssertionError("Failed to save conversation")
            
        logger.info("Successfully saved test conversation")

        # Verify the saved conversation
        logger.info("Verifying saved conversation...")
        response = supabase_service.client.table('conversations').select('*').eq('transcript', test_transcript).execute()
        
        if not response.data:
            logger.error("No conversation found in database after save")
            logger.error(f"Response: {response}")
            raise AssertionError("No conversation found in database")
        
        saved_conv = response.data[0]
        assert saved_conv['transcript'] == test_transcript, f"Transcript mismatch. Expected: {test_transcript}, Got: {saved_conv['transcript']}"
        assert saved_conv['ai_response'] == test_response, f"AI response mismatch. Expected: {test_response}, Got: {saved_conv['ai_response']}"
        assert saved_conv['audio_url'] == test_audio_url, f"Audio URL mismatch. Expected: {test_audio_url}, Got: {saved_conv['audio_url']}"
        
        logger.info("Verification successful - conversation was saved correctly")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

@pytest.mark.asyncio
async def test_save_conversation_without_audio(cleanup_test_data):
    """Test saving conversations without audio URL"""
    # Test data
    test_transcript = f"Another test query {uuid.uuid4()}"
    test_response = "Another AI response"

    try:
        # Test saving conversation without audio
        logger.info(f"Testing save_conversation without audio, transcript: {test_transcript}")
        result = await supabase_service.save_conversation(
            transcript=test_transcript,
            ai_response=test_response
        )
        
        if not result:
            logger.error("save_conversation returned False")
            raise AssertionError("Failed to save conversation without audio")
            
        logger.info("Successfully saved test conversation without audio")

        # Verify the saved conversation
        logger.info("Verifying saved conversation...")
        response = supabase_service.client.table('conversations').select('*').eq('transcript', test_transcript).execute()
        
        if not response.data:
            logger.error("No conversation found in database after save")
            logger.error(f"Response: {response}")
            raise AssertionError("No conversation found in database")
        
        saved_conv = response.data[0]
        assert saved_conv['transcript'] == test_transcript, f"Transcript mismatch. Expected: {test_transcript}, Got: {saved_conv['transcript']}"
        assert saved_conv['ai_response'] == test_response, f"AI response mismatch. Expected: {test_response}, Got: {saved_conv['ai_response']}"
        assert saved_conv['audio_url'] is None, f"Audio URL should be None, Got: {saved_conv['audio_url']}"
        
        logger.info("Verification successful - conversation was saved correctly without audio")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise
