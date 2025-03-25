"""Models for rank performance functionality."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel

from p123api_client.models.enums import PitMethod, RankStatus, RebalFreq, TransType
from p123api_client.screen_backtest.schemas import RankingDefinition, RunRankStepResponse


class RankResponse(BaseModel):
    """Response from rank performance endpoint."""

    data: dict[str, Any] | None = None
    description: str | None = None
    message: str | None = None
    status: RankStatus
    step_count: int
    step_data: dict[str, Any] | None = None
    steps: list[RunRankStepResponse]


class RankPerformanceAPIRequest:
    """Request model for rank performance API."""

    def __init__(
        self,
        start_dt: date,
        end_dt: date,
        pit_method: PitMethod,
        precision: int,
        universe: str,
        trans_type: TransType,
        ranking_method: int,
        num_buckets: int,
        min_price: float,
        min_liquidity: float,
        max_return: float,
        rebal_freq: RebalFreq,
        slippage: float,
        benchmark: str,
        output_type: str,
        ranking_definition: RankingDefinition | None = None,
        xml_file_path: str | None = None,
    ):
        """Initialize rank performance API request."""
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.pit_method = pit_method
        self.precision = precision
        self.universe = universe
        self.trans_type = trans_type
        self.ranking_method = ranking_method
        self.num_buckets = num_buckets
        self.min_price = min_price
        self.min_liquidity = min_liquidity
        self.max_return = max_return
        self.rebal_freq = rebal_freq
        self.slippage = slippage
        self.benchmark = benchmark
        self.output_type = output_type
        self.ranking_definition = ranking_definition
        self.xml_file_path = xml_file_path

    def to_api_params(self) -> dict[str, Any]:
        """Convert request to API parameters."""
        # Create mapping of parameter names
        param_mapping = {
            "start_dt": "startDt",
            "end_dt": "endDt",
            "pit_method": "pitMethod",
            "precision": "precision",
            "universe": "universe",
            "trans_type": "transType",
            "ranking_method": "rankingMethod",
            "num_buckets": "numBuckets",
            "min_price": "minPrice",
            "min_liquidity": "minLiquidity",
            "max_return": "maxReturn",
            "rebal_freq": "rebalFreq",
            "slippage": "slippage",
            "benchmark": "benchmark",
            "output_type": "outputType",
        }

        # Convert parameter names using mapping
        params = {}
        for old_name, new_name in param_mapping.items():
            value = getattr(self, old_name)
            if hasattr(value, "value"):
                value = value.value
            elif isinstance(value, date):
                value = value.strftime("%Y-%m-%d")
            params[new_name] = value

        return params


class RankPerformanceRequest(BaseModel):
    """Request for rank performance endpoint."""

    ranking_definition: str | None = None
    xml_file_path: str | None = None

    @property
    def get_rank_formula(self) -> dict[str, Any]:
        """Get rank formula from XML file or ranking definition."""
        if self.xml_file_path:
            # Read XML file
            with open(self.xml_file_path) as f:
                return {"data": f.read(), "format": "xml"}
        elif self.ranking_definition:
            return {"data": self.ranking_definition, "format": "text"}
        else:
            raise ValueError("Must provide either xml_file_path or ranking_definition")
