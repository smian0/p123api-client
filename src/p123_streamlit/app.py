import logging
import os
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables from the root directory
root_dir = Path(__file__).parent.parent.parent
env_path = root_dir / ".env"
load_dotenv(env_path)
logger.info("Loaded environment variables from %s", env_path)

from p123api_client.models.enums import PitMethod, RankType, RebalFreq, Scope, TransType
from p123api_client.models.schemas import Factor
from p123api_client.rank_performance.rank_performance_api import RankPerformanceAPI
from p123api_client.rank_performance.schemas import RankingDefinition, RankPerformanceAPIRequest
from p123api_client.screen_backtest.schemas import (
    BacktestRequest,
    Currency,
    RiskStatsPeriod,
    ScreenMethod,
    ScreenParams,
    ScreenRule,
    ScreenType,
    TransPrice,
)
from p123api_client.screen_backtest.screen_backtest_api import ScreenBacktestAPI

st.set_page_config(page_title="P123 Analysis Tools", layout="wide")

# Create tabs
tab1, tab2 = st.tabs(["Rank Performance", "Screen Backtest"])

# Common sidebar settings
st.sidebar.header("Configuration")

# Date Range Selection (common)
col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("Start Date", date(2022, 1, 1))
end_date = col2.date_input("End Date", date(2022, 12, 31))

# Check API credentials (common)
api_id = os.getenv("P123_API_ID")
api_key = os.getenv("P123_API_KEY")

if not api_id or not api_key:
    st.error("API credentials not found in .env file. Please check your .env file configuration.")
    st.code("""
    # Required format in .env file:
    P123_API_ID=your_api_id_here
    P123_API_KEY=your_api_key_here
    """)

# Rank Performance Tab
with tab1:
    st.title("Portfolio123 Rank Performance Tester")

    # Advanced Settings in Sidebar
    st.sidebar.subheader("Rank Performance Settings")
    pit_method = st.sidebar.selectbox(
        "PIT Method", options=[m.name for m in PitMethod], index=0, key="rank_pit"
    )
    trans_type = st.sidebar.selectbox(
        "Transaction Type", options=[t.name for t in TransType], index=0
    )
    rebal_freq = st.sidebar.selectbox(
        "Rebalance Frequency", options=[f.name for f in RebalFreq], index=0
    )

    # Performance Parameters
    with st.sidebar.expander("Performance Parameters"):
        min_holding_period = st.number_input(
            "Min Holding Period", value=1, min_value=1, key="rank_min_hold"
        )
        max_holding_period = st.number_input(
            "Max Holding Period", value=20, min_value=1, key="rank_max_hold"
        )
        commission = st.number_input(
            "Commission", value=0.001, format="%.3f", key="rank_commission"
        )
        slippage = st.number_input("Slippage", value=0.001, format="%.3f", key="rank_slippage")
        min_pos_size = st.number_input(
            "Min Position Size", value=0.01, format="%.2f", key="rank_min_pos"
        )
        max_pos_size = st.number_input(
            "Max Position Size", value=0.10, format="%.2f", key="rank_max_pos"
        )
        max_turnover = st.number_input(
            "Max Turnover", value=1.0, format="%.1f", key="rank_max_turnover"
        )
        max_positions = st.number_input(
            "Max Positions", value=100, min_value=1, key="rank_max_positions"
        )

    # Factor Input Method Selection
    input_method = st.radio("Choose input method:", ["Manual Input", "TSV Upload"])

    if input_method == "Manual Input":
        st.subheader("Factor Details")

        # Single/Multi Factor Selection
        factor_count = st.number_input("Number of factors", min_value=1, max_value=10, value=1)

        factors = []
        for i in range(factor_count):
            st.markdown(f"#### Factor {i + 1}")
            col1, col2 = st.columns(2)

            formula = col1.text_input(f"Formula #{i + 1}", value="Close(0)", key=f"formula_{i}")
            rank_type = col2.selectbox(
                f"Rank Type #{i + 1}", options=[rt.name for rt in RankType], key=f"rank_type_{i}"
            )

            if formula:
                factors.append(Factor(formula=formula, rank_type=RankType[rank_type], weight=1.0))

    else:
        st.subheader("Upload TSV File")
        uploaded_file = st.file_uploader("Choose a TSV file", type="tsv")

        if uploaded_file is not None:
            factors = []
            df = pd.read_csv(uploaded_file, sep="\t")
            for _, row in df.iterrows():
                factors.append(
                    Factor(
                        formula=row["formula"],
                        rank_type=RankType[row["rank_type"].upper()],
                        weight=1.0,
                    )
                )

    # Common Settings
    scope = st.sidebar.selectbox("Scope", options=[s.name for s in Scope], index=0)

    if st.button("Run Performance Test") and factors:
        try:
            # Create config from UI inputs
            config = {
                "rank_perf": {
                    "default_params": {
                        "pit_method": pit_method,
                        "trans_type": trans_type,
                        "rebal_freq": rebal_freq,
                        "min_holding_period": min_holding_period,
                        "max_holding_period": max_holding_period,
                        "commission": commission,
                        "slippage": slippage,
                        "min_pos_size": min_pos_size,
                        "max_pos_size": max_pos_size,
                        "max_turnover": max_turnover,
                        "max_positions": max_positions,
                    }
                }
            }

            # Create API client
            api = RankPerformanceAPI(config=config, api_id=api_id, api_key=api_key)

            # Create ranking definition
            ranking_def = RankingDefinition(
                factors=factors, scope=Scope[scope], description="Streamlit test"
            )

            # Create request
            request = RankPerformanceAPIRequest(
                ranking_definition=ranking_def,
                start_dt=start_date,
                end_dt=end_date,
                pit_method=PitMethod[pit_method],
            )

            with st.spinner("Running performance test..."):
                # Run performance test with request in a list
                result = api.run_rank_performance([request])

                # Try to extract returns data
                bucket_returns = None
                if isinstance(result, pd.DataFrame):
                    # Handle DataFrame response
                    bucket_cols = [
                        col for col in result.columns if col.startswith("bucket_ann_ret_")
                    ]
                    if bucket_cols:
                        bucket_cols.sort()  # Sort to ensure correct order
                        bucket_returns = result[bucket_cols].iloc[0].tolist()
                    elif "return" in result.columns:
                        bucket_returns = result["return"].tolist()
                    elif "returns" in result.columns:
                        bucket_returns = result["returns"].tolist()
                    elif "bucket_returns" in result.columns:
                        bucket_returns = result["bucket_returns"].tolist()
                elif isinstance(result, dict):
                    # Handle dictionary response
                    if "return" in result:
                        bucket_returns = result["return"]
                    elif "returns" in result:
                        bucket_returns = result["returns"]
                    elif "bucket_returns" in result:
                        bucket_returns = result["bucket_returns"]

                if bucket_returns:
                    # Display results
                    st.subheader("Performance Results")

                    # Get benchmark return
                    benchmark_return = (
                        result["benchmark_ann_ret"].iloc[0]
                        if "benchmark_ann_ret" in result.columns
                        else None
                    )

                    # Create bar chart of bucket returns with benchmark line
                    fig = go.Figure()

                    # Add bars
                    fig.add_trace(
                        go.Bar(
                            x=[f"Bucket {i + 1}" for i in range(len(bucket_returns))],
                            y=bucket_returns,
                            text=[f"{return_val:.2f}" for return_val in bucket_returns],
                            textposition="auto",
                            name="Bucket Returns",
                        )
                    )

                    # Add benchmark line if available
                    if benchmark_return is not None:
                        fig.add_trace(
                            go.Scatter(
                                x=[f"Bucket {i + 1}" for i in range(len(bucket_returns))],
                                y=[benchmark_return] * len(bucket_returns),
                                mode="lines",
                                line={"dash": "dot"},
                                name=f"Benchmark Return ({benchmark_return:.2f})",
                            )
                        )

                    fig.update_layout(
                        title="Bucket Returns",
                        xaxis_title="Buckets",
                        yaxis_title="Return",
                        yaxis_tickformat=".2f",
                        showlegend=True,
                        legend={
                            "yanchor": "top",
                            "y": 0.99,
                            "xanchor": "left",
                            "x": 0.01
                        },
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Display raw data in expandable section
                    with st.expander("Raw Data"):
                        st.write(result)
                else:
                    st.error(
                        "Could not find returns data in the response. "
                        "Please check the raw response above."
                    )

        except Exception as e:
            st.error(f"Error running performance test: {str(e)}")
            if "401" in str(e):
                st.error(
                    "Authentication failed. Please check your API credentials in the .env file."
                )

# Screen Backtest Tab
with tab2:
    st.title("Portfolio123 Screen Backtest")

    # Screen Settings
    st.sidebar.subheader("Screen Settings")
    screen_type = st.sidebar.selectbox("Screen Type", options=[t.name for t in ScreenType], index=0)
    universe = st.sidebar.text_input("Universe", value="01 SmallCap Bulls Rank US")
    benchmark = st.sidebar.text_input("Benchmark", value="spy")
    method = st.sidebar.selectbox("Method", options=[m.name for m in ScreenMethod], index=0)
    currency = st.sidebar.selectbox("Currency", options=[c.name for c in Currency], index=0)

    # Advanced Screen Parameters
    with st.sidebar.expander("Advanced Parameters"):
        precision = st.number_input(
            "Precision", value=2, min_value=2, max_value=4, key="screen_precision"
        )
        trans_price = st.selectbox(
            "Transaction Price",
            options=[t.name for t in TransPrice],
            index=0,
            key="screen_trans_price",
        )
        slippage = st.number_input("Slippage", value=0.001, format="%.3f", key="screen_slippage")
        long_weight = st.number_input(
            "Long Weight", value=100, min_value=0, max_value=100, key="screen_long_weight"
        )
        rank_tolerance = st.number_input(
            "Rank Tolerance", value=7, min_value=1, key="screen_rank_tolerance"
        )
        max_holdings = st.number_input(
            "Max Holdings", value=25, min_value=1, key="screen_max_holdings"
        )
        risk_stats_period = st.selectbox(
            "Risk Stats Period",
            options=[r.name for r in RiskStatsPeriod],
            index=0,
            key="screen_risk_period",
        )

    # Screen Rules Input
    st.subheader("Screen Rules")
    rules_text = st.text_area("Enter screen rules (one per line)", value="Close(0) > 0")
    rules = [ScreenRule(formula=rule.strip()) for rule in rules_text.split("\n") if rule.strip()]

    # Ranking Formula Input
    st.subheader("Ranking")
    ranking = st.text_input("Ranking Formula", value="Close(0)")

    if st.button("Run Screen Backtest"):
        try:
            logger.info("Creating screen backtest API client")
            api = ScreenBacktestAPI(api_id=api_id, api_key=api_key)

            logger.info("Creating screen parameters")
            screen_params = ScreenParams(
                type=ScreenType[screen_type],
                universe=universe,
                maxNumHoldings=max_holdings,
                method=ScreenMethod[method],
                currency=Currency[currency],
                benchmark=benchmark,
                ranking={"formula": ranking, "lowerIsBetter": False},
                rules=rules,
            )

            logger.info("Creating backtest request")
            request = BacktestRequest(
                startDt=start_date,
                endDt=end_date,
                pitMethod=PitMethod[pit_method],
                precision=precision,
                transPrice=TransPrice[trans_price],
                slippage=slippage,
                longWeight=long_weight,
                rankTolerance=rank_tolerance,
                rebalFreq=RebalFreq[rebal_freq],
                riskStatsPeriod=RiskStatsPeriod[risk_stats_period],
                screen=screen_params,
            )

            with st.spinner("Running screen backtest..."):
                logger.info("Running backtest with request: %s", request)
                result = api.run_backtest(request)
                logger.info("Received backtest response")

                # Display results
                st.subheader("Backtest Results")

                # Create figure with subplots
                fig = make_subplots(
                    rows=3,
                    cols=1,
                    subplot_titles=("Performance", "Turnover %", "Number of Positions"),
                    vertical_spacing=0.1,
                    specs=[
                        [{"secondary_y": True}],
                        [{"secondary_y": False}],
                        [{"secondary_y": False}],
                    ],
                )

                # Add performance traces
                fig.add_trace(
                    go.Scatter(
                        x=result.chart.dates,
                        y=result.chart.screenReturns,
                        name="Strategy",
                        line={"color": "red"},
                    ),
                    row=1,
                    col=1,
                )
                fig.add_trace(
                    go.Scatter(
                        x=result.chart.dates,
                        y=result.chart.benchReturns,
                        name="Benchmark",
                        line={"color": "blue"},
                    ),
                    row=1,
                    col=1,
                )

                # Add turnover trace
                fig.add_trace(
                    go.Bar(
                        x=result.chart.dates,
                        y=result.chart.turnoverPct,
                        name="Turnover %",
                        marker_color="lightblue",
                    ),
                    row=2,
                    col=1,
                )

                # Add positions trace
                fig.add_trace(
                    go.Bar(
                        x=result.chart.dates,
                        y=result.chart.positionCnt,
                        name="# Positions",
                        marker_color="lightgreen",
                    ),
                    row=3,
                    col=1,
                )

                # Update layout
                fig.update_layout(
                    height=800,
                    showlegend=True,
                    title_text="Screen Backtest Results",
                    title_x=0.5,
                    title_y=0.95,
                )

                # Update axes labels
                fig.update_xaxes(title_text="Date", row=3, col=1)
                fig.update_yaxes(title_text="Value", row=1, col=1)
                fig.update_yaxes(title_text="Turnover %", row=2, col=1)
                fig.update_yaxes(title_text="# Positions", row=3, col=1)

                # Display plot
                st.plotly_chart(fig, use_container_width=True)

                # Display statistics
                if hasattr(result, "stats"):
                    st.subheader("Statistics")

                    # Create DataFrame structure
                    stats_data = {
                        "": ["Screen", "S&P 500 (SPY:USA)"],  # Index names
                        "Total Return": [
                            f"{result.stats.port.total_return:.2f}%",
                            f"{result.stats.bench.total_return:.2f}%",
                        ],
                        "Annualized Return": [
                            f"{result.stats.port.annualized_return:.2f}%",
                            f"{result.stats.bench.annualized_return:.2f}%",
                        ],
                        "Max Drawdown": [
                            f"{result.stats.port.max_drawdown:.2f}%",
                            f"{result.stats.bench.max_drawdown:.2f}%",
                        ],
                        "Sharpe": [
                            f"{result.stats.port.sharpe_ratio:.2f}",
                            f"{result.stats.bench.sharpe_ratio:.2f}",
                        ],
                        "Sortino": [
                            f"{result.stats.port.sortino_ratio:.2f}",
                            f"{result.stats.bench.sortino_ratio:.2f}",
                        ],
                        "StdDev": [
                            f"{result.stats.port.standard_dev:.2f}%",
                            f"{result.stats.bench.standard_dev:.2f}%",
                        ],
                        "Correl/Bench": [f"{result.stats.correlation:.2f}", "-"],
                        "R-Squared": [f"{result.stats.r_squared:.2f}", "-"],
                        "Beta": [f"{result.stats.beta:.2f}", "-"],
                        "Alpha": [f"{result.stats.alpha:.2f}%", "-"],
                    }

                    # Create DataFrame
                    stats_df = pd.DataFrame(stats_data)
                    stats_df.set_index("", inplace=True)

                    # Display the DataFrame
                    st.dataframe(
                        stats_df,
                        use_container_width=True,
                        hide_index=False,
                        column_config={
                            "Total Return": st.column_config.NumberColumn(format="%.2f%%"),
                            "Annualized Return": st.column_config.NumberColumn(format="%.2f%%"),
                            "Max Drawdown": st.column_config.NumberColumn(format="%.2f%%"),
                            "Sharpe": st.column_config.NumberColumn(format="%.2f"),
                            "Sortino": st.column_config.NumberColumn(format="%.2f"),
                            "StdDev": st.column_config.NumberColumn(format="%.2f%%"),
                            "Correl/Bench": st.column_config.NumberColumn(format="%.2f"),
                            "R-Squared": st.column_config.NumberColumn(format="%.2f"),
                            "Beta": st.column_config.NumberColumn(format="%.2f"),
                            "Alpha": st.column_config.NumberColumn(format="%.2f%%"),
                        },
                    )

                # Display raw data in expandable section
                with st.expander("Raw Data"):
                    st.write(result)

        except Exception as e:
            st.error(f"Error running screen backtest: {str(e)}")
            if "401" in str(e):
                st.error(
                    "Authentication failed. Please check your API credentials in the .env file."
                )
