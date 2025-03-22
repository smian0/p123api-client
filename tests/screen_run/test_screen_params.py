"""Tests for screen run parameter validations and edge cases."""
import pytest
from datetime import date

from p123api_client.models.enums import ScreenType, ScreenMethod
from p123api_client.screen_run.schemas import (
    ScreenDefinition,
    ScreenRule,
    ScreenRankingDefinition,
    ScreenRankingSystemRef
)


class TestScreenParams:
    """Test case validations for screen run parameters."""
    
    def test_screen_type_validation(self):
        """Test validation of screen type."""
        # Valid stock type
        screen_def = ScreenDefinition(
            type=ScreenType.STOCK,
            universe="SP500",
            rules=["close > 100"]
        )
        assert screen_def.type == ScreenType.STOCK
        
        # Valid ETF type
        screen_def = ScreenDefinition(
            type=ScreenType.ETF,
            universe="ETFUniverse",
            rules=["aum > 100"]
        )
        assert screen_def.type == ScreenType.ETF
        
        # Default type (stock)
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"]
        )
        assert screen_def.type == ScreenType.STOCK

    def test_screen_rule_validation(self):
        """Test validation of screen rules."""
        # Single rule as string
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"]
        )
        assert len(screen_def.rules) == 1
        assert isinstance(screen_def.rules[0], ScreenRule)
        assert screen_def.rules[0].formula == "close > 100"
        
        # Multiple rules as strings
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100", "pe < 20"]
        )
        assert len(screen_def.rules) == 2
        assert all(isinstance(rule, ScreenRule) for rule in screen_def.rules)
        
        # Rule as dict
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=[{"formula": "close > 100", "type": "common"}]
        )
        assert len(screen_def.rules) == 1
        assert screen_def.rules[0].formula == "close > 100"
        assert screen_def.rules[0].type == "common"
        
        # Mixed rules
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=[
                "close > 100",
                {"formula": "pe < 20", "type": "long"},
                {"formula": "rsi > 70", "type": "short"}
            ]
        )
        assert len(screen_def.rules) == 3
        assert screen_def.rules[0].formula == "close > 100"
        assert screen_def.rules[0].type is None  # Default
        assert screen_def.rules[1].formula == "pe < 20"
        assert screen_def.rules[1].type == "long"
        assert screen_def.rules[2].formula == "rsi > 70"
        assert screen_def.rules[2].type == "short"

    def test_ranking_validation(self):
        """Test validation of ranking parameters."""
        # Ranking as formula dict
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"],
            ranking={"formula": "ROE", "lowerIsBetter": False}
        )
        assert isinstance(screen_def.ranking, ScreenRankingDefinition)
        assert screen_def.ranking.formula == "ROE"
        assert screen_def.ranking.lowerIsBetter is False
        
        # Ranking as system ID
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"],
            ranking=123
        )
        assert screen_def.ranking == 123
        
        # Ranking as system name
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"],
            ranking="My Ranking System"
        )
        assert screen_def.ranking == "My Ranking System"
        
        # Ranking as system reference
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"],
            ranking={"id": 123, "method": 2}
        )
        assert isinstance(screen_def.ranking, ScreenRankingSystemRef)
        assert screen_def.ranking.id == 123
        assert screen_def.ranking.method == 2

    def test_method_validation(self):
        """Test validation of screen method."""
        # Long method
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"],
            method=ScreenMethod.LONG
        )
        assert screen_def.method == ScreenMethod.LONG
        
        # Short method
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"],
            method=ScreenMethod.SHORT
        )
        assert screen_def.method == ScreenMethod.SHORT
        
        # Long/short method
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"],
            method=ScreenMethod.LONG_SHORT
        )
        assert screen_def.method == ScreenMethod.LONG_SHORT
        
        # Hedged method
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"],
            method=ScreenMethod.HEDGED
        )
        assert screen_def.method == ScreenMethod.HEDGED

    def test_max_results_validation(self):
        """Test validation of max results parameter."""
        # Valid max results
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"],
            maxResults=50
        )
        assert screen_def.maxResults == 50
        
        # Zero max results (should be valid)
        screen_def = ScreenDefinition(
            universe="SP500",
            rules=["close > 100"],
            maxResults=0
        )
        assert screen_def.maxResults == 0 