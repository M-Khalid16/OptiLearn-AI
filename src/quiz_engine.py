"""Deterministic formative-assessment engine for OptiLearn AI."""

from dataclasses import dataclass
from math import isfinite

from src.fso_simulator import FSOSimulationResult
from src.optical_simulator import FiberSimulationResult

SUPPORTED_LEVELS = ("Foundation", "Engineering", "Research Perspective")
SUPPORTED_TOPICS = (
    "Fiber Attenuation",
    "Chromatic Dispersion",
    "Free-Space Optical",
    "Model Assumptions",
)
SUPPORTED_QUESTION_TYPES = ("multiple_choice", "numeric", "true_false")
ALL_TOPICS = "All Topics"
ALL_LEVELS = "All Levels"


@dataclass(frozen=True)
class QuizChoice:
    """One deterministic answer choice."""

    id: str
    text: str


@dataclass(frozen=True)
class QuizQuestion:
    """One deterministic quiz question."""

    id: str
    topic: str
    level: str
    question_type: str
    prompt: str
    choices: tuple[QuizChoice, ...]
    correct_choice_id: str | None
    correct_numeric_value: float | None
    numeric_tolerance: float | None
    correct_boolean_value: bool | None
    explanation: str
    units: str | None
    source_label: str


@dataclass(frozen=True)
class QuizAttemptResult:
    """Result of grading one latest submitted answer."""

    question_id: str
    is_correct: bool
    submitted_answer: str
    correct_answer_text: str
    feedback: str


@dataclass(frozen=True)
class QuizSessionSummary:
    """Session-only score summary."""

    attempted_count: int
    correct_count: int
    incorrect_count: int
    score_percent: float


def _choice(id_: str, text: str) -> QuizChoice:
    return QuizChoice(id=id_, text=text)


def _mc(qid, topic, level, prompt, choices, correct, explanation, source):
    return QuizQuestion(qid, topic, level, "multiple_choice", prompt, tuple(choices), correct, None, None, None, explanation, None, source)


def _num(qid, topic, level, prompt, value, tol, units, explanation, source):
    return QuizQuestion(qid, topic, level, "numeric", prompt, (), None, float(value), float(tol), None, explanation, units, source)


def _tf(qid, topic, level, prompt, value, explanation, source):
    return QuizQuestion(qid, topic, level, "true_false", prompt, (), None, None, None, bool(value), explanation, None, source)


def build_quiz_question_bank() -> tuple[QuizQuestion, ...]:
    """Build the auditable deterministic base question bank."""
    qs = (
        _num("fiber_loss_4_db", "Fiber Attenuation", "Engineering", "For alpha = 0.2 dB/km and L = 20 km, what is the total fiber loss A = alpha L?", 4.0, 1e-9, "dB", "A = alpha L = 0.2 × 20 = 4 dB.", "Fiber attenuation model"),
        _num("fiber_prx_4_db", "Fiber Attenuation", "Engineering", "For P_tx = 1 mW and total loss = 4 dB, what is P_rx = P_tx 10^(-A/10)?", 0.398107, 1e-6, "mW", "The transmission is 10^(-4/10) = 0.398107, so P_rx is about 0.398107 mW.", "Fiber attenuation model"),
        _num("fiber_remaining_4_db", "Fiber Attenuation", "Engineering", "For total loss = 4 dB, what percentage of optical power remains?", 39.8107, 1e-4, "%", "Remaining power is 100 × 10^(-4/10) = 39.8107%.", "Fiber attenuation model"),
        _num("fiber_bit_duration_10g", "Fiber Attenuation", "Engineering", "At 10 Gbit/s, what is the bit duration T_b in ns?", 0.1, 1e-9, "ns", "T_b = 1/R_b. Since 1 Gbit/s corresponds to 1 ns per bit, 10 Gbit/s gives 0.1 ns.", "Fiber attenuation model"),
        _tf("fiber_length_increases_loss", "Fiber Attenuation", "Foundation", "Increasing fiber length increases attenuation loss when alpha is fixed.", True, "The model uses A = alpha L, so loss grows linearly with fiber length.", "Fiber attenuation model"),
        _tf("fiber_bitrate_not_attenuation", "Fiber Attenuation", "Research Perspective", "Changing bit rate changes attenuation loss in the current simplified attenuation equation.", False, "The attenuation equation depends on alpha and length, not bit rate.", "Fiber attenuation model"),
        _mc("fiber_attenuation_shape", "Fiber Attenuation", "Foundation", "In attenuation-only mode, what does attenuation change?", (_choice("a", "Pulse amplitude/power level"), _choice("b", "Pulse temporal shape"), _choice("c", "Bit sequence")), "a", "Attenuation scales optical power without modelling temporal pulse spreading.", "Fiber attenuation model"),
        _tf("fiber_no_ber", "Fiber Attenuation", "Research Perspective", "The current fiber attenuation model calculates BER from received power.", False, "BER is outside the current deterministic prototype scope.", "Model-scope specification"),
        _mc("fiber_linear_db", "Fiber Attenuation", "Engineering", "Which expression converts dB loss A into linear transmission T?", (_choice("a", "T = 10^(-A/10)"), _choice("b", "T = 10A"), _choice("c", "T = A/10")), "a", "Power ratios in dB convert through 10^(-A/10) for loss.", "Fiber attenuation model"),
        _num("disp_broadening_34_ps", "Chromatic Dispersion", "Engineering", "For D = 17 ps/(nm·km), Delta_lambda = 0.1 nm, and L = 20 km, what is Delta_t?", 34.0, 1e-9, "ps", "Delta_t = |17| × 0.1 × 20 = 34 ps.", "Chromatic dispersion model"),
        _num("disp_34ps_to_ns", "Chromatic Dispersion", "Engineering", "Convert 34 ps to ns.", 0.034, 1e-12, "ns", "1 ns = 1000 ps, so 34 ps = 0.034 ns.", "Chromatic dispersion model"),
        _num("disp_ratio_034", "Chromatic Dispersion", "Engineering", "With Delta_t = 0.034 ns and T_b = 0.1 ns, what is the broadening ratio?", 0.34, 1e-12, None, "The ratio is Delta_t / T_b = 0.034 / 0.1 = 0.34.", "Chromatic dispersion model"),
        _mc("disp_noticeable", "Chromatic Dispersion", "Foundation", "A broadening ratio of 0.34 is classified as what regime?", (_choice("a", "Small"), _choice("b", "Noticeable"), _choice("c", "Severe overlap risk")), "b", "The educational classifier labels ratios from 0.1 up to 0.5 as Noticeable.", "Chromatic dispersion model"),
        _tf("disp_sign_magnitude", "Chromatic Dispersion", "Engineering", "Positive and negative D with the same magnitude produce equal broadening magnitude in this model.", True, "The formula uses |D|, so the sign is not used for broadening magnitude.", "Chromatic dispersion model"),
        _tf("disp_zero_d", "Chromatic Dispersion", "Foundation", "Zero chromatic dispersion coefficient produces no temporal broadening.", True, "Delta_t = |D| Delta_lambda L, so D = 0 makes Delta_t zero.", "Chromatic dispersion model"),
        _tf("disp_zero_width", "Chromatic Dispersion", "Foundation", "Zero source spectral width produces no dispersion broadening in this model.", True, "Delta_lambda = 0 makes Delta_t zero.", "Chromatic dispersion model"),
        _mc("disp_not_loss", "Chromatic Dispersion", "Research Perspective", "What does chromatic dispersion change in this educational model?", (_choice("a", "Temporal shape"), _choice("b", "Attenuation coefficient"), _choice("c", "Transmitted bit values")), "a", "Dispersion is represented as temporal broadening, while attenuation loss is calculated separately.", "Chromatic dispersion model"),
        _tf("disp_gaussian_approx", "Chromatic Dispersion", "Research Perspective", "The Gaussian convolution is an educational approximation, not a full optical-field propagation model.", True, "The convolution demonstrates pulse spreading without modelling full field physics.", "Chromatic dispersion model"),
        _tf("disp_no_ber", "Chromatic Dispersion", "Research Perspective", "The current app calculates BER from the broadening ratio.", False, "The broadening ratio is explanatory only and is not converted to BER.", "Model-scope specification"),
        _num("fso_beam_radius_default", "Free-Space Optical", "Engineering", "Using default FSO values, what is w_rx = w_0 + theta L?", 1.02, 1e-12, "m", "w_0 = 0.02 m and theta L = 0.001 × 1000 = 1 m, so w_rx = 1.02 m.", "FSO link-budget model"),
        _num("fso_atm_loss_default", "Free-Space Optical", "Engineering", "Using gamma = 1 dB/km and L = 1 km, what is atmospheric loss?", 1.0, 1e-12, "dB", "A_atm = gamma L = 1 × 1 = 1 dB.", "FSO link-budget model"),
        _num("fso_atm_trans_default", "Free-Space Optical", "Engineering", "For 1 dB atmospheric loss, what is atmospheric transmission?", 0.794328, 1e-6, None, "Atmospheric transmission is 10^(-1/10) = 0.794328.", "FSO link-budget model"),
        _num("fso_geo_default", "Free-Space Optical", "Engineering", "Using the default FSO aperture and beam radius, what geometric capture percentage is collected?", 1.904, 0.001, "%", "eta_geo = 1 - exp(-2a^2/w^2) with a = 0.1 m and w = 1.02 m gives about 1.904%.", "FSO link-budget model"),
        _num("fso_prx_default", "Free-Space Optical", "Engineering", "Using default FSO values and zero pointing offset, what received power is predicted?", 0.151238, 1e-6, "mW", "P_rx = 10 mW × eta_geo × 1 × 0.794328, which is about 0.151238 mW.", "FSO link-budget model"),
        _num("fso_remaining_default", "Free-Space Optical", "Engineering", "Using default FSO values, what percentage of transmitted power remains?", 1.512, 0.001, "%", "Remaining power is 100 × P_rx/P_tx, about 1.512%.", "FSO link-budget model"),
        _mc("fso_regime_default", "Free-Space Optical", "Foundation", "The default FSO remaining power is about 1.512%. What is the regime?", (_choice("a", "Strong collection"), _choice("b", "Weak collection"), _choice("c", "Very weak collection")), "b", "The deterministic classifier labels 1% to below 10% as Weak collection.", "FSO link-budget model"),
        _tf("fso_aperture_monotonic", "Free-Space Optical", "Research Perspective", "Increasing receiver aperture cannot reduce geometric capture in the current equation.", True, "A larger aperture radius increases or preserves the captured fraction for a fixed beam radius.", "FSO link-budget model"),
        _tf("fso_divergence_capture", "Free-Space Optical", "Foundation", "Increasing beam divergence improves geometric capture for fixed distance and aperture.", False, "Larger divergence increases beam radius at the receiver, reducing the fraction captured by a fixed aperture.", "FSO link-budget model"),
        _tf("fso_pointing", "Free-Space Optical", "Foundation", "Increasing pointing offset cannot improve received power in this centred Gaussian model.", True, "The pointing factor exp(-2r^2/w^2) decreases as offset increases.", "FSO link-budget model"),
        _tf("fso_zero_pointing", "Free-Space Optical", "Engineering", "Zero pointing offset gives pointing factor 1.", True, "With r_offset = 0, the pointing transmission factor is 1.", "FSO link-budget model"),
        _tf("fso_zero_atm", "Free-Space Optical", "Engineering", "Zero atmospheric attenuation gives atmospheric transmission 1.", True, "If A_atm is 0 dB, 10^(-A_atm/10) equals 1.", "FSO link-budget model"),
        _tf("fso_no_turbulence", "Free-Space Optical", "Research Perspective", "The FSO model simulates turbulence and scintillation.", False, "Turbulence and scintillation are explicitly outside the current FSO model.", "Model-scope specification"),
        _mc("scope_unsupported", "Model Assumptions", "Foundation", "Which quantity is not calculated by the current prototype?", (_choice("a", "BER"), _choice("b", "Total fiber loss"), _choice("c", "FSO received power")), "a", "BER requires receiver/noise assumptions that are not included.", "Model-scope specification"),
        _mc("scope_noise", "Model Assumptions", "Research Perspective", "Which set is outside the current deterministic model scope?", (_choice("a", "SNR, OSNR, receiver noise, photodetection"), _choice("b", "A = alpha L"), _choice("c", "w_rx = w_0 + theta L")), "a", "Noise and receiver detection models are not implemented.", "Model-scope specification"),
        _mc("scope_fiber_missing", "Model Assumptions", "Research Perspective", "Which fiber effect is not modelled?", (_choice("a", "Nonlinear fiber effects"), _choice("b", "Linear attenuation"), _choice("c", "Educational chromatic broadening")), "a", "Nonlinear propagation is beyond this prototype.", "Model-scope specification"),
        _tf("scope_python_truth", "Model Assumptions", "Engineering", "Python deterministic simulation code is the scientific source of truth for calculated values.", True, "AI text may explain values, but simulation values come from deterministic Python calculations.", "Model-scope specification"),
        _tf("scope_ai_no_modify", "Model Assumptions", "Foundation", "AI explanations calculate and modify simulation values before display.", False, "AI explanations are grounded on supplied evidence and do not calculate or modify simulation outputs.", "Model-scope specification"),
        _tf("scope_separate_grounding", "Model Assumptions", "Research Perspective", "Lecture-note grounding and deterministic simulation evidence are separate sources of context.", True, "Tutor answers use retrieved lecture-note passages; simulation explanations use scalar simulation evidence.", "Model-scope specification"),
        _tf("scope_scanned_ocr", "Model Assumptions", "Foundation", "Scanned PDFs require OCR outside the current prototype.", True, "The current PDF parser expects machine-readable text and does not include OCR.", "Model-scope specification"),
        _mc("scope_availability", "Model Assumptions", "Research Perspective", "Which conclusion cannot be drawn from the prototype alone?", (_choice("a", "Certified link availability"), _choice("b", "Default FSO geometric capture"), _choice("c", "Default fiber total loss")), "a", "Link availability needs environmental statistics and reliability modelling that are not included.", "Model-scope specification"),
    )
    validate_question_bank(qs)
    return qs


def validate_quiz_question(question: QuizQuestion) -> None:
    """Validate one quiz question and raise ValueError when malformed."""
    if not isinstance(question.id, str) or not question.id.strip():
        raise ValueError("Question ID must be nonempty.")
    if question.topic not in SUPPORTED_TOPICS:
        raise ValueError("Unsupported quiz topic.")
    if question.level not in SUPPORTED_LEVELS:
        raise ValueError("Unsupported quiz level.")
    if question.question_type not in SUPPORTED_QUESTION_TYPES:
        raise ValueError("Unsupported quiz question type.")
    if not isinstance(question.prompt, str) or not question.prompt.strip():
        raise ValueError("Question prompt must be nonempty.")
    if not isinstance(question.explanation, str) or not question.explanation.strip():
        raise ValueError("Question explanation must be nonempty.")
    if not isinstance(question.source_label, str) or not question.source_label.strip():
        raise ValueError("Question source label must be nonempty.")
    if question.question_type == "multiple_choice":
        if len(question.choices) < 2:
            raise ValueError("Multiple-choice questions need at least two choices.")
        ids = [choice.id for choice in question.choices]
        if len(ids) != len(set(ids)):
            raise ValueError("Choice IDs must be unique within a question.")
        if any(not choice.id.strip() or not choice.text.strip() for choice in question.choices):
            raise ValueError("Choice IDs and text must be nonempty.")
        if ids.count(question.correct_choice_id) != 1:
            raise ValueError("Correct choice ID must match exactly one choice.")
        if question.correct_numeric_value is not None or question.numeric_tolerance is not None or question.correct_boolean_value is not None:
            raise ValueError("Multiple-choice questions cannot define numeric or boolean answers.")
    elif question.question_type == "numeric":
        if question.choices or question.correct_choice_id is not None or question.correct_boolean_value is not None:
            raise ValueError("Numeric questions cannot define choices or boolean answers.")
        if question.correct_numeric_value is None or not isfinite(question.correct_numeric_value):
            raise ValueError("Numeric answer must be finite.")
        if question.numeric_tolerance is None or not isfinite(question.numeric_tolerance) or question.numeric_tolerance < 0:
            raise ValueError("Numeric tolerance must be finite and nonnegative.")
    else:
        if question.choices or question.correct_choice_id is not None or question.correct_numeric_value is not None or question.numeric_tolerance is not None:
            raise ValueError("True/false questions cannot define choices or numeric answers.")
        if not isinstance(question.correct_boolean_value, bool):
            raise ValueError("True/false answer must be a bool.")


def validate_question_bank(questions: tuple[QuizQuestion, ...]) -> None:
    """Validate complete deterministic question bank coverage."""
    if not questions:
        raise ValueError("Question bank must be nonempty.")
    ids: set[str] = set()
    for question in questions:
        validate_quiz_question(question)
        if question.id in ids:
            raise ValueError("Question IDs must be unique.")
        ids.add(question.id)
    topics = {q.topic for q in questions}
    levels = {q.level for q in questions}
    types = {q.question_type for q in questions}
    if topics != set(SUPPORTED_TOPICS) or levels != set(SUPPORTED_LEVELS) or types != set(SUPPORTED_QUESTION_TYPES):
        raise ValueError("Question bank must represent all supported topics, levels, and types.")
    if len(questions) < 30:
        raise ValueError("Question bank must contain at least 30 questions.")
    minimums = {"Fiber Attenuation": 8, "Chromatic Dispersion": 8, "Free-Space Optical": 8, "Model Assumptions": 6}
    for topic, minimum in minimums.items():
        if sum(q.topic == topic for q in questions) < minimum:
            raise ValueError(f"Question bank needs at least {minimum} {topic} questions.")


def filter_quiz_questions(questions: tuple[QuizQuestion, ...], topic: str, level: str) -> tuple[QuizQuestion, ...]:
    """Filter questions deterministically while preserving original order."""
    if topic != ALL_TOPICS and topic not in SUPPORTED_TOPICS:
        raise ValueError("Unsupported topic filter.")
    if level != ALL_LEVELS and level not in SUPPORTED_LEVELS:
        raise ValueError("Unsupported level filter.")
    return tuple(q for q in questions if (topic == ALL_TOPICS or q.topic == topic) and (level == ALL_LEVELS or q.level == level))


def _correct_answer_text(question: QuizQuestion) -> str:
    if question.question_type == "multiple_choice":
        return next(choice.text for choice in question.choices if choice.id == question.correct_choice_id)
    if question.question_type == "numeric":
        suffix = f" {question.units}" if question.units else ""
        return f"{question.correct_numeric_value:.12g}{suffix}"
    return "True" if question.correct_boolean_value else "False"


def evaluate_quiz_answer(question: QuizQuestion, submitted_answer: str | float | bool) -> QuizAttemptResult:
    """Grade one answer deterministically."""
    validate_quiz_question(question)
    correct_text = _correct_answer_text(question)
    submitted_text = str(submitted_answer)
    is_correct = False
    if question.question_type == "multiple_choice":
        is_correct = isinstance(submitted_answer, str) and submitted_answer == question.correct_choice_id
    elif question.question_type == "numeric":
        if not isinstance(submitted_answer, bool):
            try:
                submitted_value = float(submitted_answer)
            except (TypeError, ValueError):
                submitted_value = float("nan")
            is_correct = isfinite(submitted_value) and abs(submitted_value - question.correct_numeric_value) <= question.numeric_tolerance
    else:
        normalized = submitted_answer
        if isinstance(submitted_answer, str):
            lowered = submitted_answer.strip().lower()
            normalized = True if lowered == "true" else False if lowered == "false" else None
        is_correct = isinstance(normalized, bool) and normalized is question.correct_boolean_value
    prefix = "Correct." if is_correct else "Not quite."
    feedback = f"{prefix} {question.explanation}"
    return QuizAttemptResult(question.id, is_correct, submitted_text, correct_text, feedback)


def summarize_quiz_attempts(attempts: dict[str, QuizAttemptResult]) -> QuizSessionSummary:
    """Summarize latest attempt per question."""
    attempted = len(attempts)
    correct = sum(1 for result in attempts.values() if result.is_correct)
    incorrect = attempted - correct
    score = 0.0 if attempted == 0 else 100.0 * correct / attempted
    return QuizSessionSummary(attempted, correct, incorrect, score)


def _fingerprint(*values: object) -> str:
    return "_".join(str(value).replace(" ", "-") for value in values)


def build_fiber_result_questions(result: FiberSimulationResult) -> tuple[QuizQuestion, ...]:
    """Build up to five scalar-only questions from a fiber simulation result."""
    dispersion_enabled = getattr(result, "dispersion_enabled", getattr(result, "simulation_mode", "") == "Attenuation + Chromatic Dispersion")
    suffix = _fingerprint("fiber", dispersion_enabled, f"{result.total_loss_db:.6g}", f"{result.received_power_mw:.6g}", f"{result.bit_duration_ns:.6g}", f"{result.broadening_ratio:.6g}")
    questions = [
        _num(f"current_{suffix}_loss", "Fiber Attenuation", "Engineering", "For the current fiber simulation, what is the total loss?", result.total_loss_db, max(1e-9, abs(result.total_loss_db) * 1e-6), "dB", "This is the deterministic scalar total_loss_db from the current fiber result.", "Current simulation evidence"),
        _num(f"current_{suffix}_prx", "Fiber Attenuation", "Engineering", "For the current fiber simulation, what is the received power?", result.received_power_mw, max(1e-9, abs(result.received_power_mw) * 1e-6), "mW", "This is the deterministic scalar received_power_mw from the current fiber result.", "Current simulation evidence"),
        _num(f"current_{suffix}_tb", "Fiber Attenuation", "Engineering", "For the current fiber simulation, what is the bit duration?", result.bit_duration_ns, max(1e-12, abs(result.bit_duration_ns) * 1e-6), "ns", "This is the deterministic scalar bit_duration_ns from the current fiber result.", "Current simulation evidence"),
    ]
    if dispersion_enabled:
        questions.extend([
            _num(f"current_{suffix}_broadening_ps", "Chromatic Dispersion", "Engineering", "For the current dispersion simulation, what is the temporal broadening?", result.temporal_broadening_ps, max(1e-9, abs(result.temporal_broadening_ps) * 1e-6), "ps", "This is the deterministic scalar temporal_broadening_ps from the current result.", "Current simulation evidence"),
            _mc(f"current_{suffix}_regime", "Chromatic Dispersion", "Foundation", "For the current dispersion simulation, what is the dispersion regime?", (_choice("Small", "Small"), _choice("Noticeable", "Noticeable"), _choice("Substantial", "Substantial"), _choice("Severe overlap risk", "Severe overlap risk")), result.dispersion_regime, "The regime is the deterministic classifier output from the current result.", "Current simulation evidence"),
        ])
    return tuple(questions[:5])


def build_fso_result_questions(result: FSOSimulationResult) -> tuple[QuizQuestion, ...]:
    """Build up to five scalar-only questions from an FSO simulation result."""
    suffix = _fingerprint("fso", f"{result.link_distance_km:.6g}", f"{result.beam_radius_at_receiver_m:.6g}", f"{result.received_power_mw:.6g}")
    questions = (
        _num(f"current_{suffix}_beam", "Free-Space Optical", "Engineering", "For the current FSO simulation, what is the beam radius at the receiver?", result.beam_radius_at_receiver_m, max(1e-9, abs(result.beam_radius_at_receiver_m) * 1e-6), "m", "This is the deterministic scalar beam_radius_at_receiver_m from the current FSO result.", "Current simulation evidence"),
        _num(f"current_{suffix}_atm", "Free-Space Optical", "Engineering", "For the current FSO simulation, what is the atmospheric loss?", result.atmospheric_loss_db, max(1e-9, abs(result.atmospheric_loss_db) * 1e-6), "dB", "This is the deterministic scalar atmospheric_loss_db from the current FSO result.", "Current simulation evidence"),
        _num(f"current_{suffix}_geo", "Free-Space Optical", "Engineering", "For the current FSO simulation, what geometric capture percentage is collected?", 100.0 * result.geometric_capture_fraction, max(1e-9, abs(100.0 * result.geometric_capture_fraction) * 1e-6), "%", "This is the deterministic scalar geometric capture fraction expressed as a percentage.", "Current simulation evidence"),
        _num(f"current_{suffix}_prx", "Free-Space Optical", "Engineering", "For the current FSO simulation, what is the received power?", result.received_power_mw, max(1e-9, abs(result.received_power_mw) * 1e-6), "mW", "This is the deterministic scalar received_power_mw from the current FSO result.", "Current simulation evidence"),
        _mc(f"current_{suffix}_regime", "Free-Space Optical", "Foundation", "For the current FSO simulation, what is the link regime?", (_choice("Strong collection", "Strong collection"), _choice("Moderate collection", "Moderate collection"), _choice("Weak collection", "Weak collection"), _choice("Very weak collection", "Very weak collection")), result.link_regime, "The regime is the deterministic classifier output from the current FSO result.", "Current simulation evidence"),
    )
    return questions
