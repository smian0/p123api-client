"""Test rank ranks API."""

import pandas as pd
import pytest

from p123api_client.rank_ranks.rank_ranks_api import RankRanksAPI
from p123api_client.rank_ranks.schemas import RankRanksRequest


@pytest.fixture
def rank_ranks_api(api_credentials: dict[str, str]) -> RankRanksAPI:
    """Create RankRanksAPI client for testing."""
    return RankRanksAPI(**api_credentials)


@pytest.mark.vcr()
def test_get_ranks(rank_ranks_api):
    """Test getting ranks."""
    # Use the sample request from the schemas file
    from p123api_client.rank_ranks.schemas import sample_rank_ranks_request

    # Create a copy of the sample request to avoid modifying the original
    request = RankRanksRequest(**sample_rank_ranks_request.model_dump())

    # Get ranks using the sample request
    response_df = rank_ranks_api.get_ranks(request)

    # Verify response
    assert isinstance(response_df, pd.DataFrame)
    assert not response_df.empty

    # Verify required columns
    required_columns = ["ticker", "rank"]
    for col in required_columns:
        assert col in response_df.columns, (
            f"Column {col} not found. Available columns: {response_df.columns.tolist()}"
        )
