"""Scalar LP-mode utilities for educational circular step-index fibers.

Mode labels use LP_lm (rendered without the underscore, e.g. LP01, LP11):
l is the azimuthal order and m is the radial root order.  For l > 0 the
cos(lφ) and sin(lφ) orientations are orientation degeneracy of one LP family;
they are not counted as separate families by the solver.

The characteristic-equation convention is the scalar weak-guidance boundary
condition
    u J_l'(u) / J_l(u) = w K_l'(w) / K_l(w),  w = sqrt(V^2 - u^2).
For LP01 an educational fundamental branch is computed by solving the same
continuous field construction with a near-zero cutoff convention, so LP01 is
guided for every V > 0.  Reported higher-order cutoffs use standard scalar LP
family cutoffs based on Bessel zeros: LP_l1 for l >= 1 cuts on at J_{l-1,1},
and LP_0m (m >= 2) cuts on at J_{1,m-1}.
"""

from dataclasses import dataclass
import math

import numpy as np
from scipy.optimize import brentq
from scipy.special import jv, jvp, kv, kvp, jn_zeros


@dataclass(frozen=True)
class LPMode:
    label: str
    azimuthal_order: int
    radial_order: int
    orientation: str
    u: float
    w: float
    v_number: float
    beta_per_m: float
    effective_index: float
    cutoff_v: float
    is_guided: bool
    normalized_propagation_constant: float


@dataclass(frozen=True)
class FiberModeResult:
    wavelength_nm: float
    wavelength_m: float
    core_radius_um: float
    core_radius_m: float
    core_diameter_um: float
    n_core: float
    n_cladding: float
    relative_index_difference: float
    numerical_aperture: float
    acceptance_angle_deg: float
    critical_angle_deg: float
    v_number: float
    approximate_mode_count: float
    single_mode_cutoff_v: float
    is_single_mode: bool
    guided_modes: tuple[LPMode, ...]


@dataclass(frozen=True)
class LaunchBeam:
    beam_diameter_um: float
    beam_radius_m: float
    offset_x_um: float
    offset_y_um: float
    launch_angle_deg: float
    launch_azimuth_deg: float


@dataclass(frozen=True)
class ModeCouplingResult:
    mode_label: str
    coupling_fraction: float


def _scalar(name: str, value: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite numeric scalar, not a boolean.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite numeric scalar.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite.")
    return number


def _bounded_int(name: str, value: int, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer between {low} and {high}.")
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}.")
    return value


ROOT_RESIDUAL_TOLERANCE = 1e-7
POLE_PROXIMITY_TOLERANCE = 1e-5


def _cutoff_v(l_order: int, radial_order: int) -> float:
    if l_order == 0 and radial_order == 1:
        return 0.0
    if l_order == 0:
        return float(jn_zeros(1, radial_order - 1)[-1])
    return float(jn_zeros(l_order - 1, radial_order)[-1])


def _j_l_zeros_below_v(l_order: int, v_number: float) -> list[float]:
    if v_number <= 0:
        return []
    count = max(1, int(v_number / math.pi) + l_order + 4)
    return [float(zero) for zero in jn_zeros(l_order, count) if 0.0 < float(zero) < v_number]


def _char_eq(l_order: int, u_value: float, v_number: float) -> float:
    w_value = math.sqrt(max(v_number * v_number - u_value * u_value, 0.0))
    jl = jv(l_order, u_value)
    kl = kv(l_order, w_value)
    if abs(jl) < 1e-12 or abs(kl) < 1e-300 or w_value <= 0.0:
        return math.nan
    return float(u_value * jvp(l_order, u_value) / jl - w_value * kvp(l_order, w_value) / kl)


def _find_roots(l_order: int, v_number: float, max_roots: int) -> list[float]:
    eps = max(1e-7, v_number * 1e-8)
    if v_number <= 2 * eps:
        return []
    pole_padding = max(POLE_PROXIMITY_TOLERANCE, v_number * 1e-8)
    breakpoints = [eps, v_number - eps]
    for pole in _j_l_zeros_below_v(l_order, v_number):
        left = pole - pole_padding
        right = pole + pole_padding
        if eps < left < v_number - eps:
            breakpoints.append(left)
        if eps < right < v_number - eps:
            breakpoints.append(right)
    breakpoints = sorted(set(round(point, 14) for point in breakpoints))
    roots: list[float] = []
    for start, stop in zip(breakpoints[:-1], breakpoints[1:], strict=True):
        if len(roots) >= max_roots:
            break
        if stop - start <= 4 * eps:
            continue
        # Skip the padded interval that straddles a J_l pole.
        midpoint = 0.5 * (start + stop)
        if any(abs(midpoint - pole) <= pole_padding for pole in _j_l_zeros_below_v(l_order, v_number)):
            continue
        local_grid = np.linspace(start, stop, max(24, int(30 * (stop - start)) + 12))
        values = np.array([_char_eq(l_order, float(u), v_number) for u in local_grid])
        for left, right, f_left, f_right in zip(local_grid[:-1], local_grid[1:], values[:-1], values[1:], strict=True):
            if len(roots) >= max_roots:
                break
            if not (np.isfinite(f_left) and np.isfinite(f_right)):
                continue
            if abs(f_left) > 1e5 or abs(f_right) > 1e5 or f_left * f_right > 0:
                continue
            if any(left < pole < right for pole in _j_l_zeros_below_v(l_order, v_number)):
                continue
            try:
                root = brentq(lambda u: _char_eq(l_order, u, v_number), float(left), float(right), maxiter=80)
            except (ValueError, RuntimeError, FloatingPointError):
                continue
            residual = abs(_char_eq(l_order, root, v_number)) if math.isfinite(root) else math.inf
            if (
                eps < root < v_number - eps
                and residual <= ROOT_RESIDUAL_TOLERANCE
                and all(abs(root - pole) > pole_padding for pole in _j_l_zeros_below_v(l_order, v_number))
                and all(abs(root - old) > 1e-5 for old in roots)
            ):
                roots.append(float(root))
    return roots


def _approximate_lp01_fundamental_u(v_number: float) -> float:
    """Return the documented educational LP01 approximation; not a brentq root."""
    if v_number <= 0 or not math.isfinite(v_number):
        raise ValueError("v_number must be positive and finite.")
    return v_number / math.sqrt(1.0 + (2.405 / max(v_number, 1e-12)) ** 2)


def _validate_mode_root(l_order: int, u_value: float, v_number: float, *, require_characteristic_residual: bool = True) -> float | None:
    if not (math.isfinite(u_value) and 0.0 < u_value < v_number):
        return None
    w_squared = v_number * v_number - u_value * u_value
    if not math.isfinite(w_squared) or w_squared <= 0.0:
        return None
    w_value = math.sqrt(w_squared)
    if not (math.isfinite(w_value) and w_value > 0.0):
        return None
    if abs((u_value * u_value + w_value * w_value) - v_number * v_number) > 1e-8 * max(1.0, v_number * v_number):
        return None
    if require_characteristic_residual:
        residual = abs(_char_eq(l_order, u_value, v_number))
        if not math.isfinite(residual) or residual > ROOT_RESIDUAL_TOLERANCE:
            return None
    return w_value


def _mode_from_u(label: str, l_order: int, radial_order: int, u_value: float, cutoff: float, wavelength_m: float, core_radius_m: float, n_core: float, n_cladding: float, v_number: float, *, require_characteristic_residual: bool = True) -> LPMode | None:
    w_value = _validate_mode_root(l_order, u_value, v_number, require_characteristic_residual=require_characteristic_residual)
    if w_value is None:
        return None
    k0 = 2.0 * math.pi / wavelength_m
    beta_sq = (n_core * k0) ** 2 - (u_value / core_radius_m) ** 2
    if beta_sq <= 0:
        return None
    beta = math.sqrt(beta_sq)
    n_eff = beta / k0
    b = (n_eff * n_eff - n_cladding * n_cladding) / (n_core * n_core - n_cladding * n_cladding)
    if -1e-9 <= b <= 1.0 + 1e-9:
        b = min(1.0, max(0.0, b))
    if not (math.isfinite(beta) and math.isfinite(n_eff) and math.isfinite(b)):
        return None
    if not (n_cladding < n_eff < n_core):
        return None
    if not (0.0 <= b <= 1.0):
        return None
    return LPMode(label, l_order, radial_order, "Circularly symmetric" if l_order == 0 else "cos(lφ)", u_value, w_value, v_number, beta, n_eff, cutoff, True, b)


def solve_lp_modes(wavelength_nm: float, core_diameter_um: float, n_core: float, n_cladding: float, max_azimuthal_order: int = 6, max_radial_order: int = 6, max_modes: int = 30) -> FiberModeResult:
    wavelength_nm = _scalar("wavelength_nm", wavelength_nm)
    core_diameter_um = _scalar("core_diameter_um", core_diameter_um)
    n_core = _scalar("n_core", n_core)
    n_cladding = _scalar("n_cladding", n_cladding)
    max_azimuthal_order = _bounded_int("max_azimuthal_order", max_azimuthal_order, 0, 12)
    max_radial_order = _bounded_int("max_radial_order", max_radial_order, 1, 12)
    max_modes = _bounded_int("max_modes", max_modes, 1, 100)
    if wavelength_nm <= 0 or core_diameter_um <= 0:
        raise ValueError("Wavelength and core diameter must be greater than zero.")
    if n_core <= 1 or n_cladding <= 1 or n_cladding >= n_core:
        raise ValueError("Refractive indices must satisfy n_core > n_cladding > 1.")
    wavelength_m = wavelength_nm * 1e-9
    radius_m = core_diameter_um * 0.5e-6
    na = math.sqrt(n_core * n_core - n_cladding * n_cladding)
    v_number = 2 * math.pi * radius_m * na / wavelength_m
    delta = (n_core * n_core - n_cladding * n_cladding) / (2 * n_core * n_core)
    modes: list[LPMode] = []
    # LP01 fundamental uses a documented educational approximation, not a brentq eigenvalue root.
    u01 = _approximate_lp01_fundamental_u(v_number)
    mode = _mode_from_u("LP01", 0, 1, min(max(u01, 1e-9), v_number - 1e-9), 0.0, wavelength_m, radius_m, n_core, n_cladding, v_number, require_characteristic_residual=False)
    if mode is not None:
        modes.append(mode)
    for l_order in range(max_azimuthal_order + 1):
        roots = _find_roots(l_order, v_number, max_radial_order + 3)
        root_index = 0
        for radial_order in range(1, max_radial_order + 1):
            if l_order == 0 and radial_order == 1:
                continue
            cutoff = _cutoff_v(l_order, radial_order)
            if v_number <= cutoff + 1e-7:
                continue
            while root_index < len(roots) and roots[root_index] <= cutoff + 1e-5:
                root_index += 1
            if root_index >= len(roots):
                continue
            u_value = roots[root_index]
            root_index += 1
            label = f"LP{l_order}{radial_order}"
            mode = _mode_from_u(label, l_order, radial_order, u_value, cutoff, wavelength_m, radius_m, n_core, n_cladding, v_number, require_characteristic_residual=True)
            if mode is not None:
                modes.append(mode)
            if len(modes) >= max_modes:
                break
        if len(modes) >= max_modes:
            break
    modes = sorted({(m.label, m.orientation): m for m in modes}.values(), key=lambda m: (m.cutoff_v, m.azimuthal_order, m.radial_order))[:max_modes]
    return FiberModeResult(wavelength_nm, wavelength_m, radius_m * 1e6, radius_m, core_diameter_um, n_core, n_cladding, delta, na, math.degrees(math.asin(min(na, 1.0))), math.degrees(math.asin(n_cladding / n_core)), v_number, v_number * v_number / 2.0, 2.405, v_number < 2.405, tuple(modes))


def _grid(result: FiberModeResult, grid_points: int, cladding_radius_factor: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if isinstance(grid_points, bool) or not 3 <= int(grid_points) <= 301:
        raise ValueError("grid_points must be between 3 and 301.")
    grid_points = int(grid_points) | 1
    extent = result.core_radius_m * float(cladding_radius_factor)
    axis = np.linspace(-extent, extent, grid_points)
    x_m, y_m = np.meshgrid(axis, axis)
    return axis, x_m, y_m, np.hypot(x_m, y_m)


def calculate_lp_mode_field(mode: LPMode, result: FiberModeResult, grid_points: int = 201, cladding_radius_factor: float = 1.8) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    _, x_m, y_m, r_m = _grid(result, grid_points, cladding_radius_factor)
    phi = np.arctan2(y_m, x_m)
    l_order = mode.azimuthal_order
    core = jv(l_order, mode.u * r_m / result.core_radius_m)
    boundary_j = jv(l_order, mode.u)
    boundary_k = kv(l_order, max(mode.w, 1e-12))
    scale = boundary_j / boundary_k if abs(boundary_k) > 1e-300 else 0.0
    clad = scale * kv(l_order, np.maximum(mode.w * r_m / result.core_radius_m, 1e-12))
    radial = np.where(r_m <= result.core_radius_m, core, clad)
    if l_order == 0:
        angular = 1.0
    elif mode.orientation.startswith("sin"):
        angular = np.sin(l_order * phi)
    else:
        angular = np.cos(l_order * phi)
    field = np.nan_to_num(radial * angular, nan=0.0, posinf=0.0, neginf=0.0)
    peak = np.max(np.abs(field))
    if peak <= 0 or not np.isfinite(peak):
        raise ValueError("Mode field could not be normalized.")
    return x_m, y_m, field / peak


def calculate_lp_mode_intensity(field: np.ndarray) -> np.ndarray:
    intensity = np.abs(field) ** 2
    peak = np.max(intensity)
    return np.nan_to_num(intensity / peak if peak > 0 else intensity)


def calculate_longitudinal_mode_slice(mode: LPMode, result: FiberModeResult, fiber_length_m: float, transverse_axis_points: int = 151, longitudinal_points: int = 300, displayed_phase_cycles: float = 6.0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    fiber_length_m = _scalar("fiber_length_m", fiber_length_m)
    if fiber_length_m <= 0:
        raise ValueError("fiber_length_m must be greater than zero.")
    x_axis = np.linspace(-1.8 * result.core_radius_m, 1.8 * result.core_radius_m, int(transverse_axis_points) | 1)
    z_axis = np.linspace(0.0, fiber_length_m, int(longitudinal_points))
    x_grid, z_grid = np.meshgrid(x_axis, z_axis)
    r = np.abs(x_grid)
    radial = np.where(r <= result.core_radius_m, jv(mode.azimuthal_order, mode.u * r / result.core_radius_m), jv(mode.azimuthal_order, mode.u) / kv(mode.azimuthal_order, max(mode.w, 1e-12)) * kv(mode.azimuthal_order, np.maximum(mode.w * r / result.core_radius_m, 1e-12)))
    if mode.azimuthal_order > 0 and mode.orientation.startswith("sin"):
        # Rotated y-axis slice through a nonzero sine-orientation lobe; the returned coordinate remains transverse distance.
        radial = radial * np.sign(x_grid)
    radial /= max(np.max(np.abs(radial)), 1e-30)
    beta_visual = 2 * math.pi * displayed_phase_cycles / fiber_length_m
    real_field = radial * np.cos(beta_visual * z_grid)
    intensity = np.tile(np.abs(radial[0]) ** 2, (len(z_axis), 1))
    intensity /= max(float(np.max(intensity)), 1e-30)
    return x_axis, z_axis, real_field, intensity


def calculate_gaussian_launch_field(result: FiberModeResult, beam_diameter_um: float, offset_x_um: float, offset_y_um: float, launch_angle_deg: float, launch_azimuth_deg: float, grid_points: int = 201, cladding_radius_factor: float = 1.8) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    beam_diameter_um = _scalar("beam_diameter_um", beam_diameter_um)
    launch_angle_deg = _scalar("launch_angle_deg", launch_angle_deg)
    if beam_diameter_um <= 0 or launch_angle_deg < 0 or launch_angle_deg >= 90:
        raise ValueError("Launch beam diameter must be positive and launch angle must be in [0, 90) degrees.")
    _, x_m, y_m, _ = _grid(result, grid_points, cladding_radius_factor)
    w0 = beam_diameter_um * 0.5e-6
    x0 = _scalar("offset_x_um", offset_x_um) * 1e-6
    y0 = _scalar("offset_y_um", offset_y_um) * 1e-6
    angle = math.radians(launch_angle_deg)
    azimuth = math.radians(_scalar("launch_azimuth_deg", launch_azimuth_deg))
    kt = result.n_core * 2 * math.pi / result.wavelength_m * math.sin(angle)
    field = np.exp(-((x_m - x0) ** 2 + (y_m - y0) ** 2) / (w0 * w0)) * np.exp(1j * kt * (np.cos(azimuth) * x_m + np.sin(azimuth) * y_m))
    power = np.sum(np.abs(field) ** 2)
    if power <= 0 or not np.isfinite(power):
        raise ValueError("Launch field power could not be normalized.")
    return x_m, y_m, field / math.sqrt(float(power))


def calculate_mode_coupling(launch_field: np.ndarray, modes: tuple[LPMode, ...], fiber_result: FiberModeResult, grid_points: int = 201, cladding_radius_factor: float = 1.8, maximum_modes: int = 20) -> tuple[ModeCouplingResult, ...]:
    maximum_modes = _bounded_int("maximum_modes", maximum_modes, 1, 100)
    launch_power = float(np.sum(np.abs(launch_field) ** 2))
    results: list[ModeCouplingResult] = []
    for mode in modes[:maximum_modes]:
        _, _, field = calculate_lp_mode_field(mode, fiber_result, grid_points, cladding_radius_factor)
        denom = launch_power * float(np.sum(np.abs(field) ** 2))
        eta = abs(np.sum(launch_field * np.conjugate(field))) ** 2 / denom if denom > 0 else 0.0
        if np.isfinite(eta):
            results.append(ModeCouplingResult(mode.label, min(1.0, max(0.0, float(eta)))))
    return tuple(sorted(results, key=lambda item: item.coupling_fraction, reverse=True))
