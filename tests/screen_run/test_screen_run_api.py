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
        "rules": ["close > 100", "volume > 500000"],
        "ranking": {"formula": "ROE", "lowerIsBetter": False}
    }


@pytest.mark.integration
class TestScreenRunAPI:
    """Test the screen run API."""

    @pytest.mark.vcr
    def test_run_screen_basic(self, screen_run_api, screen_data):
        """Test basic screen run functionality."""
        response = screen_run_api.run_screen(
            universe=screen_data["universe"],
            rules=screen_data["rules"],
            as_dataframe=False
        )
        
        # Verify response structure
        assert isinstance(response, ScreenRunResponse)
        assert len(response.columns) > 0
        assert len(response.rows) > 0
        assert isinstance(response.cost, int)
        assert isinstance(response.quotaRemaining, int)

    @pytest.mark.vcr
    def test_run_screen_with_ranking(self, screen_run_api, screen_data):
        """Test screen run with ranking."""
        response = screen_run_api.run_screen(
            universe=screen_data["universe"],
            rules=screen_data["rules"],
            ranking=screen_data["ranking"],
            as_dataframe=False
        )
        
        # Verify response includes ranking results
        assert isinstance(response, ScreenRunResponse)
        assert "Rank" in response.columns

    @pytest.mark.vcr
    def test_run_screen_as_dataframe(self, screen_run_api, screen_data):
        """Test screen run with DataFrame output."""
        df = screen_run_api.run_screen(
            universe=screen_data["universe"],
            rules=screen_data["rules"],
            as_dataframe=True
        )
        
        # Verify DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) > 0
        
        # Verify DataFrame metadata
        assert "cost" in df.attrs
        assert "quota_remaining" in df.attrs

    @pytest.mark.vcr
    def test_run_simple_screen(self, screen_run_api):
        """Test simplified screen run interface."""
        df = screen_run_api.run_simple_screen(
            universe="SP500",
            formula="close > 200"
        )
        
        # Verify DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_screen_parameter_validation(self, screen_run_api):
        """Test parameter validation."""
        # Test invalid date (too old)
        with pytest.raises(ValidationError):
            screen_run_api.run_screen(
                universe="SP500",
                rules=["close > 50"],
                as_of_date=date(1990, 1, 1)  # Before minimum allowed date
            )
            
        # Test future date (reasonable future date should be acceptable)
        future_date = date.today() + timedelta(days=30)
        if future_date.year <= 2025:  # Ensure within max date
            response = screen_run_api.run_screen(
                universe="SP500",
                rules=["close > 50"],
                as_of_date=future_date,
                as_dataframe=False
            )
            assert isinstance(response, ScreenRunResponse)
        
        # Test missing required parameter
        with pytest.raises(ValueError):
            screen_run_api.run_screen(
                universe="",  # Empty universe
                rules=["close > 50"]
            )

    def test_schema_validation(self):
        """Test schema validations."""
        # Test valid screen definition
        screen_def = ScreenDefinition(
            type=ScreenType.STOCK,
            universe="SP500",
            rules=["close > 100"]
        )
        assert isinstance(screen_def.rules[0], ScreenRule)
        
        # Test invalid screen definition (missing required field)
        with pytest.raises(ValidationError):
            ScreenDefinition(
                type=ScreenType.STOCK,
                # Missing universe
                rules=["close > 100"]
            )
            
        # Test valid request
        request = ScreenRunRequest(
            screen=screen_def,
            asOfDt=date.today()
        )
        assert isinstance(request.screen, ScreenDefinition)

    @pytest.mark.vcr
    def test_response_to_dict_list(self, screen_run_api):
        """Test conversion of response to dict list."""
        response = screen_run_api.run_screen(
            universe="SP500",
            rules=["close > 200"],
            max_results=5,
            as_dataframe=False
        )
        
        dict_list = response.to_dict_list()
        assert isinstance(dict_list, list)
        assert len(dict_list) <= 5  # Max 5 results
        assert all(isinstance(item, dict) for item in dict_list)
        
        # Verify dict keys match column names
        if dict_list:
            assert set(dict_list[0].keys()) == set(response.columns) 