"""Test screen run with environment-controlled VCR."""
import pytest
import os
from p123api_client.screen_run import ScreenRunAPI
from p123api_client.common.settings import Settings

# Get credentials from environment or use test values
settings = Settings()
API_ID = settings.api_id
API_KEY = settings.api_key


class TestScreenRunEnvironment:
    """Test the ScreenRunAPI with environment-controlled VCR."""

    def test_run_screen_by_id_auto_vcr(self, auto_vcr):
        """Test running screen by ID using auto_vcr fixture.
        
        This test will use VCR based on environment variables:
        - If VCR_ENABLED=true (default), it will record/replay as normal
        - If VCR_ENABLED=false, it will bypass VCR and use real API calls
        """
        # Initialize the API
        api = ScreenRunAPI(api_id=API_ID, api_key=API_KEY)
        
        # Run the screen by ID (using a known screen ID)
        screen_id = 309184  # Use your actual screen ID
        result = api.run_screen_by_id(screen_id, as_dataframe=True)
        
        # Basic validation for DataFrame
        assert result is not None
        assert len(result) > 0  
        assert 'Ticker' in result.columns 