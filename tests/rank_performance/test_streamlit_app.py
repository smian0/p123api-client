"""Test streamlit app."""

from datetime import date

import plotly.graph_objects as go

from p123api_client.rank_performance.streamlit_app import plot_bucket_returns


def test_plot_bucket_returns():
    """Test plotting bucket returns."""
    # Test data
    bucket_returns = [0.1, 0.2, 0.3, 0.4, 0.5]
    benchmark_return = 0.25
    start_date = date(2020, 1, 1)
    end_date = date(2020, 12, 31)

    # Create figure
    fig = plot_bucket_returns(bucket_returns, benchmark_return, start_date, end_date)

    # Verify figure properties
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2  # Bar chart and benchmark line

    # Verify bar chart properties
    bar_trace = fig.data[0]
    assert isinstance(bar_trace, go.Bar)
    assert len(bar_trace.y) == len(bucket_returns)
    assert bar_trace.name == "Bucket Returns"

    # Verify benchmark line properties
    line_trace = fig.data[1]
    assert isinstance(line_trace, go.Scatter)
    assert len(line_trace.y) == len(bucket_returns)
    assert line_trace.mode == "lines"
    assert line_trace.line.dash == "dot"
    assert line_trace.name == f"Benchmark Return ({benchmark_return:.2f})"

    # Verify layout properties
    layout = fig.layout
    assert layout.title.text == "Bucket Returns vs Benchmark"
    assert layout.xaxis.title.text == "Bucket"
    assert layout.yaxis.title.text == "Return"
    assert layout.yaxis.tickformat == ".2f"
    assert layout.showlegend is True
    assert layout.legend.yanchor == "top"
    assert layout.legend.y == 0.99
    assert layout.legend.xanchor == "left"
    assert layout.legend.x == 0.01
