"""Tests for cached rank performance API client."""

import logging
from datetime import date

import pandas as pd
import pytest

from p123api_client.models.enums import PitMethod, RankType, RebalFreq, Scope, TransType
from p123api_client.rank_performance.cached_rank_performance_api import CachedRankPerformanceAPI
from p123api_client.rank_performance.schemas import (
    Factor,
    RankingDefinition,
    RankPerformanceAPIRequest,
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="class")
def cached_rank_performance_api_cls(request):
    """Create CachedRankPerformanceAPI client for class-level tests."""
    api = CachedRankPerformanceAPI()
    request.cls.cached_rank_performance_api = api
    return api


@pytest.mark.usefixtures("cached_rank_performance_api_cls")
class TestCachedRankPerformanceAPI:
    """Test class for CachedRankPerformanceAPI."""

    @pytest.mark.vcr()
    def test_run_rank_performance_single_cached(self):
        """Test running rank performance for a single factor with caching."""
        # Create a test factor
        factor = Factor(
            rank_type=RankType.HIGHER, formula="Close(0)", description="Yesterday's Close Price"
        )

        ranking_def = RankingDefinition(
            factors=[factor], scope=Scope.UNIVERSE, description="Test rank update request"
        )

        request = RankPerformanceAPIRequest(
            ranking_definition=ranking_def,
            start_dt=date(2022, 1, 1),
            end_dt=date(2022, 12, 31),
            pit_method=PitMethod.PRELIM,
            precision=4,
            universe="SP500",
            trans_type=TransType.LONG,
            ranking_method=4,
            num_buckets=20,
            min_price=1.0,
            min_liquidity=100000.0,
            max_return=200.0,
            rebal_freq=RebalFreq.EVERY_WEEK,
            slippage=0.25,
            benchmark="SPY",
            output_type="ann",
        )

        # First call - should be a cache miss
        response_df1 = self.cached_rank_performance_api.run_rank_performance([request])

        # Verify the response
        assert response_df1 is not None
        assert isinstance(response_df1, pd.DataFrame)
        if not response_df1.empty:
            assert "benchmark_ann_ret" in response_df1.columns
            # Check for the presence of the split bucket_ann_ret columns
            for i in range(1, request.num_buckets + 1):
                assert f"bucket_ann_ret_{i}" in response_df1.columns

        # Second call - should be a cache hit
        response_df2 = self.cached_rank_performance_api.run_rank_performance([request])

        # Verify the second response matches the first
        assert response_df2 is not None
        assert isinstance(response_df2, pd.DataFrame)
        pd.testing.assert_frame_equal(response_df1, response_df2)

        # Third call with bypass_cache=True - should be a cache miss
        response_df3 = self.cached_rank_performance_api.run_rank_performance(
            [request], bypass_cache=True
        )

        # Verify the response
        assert response_df3 is not None
        assert isinstance(response_df3, pd.DataFrame)

    @pytest.mark.vcr()
    def test_cache_persistence(self):
        """Test that cache persists across API instances."""
        # Create a test factor
        factor = Factor(
            rank_type=RankType.HIGHER, formula="Close(0)", description="Cache Persistence Test"
        )

        ranking_def = RankingDefinition(
            factors=[factor], scope=Scope.UNIVERSE, description="Cache Persistence Test"
        )

        request = RankPerformanceAPIRequest(
            ranking_definition=ranking_def,
            start_dt=date(2022, 1, 1),
            end_dt=date(2022, 12, 31),
            universe="SP500",
        )

        # First call with first API instance
        api1 = CachedRankPerformanceAPI()
        response_df1 = api1.run_rank_performance([request])

        # Second call with a new API instance - should be a cache hit
        api2 = CachedRankPerformanceAPI()
        response_df2 = api2.run_rank_performance([request])

        # Verify the second response matches the first
        assert response_df2 is not None
        assert isinstance(response_df2, pd.DataFrame)
        pd.testing.assert_frame_equal(response_df1, response_df2)
