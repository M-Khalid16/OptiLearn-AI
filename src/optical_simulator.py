"""Deterministic optical-fiber models for OptiLearn AI."""

from dataclasses import dataclass, replace
from math import isfinite

import numpy as np


@dataclass(frozen=True)
class FiberSimulationResult:
    """Complete result for one reproducible fiber simulation."""

    bits: tuple[int, ...]
    time_ns: np.ndarray
    transmitted_signal_mw: np.ndarray
    received_signal_mw: np.ndarray
    bit_rate_gbps: float
    bit_duration_ns: float
    transmitted_power_mw: float
    received_power_mw: float
    fiber_length_km: float
    attenuation_db_per_km: float
    total_loss_db: float
    remaining_power_percent: float
    linear_attenuation_factor: float
    samples_per_bit: int
    dispersion_enabled: bool = False
    dispersion_coefficient_ps_nm_km: float = 0.0
    spectral_width_nm: float = 0.0
    temporal_broadening_ps: float = 0.0
    temporal_broadening_ns: float = 0.0
    broadening_ratio: float = 0.0
    dispersion_regime: str = "Small"
    dispersion_kernel: np.ndarray | None = None
    dispersed_received_waveform_mw: np.ndarray | None = None


def _require_finite(value: float, name: str) -> None:
    """Reject booleans, nonnumeric values, and nonfinite floating-point values."""
    if isinstance(value, bool) or not isinstance(value, int | float) or not isfinite(value):
        raise ValueError(f"{name} must be a finite number.")


def parse_bit_sequence(bit_sequence: str) -> list[int]:
    """Parse a binary bit sequence containing 2 to 32 symbols."""
    stripped_sequence = bit_sequence.strip()

    if not stripped_sequence:
        raise ValueError("Enter a bit sequence containing 2 to 32 binary digits.")
    if len(stripped_sequence) < 2:
        raise ValueError("The bit sequence must contain at least 2 bits.")
    if len(stripped_sequence) > 32:
        raise ValueError("The bit sequence must contain no more than 32 bits.")
    if any(character not in "01" for character in stripped_sequence):
        raise ValueError(
            "Use only binary digits 0 and 1 with no spaces inside the sequence."
        )

    return [int(character) for character in stripped_sequence]


def calculate_received_power(
    transmitted_power_mw: float,
    fiber_length_km: float,
    attenuation_db_per_km: float,
) -> tuple[float, float, float]:
    """Calculate received power from fiber attenuation in dB."""
    _require_finite(transmitted_power_mw, "Transmitted optical power")
    _require_finite(fiber_length_km, "Fiber length")
    _require_finite(attenuation_db_per_km, "Attenuation coefficient")

    if transmitted_power_mw <= 0:
        raise ValueError("Transmitted optical power must be greater than 0 mW.")
    if fiber_length_km < 0:
        raise ValueError("Fiber length must be 0 km or greater.")
    if attenuation_db_per_km < 0:
        raise ValueError("Attenuation coefficient must be 0 dB/km or greater.")

    total_loss_db = attenuation_db_per_km * fiber_length_km
    linear_attenuation_factor = 10 ** (-total_loss_db / 10)
    received_power_mw = transmitted_power_mw * linear_attenuation_factor

    return received_power_mw, total_loss_db, linear_attenuation_factor


def generate_nrz_ook_waveform(
    bits: list[int],
    bit_rate_gbps: float,
    optical_power_mw: float,
    samples_per_bit: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a rectangular NRZ/OOK optical-power waveform."""
    _require_finite(bit_rate_gbps, "Bit rate")
    _require_finite(optical_power_mw, "Optical power")

    if not bits:
        raise ValueError("At least one bit is required to generate a waveform.")
    if any(bit not in (0, 1) for bit in bits):
        raise ValueError("NRZ/OOK waveform bits must be binary values: 0 or 1.")
    if bit_rate_gbps <= 0:
        raise ValueError("Bit rate must be greater than 0 Gbit/s.")
    if optical_power_mw <= 0:
        raise ValueError("Optical power must be greater than 0 mW.")
    if isinstance(samples_per_bit, bool) or not isinstance(samples_per_bit, int):
        raise ValueError("Samples per bit must be an integer value.")
    if samples_per_bit < 2:
        raise ValueError("Samples per bit must be at least 2.")

    bit_rate_bps = bit_rate_gbps * 1e9
    bit_duration_seconds = 1 / bit_rate_bps
    total_samples = len(bits) * samples_per_bit

    time_seconds = np.arange(total_samples, dtype=float) * (
        bit_duration_seconds / samples_per_bit
    )
    time_ns = time_seconds * 1e9
    transmitted_signal_mw = np.repeat(np.array(bits, dtype=float), samples_per_bit)
    transmitted_signal_mw *= optical_power_mw

    return time_ns, transmitted_signal_mw


def simulate_fiber_attenuation(
    bit_sequence: str,
    bit_rate_gbps: float,
    transmitted_power_mw: float,
    fiber_length_km: float,
    attenuation_db_per_km: float,
    samples_per_bit: int = 100,
) -> FiberSimulationResult:
    """Simulate deterministic attenuation of an NRZ/OOK fiber waveform."""
    bits = parse_bit_sequence(bit_sequence)
    time_ns, transmitted_signal_mw = generate_nrz_ook_waveform(
        bits=bits,
        bit_rate_gbps=bit_rate_gbps,
        optical_power_mw=transmitted_power_mw,
        samples_per_bit=samples_per_bit,
    )
    received_power_mw, total_loss_db, linear_attenuation_factor = calculate_received_power(
        transmitted_power_mw=transmitted_power_mw,
        fiber_length_km=fiber_length_km,
        attenuation_db_per_km=attenuation_db_per_km,
    )

    received_signal_mw = transmitted_signal_mw * linear_attenuation_factor
    remaining_power_percent = 100 * received_power_mw / transmitted_power_mw
    bit_duration_ns = 1 / bit_rate_gbps

    return FiberSimulationResult(
        bits=tuple(bits),
        time_ns=time_ns,
        transmitted_signal_mw=transmitted_signal_mw,
        received_signal_mw=received_signal_mw,
        bit_rate_gbps=bit_rate_gbps,
        bit_duration_ns=bit_duration_ns,
        transmitted_power_mw=transmitted_power_mw,
        received_power_mw=received_power_mw,
        fiber_length_km=fiber_length_km,
        attenuation_db_per_km=attenuation_db_per_km,
        total_loss_db=total_loss_db,
        remaining_power_percent=remaining_power_percent,
        linear_attenuation_factor=linear_attenuation_factor,
        samples_per_bit=samples_per_bit,
        dispersion_kernel=np.array([1.0]),
        dispersed_received_waveform_mw=received_signal_mw.copy(),
    )


def classify_dispersion_regime(broadening_ratio: float) -> str:
    """Classify broadening using educational threshold labels, not BER thresholds."""
    _require_finite(broadening_ratio, "Broadening ratio")
    if broadening_ratio < 0:
        raise ValueError("Broadening ratio must be 0 or greater.")
    if broadening_ratio < 0.1:
        return "Small"
    if broadening_ratio < 0.5:
        return "Noticeable"
    if broadening_ratio < 1.0:
        return "Substantial"
    return "Severe overlap risk"


def _build_gaussian_dispersion_kernel(
    temporal_broadening_ns: float,
    sample_interval_ns: float,
    max_kernel_samples: int,
) -> np.ndarray:
    """Build a bounded, normalized Gaussian kernel for educational spreading.

    The model treats ``temporal_broadening_ns`` as an effective Gaussian full width
    at half maximum (FWHM), so sigma = FWHM / (2 sqrt(2 ln 2)). The target finite
    support spans ±4 sigma when it fits inside ``max_kernel_samples``. If that
    ideal support would be too large for interactive use, the sampled support is
    symmetrically truncated to the largest allowed odd length and renormalized.
    This keeps convolution cost bounded while preserving deterministic educational
    temporal spreading; it is not a full optical field propagation solution.
    """
    _require_finite(temporal_broadening_ns, "Temporal broadening")
    _require_finite(sample_interval_ns, "Sample interval")
    if isinstance(max_kernel_samples, bool) or not isinstance(max_kernel_samples, int):
        raise ValueError("Maximum kernel samples must be an integer value.")
    if max_kernel_samples < 1:
        raise ValueError("Maximum kernel samples must be at least 1.")
    if temporal_broadening_ns < 0:
        raise ValueError("Temporal broadening must be 0 ns or greater.")
    if sample_interval_ns <= 0:
        raise ValueError("Sample interval must be greater than 0 ns.")
    if temporal_broadening_ns <= sample_interval_ns * 1e-9:
        return np.array([1.0])

    largest_allowed_length = max_kernel_samples
    if largest_allowed_length % 2 == 0:
        largest_allowed_length -= 1
    if largest_allowed_length < 1:
        largest_allowed_length = 1

    sigma_ns = temporal_broadening_ns / (2 * np.sqrt(2 * np.log(2)))
    target_radius_samples = max(1, int(np.ceil(4 * sigma_ns / sample_interval_ns)))
    allowed_radius_samples = (largest_allowed_length - 1) // 2
    radius_samples = min(target_radius_samples, allowed_radius_samples)
    if radius_samples == 0:
        return np.array([1.0])

    sample_offsets = np.arange(-radius_samples, radius_samples + 1, dtype=float)
    kernel = np.exp(-0.5 * ((sample_offsets * sample_interval_ns) / sigma_ns) ** 2)
    kernel_sum = float(np.sum(kernel))
    if kernel_sum <= 0 or not np.isfinite(kernel_sum):
        raise ValueError("Dispersion kernel could not be normalized.")
    kernel = kernel / kernel_sum
    return kernel


def _convolve_same_length(waveform: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Convolve while preserving the original waveform length for any kernel size."""
    full = np.convolve(waveform, kernel, mode="full")
    start = (len(kernel) - 1) // 2
    stop = start + len(waveform)
    return full[start:stop]


def simulate_fiber_dispersion(
    bit_sequence: str,
    bit_rate_gbps: float,
    transmitted_power_mw: float,
    fiber_length_km: float,
    attenuation_db_per_km: float,
    dispersion_coefficient_ps_nm_km: float,
    spectral_width_nm: float,
    samples_per_bit: int = 100,
) -> FiberSimulationResult:
    """Simulate attenuation plus educational chromatic-dispersion broadening."""
    _require_finite(dispersion_coefficient_ps_nm_km, "Chromatic dispersion coefficient")
    _require_finite(spectral_width_nm, "Source spectral width")
    if spectral_width_nm < 0:
        raise ValueError("Source spectral width must be 0 nm or greater.")

    attenuation_result = simulate_fiber_attenuation(
        bit_sequence=bit_sequence,
        bit_rate_gbps=bit_rate_gbps,
        transmitted_power_mw=transmitted_power_mw,
        fiber_length_km=fiber_length_km,
        attenuation_db_per_km=attenuation_db_per_km,
        samples_per_bit=samples_per_bit,
    )
    temporal_broadening_ps = (
        abs(dispersion_coefficient_ps_nm_km) * spectral_width_nm * fiber_length_km
    )
    temporal_broadening_ns = temporal_broadening_ps / 1000
    broadening_ratio = temporal_broadening_ns / attenuation_result.bit_duration_ns
    sample_interval_ns = attenuation_result.bit_duration_ns / samples_per_bit
    kernel = _build_gaussian_dispersion_kernel(
        temporal_broadening_ns,
        sample_interval_ns,
        len(attenuation_result.transmitted_signal_mw),
    )

    normalized_binary_waveform = attenuation_result.transmitted_signal_mw / transmitted_power_mw
    broadened_normalized = _convolve_same_length(normalized_binary_waveform, kernel)
    dispersed_received = (
        broadened_normalized
        * transmitted_power_mw
        * attenuation_result.linear_attenuation_factor
    )
    dispersed_received = np.where(dispersed_received < 0, np.maximum(dispersed_received, 0), dispersed_received)

    return replace(
        attenuation_result,
        dispersion_enabled=True,
        dispersion_coefficient_ps_nm_km=dispersion_coefficient_ps_nm_km,
        spectral_width_nm=spectral_width_nm,
        temporal_broadening_ps=temporal_broadening_ps,
        temporal_broadening_ns=temporal_broadening_ns,
        broadening_ratio=broadening_ratio,
        dispersion_regime=classify_dispersion_regime(broadening_ratio),
        dispersion_kernel=kernel,
        dispersed_received_waveform_mw=dispersed_received,
    )


def build_educational_observations(result: FiberSimulationResult) -> dict[str, list[str]]:
    """Build deterministic learning observations from a simulation result."""
    foundation = [
        "A logical one means light is transmitted at the selected power.",
        "A logical zero remains at 0 mW because the idealized source is off.",
        (
            f"Over {result.fiber_length_km:.0f} km, fiber attenuation lowers "
            f"each one-level to {result.received_power_mw:.6g} mW."
        ),
        (
            f"The bit rate sets the pulse width: each bit lasts "
            f"{result.bit_duration_ns:.6g} ns in this run."
        ),
        "Attenuation reduces pulse height; it does not by itself spread pulses in time.",
    ]
    engineering = [
        (
            "Total loss uses A = α × L = "
            f"{result.attenuation_db_per_km:.2f} dB/km × "
            f"{result.fiber_length_km:.0f} km = {result.total_loss_db:.3f} dB."
        ),
        (
            "The dB loss is converted to a linear power factor using "
            f"T = 10^(-A/10) = {result.linear_attenuation_factor:.12g}."
        ),
        (
            "Received power uses P_rx = P_tx × T = "
            f"{result.transmitted_power_mw:.3f} mW × "
            f"{result.linear_attenuation_factor:.12g} = "
            f"{result.received_power_mw:.12g} mW."
        ),
        f"Bit duration uses T_b = 1 / R_b = {result.bit_duration_ns:.6g} ns.",
    ]
    research = [
        "The model assumes an ideal NRZ/OOK transmitter and zero optical power for zeros.",
        "Optical noise, receiver response, connector loss, splice loss, nonlinearities, and bit-error mechanisms are absent.",
        "The model is valid for teaching reproducible power and pulse-spreading relationships, not BER prediction.",
    ]
    if result.dispersion_enabled:
        foundation.extend(
            [
                "Chromatic dispersion means different wavelength components travel at slightly different group velocities.",
                "The pulse spreads in time in the dispersion trace while attenuation still controls its amplitude scale.",
                "Strong spreading can make neighbouring pulses overlap in this simplified waveform view.",
            ]
        )
        engineering.extend(
            [
                (
                    "Temporal broadening uses Δt = |D| Δλ L = "
                    f"{result.temporal_broadening_ps:.6g} ps = "
                    f"{result.temporal_broadening_ns:.6g} ns."
                ),
                (
                    "Broadening ratio Δt/T_b = "
                    f"{result.broadening_ratio:.6g}, classified as {result.dispersion_regime}."
                ),
                "For a fixed broadening, higher bit rate shortens T_b and increases dispersion sensitivity.",
                "Attenuation changes signal amplitude; dispersion changes temporal shape; no BER is calculated.",
            ]
        )
        research.extend(
            [
                "Gaussian convolution is an educational intensity-domain approximation of temporal spreading.",
                "The model omits chirp, second-order dispersion, PMD, noise, receiver bandwidth, and nonlinear propagation.",
                "Laboratory validation could compare measured pulse widths after known fiber lengths with this deterministic broadening estimate.",
            ]
        )
    else:
        foundation.append("This attenuation-only model reduces amplitude but does not deform pulses.")
        engineering.append("In this attenuation-only model, bit rate affects time scale but not received optical-power level.")
        research.append("Logical next extensions include connector loss, dispersion, receiver response, noise, OSNR, eye diagrams, and BER models.")
    return {"foundation": foundation, "engineering": engineering, "research": research}
