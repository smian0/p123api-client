from pydantic import BaseModel, Field


class GeneralInfo(BaseModel):
    name: str
    mkt_val: float | None = None  # Make mkt_val optional
    cash: float
    universe: str  # Add this line if universe is part of GeneralInfo
    ranking_system: str = Field(alias="rankingSystem")  # Add ranking system field with alias
    rankingSystemId: int | None = Field(None, description="The ID of the ranking system")
