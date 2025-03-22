from datetime import date

from pydantic import BaseModel, Field

from p123api_client.rank_ranks.schemas import RankRanksResponse


class StrategyRanksInput(BaseModel):
    strategy_id: int = Field(..., description="ID of the strategy to retrieve ranks for")
    from_date: date = Field(..., description="Start date for the date range")
    to_date: date = Field(..., description="End date for the date range")


class StrategyRanksOutput(BaseModel):
    results: list[RankRanksResponse]
