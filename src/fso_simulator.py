"""Deterministic free-space optical link model for OptiLearn AI."""

from dataclasses import dataclass
from math import exp, isfinite, log10


_LOG_FLOOR = 1e-300


@dataclass(frozen=True)
class FSOSimulationResult:
    """Scalar result for one deterministic educational FSO link budget."""

    link_distance_km: float
    link_distance_m: float
    transmitted_power_mw: float
    transmitter_beam_radius_m: float
    beam_divergence_mrad: float
    beam_divergence_rad: float
    receiver_aperture_diameter_m: float
    receiver_aperture_radius_m: float
    atmospheric_attenuation_db_per_km: float
    pointing_offset_m: float
    beam_radius_at_receiver_m: float
    beam_diameter_at_receiver_m: float
    geometric_capture_fraction: float
    pointing_transmission_factor: float
    atmospheric_loss_db: float
    atmospheric_transmission_factor: float
    geometric_loss_db: float
    pointing_loss_db: float
    total_link_loss_db: float
    received_power_mw: float
    remaining_power_percent: float
    link_regime: str


def _require_finite_number(value: float, name: str) -> float:
    """Reject booleans, nonnumeric values, NaN, and infinity."""
    if isinstance(value, bool) or not isinstance(value, int | float) or not isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    return float(value)


def _loss_db(transmission_factor: float) -> float:
    """Calculate nonnegative dB loss using a floor only for logarithms."""
    return max(0.0, -10.0 * log10(max(transmission_factor, _LOG_FLOOR)))


def classify_fso_link_regime(remaining_power_percent: float) -> str:
    """Classify deterministic collection strength using educational labels only."""
    remaining_power_percent = _require_finite_number(
        remaining_power_percent, "Remaining optical power percent"
    )
    if remaining_power_percent >= 50.0:
        return "Strong collection"
    if remaining_power_percent >= 10.0:
        return "Moderate collection"
    if remaining_power_percent >= 1.0:
        return "Weak collection"
    return "Very weak collection"


def simulate_fso_link(
    link_distance_km: float,
    transmitted_power_mw: float,
    transmitter_beam_radius_cm: float,
    beam_divergence_mrad: float,
    receiver_aperture_diameter_cm: float,
    atmospheric_attenuation_db_per_km: float,
    pointing_offset_cm: float,
) -> FSOSimulationResult:
    """Simulate a deterministic educational line-of-sight FSO link budget."""
    link_distance_km = _require_finite_number(link_distance_km, "Link distance")
    transmitted_power_mw = _require_finite_number(transmitted_power_mw, "Transmitted optical power")
    transmitter_beam_radius_cm = _require_finite_number(
        transmitter_beam_radius_cm, "Transmitter beam radius"
    )
    beam_divergence_mrad = _require_finite_number(beam_divergence_mrad, "Beam divergence")
    receiver_aperture_diameter_cm = _require_finite_number(
        receiver_aperture_diameter_cm, "Receiver aperture diameter"
    )
    atmospheric_attenuation_db_per_km = _require_finite_number(
        atmospheric_attenuation_db_per_km, "Atmospheric attenuation"
    )
    pointing_offset_cm = _require_finite_number(pointing_offset_cm, "Pointing offset")

    if link_distance_km <= 0:
        raise ValueError("Link distance must be greater than 0 km.")
    if transmitted_power_mw <= 0:
        raise ValueError("Transmitted optical power must be greater than 0 mW.")
    if transmitter_beam_radius_cm <= 0:
        raise ValueError("Transmitter beam radius must be greater than 0 cm.")
    if beam_divergence_mrad < 0:
        raise ValueError("Beam divergence must be 0 mrad or greater.")
    if receiver_aperture_diameter_cm <= 0:
        raise ValueError("Receiver aperture diameter must be greater than 0 cm.")
    if atmospheric_attenuation_db_per_km < 0:
        raise ValueError("Atmospheric attenuation must be 0 dB/km or greater.")
    if pointing_offset_cm < 0:
        raise ValueError("Pointing offset must be 0 cm or greater.")

    link_distance_m = link_distance_km * 1000.0
    transmitter_beam_radius_m = transmitter_beam_radius_cm / 100.0
    beam_divergence_rad = beam_divergence_mrad / 1000.0
    receiver_aperture_diameter_m = receiver_aperture_diameter_cm / 100.0
    receiver_aperture_radius_m = receiver_aperture_diameter_m / 2.0
    pointing_offset_m = pointing_offset_cm / 100.0

    beam_radius_at_receiver_m = transmitter_beam_radius_m + beam_divergence_rad * link_distance_m
    beam_diameter_at_receiver_m = 2.0 * beam_radius_at_receiver_m

    geometric_capture_fraction = 1.0 - exp(
        -2.0 * receiver_aperture_radius_m**2 / beam_radius_at_receiver_m**2
    )
    geometric_capture_fraction = min(1.0, max(0.0, geometric_capture_fraction))
    pointing_transmission_factor = (
        1.0
        if pointing_offset_m == 0.0
        else exp(-2.0 * pointing_offset_m**2 / beam_radius_at_receiver_m**2)
    )
    pointing_transmission_factor = min(1.0, max(0.0, pointing_transmission_factor))
    atmospheric_loss_db = atmospheric_attenuation_db_per_km * link_distance_km
    atmospheric_transmission_factor = 10.0 ** (-atmospheric_loss_db / 10.0)

    received_power_mw = (
        transmitted_power_mw
        * geometric_capture_fraction
        * pointing_transmission_factor
        * atmospheric_transmission_factor
    )
    remaining_power_percent = 100.0 * received_power_mw / transmitted_power_mw
    remaining_power_percent = min(100.0, max(0.0, remaining_power_percent))
    geometric_loss_db = _loss_db(geometric_capture_fraction)
    pointing_loss_db = _loss_db(pointing_transmission_factor)
    total_link_loss_db = atmospheric_loss_db + geometric_loss_db + pointing_loss_db

    return FSOSimulationResult(
        link_distance_km=link_distance_km,
        link_distance_m=link_distance_m,
        transmitted_power_mw=transmitted_power_mw,
        transmitter_beam_radius_m=transmitter_beam_radius_m,
        beam_divergence_mrad=beam_divergence_mrad,
        beam_divergence_rad=beam_divergence_rad,
        receiver_aperture_diameter_m=receiver_aperture_diameter_m,
        receiver_aperture_radius_m=receiver_aperture_radius_m,
        atmospheric_attenuation_db_per_km=atmospheric_attenuation_db_per_km,
        pointing_offset_m=pointing_offset_m,
        beam_radius_at_receiver_m=beam_radius_at_receiver_m,
        beam_diameter_at_receiver_m=beam_diameter_at_receiver_m,
        geometric_capture_fraction=geometric_capture_fraction,
        pointing_transmission_factor=pointing_transmission_factor,
        atmospheric_loss_db=atmospheric_loss_db,
        atmospheric_transmission_factor=atmospheric_transmission_factor,
        geometric_loss_db=geometric_loss_db,
        pointing_loss_db=pointing_loss_db,
        total_link_loss_db=total_link_loss_db,
        received_power_mw=received_power_mw,
        remaining_power_percent=remaining_power_percent,
        link_regime=classify_fso_link_regime(remaining_power_percent),
    )


def build_fso_educational_observations(result: FSOSimulationResult) -> dict[str, list[str]]:
    """Build deterministic learning observations from an FSO result."""
    return {
        "foundation": [
            f"The transmitter beam spreads as it travels {result.link_distance_km:.3g} km through free space.",
            f"The receiver captures only part of the arriving beam: {100 * result.geometric_capture_fraction:.3g}% of the centred Gaussian power.",
            f"Atmospheric attenuation reduces optical power by {result.atmospheric_loss_db:.3g} dB along the path.",
            f"Pointing offset moves the beam away from the receiver centre; this run uses {100 * result.pointing_offset_m:.3g} cm offset.",
            "Geometric spreading and atmospheric attenuation are different effects: one is finite aperture collection, the other is propagation loss.",
        ],
        "engineering": [
            f"Beam radius equation: w_rx = w_0 + theta L = {result.beam_radius_at_receiver_m:.6g} m.",
            f"Aperture-capture equation: eta_geo = 1 - exp(-2 a_rx^2 / w_rx^2) = {result.geometric_capture_fraction:.12g}.",
            f"Pointing-factor equation: eta_point = exp(-2 r_offset^2 / w_rx^2) = {result.pointing_transmission_factor:.12g}.",
            f"Atmospheric attenuation equation: A_atm = gamma L = {result.atmospheric_loss_db:.6g} dB and T_atm = {result.atmospheric_transmission_factor:.12g}.",
            f"Received-power equation: P_rx = P_tx eta_geo eta_point 10^(-A_atm/10) = {result.received_power_mw:.12g} mW.",
            f"Numerical values: P_tx={result.transmitted_power_mw:.6g} mW, w_0={result.transmitter_beam_radius_m:.6g} m, theta={result.beam_divergence_rad:.6g} rad, a_rx={result.receiver_aperture_radius_m:.6g} m.",
            f"Power-budget components are separate: geometric loss {result.geometric_loss_db:.6g} dB, atmospheric loss {result.atmospheric_loss_db:.6g} dB, pointing loss {result.pointing_loss_db:.6g} dB.",
        ],
        "research": [
            "This is a deterministic Gaussian-beam approximation for educational link-budget reasoning.",
            "The linear divergence model w_rx = w_0 + theta L is a simplification, not a complete diffraction solution.",
            "No turbulence or scintillation is simulated.",
            "No receiver or noise model is included.",
            "No BER calculation is performed.",
            "No link availability prediction is made.",
            "A laboratory validation could compare optical power measurements under controlled distance, aperture size, attenuation, and misalignment.",
            "Possible future extensions include turbulence, scintillation, and receiver modelling.",
        ],
    }
