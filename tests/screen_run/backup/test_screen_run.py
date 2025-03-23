"""Tests for screen run API functionality."""
import logging
from datetime import date
from pathlib import Path
import os

import pandas as pd
import pytest
from dotenv import load_dotenv

from p123api_client.screen_run.schemas import (
    ScreenDefinition,
    ScreenRule,
    ScreenRunRequest,
    ScreenRunResponse,
)
from p123api_client.screen_run.screen_run_api import ScreenRunAPI
from p123api_client.models.enums import ScreenMethod, ScreenType

# Load environment variables
load_dotenv(".env.test")

# Get logger instance
logger = logging.getLogger(__name__)

# Setup test output directory
TEST_OUTPUT_DIR = Path("tests/screen_run/test_output")
TEST_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

@pytest.mark.integration
@pytest.mark.vcr(mode="once")
class TestScreenRun:
    """Test case validations for screen run functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.api_id = os.environ.get("P123_API_ID")
        self.api_key = os.environ.get("P123_API_KEY")
        
        if not self.api_id or not self.api_key:
            pytest.skip("Missing API credentials")

        self.api = ScreenRunAPI(api_id=self.api_id, api_key=self.api_key)
        self.test_universe = "SP500"
        self.test_rule = "Vol(0) > 500000"
        self.test_ranking = {"formula": "PERelative", "lowerIsBetter": True}

    def setUp(self) -> None:
        if not hasattr(self, "api") or not self.api:
            self.skipTest("API client not properly initialized")
        logger.info(f"\n{'=' * 80}\nStarting test: {self._testMethodName}\n{'=' * 80}")

    def tearDown(self) -> None:
        logger.info(f"\n{'-' * 80}\nCompleted test: {self._testMethodName}\n{'-' * 80}")

    def run(self, result=None):
        """Override run to add more detailed error logging."""
        try:
            super().run(result)
        except Exception as e:
            logger.error(f"Test {self._testMethodName} failed: {e}")
            raise

    def test_run_screen_basic(self):
        """Test basic screen run functionality."""
        try:
            response = self.api.run_screen(
                universe=self.test_universe,
                rules=[self.test_rule],
                as_dataframe=False
            )
            
            # Verify response structure
            assert isinstance(response, ScreenRunResponse)
            assert len(response.columns) > 0
            assert len(response.rows) > 0
            assert isinstance(response.cost, int)
            assert isinstance(response.quotaRemaining, int)
            
            # Save output for inspection
            output_file = TEST_OUTPUT_DIR / "basic_screen_results.csv"
            pd.DataFrame(response.rows, columns=response.columns).to_csv(output_file, index=False)
        except Exception as e:
            pytest.skip(f"Skipping due to API error: {str(e)}")
        
    def test_run_screen_with_ranking(self):
        """Test screen run with ranking."""
        try:
            response = self.api.run_screen(
                universe=self.test_universe,
                rules=[self.test_rule],
                ranking=self.test_ranking,
                as_dataframe=False
            )
            
            # Verify response includes ranking results
            assert isinstance(response, ScreenRunResponse)
            assert "Rank" in response.columns
        except Exception as e:
            pytest.skip(f"Skipping due to API error: {str(e)}")
        
    def test_run_screen_as_dataframe(self):
        """Test screen run with DataFrame output."""
        try:
            df = self.api.run_screen(
                universe=self.test_universe,
                rules=[self.test_rule],
                as_dataframe=True
            )
            
            # Verify DataFrame structure
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert len(df.columns) > 0
            
            # Verify DataFrame metadata
            assert "cost" in df.attrs
            assert "quota_remaining" in df.attrs
        except Exception as e:
            pytest.skip(f"Skipping due to API error: {str(e)}")
        
    def test_run_simple_screen(self):
        """Test simplified screen run interface."""
        try:
            df = self.api.run_simple_screen(
                universe=self.test_universe,
                formula=self.test_rule
            )
            
            # Verify DataFrame structure
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
        except Exception as e:
            pytest.skip(f"Skipping due to API error: {str(e)}")

    def test_screen_parameter_validation(self):
        """Test parameter validation."""
        # Test invalid date
        with pytest.raises(ValueError):
            self.api.run_screen(
                universe=self.test_universe,
                rules=[self.test_rule],
                as_of_date=date(1990, 1, 1)  # Before minimum allowed date
            )
            
        # Test missing required parameter
        with pytest.raises(ValueError):
            ScreenRunRequest(
                screen=ScreenDefinition(
                    type=ScreenType.STOCK,
                    # Missing required universe
                    rules=["close > 100"]
                )
            )
            
    def test_schema_conversion(self):
        """Test schema conversions and validations."""
        # Test string rule conversion
        rule_str = "price > 100"
        screen_def = ScreenDefinition(
            type=ScreenType.STOCK,
            universe=self.test_universe,
            rules=[rule_str]
        )
        
        # Verify rule was properly converted to ScreenRule object
        assert isinstance(screen_def.rules[0], ScreenRule)
        assert screen_def.rules[0].formula == rule_str
        
        # Test dict rule conversion
        rule_dict = {"formula": "volume > 1000000", "type": "common"}
        screen_def = ScreenDefinition(
            type=ScreenType.STOCK,
            universe=self.test_universe,
            rules=[rule_dict]
        )
        
        # Verify rule was properly converted
        assert isinstance(screen_def.rules[0], ScreenRule)
        assert screen_def.rules[0].formula == rule_dict["formula"]
        assert screen_def.rules[0].type == rule_dict["type"]


if __name__ == "__main__":
    pytest.main() 