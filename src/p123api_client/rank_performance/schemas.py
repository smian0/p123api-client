"""Rank performance schemas."""
from datetime import date

from pydantic import BaseModel, Field

from p123api_client.models.enums import PitMethod, RankType, RebalFreq, Scope, TransType


class Factor(BaseModel):
    """Factor model for ranking system."""

    formula: str
    rank_type: RankType
    name: str | None = None
    description: str | None = None


class RankingDefinition(BaseModel):
    """Ranking system definition."""

    factors: list[Factor]
    scope: Scope = Scope.UNIVERSE
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
    
    # Additional parameters for rank performance API
    pit_method: PitMethod | None = None
    precision: int | None = None
    universe: str | None = None
    trans_type: TransType | None = None
    ranking_method: int | None = None
    num_buckets: int = 20
    min_price: float | None = None
    min_liquidity: float | None = None
    max_return: float | None = None
    rebal_freq: RebalFreq | None = None
    slippage: float | None = None
    benchmark: str | None = None
    output_type: str | None = None

    def to_api_params(self) -> dict:
        """Convert request to API parameters."""
        params = {
            "rankingSystem": "ApiRankingSystem",  # For temporary systems
            "startDt": self.start_dt.isoformat(),
            "endDt": self.end_dt.isoformat() if self.end_dt else None,
        }
        
        # Add ranking definition parameters if provided
        if self.xml_file_path:
            with open(self.xml_file_path, "r") as f:
                xml_content = f.read()
            params["rankingSystemXml"] = xml_content
        
        # Add additional parameters if provided
        if self.pit_method is not None:
            params["pitMethod"] = self.pit_method.value
        if self.precision is not None:
            params["precision"] = self.precision
        if self.universe is not None:
            params["universe"] = self.universe
        if self.trans_type is not None:
            params["transType"] = self.trans_type.value
        if self.ranking_method is not None:
            params["rankingMethod"] = self.ranking_method
        if self.num_buckets is not None:
            params["numBuckets"] = self.num_buckets
        if self.min_price is not None:
            params["minPrice"] = self.min_price
        if self.min_liquidity is not None:
            params["minLiquidity"] = self.min_liquidity
        if self.max_return is not None:
            params["maxReturn"] = self.max_return
        if self.rebal_freq is not None:
            params["rebalFreq"] = self.rebal_freq.value
        if self.slippage is not None:
            params["slippage"] = self.slippage
        if self.benchmark is not None:
            params["benchmark"] = self.benchmark
        if self.output_type is not None:
            params["outputType"] = self.output_type
            
        return params


class RankPerformanceResponse(BaseModel):
    """Response model for rank performance API."""

    request: RankPerformanceAPIRequest
    response: dict
