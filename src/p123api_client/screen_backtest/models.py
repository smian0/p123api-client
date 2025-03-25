"""Screen backtest models module."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from ..models.enums import Currency, PitMethod, ScreenMethod, ScreenType
from .schemas import ScreenRule


class BacktestRequest(BaseModel):
    """Request model for screen backtest API."""

    # Screen definition fields
    screen_type: ScreenType | None = Field(
        ScreenType.STOCK, description="Type of screen (stock/etf/fund)"
    )
    screen_rules: list[ScreenRule] | None = Field(None, description="List of screen rules")
    universe: str | None = Field(None, description="Universe for backtest (e.g., SP500)")
    max_num_holdings: int | None = Field(None, description="Maximum number of holdings")
    benchmark: str | None = Field(None, description="Benchmark for comparison (e.g., SPY)")

    # Date fields
    start_dt: date | None = Field(None, description="Start date for backtest")
    end_dt: date | None = Field(None, description="End date for backtest")
    start_date: date | None = Field(None, description="Alternative start date field")
    end_date: date | None = Field(None, description="Alternative end date field")

    # Method fields
    screen_method: ScreenMethod | None = Field(
        ScreenMethod.INTERSECTION, description="Screen method (intersection/union)"
    )
    pit_method: PitMethod | None = Field(None, description="Point-in-time method (prelim/complete)")

    # Additional parameters
    currency: Currency | None = Field(None, description="Currency for results")
    rebal_freq: Any | None = Field(None, description="Rebalancing frequency")
    trans_price: Any | None = Field(None, description="Transaction price")
    risk_stats_period: Any | None = Field(None, description="Risk stats period")
    screen_params: Any | None = Field(None, description="Screen parameters")

    # Multi-factor fields
    factors_tsv_path: str | None = Field(None, description="Path to TSV file with factors")

    def to_api_params(self) -> dict[str, Any]:
        """Convert to API parameters."""
        params = {}

        # Handle date fields (prioritize start_dt/end_dt over start_date/end_date)
        start_date = self.start_dt or self.start_date
        end_date = self.end_dt or self.end_date

        if start_date:
            params["startDt"] = start_date.isoformat()
        if end_date:
            params["endDt"] = end_date.isoformat()

        # Add other top-level parameters
        if self.rebal_freq is not None:
            params["rebalFreq"] = self.rebal_freq
        if self.pit_method:
            params["pitMethod"] = self.pit_method.value
        if self.trans_price is not None:
            params["transPrice"] = self.trans_price
        if self.risk_stats_period is not None:
            params["riskStatsPeriod"] = self.risk_stats_period

        # Create the screen object
        screen = {}

        # Add screen type and method if provided
        if self.screen_type:
            screen["type"] = self.screen_type.value
        if self.screen_method:
            screen["method"] = "long"  # Default to long method

        # Add universe and benchmark if provided
        if self.universe:
            screen["universe"] = self.universe
        if self.max_num_holdings:
            screen["maxNumHoldings"] = self.max_num_holdings
        if self.benchmark:
            screen["benchmark"] = self.benchmark
        if self.currency:
            screen["currency"] = self.currency.value

        # Handle screen rules
        if self.screen_rules:
            screen["rules"] = [{"formula": rule.formula} for rule in self.screen_rules]

        # Handle factors TSV file if provided
        if self.factors_tsv_path:
            import pandas as pd

            # Read the TSV file and convert to the format expected by the API
            factors_df = pd.read_csv(self.factors_tsv_path, sep="\t")

            # Set the ranking to use ApiRankingSystem - this is what the API expects
            screen["ranking"] = "ApiRankingSystem"

            # Add a simple rule to ensure we get stocks
            if "rules" not in screen:
                screen["rules"] = []
            screen["rules"].append({"formula": "Close > 0"})

        # Add the screen object to params if it has content
        if screen:
            params["screen"] = screen

        return params
