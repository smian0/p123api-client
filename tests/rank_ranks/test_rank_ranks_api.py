"""Test rank ranks API."""
from datetime import date

import pandas as pd
import pytest

from p123api_client.models.enums import PitMethod
from p123api_client.rank_ranks.rank_ranks_api import RankRanksAPI
from p123api_client.rank_ranks.schemas import RankRanksRequest


@pytest.fixture
def rank_ranks_api(api_credentials: dict[str, str]) -> RankRanksAPI:
    """Create RankRanksAPI client for testing."""
    return RankRanksAPI(**api_credentials)


@pytest.mark.vcr()
def test_get_ranks(rank_ranks_api):
    """Test getting ranks."""
    # Create request
    request = RankRanksRequest(
        ranking_system="Test Ranking System",
        as_of_dt=date(2020, 1, 1),
        universe="Test Universe",
        pit_method=PitMethod.PRELIM,
        precision=4,
    )

    # Get ranks
    response_df = rank_ranks_api.get_ranks(request)

    # Verify response
    assert isinstance(response_df, pd.DataFrame)
    assert not response_df.empty

    # Verify required columns
    required_columns = ["ticker", "rank"]
    for col in required_columns:
        assert col in response_df.columns, (
            f"Column {col} not found. Available columns: "
            f"{response_df.columns.tolist()}"
        )
