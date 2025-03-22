import logging
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from p123api_client.common.settings import Settings
from p123api_client.rank_ranks.rank_ranks_api import RankRanksAPI
from p123api_client.strategy.strategy_api import StrategyAPI
from p123api_client.strategy_ranks.models import StrategyRanksInput
from p123api_client.strategy_ranks.strategy_ranks_service import StrategyRanksService

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Define cassette directory for better organization
CASSETTE_DIR = Path(__file__).parent / "cassettes"
CASSETTE_DIR.mkdir(exist_ok=True)


def plot_rank_time_series(df: pd.DataFrame, output_dir: str) -> None:
    """Plot rank time series for each ticker in the DataFrame."""
    # Ensure the DataFrame is sorted by date
    df = df.sort_values(by="dt")

    # Get unique tickers
    tickers = df["ticker"].unique()
    logger.info(f"Plotting rank time series for {len(tickers)} tickers")

    # Create a plot for each ticker
    for ticker in tickers:
        ticker_data = df[df["ticker"] == ticker]

        plt.figure(figsize=(10, 6))
        plt.plot(ticker_data["dt"], ticker_data["rank"], marker="o", linestyle="-")
        plt.title(f"Rank Time Series for {ticker}")
        plt.xlabel("Date")
        plt.ylabel("Rank")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()

        # Save the plot
        output_path = Path(output_dir) / f"{ticker}_rank_time_series.png"
        plt.savefig(str(output_path))
        plt.close()
        logger.info(f"Saved plot for {ticker} to {output_path}")


@pytest.fixture(scope="class")
def settings():
    settings = Settings(testing=True)
    if not settings.api_id or not settings.api_key:
        raise ValueError("API credentials not properly loaded from environment")
    return settings


@pytest.fixture(scope="class")
def strategy_api(settings):
    return StrategyAPI(api_id=settings.api_id, api_key=settings.api_key)


@pytest.fixture(scope="class")
def rank_ranks_api(settings):
    return RankRanksAPI(api_id=settings.api_id, api_key=settings.api_key)


@pytest.fixture(scope="class")
def service(strategy_api, rank_ranks_api):
    return StrategyRanksService(strategy_api, rank_ranks_api)


@pytest.fixture(scope="class")
def output_dir():
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    logger.info(f"Created output directory at {output_dir}")
    return output_dir


@pytest.mark.vcr()
def test_get_rank_results_for_strategy(service, output_dir):
    """Test getting rank results for a strategy."""
    logger.info("Starting test_get_rank_results_for_strategy")

    # Create input data with a single weekday
    input_data = StrategyRanksInput(
        strategy_id=1701030,  # Use a valid strategy ID
        from_date=date(2023, 1, 6),  # Friday
        to_date=date(2023, 1, 6),  # Same day to avoid weekend
    )
    logger.info(f"Created input data: {input_data}")

    # Get rank results
    logger.info("Fetching rank results...")
    rank_results = service.get_rank_results_for_strategy(input_data)
    logger.info(f"Received {len(rank_results.results)} rank results")

    # Basic assertions
    assert rank_results is not None
    assert len(rank_results.results) > 0

    # Convert results to DataFrame
    logger.info("Converting results to DataFrame")
    rank_results_df = pd.DataFrame(
        [
            {
                "dt": result.dt,
                "p123_uid": result.p123Uids[0] if result.p123Uids else None,
                "ticker": result.tickers[0] if result.tickers else None,
                "name": result.names[0] if result.names else None,
                "na_count": result.naCnt[0] if result.naCnt else None,
                "final_stmt": result.finalStmt[0] if result.finalStmt else None,
                "rank": result.ranks[0] if result.ranks else None,
                "nodes": result.nodes,
                "figi": result.figi[0] if result.figi else None,
                "MktCap": (
                    result.additionalData[0][0]
                    if result.additionalData and len(result.additionalData[0]) > 0
                    else None
                ),
                "Close_0": (
                    result.additionalData[0][1]
                    if result.additionalData and len(result.additionalData[0]) > 1
                    else None
                ),
            }
            for result in rank_results.results
        ]
    )
    logger.info(f"Created DataFrame with {len(rank_results_df)} rows")

    # Additional assertions on DataFrame
    assert len(rank_results_df) > 0
    required_columns = ["dt", "p123_uid", "ticker", "rank"]
    for col in required_columns:
        assert col in rank_results_df.columns
        assert not rank_results_df[col].isna().all()
        logger.info(f"Verified column {col} exists and has non-null values")

    # Save results to CSV
    output_path = output_dir / "rank_results.csv"
    rank_results_df.to_csv(output_path, index=False)
    logger.info(f"Saved results to {output_path}")

    # Plot rank time series
    plot_rank_time_series(rank_results_df, str(output_dir))
    logger.info("Completed plotting rank time series")
