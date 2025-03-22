"""Screen backtest specific schemas."""
from __future__ import annotations

from collections.abc import Callable, Generator
from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator

from ..models.enums import (
    Currency,
    ScreenMethod,
    ScreenType,
)


class ScreenRule(BaseModel):
    """A single screen rule"""
    formula: str = Field(..., description="Rule formula")

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[[Any], ScreenRule], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> ScreenRule:
        if isinstance(v, str):
            return cls(formula=v)
        elif isinstance(v, dict):
            return cls(**v)
        elif isinstance(v, cls):
            return v
        raise ValueError(f"Invalid rule type: {type(v)}")


class RankingDefinition(BaseModel):
    """Ranking definition for a screen"""
    formula: str = Field(..., description="Formula to rank on")
    lowerIsBetter: bool = Field(False, description="Whether lower values are better")


class ScreenParams(BaseModel):
    """Screen parameters for backtest"""
    type: ScreenType = Field(..., description="Screen type (stock/etf)")
    universe: str = Field(..., description="Universe to screen")
    maxNumHoldings: int = Field(..., description="Maximum number of holdings")
    method: ScreenMethod = Field(..., description="Screen method (long/short/etc)")
    currency: Currency = Field(..., description="Currency for calculations")
    benchmark: str = Field(..., description="Benchmark symbol")
    ranking: dict[str, Any] | str = Field(..., description="Ranking parameters or system name")
    rules: list[ScreenRule] = Field(..., description="List of screen rules")

    @field_validator("rules", mode="before")
    @classmethod
    def validate_rules(cls, v: list[str | dict[str, Any] | ScreenRule]) -> list[ScreenRule]:
        if isinstance(v, list):
            return [
                ScreenRule(formula=r) if isinstance(r, str)
                else ScreenRule(**r) if isinstance(r, dict)
                else r
                for r in v
            ]
        return v


class BacktestRequest(BaseModel):
    """Backtest request model."""
    start_date: date
    end_date: date
    formula: str

    @classmethod
    def validate_dates(cls, v: date, data: dict[str, Any]) -> date:
        """Validate start and end dates."""
        if data.get("end_date") and v > data["end_date"]:
            raise ValueError("Start date must be before end date")
        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def check_date_range(cls, value: date) -> date:
        """Check if date is within valid range."""
        min_date = date(2000, 1, 1)
        max_date = date(2025, 12, 31)
        if value < min_date or value > max_date:
            raise ValueError(f"Date must be between {min_date} and {max_date}")
        return value


class PortfolioStats(BaseModel):
    """Portfolio statistics."""
    return_value: float = Field(default=0.0)
    alpha: float = Field(default=0.0)
    beta: float = Field(default=0.0)
    sharpe: float = Field(default=0.0)
    volatility: float = Field(default=0.0)
    max_drawdown: float = Field(default=0.0)


class BacktestStats(BaseModel):
    """Backtest statistics."""
    portfolio_stats: PortfolioStats = Field(default_factory=PortfolioStats)
    benchmark_stats: PortfolioStats = Field(default_factory=PortfolioStats)


class ChartData(BaseModel):
    """Time series data for charts"""
    dates: list[str] = Field(default_factory=list, description="Date strings")
    screenReturns: list[float] = Field(default_factory=list, description="Strategy returns")
    benchReturns: list[float] = Field(default_factory=list, description="Benchmark returns")
    turnoverPct: list[float] = Field(default_factory=list, description="Turnover percentages")
    positionCnt: list[int] = Field(default_factory=list, description="Position counts")


class BacktestResults(BaseModel):
    """Detailed backtest results"""
    columns: list[str] = Field(default_factory=list, description="Column names")
    rows: list[list[str | float | int]] = Field(default_factory=list, description="Data rows")
    average: list[float | None] = Field(default_factory=list, description="Average values")
    upMarkets: list[float | None] = Field(
        default_factory=list, description="Up market values"
    )
    downMarkets: list[float | None] = Field(
        default_factory=list, description="Down market values"
    )


class BacktestResponse(BaseModel):
    """Complete backtest response"""
    cost: int = Field(0, description="API cost")
    quotaRemaining: int = Field(0, description="Remaining API quota")
    stats: BacktestStats = Field(default_factory=BacktestStats, description="Backtest statistics")
    chart: ChartData = Field(default_factory=ChartData, description="Chart data")
    results: BacktestResults = Field(
        default_factory=BacktestResults, description="Detailed results"
    )
