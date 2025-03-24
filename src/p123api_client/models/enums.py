"""
Common enums used across the P123 API client.
"""

from enum import Enum


class RankType(str, Enum):
    """Type of ranking (Higher/Lower/Full)"""

    HIGHER = "Higher"
    LOWER = "Lower"
    FULL = "Full"


class Scope(str, Enum):
    """Scope of the ranking (Universe/Industry/Sector/Full)"""

    UNIVERSE = "Universe"
    SECTOR = "Sector"
    INDUSTRY = "Industry"
    FULL = "Full"


class PitMethod(str, Enum):
    """Point-in-time method for data"""

    PRELIM = "Prelim"
    COMPLETE = "Complete"


class TransType(str, Enum):
    """Position type for transactions (long/short)"""

    LONG = "long"
    SHORT = "short"


class RebalFreq(str, Enum):
    """Rebalancing frequency"""

    EVERY_WEEK = "Every Week"
    EVERY_2_WEEKS = "Every 2 Weeks"
    EVERY_3_WEEKS = "Every 3 Weeks"
    EVERY_4_WEEKS = "Every 4 Weeks"
    EVERY_MONTH = "Every 4 Weeks"


class RiskStatsPeriod(str, Enum):
    """Period for risk statistics calculation"""

    MONTHLY = "Monthly"
    WEEKLY = "Weekly"


class OutputFormat(str, Enum):
    """Output format for API responses"""

    CSV = "csv"
    JSON = "json"
    DATAFRAME = "dataframe"


class ScreenType(str, Enum):
    """Type of screen (stock/ETF/formula)"""

    STOCK = "stock"
    ETF = "etf"
    FORMULA = "formula"


class ScreenMethod(str, Enum):
    """Screen method for position types"""

    INTERSECTION = "intersection"
    UNION = "union"
    SCREEN = "screen"
    # Legacy values maintained for backward compatibility
    LONG = "long"
    SHORT = "short"
    LONG_SHORT = "long/short"
    HEDGED = "hedged"


class Currency(str, Enum):
    """Available currencies"""

    USD = "USD"
    CAD = "CAD"
    CHF = "CHF"
    EUR = "EUR"
    GBP = "GBP"
    NOK = "NOK"
    PLN = "PLN"
    SEK = "SEK"
    TRY = "TRY"


class TransPrice(int, Enum):
    """Transaction price timing types"""

    NEXT_OPEN = 1
    NEXT_CLOSE = 4
    NEXT_AVG_HI_LOW = 3


class OutputType(str, Enum):
    """Output type for performance metrics"""

    ANNUALIZED = "ann"  # Annualized returns
    CUMULATIVE = "cumm"  # Cumulative returns


class RankingMethod(int, Enum):
    """Method for calculating ranks"""

    NORMAL_DISTRIBUTION = 1  # Experimental
    PERCENTILE_NAS_NEGATIVE = 2  # Default
    PERCENTILE_NAS_NEUTRAL = 4


# Common universe values (but not enforced as enum since universes can be user-defined)
UNIVERSE_SP500 = "SP500"
UNIVERSE_SP1500 = "SP1500"
UNIVERSE_RUSSELL3000 = "Russell3000"
UNIVERSE_RUSSELL1000 = "Russell1000"
UNIVERSE_RUSSELL2000 = "Russell2000"
UNIVERSE_RUSSELL_MICRO = "RussellMicro"
UNIVERSE_DOW30 = "DOW30"
UNIVERSE_NASDAQ100 = "NASDAQ100"
