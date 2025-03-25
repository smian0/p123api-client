"""Streamlit app for rank performance visualization."""

from datetime import date

import plotly.graph_objects as go


def plot_bucket_returns(
    bucket_returns: list[float],
    benchmark_return: float,
    start_date: date,
    end_date: date,
) -> go.Figure:
    """Plot bucket returns vs benchmark.

    Args:
        bucket_returns: List of bucket returns
        benchmark_return: Benchmark return
        start_date: Start date
        end_date: End date

    Returns:
        Plotly figure
    """
    # Create figure
    fig = go.Figure()

    # Add bucket returns bar chart
    fig.add_trace(
        go.Bar(
            x=list(range(1, len(bucket_returns) + 1)),
            y=bucket_returns,
            name="Bucket Returns",
        )
    )

    # Add benchmark line
    fig.add_trace(
        go.Scatter(
            x=list(range(1, len(bucket_returns) + 1)),
            y=[benchmark_return] * len(bucket_returns),
            mode="lines",
            line={"dash": "dot"},
            name=f"Benchmark Return ({benchmark_return:.2f})",
        )
    )

    # Update layout
    fig.update_layout(
        title="Bucket Returns vs Benchmark",
        xaxis_title="Bucket",
        yaxis_title="Return",
        yaxis_tickformat=".2f",
        showlegend=True,
        legend={"yanchor": "top", "y": 0.99, "xanchor": "left", "x": 0.01},
    )

    return fig
