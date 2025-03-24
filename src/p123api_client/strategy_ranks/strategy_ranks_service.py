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
    
    def __init__(self, strategy_api=None, rank_ranks_api=None):
        """Initialize the service.
        
        Args:
            strategy_api: Optional strategy API client.
            rank_ranks_api: Optional rank ranks API client.
        """
        self.strategy_api = strategy_api
        self.rank_ranks_api = rank_ranks_api

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
        rank_results_df = rank_ranks_api.get_ranks(request)
        
        # Convert DataFrame to RankRanksResponse
        from p123api_client.rank_ranks.schemas import RankRanksResponse
        
        # Create a RankRanksResponse object from the DataFrame
        rank_response = RankRanksResponse(
            dt=current_date,
            p123Uids=rank_results_df['p123_uid'].tolist() if 'p123_uid' in rank_results_df.columns else [],
            tickers=rank_results_df['ticker'].tolist() if 'ticker' in rank_results_df.columns else [],
            ranks=rank_results_df['rank'].tolist() if 'rank' in rank_results_df.columns else [],
            # Other fields can be None
            names=None,
            naCnt=None,
            finalStmt=None,
            nodes=None,
            additionalData=None,
            figi=None,
            data={"dataframe": rank_results_df}  # Store the original DataFrame in the data field
        )
        
        return StrategyRanksOutput(results=[rank_response])

    def get_rank_results_for_strategy(
        self, input_data: StrategyRanksInput, strategy_api: Any = None, rank_ranks_api: RankRanksAPI = None
    ) -> StrategyRanksOutput:
        """Get rank results for a strategy."""
        # Use provided APIs or fall back to instance variables
        strategy_api = strategy_api or self.strategy_api
        rank_ranks_api = rank_ranks_api or self.rank_ranks_api
        
        if not strategy_api or not rank_ranks_api:
            raise ValueError("Strategy API and Rank Ranks API must be provided either at initialization or method call")
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
        rank_results_df = rank_ranks_api.get_ranks(request)
        
        # Convert DataFrame to RankRanksResponse
        from p123api_client.rank_ranks.schemas import RankRanksResponse
        
        # Create a RankRanksResponse object from the DataFrame
        rank_response = RankRanksResponse(
            dt=input_data.from_date,
            p123Uids=rank_results_df['p123_uid'].tolist() if 'p123_uid' in rank_results_df.columns else [],
            tickers=rank_results_df['ticker'].tolist() if 'ticker' in rank_results_df.columns else [],
            ranks=rank_results_df['rank'].tolist() if 'rank' in rank_results_df.columns else [],
            # Other fields can be None
            names=None,
            naCnt=None,
            finalStmt=None,
            nodes=None,
            additionalData=None,
            figi=None,
            data={"dataframe": rank_results_df}  # Store the original DataFrame in the data field
        )
        
        return StrategyRanksOutput(results=[rank_response])

