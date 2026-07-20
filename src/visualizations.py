"""Plotly visualizations for OptiLearn AI scientific results."""

import numpy as np
import plotly.graph_objects as go

from src.fso_simulator import FSOSimulationResult
from src.optical_simulator import FiberSimulationResult


def create_signal_comparison_figure(result: FiberSimulationResult) -> go.Figure:
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


def create_dispersion_comparison_figure(result: FiberSimulationResult) -> go.Figure:
    """Compare transmitted, attenuation-only, and dispersed received waveforms."""
    if result.dispersed_received_waveform_mw is None:
        raise ValueError("Dispersion waveform is required for the dispersion figure.")
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=result.time_ns,
            y=result.transmitted_signal_mw,
            mode="lines",
            line={"shape": "hv", "width": 2},
            name="Transmitted",
            hovertemplate="Time: %{x:.4f} ns<br>Power: %{y:.6g} mW<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=result.time_ns,
            y=result.received_signal_mw,
            mode="lines",
            line={"shape": "hv", "width": 2},
            name="Received: Attenuation Only",
            hovertemplate="Time: %{x:.4f} ns<br>Power: %{y:.6g} mW<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=result.time_ns,
            y=result.dispersed_received_waveform_mw,
            mode="lines",
            line={"width": 3},
            name="Received: Attenuation + Dispersion",
            hovertemplate="Time: %{x:.4f} ns<br>Power: %{y:.6g} mW<extra></extra>",
        )
    )
    figure.update_layout(
        title="Attenuation and Chromatic Dispersion",
        xaxis_title="Time (ns)",
        yaxis_title="Optical Power (mW)",
        template="plotly_white",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        margin={"l": 70, "r": 30, "t": 90, "b": 70},
        hovermode="x unified",
    )
    return figure


def create_fso_power_budget_figure(result: FSOSimulationResult) -> go.Figure:
    """Create an FSO optical-power progression chart in mW."""
    after_atmosphere = result.transmitted_power_mw * result.atmospheric_transmission_factor
    after_geometric = after_atmosphere * result.geometric_capture_fraction
    stages = [
        "Transmitted Power",
        "After Atmospheric Loss",
        "After Geometric Collection",
        "After Pointing Loss / Received Power",
    ]
    powers_mw = [
        result.transmitted_power_mw,
        after_atmosphere,
        after_geometric,
        result.received_power_mw,
    ]
    figure = go.Figure(
        go.Bar(
            x=stages,
            y=powers_mw,
            text=[f"{power:.6g} mW" for power in powers_mw],
            textposition="auto",
            hovertemplate="Stage: %{x}<br>Optical power: %{y:.6g} mW<extra></extra>",
        )
    )
    figure.update_layout(
        title="Deterministic FSO Power Budget",
        xaxis_title="Link-budget stage",
        yaxis_title="Optical Power (mW)",
        template="plotly_white",
        margin={"l": 70, "r": 30, "t": 80, "b": 90},
    )
    return figure


def create_fso_beam_profile_figure(result: FSOSimulationResult) -> go.Figure:
    """Create a normalized receiver-plane Gaussian beam profile figure."""
    radial_limit_m = max(
        3.0 * result.beam_radius_at_receiver_m,
        result.receiver_aperture_radius_m * 1.25,
        result.pointing_offset_m * 1.25,
    )
    radial_distance_m = np.linspace(0.0, radial_limit_m, 401)
    normalized_intensity = np.exp(
        -2.0 * radial_distance_m**2 / result.beam_radius_at_receiver_m**2
    )
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=radial_distance_m,
            y=normalized_intensity,
            mode="lines",
            name="Normalized Gaussian intensity",
            hovertemplate="Radius: %{x:.4f} m<br>Normalized intensity: %{y:.6g}<extra></extra>",
        )
    )
    figure.add_vline(
        x=result.receiver_aperture_radius_m,
        line_dash="dash",
        annotation_text="Receiver aperture radius",
        annotation_position="top right",
    )
    figure.add_vline(
        x=result.pointing_offset_m,
        line_dash="dot",
        annotation_text="Pointing offset",
        annotation_position="bottom right",
    )
    figure.update_layout(
        title="Receiver-Plane Gaussian Beam Profile",
        xaxis_title="Radial Distance at Receiver Plane (m)",
        yaxis_title="Normalized Intensity (dimensionless)",
        template="plotly_white",
        margin={"l": 70, "r": 30, "t": 80, "b": 70},
    )
    return figure
