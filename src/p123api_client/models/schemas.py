"""
Data models and schemas for the P123 API client.
"""

from datetime import date
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from .enums import RankType, Scope

T = TypeVar("T", bound=BaseModel)


class RankUpdateResponse(BaseModel):
    """Response from a rank update operation."""

    status: str = Field(..., description="Status of the rank update operation")
    message: str = Field(..., description="Detailed message about the operation result")


class FactorDetails(BaseModel):
    """Details about a ranking factor."""

    rank_type: RankType = Field(..., description="Type of ranking (Higher/Lower)")
    formula: str = Field(..., description="Formula used for ranking calculation")
    scope: Scope = Field(..., description="Scope of the ranking (Universe/Industry)")
    description: str | None = Field(None, description="Optional description of the factor")


class RankPerfRequest(BaseModel):
    """Request for rank performance calculation."""

    start_date: date = Field(..., description="Start date for performance calculation")
    end_date: date = Field(..., description="End date for performance calculation")
    factor: FactorDetails = Field(..., description="Factor details for performance calculation")


class MultiRankPerfRequest(BaseModel):
    """Request for multiple rank performance calculations."""

    factor: FactorDetails = Field(..., description="Base factor details")
    rank_performance_requests: list[RankPerfRequest] = Field(
        ..., description="List of rank performance requests"
    )


class Factor(BaseModel):
    """Factor model for ranking system."""

    formula: str
    rank_type: RankType
    name: str | None = None
    description: str | None = None

    def to_xml(self, default_scope: Scope) -> str:
        """Convert factor to XML format."""
        name = self.name or self.formula[:30]
        scope = default_scope
        return (
            '<StockFormula Weight="1" RankType="{rank_type}" Name="{name}" '
            'Description="{description}" Scope="{scope}">\n'
            "        <Formula>{formula}</Formula>\n"
            "    </StockFormula>"
        ).format(
            rank_type=self.rank_type.value,
            name=name,
            description=self.description or "",
            scope=scope.value,
            formula=self.formula,
        )


class RankUpdateRequest(BaseModel):
    """Request for updating a ranking system."""

    factors: list[Factor] = Field(..., description="List of ranking factors")
    scope: Scope = Field(..., description="Default scope of the ranking")
    description: str | None = Field(None, description="Optional description")
    category: str | None = Field(None, description="Optional category")

    def to_xml(self) -> str:
        """Convert the request to XML format supporting both single and multiple factors."""
        # Use the first factor's rank type as the system rank type
        system_rank_type = self.factors[0].rank_type.value

        # Generate XML for all factors
        factors_xml = "\n".join(factor.to_xml(default_scope=self.scope) for factor in self.factors)

        return f'<RankingSystem RankType="{system_rank_type}">\n{factors_xml}\n</RankingSystem>'

    @classmethod
    def from_xml_file(cls, file_path: str) -> str:
        """Load XML content from a file."""
        with open(file_path) as file:
            return file.read()

    def to_dict(self) -> dict:
        """Convert the request to a dictionary for JSON serialization"""
        return {
            "factors": [factor.dict() for factor in self.factors],
            "scope": self.scope.value if self.scope else None,
            "description": self.description,
            "category": self.category,
        }


def convert_enums_to_strings(data: dict[str, Any]) -> dict[str, Any]:
    """Convert enum values in a dictionary to their string representations."""
    return {k: v.value if isinstance(v, Enum) else v for k, v in data.items()}


# Sample data (updated)
sample_rank_update_request = RankUpdateRequest(
    factors=[Factor(rank_type=RankType.HIGHER, formula="Close(0)", description="Sample factor")],
    scope=Scope.UNIVERSE,
    description="Sample details for rank update",
)
