import logging
import unittest
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from p123api_client.common.settings import Settings
from p123api_client.screen_backtest.schemas import (
    BacktestRequest,
    BacktestResponse,
    Currency,
    PitMethod,
    RebalFreq,
    RiskStatsPeriod,
    ScreenMethod,
    ScreenParams,
    ScreenRule,
    ScreenType,
    TransPrice,
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
            # Create backtest request
            request = BacktestRequest(
                screen_params=ScreenParams(
                    screen_type=ScreenType.FORMULA,
                    screen_method=ScreenMethod.SCREEN,
                    screen_rules=[
                        ScreenRule(
                            formula="MktCap > 1000",
                            description="Market Cap > $1B"
                        )
                    ],
                ),
                start_dt=date(2022, 1, 1),
                end_dt=date(2022, 12, 31),
                rebal_freq=RebalFreq.MONTHLY,
                pit_method=PitMethod.PRELIM,
                currency=Currency.USD,
                trans_price=TransPrice.CLOSE,
                risk_stats_period=RiskStatsPeriod.MONTHLY,
            )

            # Run backtest
            logger.info("Running backtest...")
            response_dict = self.api.make_request(
                "screen_backtest", request.model_dump(), as_dataframe=True
            )
            result = BacktestResponse(**response_dict)

            # Verify response
            self.assertIsNotNone(result)

            # Verify stats
            self.assertIsNotNone(result.stats)

            # Verify stats
            self.assertIsNotNone(result.stats)
            self.assertGreaterEqual(result.stats.samples, 0)
            self.assertIsInstance(result.stats.correlation, float)
            self.assertIsInstance(result.stats.r_squared, float)
            self.assertIsInstance(result.stats.beta, float)
            self.assertIsInstance(result.stats.alpha, float)

            # Verify portfolio stats
            self.assertIsNotNone(result.stats.port)
            self.assertIsInstance(result.stats.port.total_return, float)
            self.assertIsInstance(result.stats.port.annualized_return, float)
            self.assertIsInstance(result.stats.port.max_drawdown, float)
            self.assertIsInstance(result.stats.port.standard_dev, float)
            self.assertIsInstance(result.stats.port.sharpe_ratio, float)
            self.assertIsInstance(result.stats.port.sortino_ratio, float)

            # Verify benchmark stats
            self.assertIsNotNone(result.stats.bench)
            self.assertIsInstance(result.stats.bench.total_return, float)
            self.assertIsInstance(result.stats.bench.annualized_return, float)
            self.assertIsInstance(result.stats.bench.max_drawdown, float)
            self.assertIsInstance(result.stats.bench.standard_dev, float)
            self.assertIsInstance(result.stats.bench.sharpe_ratio, float)
            self.assertIsInstance(result.stats.bench.sortino_ratio, float)

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
