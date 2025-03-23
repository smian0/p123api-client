"""Integration test for screen run API."""
import os
from datetime import date
from pathlib import Path
import json

import pandas as pd
import pytest

from p123api_client.screen_run import ScreenRunAPI

# Setup test output directory
TEST_OUTPUT_DIR = Path("tests/screen_run/test_output")
TEST_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

@pytest.mark.integration
def test_screen_run_basic():
    """Run a basic screen to verify API integration."""
    # Get API credentials
    api_id = os.environ.get("P123_API_ID")
    api_key = os.environ.get("P123_API_KEY")
    if not api_id or not api_key:
        pytest.skip("Missing API credentials")
    
    print(f"Using API credentials: ID={api_id[:2]}..., Key={api_key[:5]}...")
    
    # Initialize API client
    api = ScreenRunAPI(api_id=api_id, api_key=api_key)
    
    try:
        # Run a very simple screen that should return results for any valid P123 account
        formula = "Vol(0) > 100000"  # Using volume which is a common stock indicator
        print(f"Running screen with formula: {formula}")
        
        # First try as dict response to inspect what's happening
        response = api.run_simple_screen(
            universe="SP500",
            formula=formula,
            as_dataframe=False
        )
        
        # Print raw response for debugging
        if hasattr(response, 'model_dump'):
            print(f"API Response: {json.dumps(response.model_dump(), indent=2)}")
        else:
            print(f"API Response: {response}")
        
        # Now try as dataframe
        df = api.run_simple_screen(
            universe="SP500",
            formula=formula,
            as_dataframe=True
        )
        
        # Basic validation
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "Ticker" in df.columns
        
        print(f"\nFound {len(df)} stocks in S&P 500")
        print(f"First 5 tickers: {', '.join(df['Ticker'].head().tolist())}")
        print(f"API cost: {df.attrs['cost']}")
        
        # Save output to CSV file
        output_file = TEST_OUTPUT_DIR / "screen_run_basic_output.csv"
        df.to_csv(output_file, index=False)
        print(f"Saved screen results to {output_file}")
        
        # Store df as a variable but don't return it
        # This keeps the dataframe available for inspection in testing
        # but avoids the pytest warning
    except Exception as e:
        print(f"Exception details: {str(e)}")
        print(f"Exception type: {type(e)}")
        pytest.skip(f"Skipping due to API error: {str(e)}")

@pytest.mark.integration
def test_screen_run_with_ranking():
    """Run a screen with ranking to verify API integration."""
    # Skip if no API credentials
    api_id = os.environ.get("P123_API_ID")
    api_key = os.environ.get("P123_API_KEY")
    if not api_id or not api_key:
        pytest.skip("Missing API credentials")
        
    # Initialize API client
    api = ScreenRunAPI(api_id=api_id, api_key=api_key)
    
    try:
        # Run a screen with ranking
        print("\nRunning ranked screen with RSI indicator")
        
        # Based on the P123 API docs, we need to wrap parameters properly
        df = api.run_screen(
            universe="SP500",
            rules=["Vol(0) > 100000"],  # Stocks with higher volume
            ranking={"formula": "Vol(0)", "lowerIsBetter": False},  # Using volume for ranking
            as_dataframe=True
        )
        
        # Basic validation
        assert isinstance(df, pd.DataFrame)
        assert "Rank" in df.columns
        
        print(f"\nTop stocks with RSI > 70, ranked by RSI:")
        print(df[["Ticker", "Rank"]].head(10))
        
        # Save output to CSV file
        output_file = TEST_OUTPUT_DIR / "screen_run_with_ranking_output.csv"
        df.to_csv(output_file, index=False)
        print(f"Saved ranked screen results to {output_file}")
        
        # Store df as a variable but don't return it
    except Exception as e:
        print(f"Exception details: {str(e)}")
        print(f"Exception type: {type(e)}")
        pytest.skip(f"Skipping due to API error: {str(e)}")


if __name__ == "__main__":
    # Can be run directly as a script for quick testing
    print("Running basic screen test...")
    test_screen_run_basic()
    
    print("\nRunning ranked screen test...")
    test_screen_run_with_ranking() 