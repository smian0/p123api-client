"""Screen backtest models module."""
from __future__ import annotations

from datetime import date
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from ..models.enums import Currency, PitMethod, ScreenMethod, ScreenType
from .schemas import ScreenRule


class BacktestRequest(BaseModel):
    """Request model for screen backtest API."""

    screen_type: ScreenType = Field(..., description="Type of screen (stock/etf/fund)")
    screen_rules: List[ScreenRule] = Field(..., description="List of screen rules")
    start_date: date = Field(..., description="Start date for backtest")
    end_date: date = Field(..., description="End date for backtest")
    screen_method: ScreenMethod = Field(
        ScreenMethod.INTERSECTION, description="Screen method (intersection/union)"
    )
    pit_method: Optional[PitMethod] = Field(
        None, description="Point-in-time method (prelim/complete)"
    )
    currency: Optional[Currency] = Field(None, description="Currency for results")
    
    def to_api_params(self) -> dict[str, Any]:
        """Convert to API parameters."""
        params = {
            "screenType": self.screen_type.value,
            "screenMethod": self.screen_method.value,
            "startDate": self.start_date.isoformat(),
            "endDate": self.end_date.isoformat(),
        }
        
        # Add screen rules
        rules = [rule.formula for rule in self.screen_rules]
        params["screenRules"] = rules
        
        # Add optional parameters if provided
        if self.pit_method:
            params["pitMethod"] = self.pit_method.value
        if self.currency:
            params["currency"] = self.currency.value
            
        return params
