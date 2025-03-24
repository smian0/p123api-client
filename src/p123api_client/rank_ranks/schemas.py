"""Rank ranks API schemas."""
from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator

from ..models.enums import Currency, PitMethod, RankingMethod


class RankRanksRequest(BaseModel):
    """Request schema for rank_ranks API endpoint"""

    ranking_system: str = Field(default="ApiRankingSystem", description="Ranking system name or ID")
    as_of_dt: date = Field(
        ..., description="As of date (will use last trading day if non-trading day)"
    )
    universe: str = Field(..., description="Universe name")
    pit_method: PitMethod = Field(default=PitMethod.PRELIM)
    precision: int = Field(default=4, ge=2, le=4, description="Precision level (2-4)")
    ranking_method: RankingMethod = Field(
        default=RankingMethod.PERCENTILE_NAS_NEGATIVE, description="Method for calculating ranks"
    )
    tickers: str | None = Field(None, description="Comma-separated list of tickers to filter")
    include_names: bool = Field(default=False, description="Include company names in response")
    include_na_cnt: bool = Field(default=False, description="Include NA count in response")
    include_final_stmt: bool = Field(
        default=False, description="Include final statement flag in response"
    )
    node_details: str | None = Field(None, description="composite or factor")
    currency: Currency = Field(default=Currency.USD, description="Currency for financial data")
    additional_data: list[str] | None = Field(
        None, description="List of additional formulas to calculate"
    )

    @field_validator("node_details")
    @classmethod
    def validate_node_details(cls, v: str | None) -> str | None:
        if v is not None and v not in ["composite", "factor"]:
            raise ValueError("node_details must be either 'composite' or 'factor'")
        return v


class RankRanksResponse(BaseModel):
    """Response schema for rank_ranks API endpoint"""

    dt: date = Field(..., description="Response date")
    p123Uids: list[int] = Field(..., description="List of P123 unique identifiers")
    tickers: list[str] = Field(..., description="List of security tickers")
    names: list[str] | None = Field(None, description="List of company names")
    naCnt: list[int] | None = Field(None, description="List of NA counts")
    finalStmt: list[bool] | None = Field(None, description="List of final statement flags")
    ranks: list[float] = Field(..., description="List of rank values")
    nodes: dict | None = Field(None, description="Node details for composite or factor ranks")
    additionalData: list[list[float]] | None = Field(
        None, description="Additional formula results"
    )
    figi: list[str] | None = Field(None, description="List of FIGI identifiers")
    data: dict[str, Any] | None = None
    step_count: int = 0
    step_data: dict[str, Any] | None = None


def convert_to_pivot(data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Convert rank ranks data to pivot format.

    Args:
        data: List of rank data dictionaries

    Returns:
        Dictionary with date keys and nested symbol/value dictionaries
    """
    result: dict[str, dict[str, Any]] = {}
    for row in data:
        date = row.get("date")
        symbol = row.get("symbol")
        value = row.get("value")
        if date and symbol:
            if date not in result:
                result[date] = {}
            result[date][symbol] = value
    return result


# Sample request for testing
sample_rank_ranks_request = RankRanksRequest(
    ranking_system="ApiRankingSystem",  # Using a built-in ranking system that should exist in all P123 accounts
    as_of_dt=date(2023, 1, 6),
    universe="SP500",
    pit_method=PitMethod.PRELIM,
    precision=4,
    ranking_method=RankingMethod.PERCENTILE_NAS_NEGATIVE,
    tickers="AAPL,MSFT,GOOGL",
    include_names=True,
    include_na_cnt=True,
    include_final_stmt=True,
    node_details="factor",
    additional_data=["Close(0)", "mktcap"],
)
