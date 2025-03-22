"""Rank performance schemas."""
from datetime import date

from pydantic import BaseModel, Field

from p123api_client.models.enums import RankType, Scope


class Factor(BaseModel):
    """Factor model for ranking system."""

    formula: str
    rank_type: RankType
    name: str | None = None
    description: str | None = None


class RankingDefinition(BaseModel):
    """Ranking system definition."""

    factors: list[Factor]
    scope: Scope = Scope.FULL
    description: str | None = None


class RankPerformanceAPIRequest(BaseModel):
    """Request model for rank performance API."""

    start_dt: date
    end_dt: date | None = None
    xml_file_path: str | None = Field(
        None,
        description=(
            "Path to XML file containing ranking system. "
            "Required if ranking_definition not provided."
        ),
    )
    ranking_definition: RankingDefinition | None = Field(
        None,
        description=(
            "Ranking system definition. "
            "Required if xml_file_path not provided."
        ),
    )

    def to_api_params(self) -> dict:
        """Convert request to API parameters."""
        return {
            "rankingSystem": "ApiRankingSystem",  # For temporary systems
            "startDt": self.start_dt.isoformat(),
            "endDt": self.end_dt.isoformat() if self.end_dt else None,
        }


class RankPerformanceResponse(BaseModel):
    """Response model for rank performance API."""

    request: RankPerformanceAPIRequest
    response: dict
