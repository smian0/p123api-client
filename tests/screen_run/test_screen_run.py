"""Tests for screen run API functionality."""
import logging
import unittest
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from p123api_client.common.settings import Settings
from p123api_client.screen_run.schemas import (
    ScreenDefinition,
    ScreenRule,
    ScreenRunRequest,
    ScreenRunResponse,
)
from p123api_client.screen_run.screen_run_api import ScreenRunAPI
from p123api_client.models.enums import (
    Currency,
    PitMethod,
    ScreenMethod,
    ScreenType,
)

# Get logger instance
logger = logging.getLogger(__name__)


class TestScreenRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Configure basic logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Set up paths
        cls.test_dir = Path(__file__).parent
        cls.test_data_dir = cls.test_dir / "test_input"
        cls.output_dir = cls.test_dir / "test_output"
        
        # Ensure output directory exists
        cls.output_dir.mkdir(exist_ok=True)

        # Initialize settings and API client
        settings = Settings(testing=True)
        cls.api_id = settings.api_id
        cls.api_key = settings.api_key

        if not cls.api_id or not cls.api_key:
            raise ValueError("API credentials not properly loaded from environment")

        cls.api = ScreenRunAPI(api_id=cls.api_id, api_key=cls.api_key)

        # Test data
        cls.test_universe = "SP500"
        cls.test_rule = "close > 50"
        cls.test_ranking = {"formula": "ROE", "lowerIsBetter": False}

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

    @pytest.mark.vcr()
    def test_run_screen_basic(self):
        """Test basic screen run functionality."""
        response = self.api.run_screen(
            universe=self.test_universe,
            rules=[self.test_rule],
            as_dataframe=False
        )
        
        # Verify response structure
        self.assertIsInstance(response, ScreenRunResponse)
        self.assertGreater(len(response.columns), 0)
        self.assertGreater(len(response.rows), 0)
        self.assertIsInstance(response.cost, int)
        self.assertIsInstance(response.quotaRemaining, int)
        
        # Save output for inspection
        output_file = self.output_dir / "basic_screen_results.csv"
        pd.DataFrame(response.rows, columns=response.columns).to_csv(output_file, index=False)
        
    @pytest.mark.vcr()
    def test_run_screen_with_ranking(self):
        """Test screen run with ranking."""
        response = self.api.run_screen(
            universe=self.test_universe,
            rules=[self.test_rule],
            ranking=self.test_ranking,
            as_dataframe=False
        )
        
        # Verify response includes ranking results
        self.assertIsInstance(response, ScreenRunResponse)
        self.assertIn("Rank", response.columns)
        
    @pytest.mark.vcr()
    def test_run_screen_as_dataframe(self):
        """Test screen run with DataFrame output."""
        df = self.api.run_screen(
            universe=self.test_universe,
            rules=[self.test_rule],
            as_dataframe=True
        )
        
        # Verify DataFrame structure
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertGreater(len(df.columns), 0)
        
        # Verify DataFrame metadata
        self.assertIn("cost", df.attrs)
        self.assertIn("quota_remaining", df.attrs)
        
    @pytest.mark.vcr()
    def test_run_simple_screen(self):
        """Test simplified screen run interface."""
        df = self.api.run_simple_screen(
            universe=self.test_universe,
            formula=self.test_rule
        )
        
        # Verify DataFrame structure
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        
    def test_screen_parameter_validation(self):
        """Test parameter validation."""
        # Test invalid date
        with self.assertRaises(ValueError):
            self.api.run_screen(
                universe=self.test_universe,
                rules=[self.test_rule],
                as_of_date=date(1990, 1, 1)  # Before minimum allowed date
            )
            
        # Test missing required parameter
        with self.assertRaises(ValueError):
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
        self.assertIsInstance(screen_def.rules[0], ScreenRule)
        self.assertEqual(screen_def.rules[0].formula, rule_str)
        
        # Test dict rule conversion
        rule_dict = {"formula": "volume > 1000000", "type": "common"}
        screen_def = ScreenDefinition(
            type=ScreenType.STOCK,
            universe=self.test_universe,
            rules=[rule_dict]
        )
        
        # Verify rule was properly converted
        self.assertIsInstance(screen_def.rules[0], ScreenRule)
        self.assertEqual(screen_def.rules[0].formula, rule_dict["formula"])
        self.assertEqual(screen_def.rules[0].type, rule_dict["type"])


if __name__ == "__main__":
    unittest.main() 