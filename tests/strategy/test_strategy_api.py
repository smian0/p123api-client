"""Test suite for Strategy API functionality."""

from pathlib import Path

import pytest

from p123api_client.strategy.schemas import StrategyResponse

# Test data
VALID_STRATEGY_ID = 1701030


@pytest.fixture
def output_dir():
    """Create and return output directory for test artifacts."""
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.mark.vcr()
def test_get_strategy_details(strategy_api):
    """Test getting strategy details from API."""
    response = strategy_api.get_strategy(VALID_STRATEGY_ID)

    assert isinstance(response, StrategyResponse)
    assert response.general_info is not None
    assert response.holdings is not None
    assert isinstance(response.general_info.name, str)
    assert isinstance(response.general_info.mkt_val, (float, type(None)))


@pytest.mark.vcr()
def test_holdings_dataframe_conversion(strategy_api, output_dir):
    """Test conversion of API holdings data to DataFrame."""
    response = strategy_api.get_strategy(VALID_STRATEGY_ID)

    # Save response data
    response.holdings_df.to_csv(output_dir / "holdings.csv")
    response.get_sector_weights().to_csv(output_dir / "sector_weights.csv")
    response.get_top_holdings(50).to_csv(output_dir / "top_holdings.csv")

    df = response.holdings_df
    if not df.empty:
        expected_columns = {"weight", "sector", "value", "shares", "name"}
        assert expected_columns.issubset(set(df.columns))

        # Verify sector weights
        sector_weights = response.get_sector_weights()
        assert sector_weights.sum() <= 1.01

        # Verify top holdings sorting
        top_holdings = response.get_top_holdings(50)
        if len(top_holdings) > 1:
            assert top_holdings.iloc[0]["weight"] >= top_holdings.iloc[-1]["weight"]


@pytest.mark.vcr()
def test_empty_strategy(strategy_api):
    """Test handling of strategy with no holdings."""
    response = strategy_api.get_strategy(VALID_STRATEGY_ID)
    assert len(response.holdings) > 0
    assert not response.holdings_df.empty
    assert not response.get_sector_weights().empty
    assert not response.get_top_holdings().empty
