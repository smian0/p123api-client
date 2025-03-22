"""Strategy ranks service module."""
from datetime import date
from typing import Any

from p123api_client.models.enums import OutputFormat, PitMethod, RankType, Scope
from p123api_client.rank_ranks.rank_ranks_api import RankRanksAPI
from p123api_client.rank_ranks.schemas import RankRanksRequest
from p123api_client.strategy.schemas import StrategyResponse

from .models import StrategyRanksInput, StrategyRanksOutput


class StrategyRanksService:
    """Service for getting rank results for a strategy."""

    def get_rank_results(
        self,
        strategy_response: StrategyResponse,
        rank_ranks_api: RankRanksAPI,
        current_date: date,
    ) -> StrategyRanksOutput:
        """Get rank results for a strategy."""
        # Create request for rank ranks API
        request = RankRanksRequest(
            ranking_system=(
                strategy_response.summary.generalInfo.ranking_system
            ),
            as_of_dt=current_date,
            universe=(
                strategy_response.summary.generalInfo.universe
            ),
            pit_method=PitMethod.PRELIM,
            precision=4,
            scope=Scope.FULL,
            rank_type=RankType.FULL,
            output_format=OutputFormat.CSV,
        )

        # Get rank results
        rank_results = rank_ranks_api.get_ranks(request)

        return StrategyRanksOutput(results=[rank_results])

    def get_rank_results_for_strategy(
        self, input_data: StrategyRanksInput, strategy_api: Any, rank_ranks_api: RankRanksAPI
    ) -> StrategyRanksOutput:
        """Get rank results for a strategy."""
        # Get strategy response
        strategy_response = strategy_api.get_strategy(input_data.strategy_id)

        # Create request for rank ranks API
        request = RankRanksRequest(
            ranking_system=(
                strategy_response.summary.generalInfo.ranking_system
            ),
            as_of_dt=input_data.from_date,
            universe=strategy_response.summary.generalInfo.universe,
            pit_method=PitMethod.PRELIM,
            precision=4,
            scope=Scope.FULL,
            rank_type=RankType.FULL,
            output_format=OutputFormat.CSV,
        )

        # Get rank results
        rank_results = rank_ranks_api.get_ranks(request)

        return StrategyRanksOutput(results=[rank_results])

