"""Tests for rank performance API client."""

import csv
import logging
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from p123api_client.common.settings import Settings
from p123api_client.models.enums import PitMethod, RankType, RebalFreq, Scope, TransType
from p123api_client.models.schemas import Factor
from p123api_client.rank_performance.rank_performance_api import RankPerformanceAPI
from p123api_client.rank_performance.schemas import (
    RankingDefinition,
    RankPerformanceAPIRequest,
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="class")
def rank_performance_api_cls(request, rank_perf_config):
    """Create RankPerformanceAPI client for class-level tests."""
    settings = Settings(testing=True)
    api = RankPerformanceAPI(
        config=rank_perf_config, api_id=settings.api_id, api_key=settings.api_key
    )
    request.cls.rank_performance_api = api
    return api


@pytest.mark.usefixtures("rank_performance_api_cls")
class TestRankPerformanceAPI:
    """Test rank performance API."""

    @classmethod
    def setup_class(cls):
        """Set up test class."""
        settings = Settings(testing=True)  # Enable testing mode
        cls.api_id = settings.api_id
        cls.api_key = settings.api_key

        if not cls.api_id or not cls.api_key:
            raise ValueError("API credentials not properly loaded from environment")

        # Set up test data directory
        cls.test_data_dir = Path(__file__).parent / "test_input"

    def _read_factors_from_tsv(self, tsv_file_path: str) -> list[RankPerformanceAPIRequest]:
        """Helper method to read factors from a TSV file for testing."""
        logger.info(f"Reading test factors from {tsv_file_path}")
        try:
            requests = []
            with open(tsv_file_path) as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    factor = Factor(
                        rank_type=RankType[row["rank_type"].upper()],
                        formula=row["formula"],
                        description=row.get("description"),
                        name=row.get("name", row["formula"][:30]),
                    )

                    ranking_def = RankingDefinition(
                        factors=[factor],
                        scope=Scope[row["scope"].upper()],
                        description=row.get("description"),
                        category=row.get("category"),
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
                    requests.append(request)

            logger.info(f"Successfully read {len(requests)} test factors")
            return requests
        except Exception as e:
            logger.error(f"Failed to read test factors from {tsv_file_path}: {str(e)}")
            logger.debug("Error details:", exc_info=True)
            raise

    @pytest.mark.vcr()
    def test_run_rank_performance_single(self):
        """Test running rank performance for a single factor."""
        # Create a test factor
        factor = Factor(
            rank_type=RankType.HIGHER, formula="Close(0)", description="Yesterday's Close Price"
        )

        ranking_def = RankingDefinition(
            factors=[factor], scope=Scope.UNIVERSE, description="Test rank update request"
        )

        request = RankPerformanceAPIRequest(
            ranking_definition=ranking_def,  # This will be used by _update_rank
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

        # Call the run_rank_performance method
        response_df = self.rank_performance_api.run_rank_performance([request])

        # Verify the response
        assert response_df is not None
        assert isinstance(response_df, pd.DataFrame)
        if not response_df.empty:
            assert "benchmark_ann_ret" in response_df.columns
            # Check for the presence of the split bucket_ann_ret columns
            for i in range(1, request.num_buckets + 1):
                assert f"bucket_ann_ret_{i}" in response_df.columns
        else:
            pytest.fail("The response DataFrame is empty.")

    @pytest.mark.vcr()
    def test_run_rank_performance_from_xml(self):
        """Test running rank performance from an XML file."""
        xml_file_path = (
            Path(__file__).parent / "test_input" / "ranking_system_core_combination_v2.xml"
        )

        # Verify the XML file exists
        if not xml_file_path.exists():
            pytest.skip(f"XML file not found: {xml_file_path}")

        request = RankPerformanceAPIRequest(
            xml_file_path=str(xml_file_path),  # This will be used by _update_rank
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

        # Call the run_rank_performance method
        response_df = self.rank_performance_api.run_rank_performance([request])

        # Verify the response
        assert response_df is not None
        assert isinstance(response_df, pd.DataFrame)
        if not response_df.empty:
            assert "benchmark_ann_ret" in response_df.columns
            # Check for the presence of the split bucket_ann_ret columns
            for i in range(1, request.num_buckets + 1):
                assert f"bucket_ann_ret_{i}" in response_df.columns
        else:
            pytest.fail("The response DataFrame is empty.")

    @pytest.mark.vcr()
    def test_run_rank_performance_multiple(self):
        """Test running rank performance with multiple factors."""
        factors_tsv_path = Path(__file__).parent / "test_input" / "test_factors.tsv"

        # Read factors from TSV file and create requests
        requests = self._read_factors_from_tsv(str(factors_tsv_path))

        # Run rank performance tests
        response_df = self.rank_performance_api.run_rank_performance(requests)

        # Verify the response
        assert response_df is not None
        assert isinstance(response_df, pd.DataFrame)
        if not response_df.empty:
            assert "benchmark_ann_ret" in response_df.columns
            # Check for the presence of the split bucket_ann_ret columns
            for i in range(1, requests[0].num_buckets + 1):
                assert f"bucket_ann_ret_{i}" in response_df.columns
        else:
            pytest.fail("The response DataFrame is empty.")
