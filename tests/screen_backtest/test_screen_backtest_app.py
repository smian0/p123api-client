"""Test screen backtest app."""
from datetime import date

from p123api_client.models.enums import PitMethod
from p123api_client.screen_backtest.models import BacktestRequest
from p123api_client.screen_backtest.screen_backtest_app import ScreenBacktestApp

from ..base import BaseTest


class TestScreenBacktestApp(BaseTest):
    """Test screen backtest app."""

    def test_single_factor_screen_backtest(self):
        """Test single factor screen backtest."""
        app = ScreenBacktestApp()
        screen_params = {"factor": "pe_ratio"}
        request = BacktestRequest(
            screen_params=screen_params,
            start_dt=date(2020, 1, 1),
            end_dt=date(2020, 12, 31),
            rebal_freq=30,
            pit_method=PitMethod.PRELIM,
            currency="USD",
            trans_price=0.01,
            risk_stats_period=30,
        )
        result = app.run_backtest(request)
        self.assertIsNotNone(result)

    def test_multi_factor_screen_backtest_from_tsv(self):
        """Test multi factor screen backtest from TSV."""
        app = ScreenBacktestApp()
        screen_params = {"factors": ["pe_ratio", "pb_ratio"]}
        request = BacktestRequest(
            screen_params=screen_params,
            start_dt=date(2020, 1, 1),
            end_dt=date(2020, 12, 31),
            rebal_freq=30,
            pit_method=PitMethod.PRELIM,
            currency="USD",
            trans_price=0.01,
            risk_stats_period=30,
        )
        result = app.run_backtest(request)
        self.assertIsNotNone(result)
