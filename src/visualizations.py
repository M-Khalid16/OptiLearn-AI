
"""Plotly visualizations for OptiLearn AI scientific results."""

import plotly.graph_objects as go

from src.optical_simulator import FiberSimulationResult


def create_signal_comparison_figure(
    result: FiberSimulationResult,
) -> go.Figure:
    """Create a step-style comparison of transmitted and received signals."""
    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=result.time_ns,
            y=result.transmitted_signal_mw,
            mode="lines",
            line={"shape": "hv", "width": 2},
            name="Transmitted optical power",
            hovertemplate="Time: %{x:.4f} ns<br>Power: %{y:.6g} mW<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=result.time_ns,
            y=result.received_signal_mw,
            mode="lines",
            line={"shape": "hv", "width": 2},
            name="Received optical power",
            hovertemplate="Time: %{x:.4f} ns<br>Power: %{y:.6g} mW<extra></extra>",
        )
    )

    figure.update_layout(
        title="NRZ/OOK Optical Power Before and After Fiber Attenuation",
        xaxis_title="Time (ns)",
        yaxis_title="Optical Power (mW)",
        template="plotly_white",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        margin={"l": 70, "r": 30, "t": 90, "b": 70},
        hovermode="x unified",
    )
    figure.add_annotation(
        text="Attenuation-only model: pulse shape is preserved",
        xref="paper",
        yref="paper",
        x=0.01,
        y=0.98,
        showarrow=False,
        align="left",
        bgcolor="rgba(255, 255, 255, 0.85)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1,
    )

    return figure

"""Visualization module for future learning and simulation outputs."""

# TODO: Define interfaces for future educational visualizations.
# TODO: Add visualization implementation in a later milestone.

