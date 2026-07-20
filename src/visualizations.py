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


def _circle(radius_um: float, points: int = 240) -> tuple[np.ndarray, np.ndarray]:
    theta = np.linspace(0, 2 * np.pi, points)
    return radius_um * np.cos(theta), radius_um * np.sin(theta)


def create_lp_mode_cross_section_figure(x_m, y_m, intensity, core_radius_m, mode_label, show_cladding=True) -> go.Figure:
    """Create a normalized LP-mode intensity cross-section."""
    figure = go.Figure(go.Heatmap(x=x_m[0] * 1e6, y=y_m[:, 0] * 1e6, z=np.maximum(intensity, 0), colorscale="Viridis", colorbar={"title": "Normalized intensity"}, hovertemplate="x=%{x:.3f} µm<br>y=%{y:.3f} µm<br>I=%{z:.4f}<extra></extra>"))
    cx, cy = _circle(core_radius_m * 1e6)
    figure.add_trace(go.Scatter(x=cx, y=cy, mode="lines", name="Core boundary", line={"color": "white", "width": 2}))
    if show_cladding:
        cx, cy = _circle(core_radius_m * 1.8e6)
        figure.add_trace(go.Scatter(x=cx, y=cy, mode="lines", name="Displayed cladding window", line={"color": "rgba(255,255,255,0.55)", "dash": "dash"}))
    figure.update_layout(title=f"Normalized intensity for {mode_label}", xaxis_title="x (µm)", yaxis_title="y (µm)", template="plotly_white", yaxis={"scaleanchor": "x", "scaleratio": 1}, margin={"l": 70, "r": 30, "t": 80, "b": 70})
    return figure


def create_lp_mode_longitudinal_figure(x_m, z_m, real_field, intensity, mode_label, display="Field Phase") -> go.Figure:
    """Create a compressed longitudinal LP-mode phase or invariant-intensity view."""
    z = z_m
    data = real_field if display == "Field Phase" else intensity
    title = f"{mode_label} longitudinal field phase (visual phase compression)" if display == "Field Phase" else f"{mode_label} ideal single-mode intensity is invariant along z"
    colorbar = "Normalized field" if display == "Field Phase" else "Normalized intensity"
    figure = go.Figure(go.Heatmap(x=x_m * 1e6, y=z, z=data, colorscale="RdBu" if display == "Field Phase" else "Viridis", colorbar={"title": colorbar}, zmin=-1 if display == "Field Phase" else 0, zmax=1))
    figure.update_layout(title=title, xaxis_title="Transverse axis x (µm)", yaxis_title="Displayed fiber distance z (m)", template="plotly_white", margin={"l": 70, "r": 30, "t": 80, "b": 70})
    return figure


def create_launch_field_figure(x_m, y_m, launch_field, core_radius_m, offset_x_um=0.0, offset_y_um=0.0, launch_azimuth_deg=0.0) -> go.Figure:
    """Create a Gaussian launch intensity figure."""
    intensity = np.abs(launch_field) ** 2
    intensity = intensity / max(float(np.max(intensity)), 1e-30)
    figure = go.Figure(go.Heatmap(x=x_m[0] * 1e6, y=y_m[:, 0] * 1e6, z=intensity, colorscale="Plasma", colorbar={"title": "Normalized launch intensity"}))
    cx, cy = _circle(core_radius_m * 1e6)
    figure.add_trace(go.Scatter(x=cx, y=cy, mode="lines", name="Core boundary", line={"color": "white", "width": 2}))
    figure.add_trace(go.Scatter(x=[offset_x_um], y=[offset_y_um], mode="markers", name="Beam centre", marker={"color": "cyan", "size": 9}))
    dx = 0.4 * core_radius_m * 1e6 * np.cos(np.radians(launch_azimuth_deg)); dy = 0.4 * core_radius_m * 1e6 * np.sin(np.radians(launch_azimuth_deg))
    figure.add_trace(go.Scatter(x=[offset_x_um, offset_x_um + dx], y=[offset_y_um, offset_y_um + dy], mode="lines+markers", name="Launch tilt direction", line={"color": "cyan"}))
    figure.update_layout(title="Deterministic Gaussian launch field", xaxis_title="x (µm)", yaxis_title="y (µm)", template="plotly_white", yaxis={"scaleanchor": "x", "scaleratio": 1}, margin={"l": 70, "r": 30, "t": 80, "b": 70})
    return figure


def create_mode_coupling_figure(couplings, top_n=10) -> go.Figure:
    """Create a sorted modal-overlap chart."""
    shown = list(couplings)[:top_n]
    labels = [item.mode_label for item in shown]
    percentages = [100 * max(0.0, item.coupling_fraction) for item in shown]
    figure = go.Figure(go.Bar(x=labels, y=percentages, text=[f"{v:.2f}%" for v in percentages], textposition="auto"))
    figure.update_layout(title="Calculated scalar LP overlap fractions (not measured power)", xaxis_title="Mode label", yaxis_title="Coupling percentage (%)", template="plotly_white", margin={"l": 70, "r": 30, "t": 80, "b": 70})
    return figure


def create_meridional_ray_figure(ray_result, core_radius_m) -> go.Figure:
    """Create an x-z meridional ray path figure."""
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=ray_result.z_m, y=ray_result.x_m * 1e6, mode="lines+markers", name="Ray path"))
    z = np.array([ray_result.z_m.min(), ray_result.z_m.max()]) if len(ray_result.z_m) else np.array([0, 1])
    figure.add_trace(go.Scatter(x=z, y=np.full(2, core_radius_m * 1e6), mode="lines", name="Upper core boundary", line={"dash": "dash"}))
    figure.add_trace(go.Scatter(x=z, y=np.full(2, -core_radius_m * 1e6), mode="lines", name="Lower core boundary", line={"dash": "dash"}))
    figure.add_trace(go.Scatter(x=[ray_result.z_m[0]], y=[ray_result.x_m[0] * 1e6], mode="markers", name="Launch point", marker={"size": 10}))
    figure.update_layout(title=f"Meridional ray x-z projection — {'accepted' if ray_result.is_accepted else 'rejected'}", xaxis_title="z (m)", yaxis_title="x (µm)", template="plotly_white", margin={"l": 70, "r": 30, "t": 80, "b": 70})
    return figure


def create_skew_ray_figure(ray_result, core_radius_m) -> go.Figure:
    """Create a bounded 3D skew ray path figure."""
    figure = go.Figure()
    figure.add_trace(go.Scatter3d(x=ray_result.z_m, y=ray_result.x_m * 1e6, z=ray_result.y_m * 1e6, mode="lines+markers", name="Skew ray path", line={"width": 5}))
    for zpos in np.linspace(float(ray_result.z_m.min()), float(ray_result.z_m.max()), 8):
        cx, cy = _circle(core_radius_m * 1e6, 80)
        figure.add_trace(go.Scatter3d(x=np.full_like(cx, zpos), y=cx, z=cy, mode="lines", name="Core boundary ring", showlegend=False, line={"color": "rgba(80,80,80,0.35)"}))
    figure.add_trace(go.Scatter3d(x=[ray_result.z_m[0]], y=[ray_result.x_m[0] * 1e6], z=[ray_result.y_m[0] * 1e6], mode="markers", name="Launch point", marker={"size": 5}))
    figure.update_layout(title=f"Skew ray 3D path — {'accepted' if ray_result.is_accepted else 'rejected'}", scene={"xaxis_title": "z (m)", "yaxis_title": "x (µm)", "zaxis_title": "y (µm)"}, template="plotly_white", margin={"l": 0, "r": 0, "t": 80, "b": 0})
    return figure
