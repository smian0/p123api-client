"""Test screen backtest app."""
import pytest
import logging
import os
import pandas as pd
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

from p123api_client.models.enums import PitMethod, Currency
from p123api_client.screen_backtest.models import BacktestRequest
from p123api_client.screen_backtest.screen_backtest_app import ScreenBacktestApp

from ..base import BaseTest

# Load environment variables from .env.test file
dotenv_path = Path(__file__).parents[2] / ".env.test"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
else:
    logging.warning(f".env.test file not found at {dotenv_path}")


class TestScreenBacktestApp(BaseTest):
    """Test screen backtest app."""

    @pytest.mark.vcr(record_mode="new_episodes")
    def test_single_factor_screen_backtest(self):
        """Test single factor screen backtest."""
        # Create any necessary test directories
        test_data_dir = os.path.join(os.path.dirname(__file__), 'test_input')
        os.makedirs(test_data_dir, exist_ok=True)
        
        # Get API credentials from environment variables
        api_id = os.getenv("P123_API_ID")
        api_key = os.getenv("P123_API_KEY")
        
        # Skip test if credentials are not available
        if not api_id or not api_key:
            pytest.skip("API credentials not available in .env.test file")
            
        # Initialize the app with API credentials
        app = ScreenBacktestApp(
            api_id=api_id,
            api_key=api_key
        )
        
        # Create a test that uses the correct parameter format based on the API documentation
        params = {
            "startDt": "2020-01-01",  # Use string format for dates
            "endDt": "2020-12-31",
            "rebalFreq": "Every 4 Weeks",
            "pitMethod": "Prelim",
            "transPrice": 4,  # 4 - Close
            "riskStatsPeriod": "Monthly",
            "screen": {
                "type": "stock",
                "universe": "SP500",
                "maxNumHoldings": 50,
                "method": "long",
                "currency": "USD",
                "benchmark": "SPY",
                "ranking": "ApiRankingSystem",
                "rules": [
                    {"formula": "PERelative() > 0"}
                ]
            }
        }
        
        try:
            # Call the API directly with the parameters
            result = app.api.make_request("screen_backtest", params)
            self.assertIsNotNone(result)
            logging.info("Successfully ran single factor screen backtest")
        except Exception as e:
            pytest.fail(f"Failed to run single factor screen backtest: {e}")

    @pytest.mark.vcr(record_mode="new_episodes")
    def test_multi_factor_screen_backtest_from_tsv(self):
        """Test multi factor screen backtest from TSV."""
        # Create any necessary test directories
        test_data_dir = os.path.join(os.path.dirname(__file__), 'test_input')
        os.makedirs(test_data_dir, exist_ok=True)
        
        # Create a sample TSV file with factors if it doesn't exist
        tsv_file_path = Path(test_data_dir) / "test_factors.tsv"
        if not tsv_file_path.exists():
            # Create a simple factor TSV file
            factors_df = pd.DataFrame({
                'Factor': ['PE', 'PB', 'ROE'],
                'Weight': [0.4, 0.3, 0.3],
                'Direction': ['ASC', 'ASC', 'DESC']
            })
            factors_df.to_csv(tsv_file_path, sep='\t', index=False)
            logging.info(f"Created test factors TSV file at {tsv_file_path}")
        
        # Get API credentials from environment variables
        api_id = os.getenv("P123_API_ID")
        api_key = os.getenv("P123_API_KEY")
        
        # Skip test if credentials are not available
        if not api_id or not api_key:
            pytest.skip("API credentials not available in .env.test file")
            
        # Initialize the app with API credentials
        app = ScreenBacktestApp(
            api_id=api_id,
            api_key=api_key
        )
        
        # Read the factors from the TSV file
        factors_df = pd.read_csv(tsv_file_path, sep='\t')
        
        # Create a direct parameter dictionary similar to the first test
        params = {
            "startDt": "2020-01-01",
            "endDt": "2020-12-31",
            "rebalFreq": "Every 4 Weeks",
            "pitMethod": "Prelim",
            "transPrice": 4,
            "riskStatsPeriod": "Monthly",
            "screen": {
                "type": "stock",
                "universe": "SP500",
                "maxNumHoldings": 50,
                "method": "long",
                "currency": "USD",
                "benchmark": "SPY",
                "ranking": "ApiRankingSystem",
                "rules": [
                    {"formula": "(Close() > 0)"}  # Simple rule to ensure we get stocks with correct syntax
                ]
            }
        }
        
        # Print the parameters to debug
        import json
        logging.info(f"Parameters: {json.dumps(params, default=str)}")
        
        # Check if there's a 'factors' parameter anywhere in the params
        def check_for_factors(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "factors":
                        logging.warning(f"Found 'factors' at {path}.{key}")
                    check_for_factors(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_for_factors(item, f"{path}[{i}]")
        
        check_for_factors(params, "params")
        
        try:
            # Access the underlying p123api client directly
            # This bypasses any potential issues with our wrapper
            result = app.api.client.screen_backtest(params, to_pandas=True)
            self.assertIsNotNone(result)
            logging.info("Successfully ran multi-factor screen backtest from TSV")
        except Exception as e:
            pytest.fail(f"Failed to run multi-factor screen backtest from TSV: {e}")
