"""Screen run specific schemas."""
from __future__ import annotations

from collections.abc import Callable, Generator
from datetime import date
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from ..models.enums import (
    Currency,
    PitMethod,
    ScreenMethod,
    ScreenType,
)


class ScreenRule(BaseModel):
    """A single screen rule"""
    formula: str = Field(..., description="Rule formula (500 chars max)")
    type: Optional[str] = Field(None, description="Rule type (common, long, short, hedge)")

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


class ScreenRankingDefinition(BaseModel):
    """Quick rank formula for screen ranking"""
    formula: str = Field(..., description="Quick rank formula")
    lowerIsBetter: bool = Field(False, description="Lower is better")


class ScreenRankingSystemRef(BaseModel):
    """Reference to an existing ranking system by ID or name"""
    id: Optional[int] = Field(None, description="Ranking system ID")
    name: Optional[str] = Field(None, description="Ranking system name")
    method: Optional[int] = Field(None, description="Ranking method")


class ScreenDefinition(BaseModel):
    """Screen definition parameters"""
    type: ScreenType = Field(ScreenType.STOCK, description="Type of screen (stock/etf)")
    universe: str = Field(..., description="Universe to screen")
    rules: List[Union[str, Dict[str, Any], ScreenRule]] = Field(
        ..., description="List of screen rules"
    )
    ranking: Optional[Union[ScreenRankingDefinition, ScreenRankingSystemRef, str, int]] = Field(
        None, description="Ranking definition, system ID, or system name"
    )
    maxResults: Optional[int] = Field(None, description="Maximum results to return")
    method: Optional[ScreenMethod] = Field(None, description="Screen method (long/short/etc)")

    @field_validator("rules", mode="before")
    @classmethod
    def validate_rules(cls, v: List[Union[str, Dict[str, Any], ScreenRule]]) -> List[ScreenRule]:
        if isinstance(v, list):
            return [
                ScreenRule(formula=r) if isinstance(r, str)
                else ScreenRule(**r) if isinstance(r, dict)
                else r
                for r in v
            ]
        return v

    @field_validator("ranking", mode="before")
    @classmethod
    def validate_ranking(cls, v: Any) -> Union[ScreenRankingDefinition, ScreenRankingSystemRef, str, int]:
        if isinstance(v, (str, int)):
            return v
        elif isinstance(v, dict):
            if "formula" in v:
                return ScreenRankingDefinition(**v)
            else:
                return ScreenRankingSystemRef(**v)
        return v


class ScreenRunRequest(BaseModel):
    """Screen run request model."""
    screen: ScreenDefinition = Field(..., description="Screen definition")
    asOfDt: Optional[date] = Field(None, description="As of date (defaults to today)")
    endDt: Optional[date] = Field(None, description="End date for historical screening")
    vendor: Optional[str] = Field(None, description="Data vendor")
    pitMethod: Optional[PitMethod] = Field(None, description="Point-in-time method")
    precision: Optional[int] = Field(None, description="Result precision")

    @field_validator("asOfDt", "endDt")
    @classmethod
    def check_date_range(cls, value: Optional[date]) -> Optional[date]:
        """Check if date is within valid range."""
        if value is None:
            return None
            
        min_date = date(2000, 1, 1)
        max_date = date(2025, 12, 31)
        if value < min_date or value > max_date:
            raise ValueError(f"Date must be between {min_date} and {max_date}")
        return value


class ScreenRunResponse(BaseModel):
    """Screen run response model."""
    cost: int = Field(0, description="API cost")
    quotaRemaining: int = Field(0, description="Remaining API quota")
    columns: List[str] = Field(default_factory=list, description="Column names")
    rows: List[List[Any]] = Field(default_factory=list, description="Data rows")

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert rows to a list of dictionaries using column names as keys."""
        return [
            {col: value for col, value in zip(self.columns, row)}
            for row in self.rows
        ] 