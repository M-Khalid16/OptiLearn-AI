
"""Deterministic optical-fiber attenuation model for OptiLearn AI."""

from dataclasses import dataclass
from math import isfinite

import numpy as np


@dataclass(frozen=True)
class FiberSimulationResult:
    """Complete result for one reproducible fiber attenuation simulation."""

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


def _require_finite(value: float, name: str) -> None:
    """Reject nonfinite floating-point input values."""
    if not isfinite(value):
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
    received_power_mw, total_loss_db, linear_attenuation_factor = (
        calculate_received_power(
            transmitted_power_mw=transmitted_power_mw,
            fiber_length_km=fiber_length_km,
            attenuation_db_per_km=attenuation_db_per_km,
        )
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
    )


def build_educational_observations(
    result: FiberSimulationResult,
) -> dict[str, list[str]]:
    """Build deterministic learning observations from a simulation result."""
    return {
        "foundation": [
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
            "This attenuation-only model reduces amplitude but does not deform pulses.",
        ],
        "engineering": [
            (
                "Total loss uses A = α × L = "
                f"{result.attenuation_db_per_km:.2f} dB/km × "
                f"{result.fiber_length_km:.0f} km = "
                f"{result.total_loss_db:.3f} dB."
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
            (
                "Bit duration uses T_b = 1 / R_b = "
                f"{result.bit_duration_ns:.6g} ns."
            ),
            (
                "In this attenuation-only model, bit rate affects the time "
                "scale but not the received optical-power level."
            ),
        ],
        "research": [
            (
                "The model assumes deterministic attenuation only, with an "
                "ideal NRZ/OOK transmitter and zero optical power for zeros."
            ),
            (
                "Dispersion, optical noise, receiver response, connector loss, "
                "splice loss, nonlinearities, and bit-error mechanisms are absent."
            ),
            (
                "The model is valid for teaching and reproducing dB-to-linear "
                "power relationships, not for waveform-fidelity or BER prediction."
            ),
            (
                "A calibrated optical source, known fiber length, and optical "
                "power meter could compare measured loss with this prediction."
            ),
            (
                "Logical next extensions include connector loss, dispersion, "
                "receiver response, noise, OSNR, eye diagrams, and BER models."
            ),
        ],
    }
"""Optical simulator module for future communication concept modeling."""

# TODO: Define interfaces for future optical communication simulations.
# TODO: Add simulation implementation in a later milestone.

