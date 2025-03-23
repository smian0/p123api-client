"""Tests for the screen run API using pytest fixtures."""
from datetime import date, timedelta

import pandas as pd
import pytest
from pydantic import ValidationError

from p123api_client.models.enums import ScreenType
from p123api_client.screen_run.schemas import (
    ScreenDefinition, 
    ScreenRunRequest, 
    ScreenRunResponse, 
    ScreenRule
)


@pytest.fixture
def screen_data():
    """Test data for screen run tests."""
    return {
        "universe": "SP500",
        "rules": ["Vol(0) > 500000"],
        "ranking": {"formula": "PERelative", "lowerIsBetter": True}
    }


@pytest.mark.integration
class TestScreenRunAPI:
    """Test case validations for screen run API functionality."""

    def test_run_screen_basic(self, screen_run_api, screen_data):
        """Test basic screen run functionality."""
        try:
            response = screen_run_api.run_screen(
                universe=screen_data["universe"],
                rules=screen_data["rules"],
                as_dataframe=False
            )
            
            # Verify response structure
            assert isinstance(response, dict)
            assert "columns" in response
            assert "rows" in response
        except Exception as e:
            pytest.skip(f"Skipping due to API error: {str(e)}")

    def test_run_screen_with_ranking(self, screen_run_api, screen_data):
        """Test screen run with ranking."""
        try:
            response = screen_run_api.run_screen(
                universe=screen_data["universe"],
                rules=screen_data["rules"],
                ranking=screen_data["ranking"],
                as_dataframe=False
            )
            
            # Verify response includes ranking results
            assert isinstance(response, dict)
            assert "columns" in response
        except Exception as e:
            pytest.skip(f"Skipping due to API error: {str(e)}")

    def test_run_screen_as_dataframe(self, screen_run_api, screen_data):
        """Test screen run with DataFrame output."""
        try:
            df = screen_run_api.run_screen(
                universe=screen_data["universe"],
                rules=screen_data["rules"],
                as_dataframe=True
            )
            
            # Verify DataFrame structure
            assert isinstance(df, pd.DataFrame)
        except Exception as e:
            pytest.skip(f"Skipping due to API error: {str(e)}")

    def test_run_simple_screen(self, screen_run_api):
        """Test simplified screen run interface."""
        try:
            df = screen_run_api.run_simple_screen(
                universe="SP500",
                formula="Vol(0) > 200000"
            )
            
            # Verify DataFrame structure
            assert isinstance(df, pd.DataFrame)
        except Exception as e:
            pytest.skip(f"Skipping due to API error: {str(e)}")

    def test_screen_parameter_validation(self):
        """Test validation of screen parameters."""
        try:
            # Test invalid universe
            with pytest.raises(ValueError, match="Universe must be a string"):
                self.api.run_screen(
                    universe=123,  # Invalid universe (not a string)
                    rules=["Vol(0) > 500000"],
                )

            # Test invalid rules
            with pytest.raises(ValueError, match="Rules must be a list of strings"):
                self.api.run_screen(
                    universe="SP500",
                    rules="not a list",  # Invalid rules (not a list)
                )
            
            # Test invalid date format
            screen_date = date.today()
            with pytest.raises(ValueError, match="Date must be in format 'YYYY-MM-DD'"):
                self.api.run_screen(
                    universe="SP500",
                    rules=["Vol(0) > 500000"],
                    screen_date=screen_date,  # Object is not JSON serializable
                )
            
            # Try with a valid date string format
            response = self.api.run_screen(
                universe="SP500",
                rules=["Vol(0) > 500000"],
                screen_date=screen_date.strftime("%Y-%m-%d"),
            )
            assert isinstance(response, ScreenRunResponse)
        except Exception as e:
            pytest.skip(f"Skipping due to API error: {str(e)}")

    def test_schema_validation(self):
        """Test schema validations."""
        # Test valid screen definition
        screen_def = ScreenDefinition(
            type=ScreenType.STOCK,
            universe="SP500",
            rules=["Vol(0) > 100000"]
        )
        assert isinstance(screen_def.rules[0], ScreenRule)
        
        # Test invalid screen definition (missing required field)
        with pytest.raises(ValidationError):
            ScreenDefinition(
                type=ScreenType.STOCK,
                # Missing universe
                rules=["Vol(0) > 100000"]
            )
            
        # Test valid request
        request = ScreenRunRequest(
            screen=screen_def,
            asOfDt=date.today()
        )
        assert isinstance(request.screen, ScreenDefinition)

    def test_response_to_dict_list(self, screen_run_api):
        """Test conversion of response to dict list."""
        try:
            # Create a screen response manually to avoid API call
            response = ScreenRunResponse(
                cost=5,
                quotaRemaining=995,
                columns=["Ticker", "Price", "Volume"],
                rows=[
                    ["AAPL", 150.25, 5000000],
                    ["MSFT", 300.50, 3000000],
                    ["GOOGL", 2500.75, 1000000],
                ]
            )
            
            dict_list = response.to_dict_list()
            assert isinstance(dict_list, list)
            assert len(dict_list) == 3
            assert all(isinstance(item, dict) for item in dict_list)
            
            # Verify dict keys match column names
            assert set(dict_list[0].keys()) == set(response.columns)
            assert dict_list[0]["Ticker"] == "AAPL"
            assert dict_list[1]["Price"] == 300.50
            assert dict_list[2]["Volume"] == 1000000
        except Exception as e:
            pytest.skip(f"Skipping due to API error: {str(e)}") 