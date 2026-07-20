"""Deterministic geometric ray tracing for ideal circular optical-fiber cores."""

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class RayLaunch:
    ray_type: str
    launch_angle_deg: float
    launch_azimuth_deg: float
    radial_offset_fraction: float
    fiber_length_m: float
    core_radius_m: float
    n_core: float
    n_cladding: float


@dataclass(frozen=True)
class RayTraceResult:
    ray_type: str
    is_accepted: bool
    acceptance_angle_deg: float
    critical_angle_deg: float
    reflection_count: int
    x_m: np.ndarray
    y_m: np.ndarray
    z_m: np.ndarray
    message: str


def _angles(launch: RayLaunch) -> tuple[float, float]:
    na = math.sqrt(max(launch.n_core**2 - launch.n_cladding**2, 0.0))
    return math.degrees(math.asin(min(na, 1.0))), math.degrees(math.asin(launch.n_cladding / launch.n_core))


def _validate(launch: RayLaunch) -> None:
    if launch.ray_type not in {"Meridional Ray", "Skew Ray"}:
        raise ValueError("ray_type must be Meridional Ray or Skew Ray.")
    vals = [launch.launch_angle_deg, launch.launch_azimuth_deg, launch.radial_offset_fraction, launch.fiber_length_m, launch.core_radius_m, launch.n_core, launch.n_cladding]
    if any(isinstance(v, bool) or not math.isfinite(float(v)) for v in vals):
        raise ValueError("Ray launch values must be finite numeric scalars.")
    if launch.launch_angle_deg < 0 or launch.launch_angle_deg >= 90 or launch.fiber_length_m <= 0 or launch.core_radius_m <= 0:
        raise ValueError("Ray launch angle, length, and radius are outside supported ranges.")
    if not 0 <= launch.radial_offset_fraction < 1 or not launch.n_core > launch.n_cladding > 1:
        raise ValueError("Ray offset and refractive indices are outside supported ranges.")


def _rejected(launch: RayLaunch, acceptance: float, critical: float) -> RayTraceResult:
    z = np.array([0.0, min(launch.fiber_length_m, 4 * launch.core_radius_m)])
    x = np.array([launch.radial_offset_fraction * launch.core_radius_m, launch.radial_offset_fraction * launch.core_radius_m + z[-1] * math.tan(math.radians(launch.launch_angle_deg))])
    y = np.zeros_like(x)
    return RayTraceResult(launch.ray_type, False, acceptance, critical, 0, x, y, z, "Launch angle is outside the air acceptance cone; guided reflections are not traced.")


def trace_meridional_ray(launch: RayLaunch, maximum_reflections: int = 500) -> RayTraceResult:
    _validate(launch)
    acceptance, critical = _angles(launch)
    if launch.launch_angle_deg > acceptance:
        return _rejected(launch, acceptance, critical)
    theta = math.radians(launch.launch_angle_deg)
    if abs(theta) < 1e-12:
        z = np.array([0.0, launch.fiber_length_m]); x = np.zeros(2); y = np.zeros(2)
        return RayTraceResult(launch.ray_type, True, acceptance, critical, 0, x, y, z, "Accepted axial meridional ray.")
    radius = launch.core_radius_m
    x = [launch.radial_offset_fraction * radius]
    z = [0.0]
    vx = math.tan(theta)
    reflections = 0
    while z[-1] < launch.fiber_length_m and reflections < maximum_reflections:
        target = radius if vx > 0 else -radius
        dz = (target - x[-1]) / vx
        if dz <= 1e-15:
            break
        next_z = z[-1] + dz
        if next_z >= launch.fiber_length_m:
            x.append(x[-1] + vx * (launch.fiber_length_m - z[-1])); z.append(launch.fiber_length_m); break
        x.append(target); z.append(next_z); vx = -vx; reflections += 1
    return RayTraceResult(launch.ray_type, True, acceptance, critical, reflections, np.array(x), np.zeros(len(x)), np.array(z), "Accepted meridional ray with ideal specular core-boundary reflections.")


def trace_skew_ray(launch: RayLaunch, maximum_reflections: int = 1000) -> RayTraceResult:
    _validate(launch)
    acceptance, critical = _angles(launch)
    if launch.launch_angle_deg > acceptance:
        return _rejected(launch, acceptance, critical)
    if launch.radial_offset_fraction <= 1e-6 or abs(math.sin(math.radians(launch.launch_azimuth_deg))) <= 1e-6:
        raise ValueError("Skew rays require nonzero radial offset and nonzero azimuthal component.")
    radius = launch.core_radius_m
    theta = math.radians(max(launch.launch_angle_deg, 1e-9))
    az = math.radians(launch.launch_azimuth_deg)
    pos = np.array([launch.radial_offset_fraction * radius, 0.0, 0.0], dtype=float)
    slope_mag = math.tan(theta)
    direction = np.array([slope_mag * math.cos(az), slope_mag * math.sin(az), 1.0], dtype=float)
    xs = [pos[0]]; ys = [pos[1]]; zs = [0.0]; reflections = 0
    while pos[2] < launch.fiber_length_m and reflections < maximum_reflections:
        a = direction[0] ** 2 + direction[1] ** 2
        b = 2 * (pos[0] * direction[0] + pos[1] * direction[1])
        c = pos[0] ** 2 + pos[1] ** 2 - radius ** 2
        disc = b * b - 4 * a * c
        if a <= 1e-30 or disc <= 0:
            break
        roots = [t for t in ((-b - math.sqrt(disc)) / (2 * a), (-b + math.sqrt(disc)) / (2 * a)) if t > 1e-12]
        if not roots:
            break
        t = min(roots)
        next_pos = pos + t * direction
        if next_pos[2] >= launch.fiber_length_m:
            t_end = (launch.fiber_length_m - pos[2]) / direction[2]
            end = pos + t_end * direction
            xs.append(end[0]); ys.append(end[1]); zs.append(end[2]); break
        xs.append(next_pos[0]); ys.append(next_pos[1]); zs.append(next_pos[2])
        normal = np.array([next_pos[0], next_pos[1], 0.0]) / radius
        direction = direction - 2 * np.dot(direction, normal) * normal
        direction[2] = abs(direction[2])
        pos = next_pos
        reflections += 1
    return RayTraceResult(launch.ray_type, True, acceptance, critical, reflections, np.array(xs), np.array(ys), np.array(zs), "Accepted skew ray with ideal specular reflections on the circular core boundary.")
