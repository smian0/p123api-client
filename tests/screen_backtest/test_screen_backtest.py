import logging
import unittest
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from p123api_client.common.settings import Settings
from p123api_client.models.enums import (
    Currency,
    PitMethod,
    RebalFreq,
    RiskStatsPeriod,
    ScreenMethod,
    ScreenType,
    TransPrice,
)
from p123api_client.screen_backtest.models import BacktestRequest
from p123api_client.screen_backtest.schemas import (
    BacktestResponse,
    ScreenParams,
    ScreenRule,
)
from p123api_client.screen_backtest.screen_backtest_api import ScreenBacktestAPI

# Get logger instance
logger = logging.getLogger(__name__)


class TestScreenBacktest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Configure basic logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Set up paths
        cls.test_dir = Path(__file__).parent
        cls.test_data_dir = cls.test_dir / "test_input"

        # Initialize settings and API client
        settings = Settings(testing=True)
        cls.api_id = settings.api_id
        cls.api_key = settings.api_key

        if not cls.api_id or not cls.api_key:
            raise ValueError("API credentials not properly loaded from environment")

        cls.api = ScreenBacktestAPI(api_id=cls.api_id, api_key=cls.api_key)

        # Load test data
        try:
            cls.params_df = pd.read_csv(cls.test_data_dir / "test_screen_params.csv")
            cls.factors_df = pd.read_csv(cls.test_data_dir / "test_quickrank_factors.csv")
            cls.test_params = cls.params_df.iloc[0].to_dict()
            cls.factor = cls.factors_df.iloc[0]
        except Exception as e:
            logger.error(f"Failed to load test data: {e}")
            raise

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
    def test_run_backtest(self):
        """Test running a backtest."""
        try:
            # Create parameters using the correct format from the API documentation
            params = {
                "startDt": "2022-01-01",
                "endDt": "2022-12-31",
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

            # Run backtest directly using make_request
            logger.info("Running backtest...")
            # Call the API directly with the parameters
            result = self.api.make_request("screen_backtest", params, as_dataframe=True)

            # Verify response
            self.assertIsNotNone(result)

            # Verify stats
            self.assertIsNotNone(result.stats)
            
            # Verify portfolio stats
            self.assertIsNotNone(result.stats.portfolio_stats)
            self.assertIsInstance(result.stats.portfolio_stats.return_value, float)
            self.assertIsInstance(result.stats.portfolio_stats.alpha, float)
            self.assertIsInstance(result.stats.portfolio_stats.beta, float)
            self.assertIsInstance(result.stats.portfolio_stats.sharpe, float)
            self.assertIsInstance(result.stats.portfolio_stats.volatility, float)
            self.assertIsInstance(result.stats.portfolio_stats.max_drawdown, float)
            
            # Verify benchmark stats
            self.assertIsNotNone(result.stats.benchmark_stats)
            self.assertIsInstance(result.stats.benchmark_stats.return_value, float)
            self.assertIsInstance(result.stats.benchmark_stats.alpha, float)
            self.assertIsInstance(result.stats.benchmark_stats.beta, float)
            self.assertIsInstance(result.stats.benchmark_stats.sharpe, float)
            self.assertIsInstance(result.stats.benchmark_stats.volatility, float)
            self.assertIsInstance(result.stats.benchmark_stats.max_drawdown, float)

            # Verify chart data
            self.assertIsNotNone(result.chart)
            self.assertIsInstance(result.chart.dates, list)
            self.assertIsInstance(result.chart.screenReturns, list)
            self.assertIsInstance(result.chart.benchReturns, list)
            self.assertIsInstance(result.chart.turnoverPct, list)
            self.assertIsInstance(result.chart.positionCnt, list)

            # Verify results
            self.assertIsNotNone(result.results)
            self.assertIsInstance(result.results.columns, list)
            self.assertIsInstance(result.results.rows, list)
            self.assertIsInstance(result.results.average, list)
            self.assertIsInstance(result.results.upMarkets, list)
            self.assertIsInstance(result.results.downMarkets, list)

        except Exception as e:
            logger.error(f"Error running backtest: {e}", exc_info=True)
            raise

    def _create_backtest_request(self) -> BacktestRequest:
        """Helper method to create a backtest request from test data."""
        screen_params = ScreenParams(
            type=ScreenType.STOCK,
            universe="01 SmallCap Bulls Rank US",
            maxNumHoldings=25,
            method=ScreenMethod.LONG,
            currency=Currency.USD,
            benchmark="spy",
            ranking={"formula": "Close(0)", "lowerIsBetter": False},
            rules=[ScreenRule(formula="Close(0) > 0")],
        )

        request = BacktestRequest(
            startDt=date(2022, 1, 1),
            endDt=date(2022, 12, 31),
            pitMethod=PitMethod.PRELIM,
            precision=2,
            transPrice=TransPrice.NEXT_CLOSE,
            slippage=0.001,
            longWeight=100,
            rankTolerance=7,
            rebalFreq=RebalFreq.EVERY_WEEK,
            riskStatsPeriod=RiskStatsPeriod.MONTHLY,
            screen=screen_params,
        )

        return request
