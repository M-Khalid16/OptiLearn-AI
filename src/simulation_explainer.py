"""OpenAI-powered explanations for deterministic fiber simulation results."""

from dataclasses import asdict, dataclass
import hashlib
import json
from math import isfinite
import re
from typing import Any

from openai import OpenAI

from src.optical_simulator import FiberSimulationResult


SUPPORTED_EXPLANATION_LEVELS = (
    "Foundation",
    "Engineering",
    "Research Perspective",
)
_UNSUPPORTED_CAPABILITY_MESSAGE = (
    "The generated explanation included a capability that is outside the current simulation model."
)


@dataclass(frozen=True)
class SimulationEvidence:
    """Scalar evidence extracted from a deterministic fiber simulation result."""

    bit_sequence: str
    bit_count: int
    bit_rate_gbps: float
    bit_duration_ns: float
    transmitted_power_mw: float
    received_power_mw: float
    fiber_length_km: float
    attenuation_db_per_km: float
    total_loss_db: float
    linear_attenuation_factor: float
    remaining_power_percent: float
    samples_per_bit: int


@dataclass(frozen=True)
class SimulationExplanation:
    """Generated explanation plus the exact scalar evidence it explains."""

    explanation_text: str
    model: str
    level: str
    evidence: SimulationEvidence


def _require_finite_scalar(value: float | int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float) or not isfinite(value):
        raise ValueError(f"{name} must be a finite scalar value.")


def build_simulation_evidence(result: FiberSimulationResult) -> SimulationEvidence:
    """Build scalar evidence from a deterministic simulation result."""
    bits = tuple(result.bits)
    if not bits:
        raise ValueError("Simulation result must contain at least one bit.")
    if any(isinstance(bit, bool) or bit not in (0, 1) for bit in bits):
        raise ValueError("Simulation result bits must be binary values: 0 or 1.")

    scalar_values = {
        "bit_rate_gbps": result.bit_rate_gbps,
        "bit_duration_ns": result.bit_duration_ns,
        "transmitted_power_mw": result.transmitted_power_mw,
        "received_power_mw": result.received_power_mw,
        "fiber_length_km": result.fiber_length_km,
        "attenuation_db_per_km": result.attenuation_db_per_km,
        "total_loss_db": result.total_loss_db,
        "linear_attenuation_factor": result.linear_attenuation_factor,
        "remaining_power_percent": result.remaining_power_percent,
        "samples_per_bit": result.samples_per_bit,
    }
    for name, value in scalar_values.items():
        _require_finite_scalar(value, name)
    if isinstance(result.samples_per_bit, bool) or not isinstance(result.samples_per_bit, int):
        raise ValueError("samples_per_bit must be an integer scalar value.")

    return SimulationEvidence(
        bit_sequence="".join(str(bit) for bit in bits),
        bit_count=len(bits),
        bit_rate_gbps=result.bit_rate_gbps,
        bit_duration_ns=result.bit_duration_ns,
        transmitted_power_mw=result.transmitted_power_mw,
        received_power_mw=result.received_power_mw,
        fiber_length_km=result.fiber_length_km,
        attenuation_db_per_km=result.attenuation_db_per_km,
        total_loss_db=result.total_loss_db,
        linear_attenuation_factor=result.linear_attenuation_factor,
        remaining_power_percent=result.remaining_power_percent,
        samples_per_bit=result.samples_per_bit,
    )


def format_simulation_evidence(evidence: SimulationEvidence) -> str:
    """Format deterministic scalar evidence for display and OpenAI grounding."""
    return "\n".join(
        [
            "SIMULATION INPUTS",
            f"Bit sequence: {evidence.bit_sequence}",
            f"Bit count: {evidence.bit_count}",
            f"Bit rate: {evidence.bit_rate_gbps:.12g} Gbit/s",
            f"Transmitted optical power: {evidence.transmitted_power_mw:.12g} mW",
            f"Fiber length: {evidence.fiber_length_km:.12g} km",
            f"Attenuation coefficient: {evidence.attenuation_db_per_km:.12g} dB/km",
            "",
            "DETERMINISTIC PYTHON RESULTS",
            f"Bit duration: {evidence.bit_duration_ns:.12g} ns",
            f"Total fiber loss: {evidence.total_loss_db:.12g} dB",
            f"Linear attenuation factor: {evidence.linear_attenuation_factor:.12g}",
            f"Received optical power: {evidence.received_power_mw:.12g} mW",
            f"Remaining optical power: {evidence.remaining_power_percent:.12g}%",
            f"Samples per bit: {evidence.samples_per_bit}",
            "",
            "MODEL SCOPE",
            "- Ideal NRZ/OOK transmitter",
            "- Logical zero has zero optical power",
            "- Constant attenuation coefficient",
            "- Attenuation only",
            "- Pulse amplitude changes",
            "- Pulse shape is preserved",
            "- No connector or splice loss",
            "- No dispersion",
            "- No optical or electrical noise",
            "- No receiver model",
            "- No BER calculation",
            "- No nonlinear effects",
        ]
    )


def build_simulation_explanation_instructions(level: str) -> str:
    """Build grounded Responses API instructions for the selected learning level."""
    if level not in SUPPORTED_EXPLANATION_LEVELS:
        raise ValueError("Unsupported simulation explanation level.")
    level_guidance = {
        "Foundation": (
            "Explain the physical meaning intuitively. Define attenuation and optical power. "
            "Explain what logical ones and zeros represent. Avoid unnecessary mathematics. "
            "Remain scientifically accurate. Explicitly state that amplitude changes but pulse shape does not change in this model."
        ),
        "Engineering": (
            "Explain the equations A = alpha L, T = 10^(-A/10), P_rx = P_tx T, and T_b = 1/R_b. "
            "Define each variable and unit. Explain cause-and-effect relationships, distinguish dB and linear power, "
            "explain why bit rate changes the time scale but not attenuation in this simplified model, and distinguish inputs, calculated results, and assumptions."
        ),
        "Research Perspective": (
            "Describe model assumptions, state the domain of validity, discuss what conclusions cannot be drawn, "
            "explain missing physics, mention experimental validation using calibrated optical power measurements, "
            "identify logical higher-fidelity extensions, and avoid claiming experimental or full-system accuracy."
        ),
    }
    return (
        "You are explaining one deterministic optical-fiber attenuation simulation for OptiLearn AI. "
        "The supplied simulation evidence is authoritative. All numerical values were calculated in Python. "
        "Do not recalculate, alter, round inconsistently, or contradict those values. Do not invent parameters. "
        "Do not invent equations beyond the specified attenuation model. Do not claim dispersion, noise, detection, BER, nonlinearities, or free-space optical effects were simulated. "
        "Do not claim experimental validation occurred. Distinguish simulation facts from educational interpretation. "
        "Explain only the supplied simulation. Do not use web knowledge. Do not request tools. Do not mention lecture-note grounding. "
        "Do not imply that the AI controlled the simulation. Recommended structure: 1. Direct Interpretation 2. What the Python Simulation Calculated 3. Physical Meaning 4. Assumptions and Limitations. "
        f"Learning level: {level}. {level_guidance[level]}"
    )


def simulation_evidence_fingerprint(evidence: SimulationEvidence) -> str:
    """Return a SHA-256 fingerprint for scalar simulation evidence."""
    payload = json.dumps(asdict(evidence), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _split_capability_clauses(explanation_text: str) -> list[str]:
    """Split generated text into local clauses for unsupported-claim checks."""
    normalized = re.sub(r"\s+", " ", explanation_text.strip())
    clauses = re.split(
        r"(?<=[.!?;])\s+|\s*,\s*(?:but|and|while|although|though|whereas)\s+|\s+\b(?:but|while|whereas)\b\s+",
        normalized,
        flags=re.IGNORECASE,
    )
    return [clause.strip(" ,;:.!?\t\n") for clause in clauses if clause.strip(" ,;:.!?\t\n")]


_CAPABILITY_PATTERNS = {
    "dispersion": r"\b(?:chromatic\s+)?dispersion\b",
    "noise": r"\b(?:receiver\s+|optical\s+|electrical\s+)?noise\b",
    "ber": r"\bBER\b|\bbit[- ]error\s+rate\b",
    "eye_diagram": r"\beye\s+diagrams?\b",
    "receiver": r"\breceivers?\b",
    "nonlinear": r"\bnonlinear\s+effects?\b|\bnonlinearities\b",
    "free_space": r"\bfree[- ]space\s+optical(?:\s+propagation)?\b",
}
_ACTION_PATTERN = (
    r"\b(?:simulat(?:ed|es|e|ing)|includ(?:ed|es|e|ing)|calculat(?:ed|es|e|ing)|"
    r"comput(?:ed|es|e|ing)|estimat(?:ed|es|e|ing)|predict(?:ed|s|ing)?|"
    r"generat(?:ed|es|e|ing)|modell?ed|modell?ing|models?|perform(?:ed|s|ing)?)\b"
)
_LIMITATION_PATTERN = (
    r"\b(?:no|not|never|without|absent|excludes?|excluded|outside|beyond|"
    r"does\s+not|did\s+not|is\s+not|was\s+not|were\s+not|are\s+not|"
    r"cannot|can't|not\s+included|not\s+performed|not\s+part\s+of)\b"
)


def _contains_capability(clause: str, capability_pattern: str) -> bool:
    return re.search(capability_pattern, clause, flags=re.IGNORECASE) is not None


def _is_limitation_for_capability(clause: str, capability_pattern: str) -> bool:
    cap_then_limitation = rf"(?:{capability_pattern})[^.;,]*{_LIMITATION_PATTERN}"
    limitation_then_cap = rf"{_LIMITATION_PATTERN}[^.;,]*(?:{capability_pattern})"
    return bool(
        re.search(cap_then_limitation, clause, flags=re.IGNORECASE)
        or re.search(limitation_then_cap, clause, flags=re.IGNORECASE)
    )


def _is_affirmative_capability_claim(clause: str, capability_pattern: str) -> bool:
    capability_then_action = rf"(?:{capability_pattern})[^.;,]*{_ACTION_PATTERN}"
    action_then_capability = rf"{_ACTION_PATTERN}[^.;,]*(?:{capability_pattern})"
    return bool(
        re.search(capability_then_action, clause, flags=re.IGNORECASE)
        or re.search(action_then_capability, clause, flags=re.IGNORECASE)
    )


def validate_simulation_explanation(explanation_text: str, evidence: SimulationEvidence) -> None:
    """Reject blank explanations or affirmative unsupported simulation claims."""
    if not isinstance(evidence, SimulationEvidence):
        raise ValueError("evidence must be a SimulationEvidence instance.")
    if not isinstance(explanation_text, str) or not explanation_text.strip():
        raise RuntimeError("The OpenAI response did not contain a simulation explanation.")

    for clause in _split_capability_clauses(explanation_text):
        for capability_pattern in _CAPABILITY_PATTERNS.values():
            if not _contains_capability(clause, capability_pattern):
                continue
            if _is_limitation_for_capability(clause, capability_pattern):
                continue
            if _is_affirmative_capability_claim(clause, capability_pattern):
                raise RuntimeError(_UNSUPPORTED_CAPABILITY_MESSAGE)


def generate_simulation_explanation(
    result: FiberSimulationResult,
    level: str,
    api_key: str,
    model: str = "gpt-5-mini",
    client: Any | None = None,
) -> SimulationExplanation:
    """Generate an AI explanation for Python-calculated simulation results."""
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("OpenAI API key must be configured.")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("OpenAI model must be a nonempty string.")
    evidence = build_simulation_evidence(result)
    evidence_text = format_simulation_evidence(evidence)
    instructions = build_simulation_explanation_instructions(level)
    openai_client = client if client is not None else OpenAI(api_key=api_key.strip())
    response = openai_client.responses.create(
        model=model.strip(),
        instructions=instructions,
        input=evidence_text,
        store=False,
    )
    explanation_text = getattr(response, "output_text", "")
    if not isinstance(explanation_text, str) or not explanation_text.strip():
        raise RuntimeError("The OpenAI response did not contain a simulation explanation.")
    validate_simulation_explanation(explanation_text, evidence)
    return SimulationExplanation(
        explanation_text=explanation_text.strip(),
        model=model.strip(),
        level=level,
        evidence=evidence,
    )
