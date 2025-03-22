from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from .general_info import GeneralInfo


class QuickStats(BaseModel):
    totalReturn: float
    benchReturn: float
    activeReturn: float
    annualizedReturn: float
    annualTurnover: float
    maxDrawdown: float
    benchMaxDrawdown: float
    overallWinners: int
    overallWinnersPct: float
    sharpeRatio: float
    benchCorrel: float


class Summary(BaseModel):
    generalInfo: GeneralInfo
    quickStats: QuickStats


class Holding(BaseModel):
    weight: float
    ticker: str
    name: str
    mkt_uid: int = Field(..., alias="mktUid")
    ret_pct: float = Field(..., alias="retPct")
    ret: float
    rank: float | None = None
    shares: float
    avg_share_cost: float = Field(..., alias="avgShareCost")
    curr_price: float = Field(..., alias="currPrice")
    value: float
    days_held: int = Field(..., alias="daysHeld")
    sector: str


class StrategyRequest(BaseModel):
    strategy_id: int = Field(..., description="ID of the strategy/book to retrieve")


class StrategyResponse(BaseModel):
    summary: Summary
    holdings: list[Holding]
    stats: dict[str, Any]
    trading: dict[str, Any]
    riskMeasurements: dict[str, Any]

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

    @property
    def general_info(self) -> GeneralInfo:
        """Extract general info from summary"""
        return self.summary.generalInfo

    @property
    def holdings_df(self) -> pd.DataFrame:
        """Convert holdings to DataFrame for easier analysis"""
        if not self.holdings:
            return pd.DataFrame()

        # Convert holdings list to DataFrame
        df = pd.DataFrame([holding.model_dump() for holding in self.holdings])

        # Rename columns to match API response
        column_mapping = {
            "mkt_uid": "mktUid",
            "ret_pct": "retPct",
            "avg_share_cost": "avgShareCost",
            "curr_price": "currPrice",
            "days_held": "daysHeld",
        }
        df = df.rename(columns=column_mapping)

        # Set index to ticker for easier lookup
        df.set_index("ticker", inplace=True)

        return df

    def save_full_response_as_csv(self, output_dir: Path) -> None:
        """Save the full response data as CSV files."""
        # Ensure the output directory exists
        output_dir.mkdir(exist_ok=True)

        # Save summary data
        summary_data = self.summary.model_dump()
        summary_df = pd.json_normalize(summary_data)
        summary_df.to_csv(output_dir / "summary.csv", index=False)

        # Save holdings data
        self.holdings_df.to_csv(output_dir / "holdings.csv")

        # Convert and save stats data
        stats_data = self.stats
        stats_df = pd.json_normalize(stats_data, sep="_")
        stats_df.to_csv(output_dir / "stats.csv", index=False)

        # Convert and save trading data
        trading_data = self.trading
        trading_df = pd.json_normalize(trading_data, sep="_")
        trading_df.to_csv(output_dir / "trading.csv", index=False)

        # Convert and save risk measurements data
        risk_measurements_data = self.riskMeasurements
        risk_measurements_df = pd.json_normalize(risk_measurements_data, sep="_")
        risk_measurements_df.to_csv(output_dir / "risk_measurements.csv", index=False)
        """Get portfolio weights by sector"""
        df = self.holdings_df
        if df.empty:
            return pd.Series()
        total_weight = df["weight"].sum()
        return df.groupby("sector")["weight"].sum() / total_weight

    def get_sector_weights(self) -> pd.Series:
        """Get portfolio weights by sector"""
        df = self.holdings_df
        if df.empty:
            return pd.Series(dtype=float)
        total_weight = df["weight"].sum()
        return df.groupby("sector")["weight"].sum() / total_weight

    def get_top_holdings(self, n: int = 50) -> pd.DataFrame:
        """Get top N holdings by weight"""
        df = self.holdings_df
        if df.empty:
            return pd.DataFrame()
        return df.nlargest(n, "weight")
