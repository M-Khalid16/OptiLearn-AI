"""Streamlit application shell for OptiLearn AI."""

from collections.abc import Callable
import hashlib
import os
from pathlib import PurePath

from openai import APIConnectionError, APIError, AuthenticationError, RateLimitError
import streamlit as st

from src.ai_tutor import (
    generate_grounded_answer,
    normalize_question,
    validate_answer_citations,
)
from src.pdf_parser import PDFDocument, extract_pdf_document
from src.quiz_engine import (
    ALL_LEVELS,
    ALL_TOPICS,
    SUPPORTED_LEVELS,
    SUPPORTED_TOPICS,
    QuizQuestion,
    build_fiber_result_questions,
    build_fso_result_questions,
    build_quiz_question_bank,
    evaluate_quiz_answer,
    filter_quiz_questions,
    summarize_quiz_attempts,
)

from src.fso_simulator import (
    build_fso_educational_observations,
    simulate_fso_link,
)
from src.optical_simulator import (
    build_educational_observations,
    simulate_fiber_attenuation,
    simulate_fiber_dispersion,
)
from src.simulation_explainer import (
    build_fso_simulation_evidence,
    build_simulation_evidence,
    format_simulation_evidence,
    generate_simulation_explanation,
    simulation_evidence_fingerprint,
)
from src.lp_mode_solver import (
    calculate_gaussian_launch_field,
    calculate_longitudinal_mode_slice,
    calculate_lp_mode_field,
    calculate_lp_mode_intensity,
    calculate_mode_coupling,
    solve_lp_modes,
)
from src.ray_tracer import RayLaunch, trace_meridional_ray, trace_skew_ray

from src.ui_components import (
    inject_global_styles,
    render_feature_card,
    render_footer,
    render_learning_step,
    render_next_step,
    render_page_header,
    render_scientific_trust_panel,
    render_scope_notice,
    render_status_badge,
)

from src.visualizations import (
    create_dispersion_comparison_figure,
    create_fso_beam_profile_figure,
    create_fso_power_budget_figure,
    create_signal_comparison_figure,
    create_launch_field_figure,
    create_lp_mode_cross_section_figure,
    create_lp_mode_longitudinal_figure,
    create_meridional_ray_figure,
    create_mode_coupling_figure,
    create_skew_ray_figure,
)


PageRenderer = Callable[[], None]


def _is_demo_mode_enabled() -> bool:
    """Return whether transparent local demo mode is enabled."""
    try:
        value = st.secrets["OPTILEARN_DEMO_MODE"]
    except (KeyError, FileNotFoundError):
        value = os.environ.get("OPTILEARN_DEMO_MODE", "")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _request_page(page: str) -> None:
    """Safely request sidebar navigation on the next rerun."""
    st.session_state["requested_page"] = page
    st.rerun()


def render_home() -> None:
    """Render the polished project landing page."""
    st.markdown('<div class="optilearn-hero">', unsafe_allow_html=True)
    render_page_header(
        "OptiLearn AI",
        "AI-Powered Educational Digital Twin for Optical Communication",
        eyebrow="OpenAI Build Week Prototype",
        badge="OpenAI Build Week Prototype",
    )
    st.header("Learn optical communication by exploring the physics—not just memorizing the equations.")
    st.write("OptiLearn AI combines grounded tutoring, deterministic digital twins, formative quizzes, and interactive optical-fiber mode visualization in one educational workspace.")
    st.info("Scientific values are calculated in deterministic Python models. AI is used only for grounded explanations and tutoring.")
    c1, c2, c3 = st.columns(3)
    if c1.button("Explore the Digital Twin", use_container_width=True):
        _request_page("Digital Twin")
    if c2.button("Open Mode Explorer", use_container_width=True):
        _request_page("Mode Explorer")
    if c3.button("Upload Lecture Notes", use_container_width=True):
        _request_page("Lecture Notes")
    st.markdown('</div>', unsafe_allow_html=True)

    st.header("Core Capabilities")
    cards = [
        ("📄", "Lecture Notes", "Upload text-based PDFs and preserve page-level evidence."),
        ("🔬", "Digital Twin", "Explore deterministic fiber attenuation, dispersion, and FSO link budgets."),
        ("💬", "Grounded AI Tutor", "Ask questions answered from retrieved lecture-note passages."),
        ("✓", "Quiz Lab", "Practise with deterministic, locally graded optical-communication questions."),
        ("◎", "Mode Explorer", "Examine scalar LP modes, launch coupling, meridional rays, and skew rays."),
        ("ℹ", "Scientific Transparency", "See equations, assumptions, limitations, and deterministic evidence."),
    ]
    for row in (cards[:3], cards[3:]):
        cols = st.columns(3)
        for col, card in zip(cols, row, strict=True):
            with col:
                render_feature_card(*card)

    st.header("A Guided Learning Journey")
    steps = [
        (1, "Upload", "Add text-based optical-communication lecture notes."),
        (2, "Understand", "Ask grounded questions with page-level evidence."),
        (3, "Explore", "Change physical parameters in deterministic simulations."),
        (4, "Practise", "Test understanding with formative quizzes."),
        (5, "Investigate", "Explore LP modes, Gaussian coupling, and ray propagation."),
    ]
    cols = st.columns(2)
    for i, step in enumerate(steps):
        with cols[i % 2]:
            render_learning_step(*step)

    st.header("What You Can Explore")
    models = [
        ("Fiber attenuation", "Calculates dB loss and received power; useful for link-loss intuition; limited to ideal attenuation without noise."),
        ("Chromatic dispersion", "Calculates temporal broadening; useful for symbol-spreading intuition; not a full optical-field or receiver model."),
        ("Free-space optical links", "Calculates beam spreading, aperture capture, pointing loss, and atmospheric loss; omits turbulence and scintillation."),
        ("Scalar LP modes", "Solves guided weak-guidance mode families; connects V-number to fields; not full-vector FEM/BPM/FDTD."),
        ("Meridional and skew rays", "Traces geometric ray paths; useful for acceptance intuition; rays are not wave modes."),
        ("Gaussian launch coupling", "Computes overlap with displayed scalar modes; useful for alignment intuition; not an experimental power measurement."),
    ]
    for title, body in models:
        render_feature_card("•", title, body)

    render_scientific_trust_panel()
    st.header("Start Exploring")
    st.write("Start with a deterministic simulation, then use the explanations and quizzes to test your understanding.")
    if st.button("Start Exploring", type="primary"):
        _request_page("Digital Twin")
    render_footer()


@st.cache_data(show_spinner=False)
def parse_uploaded_pdf(pdf_bytes: bytes, filename: str) -> PDFDocument:
    """Extract uploaded PDF text using the parser module."""
    return extract_pdf_document(pdf_bytes=pdf_bytes, filename=filename)


def _display_empty_lecture_notes_state() -> None:
    """Render guidance for the Lecture Notes page before upload."""
    with st.container(border=True):
        st.subheader("Upload a text-based PDF to begin")
        st.write("- Supported format: text-based PDF")
        st.write("- Maximum size: 25 MiB")
        st.write("- Maximum pages: 300")
        st.write("- Scanned PDFs are not yet supported because OCR is not included.")
        st.write("- Try uploading optical communication lecture notes.")


def _format_metadata_value(value: str | None) -> str:
    """Return display text for optional PDF metadata."""
    return value if value else "Not provided"


def _download_filename(filename: str) -> str:
    """Build the extracted-text download filename from the PDF name."""
    stem = PurePath(filename).stem or "lecture_notes"
    return f"{stem}_extracted.txt"


def _fingerprint_pdf_bytes(pdf_bytes: bytes) -> str:
    """Return a deterministic fingerprint for uploaded PDF bytes."""
    return hashlib.sha256(pdf_bytes).hexdigest()


def _clear_active_lecture_notes() -> None:
    """Clear active lecture-note state and reset the upload widget generation."""
    st.session_state.pop("active_pdf_document", None)
    st.session_state.pop("active_pdf_filename", None)
    st.session_state.pop("active_pdf_fingerprint", None)
    st.session_state["tutor_messages"] = []
    current_generation = st.session_state.get("lecture_uploader_generation", 0)
    st.session_state["lecture_uploader_generation"] = current_generation + 1


def render_lecture_notes() -> None:
    """Render the lecture-note PDF extraction workflow."""
    render_page_header("Lecture Notes Workspace", "Prepare text-based optical-communication notes for grounded tutoring with page-level provenance.", eyebrow="Lecture Notes")
    st.info(
        "Files are processed in memory for this session and are not written "
        "to the project repository."
    )
    st.caption(
        "Scanned or image-only PDFs require OCR, which is not included in "
        "this milestone."
    )

    if st.session_state.pop("active_notes_cleared", False):
        st.success("Active lecture notes and tutor history were cleared for this session.")

    if "lecture_uploader_generation" not in st.session_state:
        st.session_state["lecture_uploader_generation"] = 0

    if st.button("Clear active lecture notes"):
        _clear_active_lecture_notes()
        st.session_state["active_notes_cleared"] = True
        st.rerun()

    uploader_generation = st.session_state["lecture_uploader_generation"]
    uploaded_file = st.file_uploader(
        "Upload PDF lecture notes",
        type=["pdf"],
        accept_multiple_files=False,
        help="Upload one text-based PDF. Application limit: 25 MiB and 300 pages.",
        key=f"lecture_pdf_uploader_{uploader_generation}",
    )

    if uploaded_file is None:
        _display_empty_lecture_notes_state()
        render_next_step("Next: ask grounded questions", "After uploading text-based notes, open AI Tutor for page-cited explanations.", "AI Tutor")
        render_footer()
        return

    pdf_bytes = uploaded_file.getvalue()
    try:
        with st.spinner("Extracting lecture notes..."):
            document = parse_uploaded_pdf(pdf_bytes, uploaded_file.name)
    except ValueError as error:
        st.error(str(error))
        return

    pdf_fingerprint = _fingerprint_pdf_bytes(pdf_bytes)
    previous_fingerprint = st.session_state.get("active_pdf_fingerprint")
    if previous_fingerprint != pdf_fingerprint:
        st.session_state["tutor_messages"] = []
    st.session_state["active_pdf_document"] = document
    st.session_state["active_pdf_filename"] = uploaded_file.name
    st.session_state["active_pdf_fingerprint"] = pdf_fingerprint

    st.success("Lecture notes extracted successfully.")
    st.info("This document is now available to the grounded AI Tutor for the current session.")
    st.write(f"Filename: {document.filename}")

    st.header("Document Overview")
    text_coverage_percent = 100 * document.nonempty_page_count / document.page_count
    overview_columns = st.columns(6)
    overview_metrics = [
        ("Pages", f"{document.page_count:,}"),
        ("Words", f"{document.word_count:,}"),
        ("Characters", f"{document.character_count:,}"),
        ("Nonempty Pages", f"{document.nonempty_page_count:,}"),
        ("Sparse Pages", f"{document.sparse_page_count:,}"),
        ("Text Coverage", f"{text_coverage_percent:.1f} %"),
    ]
    for column, (label, value) in zip(overview_columns, overview_metrics, strict=True):
        with column:
            st.metric(label=label, value=value)

    with st.expander("PDF Metadata"):
        st.write(f"Title: {_format_metadata_value(document.title)}")
        st.write(f"Author: {_format_metadata_value(document.author)}")
        st.write(f"Subject: {_format_metadata_value(document.subject)}")
        st.write(f"Keywords: {_format_metadata_value(document.keywords)}")
        st.write(f"Filename: {document.filename}")

    if document.is_likely_scanned:
        st.warning(
            "Little or no machine-readable text was found. The document may "
            "consist primarily of scanned images. OCR is not part of the current "
            "prototype, so the extracted text should not be used for future AI "
            "grounding unless you provide a text-based PDF."
        )

    st.header("Page Explorer")
    selected_page_number = st.number_input(
        "Select page",
        min_value=1,
        max_value=document.page_count,
        value=1,
        step=1,
    )
    selected_page = document.pages[int(selected_page_number) - 1]
    st.write(f"Page number: {selected_page.page_number}")
    st.write(f"Word count: {selected_page.word_count:,}")
    st.write(f"Character count: {selected_page.character_count:,}")
    if selected_page.is_text_sparse:
        st.warning("Text sparse")

    page_text = selected_page.text
    if not page_text:
        st.info("No machine-readable text was extracted from this page.")
    st.text_area(
        "Extracted page text",
        value=page_text,
        height=400,
        disabled=True,
    )

    with st.expander("Full Extracted Text"):
        st.text_area(
            "Full extracted text",
            value=document.full_text,
            height=450,
            disabled=True,
        )

    st.download_button(
        label="Download extracted text",
        data=document.full_text.encode("utf-8"),
        file_name=_download_filename(document.filename),
        mime="text/plain",
    )

    st.header("Study Readiness")
    if document.is_likely_scanned:
        st.warning(
            "The document has limited machine-readable text and is not yet "
            "reliable for grounded AI tutoring. A text-based PDF export is "
            "preferred."
        )
    else:
        st.success(
            "The document contains machine-readable text and is ready for the "
            "grounded AI Tutor."
        )
        st.write("- Page provenance has been preserved for future grounded answers.")
        st.write(
            "- Equations and complex layouts may still require manual verification."
        )
    render_next_step("Move to grounded tutoring", "Ask the AI Tutor questions that cite retrieved pages from these active notes.", "AI Tutor")
    render_footer()


def render_digital_twin() -> None:
    """Render the educational Digital Twin page."""
    render_page_header("Optical Communication Digital Twin", "Explore link-level behavior for optical fiber and free-space optical communication using deterministic engineering models.", eyebrow="Deterministic Simulation")
    render_scope_notice("Optical Fiber: attenuation and chromatic dispersion. Free-Space Optical: beam spreading, aperture collection, pointing, and atmospheric attenuation.", "Optical noise, receiver detection, SNR, BER, eye diagrams, turbulence, scintillation, or link availability prediction.")

    st.header("1. Simulation Controls")
    link_type = st.selectbox(
        "Link Type",
        options=["Optical Fiber", "Free-Space Optical"],
        index=0,
        key="digital_twin_link_type",
    )

    if link_type == "Free-Space Optical":
        left_column, middle_column, right_column = st.columns(3)
        with left_column:
            link_distance_km = st.slider("Link Distance (km)", 0.1, 20.0, 1.0, 0.1)
            transmitted_power_mw = st.slider("Transmitted Optical Power (mW)", 0.1, 100.0, 10.0, 0.1)
            transmitter_beam_radius_cm = st.slider("Transmitter Beam Radius (cm)", 0.1, 10.0, 2.0, 0.1)
        with middle_column:
            beam_divergence_mrad = st.slider("Beam Divergence Half-Angle (mrad)", 0.0, 10.0, 1.0, 0.1)
            receiver_aperture_diameter_cm = st.slider("Receiver Aperture Diameter (cm)", 1.0, 100.0, 20.0, 1.0)
        with right_column:
            atmospheric_attenuation_db_per_km = st.slider("Atmospheric Attenuation (dB/km)", 0.0, 100.0, 1.0, 0.1)
            pointing_offset_cm = st.slider("Pointing Offset at Receiver Plane (cm)", 0.0, 200.0, 0.0, 1.0)
        try:
            result = simulate_fso_link(
                link_distance_km=float(link_distance_km),
                transmitted_power_mw=float(transmitted_power_mw),
                transmitter_beam_radius_cm=float(transmitter_beam_radius_cm),
                beam_divergence_mrad=float(beam_divergence_mrad),
                receiver_aperture_diameter_cm=float(receiver_aperture_diameter_cm),
                atmospheric_attenuation_db_per_km=float(atmospheric_attenuation_db_per_km),
                pointing_offset_cm=float(pointing_offset_cm),
            )
        except ValueError as error:
            st.error(str(error))
            return

        first_metric_columns = st.columns(5)
        first_metric_values = [
            ("Transmitted Power", f"{result.transmitted_power_mw:.3f} mW"),
            ("Received Power", f"{result.received_power_mw:.6g} mW"),
            ("Total Link Loss", f"{result.total_link_loss_db:.3f} dB"),
            ("Remaining Optical Power", f"{result.remaining_power_percent:.3f} %"),
            ("Link Regime", result.link_regime),
        ]
        for column, (label, value) in zip(first_metric_columns, first_metric_values, strict=True):
            with column:
                st.metric(label=label, value=value)

        second_metric_columns = st.columns(5)
        second_metric_values = [
            ("Beam Radius at Receiver", f"{result.beam_radius_at_receiver_m:.6g} m"),
            ("Beam Diameter at Receiver", f"{result.beam_diameter_at_receiver_m:.6g} m"),
            ("Geometric Capture", f"{100 * result.geometric_capture_fraction:.6g} %"),
            ("Atmospheric Loss", f"{result.atmospheric_loss_db:.6g} dB"),
            ("Pointing Loss", f"{result.pointing_loss_db:.6g} dB"),
        ]
        for column, (label, value) in zip(second_metric_columns, second_metric_values, strict=True):
            with column:
                st.metric(label=label, value=value)

        st.warning(
            "This deterministic FSO model demonstrates Gaussian-beam spreading, finite "
            "receiver-aperture collection, atmospheric attenuation, and pointing-offset "
            "loss. It does not model turbulence, scintillation, receiver noise, BER, or link availability."
        )
        st.header("FSO Power Budget")
        st.plotly_chart(create_fso_power_budget_figure(result), width="stretch")
        st.header("Receiver-Plane Beam Profile")
        st.plotly_chart(create_fso_beam_profile_figure(result), width="stretch")

        st.header("Understanding Free-Space Optical Links")
        observations = build_fso_educational_observations(result)
        foundation_tab, engineering_tab, research_tab = st.tabs(["Foundation", "Engineering", "Research Perspective"])
        with foundation_tab:
            for observation in observations["foundation"]:
                st.write(f"- {observation}")
        with engineering_tab:
            st.latex(r"w_{rx} = w_0 + \theta L")
            st.latex(r"\eta_{geo} = 1 - \exp(-2 a_{rx}^2 / w_{rx}^2)")
            st.latex(r"\eta_{point} = \exp(-2 r_{offset}^2 / w_{rx}^2)")
            st.latex(r"A_{atm} = \gamma L")
            st.latex(r"P_{rx} = P_{tx}\eta_{geo}\eta_{point}10^{-A_{atm}/10}")
            st.write("- w_rx: beam radius at receiver in m; w_0: transmitter beam radius in m; theta: divergence half-angle in rad; L: distance in m or km as labelled.")
            st.write("- a_rx: receiver aperture radius in m; r_offset: lateral beam-centre displacement in m; gamma: atmospheric attenuation in dB/km.")
            st.write("- Geometric loss is caused by finite aperture capture.")
            st.write("- Atmospheric loss is caused by propagation attenuation.")
            st.write("- Pointing loss is caused by beam-centre displacement.")
            st.write("- No BER is calculated.")
            for observation in observations["engineering"]:
                st.write(f"- {observation}")
        with research_tab:
            for observation in observations["research"]:
                st.write(f"- {observation}")

        simulation_evidence = build_fso_simulation_evidence(result)
        st.session_state["latest_simulation_link_type"] = "Free-Space Optical"
        st.session_state["latest_simulation_evidence"] = simulation_evidence
    else:
        simulation_mode = st.selectbox(
            "Simulation Mode",
            options=["Attenuation Only", "Attenuation + Chromatic Dispersion"],
            index=0,
            key="digital_twin_simulation_mode",
        )
        left_column, middle_column, right_column = st.columns(3)
        with left_column:
            bit_sequence = st.text_input("Bit Sequence", value="10110010")
            bit_rate_gbps = st.slider("Bit Rate (Gbit/s)", min_value=1, max_value=100, value=10, step=1)
        with middle_column:
            transmitted_power_mw = st.slider("Transmitted Optical Power (mW)", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
            fiber_length_km = st.slider("Fiber Length (km)", min_value=0, max_value=100, value=20, step=1)
        with right_column:
            attenuation_db_per_km = st.slider("Attenuation Coefficient (dB/km)", min_value=0.10, max_value=1.00, value=0.20, step=0.05)
        dispersion_coefficient_ps_nm_km = 0.0
        spectral_width_nm = 0.0
        if simulation_mode == "Attenuation + Chromatic Dispersion":
            dispersion_column, spectral_column = st.columns(2)
            with dispersion_column:
                dispersion_coefficient_ps_nm_km = st.slider("Chromatic Dispersion Coefficient (ps/(nm·km))", -30.0, 30.0, 17.0, 0.5)
            with spectral_column:
                spectral_width_nm = st.slider("Source Spectral Width (nm)", 0.0, 5.0, 0.1, 0.01)
        try:
            result = simulate_fiber_dispersion(bit_sequence, float(bit_rate_gbps), float(transmitted_power_mw), float(fiber_length_km), float(attenuation_db_per_km), float(dispersion_coefficient_ps_nm_km), float(spectral_width_nm)) if simulation_mode == "Attenuation + Chromatic Dispersion" else simulate_fiber_attenuation(bit_sequence, float(bit_rate_gbps), float(transmitted_power_mw), float(fiber_length_km), float(attenuation_db_per_km))
        except ValueError as error:
            st.error(str(error))
            return

        metric_columns = st.columns(5)
        metric_values = [("Transmitted Power", f"{result.transmitted_power_mw:.3f} mW"), ("Received Power", f"{result.received_power_mw:.6g} mW"), ("Total Fiber Loss", f"{result.total_loss_db:.3f} dB"), ("Remaining Optical Power", f"{result.remaining_power_percent:.3f} %"), ("Bit Duration", f"{result.bit_duration_ns:.6g} ns")]
        for column, (label, value) in zip(metric_columns, metric_values, strict=True):
            with column:
                st.metric(label=label, value=value)
        if result.dispersion_enabled:
            dispersion_metric_columns = st.columns(5)
            dispersion_metric_values = [("Temporal Broadening (ps)", f"{result.temporal_broadening_ps:.6g} ps"), ("Temporal Broadening (ns)", f"{result.temporal_broadening_ns:.6g} ns"), ("Bit Duration (ns)", f"{result.bit_duration_ns:.6g} ns"), ("Broadening Ratio", f"{result.broadening_ratio:.6g}"), ("Dispersion Regime", result.dispersion_regime)]
            for column, (label, value) in zip(dispersion_metric_columns, dispersion_metric_values, strict=True):
                with column:
                    st.metric(label=label, value=value)
        st.header("Transmitted and Received NRZ/OOK Signals")
        figure = create_dispersion_comparison_figure(result) if result.dispersion_enabled else create_signal_comparison_figure(result)
        st.plotly_chart(figure, width="stretch")
        st.header("Understand the Result")
        observations = build_educational_observations(result)
        foundation_tab, engineering_tab, research_tab = st.tabs(["Foundation", "Engineering", "Research Perspective"])
        with foundation_tab:
            for observation in observations["foundation"]:
                st.write(f"- {observation}")
        with engineering_tab:
            st.latex(r"A = \alpha L")
            st.write(f"Current substitution: A = {result.attenuation_db_per_km:.2f} dB/km × {result.fiber_length_km:.0f} km = {result.total_loss_db:.3f} dB.")
            st.latex(r"T = 10^{-A/10}")
            st.write(f"Linear attenuation factor: T = {result.linear_attenuation_factor:.12g}.")
            st.latex(r"P_{rx} = P_{tx} T")
            st.write(f"Current received power: {result.transmitted_power_mw:.3f} mW × {result.linear_attenuation_factor:.12g} = {result.received_power_mw:.12g} mW.")
            st.latex(r"T_b = \frac{1}{R_b}")
            st.write(f"Current bit duration: {result.bit_duration_ns:.6g} ns.")
            for observation in observations["engineering"]:
                st.write(f"- {observation}")
        if result.dispersion_enabled:
            st.info("This model uses a deterministic Gaussian-convolution approximation to demonstrate chromatic-dispersion-induced temporal broadening. The Gaussian kernel uses finite, computationally bounded support for interactive visualization. It is not a full optical field or receiver simulation.")
            st.header("Understanding Chromatic Dispersion")
            dispersion_foundation_tab, dispersion_engineering_tab, dispersion_research_tab = st.tabs(["Foundation", "Engineering", "Research Perspective"])
            with dispersion_foundation_tab:
                st.write("- Different wavelength components travel at slightly different group velocities.")
                st.write("- Pulses spread in time, so adjacent symbols can overlap when broadening is large.")
                st.write("- Attenuation reduces pulse height; dispersion changes pulse width and shape.")
            with dispersion_engineering_tab:
                st.latex(r"\Delta t = |D| \Delta\lambda L")
                st.write("- Δt: estimated total temporal broadening.")
                st.write("- D: chromatic dispersion coefficient in ps/(nm·km).")
                st.write("- Δλ: source spectral width in nm.")
                st.write("- L: fiber length in km.")
                st.latex(r"\mathrm{Broadening\ ratio} = \frac{\Delta t}{T_b}")
                st.write("- Attenuation changes signal amplitude.")
                st.write("- Dispersion changes temporal shape.")
                st.write("- The current model does not calculate BER.")
            with dispersion_research_tab:
                st.write("- Gaussian convolution is an educational intensity-domain approximation.")
                st.write("- The model omits chirp, PMD, noise, receiver bandwidth, and nonlinear propagation.")
                st.write("- It is not a full optical field or receiver simulation.")
        with research_tab:
            st.subheader("Model assumptions")
            assumptions = ["ideal NRZ/OOK transmitter", "zero optical power for logical zero", "constant attenuation coefficient", "no connector or splice loss", "no dispersion" if not result.dispersion_enabled else "educational chromatic dispersion included", "no noise", "ideal bandwidth", "ideal detection is not modelled"]
            for assumption in assumptions:
                st.write(f"- {assumption}")
            st.subheader("Validity and limitations")
            st.write("This model is useful for:")
            for useful_case in ["verifying dB-to-linear power relationships", "studying link-loss sensitivity", "teaching attenuation", "building the first layer of a digital twin"]:
                st.write(f"- {useful_case}")
            st.write("This model is not sufficient for:")
            for limitation in ["waveform fidelity studies", "high-speed system design", "eye-diagram prediction", "BER estimation", "nonlinear-regime analysis", "experimental receiver prediction"]:
                st.write(f"- {limitation}")
            st.subheader("Research extensions")
            for extension in ["wavelength-dependent attenuation", "connector and splice loss", "chromatic dispersion", "laser chirp", "receiver responsivity", "shot and thermal noise", "OSNR", "eye diagrams", "BER estimation", "nonlinear Schrödinger equation models", "validation against laboratory measurements"]:
                st.write(f"- {extension}")
            st.subheader("Experimental connection")
            st.write("The attenuation model could be validated by launching known power from a calibrated optical source into a known fiber length, measuring input and output power with an optical power meter, and comparing the measured loss with the predicted dB loss.")
            for observation in observations["research"]:
                st.write(f"- {observation}")
        simulation_evidence = build_simulation_evidence(result)
        st.session_state["latest_simulation_link_type"] = "Optical Fiber"
        st.session_state["latest_simulation_evidence"] = simulation_evidence

    st.header("5. AI Explanation")
    st.info("Simulation values are calculated deterministically in Python. OpenAI explains the supplied results but does not calculate or modify them.")
    current_simulation_fingerprint = simulation_evidence_fingerprint(simulation_evidence)
    evidence_text = format_simulation_evidence(simulation_evidence)
    api_key = _get_openai_api_key()
    model = _get_openai_model()

    if st.button("Clear AI simulation explanation"):
        st.session_state.pop("simulation_ai_explanation", None)
        st.success("AI simulation explanation cleared.")

    if api_key is None:
        st.info("Live AI explanation is unavailable because OpenAI API access is not configured. The deterministic simulation and evidence remain fully available.")
        if _is_demo_mode_enabled():
            render_status_badge("Demo explanation", "warning")
            st.write(_build_demo_simulation_text(simulation_evidence))
            st.caption("Source: Local deterministic template. This is not a live OpenAI response.")
    else:
        with st.form("simulation_ai_explanation_form"):
            explanation_level = st.selectbox("Explanation Level", options=["Foundation", "Engineering", "Research Perspective"], index=1, key="simulation_explanation_level")
            submitted = st.form_submit_button("Explain Current Simulation")
        if submitted:
            try:
                with st.spinner("Generating an AI explanation for the current deterministic result..."):
                    explanation = generate_simulation_explanation(result=result, level=explanation_level, api_key=api_key, model=model)
                st.session_state["simulation_ai_explanation"] = {"explanation_text": explanation.explanation_text, "model": explanation.model, "level": explanation.level, "simulation_fingerprint": current_simulation_fingerprint}
            except ValueError as error:
                st.error(str(error))
            except AuthenticationError:
                st.error("The OpenAI API key was rejected. Check the app’s secret configuration.")
            except RateLimitError:
                st.error("The OpenAI API usage limit was reached. Deterministic calculations are unaffected.")
            except APIConnectionError:
                st.error("OptiLearn AI could not connect to the OpenAI API. Please try again.")
            except APIError:
                st.error("The OpenAI API could not complete the simulation explanation request.")
            except RuntimeError as error:
                st.error(str(error))

    stored_explanation = st.session_state.get("simulation_ai_explanation")
    if isinstance(stored_explanation, dict):
        if stored_explanation.get("simulation_fingerprint") == current_simulation_fingerprint:
            st.subheader("AI Simulation Explanation")
            st.write(stored_explanation.get("explanation_text", ""))
            st.caption(f"Model used: {stored_explanation.get('model', 'Unknown')}")
            st.caption(f"Explanation level: {stored_explanation.get('level', 'Unknown')}")
            with st.expander("Simulation Evidence Sent to OpenAI"):
                st.text(evidence_text)
        else:
            st.caption("Simulation parameters changed. Generate a new AI explanation for the current result.")

    render_next_step("Continue with wave and ray intuition", "For guided LP modes, launch coupling, and meridional/skew-ray propagation, open Mode Explorer.", "Mode Explorer")
    render_footer()


QUIZ_SESSION_KEYS = (
    "quiz_active_question_ids",
    "quiz_attempts",
    "quiz_topic_filter",
    "quiz_level_filter",
    "quiz_question_count",
    "quiz_started",
    "quiz_dynamic_questions",
)


def _reset_current_quiz() -> None:
    """Clear only the active quiz and latest attempts."""
    st.session_state.pop("quiz_active_question_ids", None)
    st.session_state.pop("quiz_attempts", None)
    st.session_state["quiz_started"] = False


def _clear_quiz_progress() -> None:
    """Clear all quiz-specific session keys only."""
    for key in QUIZ_SESSION_KEYS:
        st.session_state.pop(key, None)


def _question_count_limit(selection: str, available_count: int) -> int:
    """Return deterministic quiz length from selector text."""
    return available_count if selection == "All Available" else min(int(selection), available_count)


def _active_quiz_questions(question_bank: tuple[QuizQuestion, ...]) -> tuple[QuizQuestion, ...]:
    """Resolve active session question IDs against base and dynamic banks."""
    dynamic_questions = tuple(st.session_state.get("quiz_dynamic_questions", ()))
    question_by_id = {question.id: question for question in (*question_bank, *dynamic_questions)}
    return tuple(
        question_by_id[question_id]
        for question_id in st.session_state.get("quiz_active_question_ids", ())
        if question_id in question_by_id
    )


def _render_simulation_quiz_section() -> None:
    """Render deterministic quiz creation from current scalar simulation state."""
    st.header("Quiz the Current Simulation")
    latest_link_type = st.session_state.get("latest_simulation_link_type")
    latest_result = st.session_state.get("latest_simulation_evidence")
    if latest_result is None or latest_link_type not in {"Optical Fiber", "Free-Space Optical"}:
        st.info("Run a Digital Twin simulation first to create result-specific questions.")
        return

    st.write(f"Current link type: {latest_link_type}")
    if latest_link_type == "Optical Fiber":
        st.write(f"Current mode: {latest_result.simulation_mode}")
        st.write(f"Total loss: {latest_result.total_loss_db:.6g} dB")
        st.write(f"Received power: {latest_result.received_power_mw:.6g} mW")
        st.write(f"Bit duration: {latest_result.bit_duration_ns:.6g} ns")
        if latest_result.simulation_mode == "Attenuation + Chromatic Dispersion":
            st.write(f"Broadening ratio: {latest_result.broadening_ratio:.6g}")
            st.write(f"Dispersion regime: {latest_result.dispersion_regime}")
    else:
        st.write("Current mode: FSO power budget")
        st.write(f"Beam radius at receiver: {latest_result.beam_radius_at_receiver_m:.6g} m")
        st.write(f"Geometric capture: {100 * latest_result.geometric_capture_fraction:.6g} %")
        st.write(f"Received power: {latest_result.received_power_mw:.6g} mW")
        st.write(f"Link regime: {latest_result.link_regime}")

    if st.button("Create Quiz from Current Simulation"):
        questions = (
            build_fiber_result_questions(latest_result)
            if latest_link_type == "Optical Fiber"
            else build_fso_result_questions(latest_result)
        )
        st.session_state["quiz_dynamic_questions"] = questions
        st.session_state["quiz_active_question_ids"] = tuple(question.id for question in questions)
        st.session_state["quiz_attempts"] = {}
        st.session_state["quiz_topic_filter"] = "Current Simulation"
        st.session_state["quiz_level_filter"] = "Mixed"
        st.session_state["quiz_question_count"] = "All Available"
        st.session_state["quiz_started"] = True
        st.rerun()


def render_quiz() -> None:
    """Render the deterministic formative Quiz Lab."""
    render_page_header("Quiz Lab", "Test your understanding with deterministic, locally graded optical-communication questions.", eyebrow="Formative Practice")
    st.info("Quiz results are formative learning feedback, not professional certification or experimental validation.")

    question_bank = build_quiz_question_bank()
    topic_options = (ALL_TOPICS, *SUPPORTED_TOPICS)
    level_options = (ALL_LEVELS, *SUPPORTED_LEVELS)
    count_options = ("5", "10", "15", "All Available")

    control_columns = st.columns(3)
    with control_columns[0]:
        selected_topic = st.selectbox("Topic selector", options=topic_options, index=0, key="quiz_topic_selector")
    with control_columns[1]:
        selected_level = st.selectbox("Learning Level selector", options=level_options, index=0, key="quiz_level_selector")
    with control_columns[2]:
        selected_count = st.selectbox("Question Count selector", options=count_options, index=1, key="quiz_count_selector")

    filtered_questions = filter_quiz_questions(question_bank, selected_topic, selected_level)
    if st.button("Start / Refresh Quiz"):
        limit = _question_count_limit(selected_count, len(filtered_questions))
        active_questions = filtered_questions[:limit]
        st.session_state["quiz_active_question_ids"] = tuple(question.id for question in active_questions)
        st.session_state["quiz_attempts"] = {}
        st.session_state["quiz_topic_filter"] = selected_topic
        st.session_state["quiz_level_filter"] = selected_level
        st.session_state["quiz_question_count"] = selected_count
        st.session_state["quiz_started"] = True
        st.session_state.pop("quiz_dynamic_questions", None)
        st.rerun()

    reset_columns = st.columns(2)
    with reset_columns[0]:
        if st.button("Reset Current Quiz"):
            _reset_current_quiz()
            st.rerun()
    with reset_columns[1]:
        if st.button("Clear Quiz Progress"):
            _clear_quiz_progress()
            st.rerun()

    _render_simulation_quiz_section()

    if not st.session_state.get("quiz_started"):
        st.info("No quiz is active. Choose filters and select Start / Refresh Quiz to begin. Simulations and Mode Explorer remain available while you prepare.")
        render_next_step("Need a concept to practise?", "Run a Digital Twin simulation first, then create result-specific questions.", "Digital Twin")
        render_footer()
        return

    active_questions = _active_quiz_questions(question_bank)
    if not active_questions:
        st.warning("No questions are available for the selected filters.")
        return

    attempts = st.session_state.setdefault("quiz_attempts", {})
    summary = summarize_quiz_attempts(attempts)
    metric_columns = st.columns(4)
    metric_columns[0].metric("Attempted", summary.attempted_count)
    metric_columns[1].metric("Correct", summary.correct_count)
    metric_columns[2].metric("Incorrect", summary.incorrect_count)
    metric_columns[3].metric("Score", f"{summary.score_percent:.1f} %")
    st.progress(summary.attempted_count / len(active_questions))

    for index, question in enumerate(active_questions, start=1):
        with st.container(border=True):
            st.subheader(f"Question {index}")
            st.caption(f"Topic: {question.topic} | Learning level: {question.level} | Source: {question.source_label}")
            st.write(question.prompt)
            with st.form(f"quiz_form_{question.id}"):
                if question.question_type == "multiple_choice":
                    labels = [choice.text for choice in question.choices]
                    ids = [choice.id for choice in question.choices]
                    selected_text = st.radio("Choose one answer", labels, key=f"quiz_answer_{question.id}")
                    submitted_answer = ids[labels.index(selected_text)]
                elif question.question_type == "numeric":
                    submitted_answer = st.text_input("Enter numeric answer", key=f"quiz_answer_{question.id}")
                    if question.units:
                        st.caption(f"Units: {question.units}")
                else:
                    submitted_answer = st.radio("Choose one answer", ["True", "False"], key=f"quiz_answer_{question.id}")
                submitted = st.form_submit_button("Submit Answer")
            if submitted:
                attempts[question.id] = evaluate_quiz_answer(question, submitted_answer)
                st.session_state["quiz_attempts"] = attempts
                st.rerun()
            result = attempts.get(question.id)
            if result is not None:
                message = (
                    f"{result.feedback}\n\nSubmitted answer: {result.submitted_answer}\n\n"
                    f"Correct answer: {result.correct_answer_text}"
                )
                if result.is_correct:
                    st.success(message)
                else:
                    st.warning(message)

    summary = summarize_quiz_attempts(st.session_state.get("quiz_attempts", {}))
    if summary.attempted_count == len(active_questions):
        st.success("Quiz Complete")
        st.write(f"Total questions: {len(active_questions)}")
        st.write(f"Correct: {summary.correct_count}")
        st.write(f"Incorrect: {summary.incorrect_count}")
        st.write(f"Score percentage: {summary.score_percent:.1f} %")
        if summary.score_percent >= 90.0:
            st.write("Excellent understanding of the current model scope.")
        elif summary.score_percent >= 70.0:
            st.write("Good progress. Review the explanations for missed questions.")
        else:
            st.write("Continue practising with the deterministic explanations and simulations.")
        st.caption("These are formative descriptors only.")


def _build_demo_simulation_text(evidence) -> str:
    """Build a transparent local explanation from deterministic evidence."""
    mode = getattr(evidence, "simulation_mode", "FSO power budget")
    if hasattr(evidence, "total_loss_db"):
        text = (
            f"Demo explanation: the deterministic {mode} result reports {evidence.total_loss_db:.6g} dB of fiber loss, "
            f"{evidence.received_power_mw:.6g} mW received power, and {evidence.remaining_power_percent:.6g}% remaining optical power. "
            "Use the shown equations to connect the dB loss to the linear power ratio."
        )
        if getattr(evidence, "simulation_mode", "") == "Attenuation + Chromatic Dispersion":
            text += f" The local dispersion evidence reports {evidence.temporal_broadening_ps:.6g} ps broadening and a {evidence.broadening_ratio:.6g} broadening ratio."
        return text
    return (
        f"Demo explanation: the deterministic FSO result reports a {evidence.beam_radius_at_receiver_m:.6g} m beam radius at the receiver, "
        f"{100 * evidence.geometric_capture_fraction:.6g}% geometric capture, {evidence.received_power_mw:.6g} mW received power, "
        f"and the {evidence.link_regime} link regime. This local template uses only the calculated evidence above."
    )


def _get_openai_api_key() -> str | None:
    """Return the configured OpenAI API key without storing or displaying it."""
    try:
        secret_key = st.secrets["OPENAI_API_KEY"]
    except (KeyError, FileNotFoundError):
        secret_key = None
    if isinstance(secret_key, str) and secret_key.strip():
        return secret_key.strip()
    env_key = os.environ.get("OPENAI_API_KEY")
    return env_key.strip() if env_key and env_key.strip() else None


def _get_openai_model() -> str:
    """Return the configured OpenAI model name."""
    try:
        secret_model = st.secrets["OPENAI_MODEL"]
    except (KeyError, FileNotFoundError):
        secret_model = None
    if isinstance(secret_model, str) and secret_model.strip():
        return secret_model.strip()
    env_model = os.environ.get("OPENAI_MODEL")
    return env_model.strip() if env_model and env_model.strip() else "gpt-5-mini"


def _readiness_status(document: PDFDocument) -> str:
    """Summarize whether extracted text is suitable for grounded tutoring."""
    return "Limited machine-readable text" if document.is_likely_scanned else "Ready for grounded tutoring"

def _display_tutor_answer(answer) -> None:
    """Render a tutor answer and its retrieved evidence."""
    st.header("Grounded Explanation")
    st.write(answer.answer_text)
    st.caption(f"Model used: {answer.model}")
    with st.expander("Retrieved Evidence"):
        if not answer.retrieved_passages:
            st.info("No relevant lecture-note passages were retrieved.")
        for passage in answer.retrieved_passages:
            st.subheader(f"Page {passage.page_number} — {passage.chunk_id}")
            st.caption(f"Relevance score: {passage.score:.3f}")
            st.text_area(
                f"Passage text ({passage.chunk_id})",
                value=passage.text,
                height=180,
                disabled=True,
            )


def render_ai_tutor() -> None:
    """Render the grounded AI Tutor page."""
    render_page_header("Grounded AI Tutor", "Ask questions answered from retrieved passages in your active lecture notes.", eyebrow="Grounded Tutoring")
    st.info(
        "Answers are grounded in retrieved text from the uploaded PDF. PDF "
        "extraction may not perfectly preserve equations, tables, or multi-column layouts."
    )

    document = st.session_state.get("active_pdf_document")
    filename = st.session_state.get("active_pdf_filename")
    if not isinstance(document, PDFDocument):
        render_status_badge("No lecture notes loaded", "warning")
        st.info("Open Lecture Notes, upload a text-based PDF, and return to the AI Tutor. Deterministic simulations, Quiz Lab, and Mode Explorer remain available without notes.")
        render_next_step("Prepare evidence", "Upload lecture notes so answers can include page-level provenance.", "Lecture Notes")
        render_footer()
        return

    if document.is_likely_scanned:
        st.warning(
            "The active PDF has limited machine-readable text. Grounded tutoring may be unreliable. "
            "A text-based PDF export is recommended."
        )

    st.header("Active Document")
    text_coverage_percent = 100 * document.nonempty_page_count / document.page_count
    summary_columns = st.columns(5)
    summary_metrics = [
        ("Filename", filename or document.filename),
        ("Pages", f"{document.page_count:,}"),
        ("Words", f"{document.word_count:,}"),
        ("Text Coverage", f"{text_coverage_percent:.1f} %"),
        ("Readiness", _readiness_status(document)),
    ]
    for column, (label, value) in zip(summary_columns, summary_metrics, strict=True):
        with column:
            st.metric(label=label, value=value)

    api_key = _get_openai_api_key()
    model = _get_openai_model()
    if api_key is None:
        render_status_badge("API unavailable", "warning")
        st.info("Live AI tutoring is unavailable because OpenAI API access is not configured. Uploaded notes remain available in this session, and deterministic pages still work.")
        if _is_demo_mode_enabled():
            render_status_badge("Demo explanation", "warning")
            st.write("Demo tutor readiness: local templates can summarize retrieved lecture-note text only when passages are available, and they are not live OpenAI responses.")
            st.caption("Source: Local deterministic template")
        render_footer()
        return

    if "tutor_messages" not in st.session_state:
        st.session_state["tutor_messages"] = []

    with st.form("grounded_ai_tutor_form"):
        level = st.selectbox(
            "Explanation Level",
            options=["Foundation", "Engineering", "Research Perspective"],
            index=1,
        )
        question = st.text_area(
            "Question",
            placeholder="Example: Why does chromatic dispersion broaden an optical pulse?",
        )
        submitted = st.form_submit_button(
            "Ask OptiLearn AI",
            disabled=not question.strip(),
        )

    current_answer = None
    if submitted:
        try:
            normalized_question = normalize_question(question)
            with st.spinner("Retrieving lecture passages and preparing a grounded explanation..."):
                current_answer = generate_grounded_answer(
                    question=normalized_question,
                    document=document,
                    level=level,
                    api_key=api_key,
                    model=model,
                )
        except ValueError as error:
            st.error(str(error))
        except AuthenticationError:
            st.error("The OpenAI API key was rejected. Check the app’s secret configuration.")
        except RateLimitError:
            st.error("The OpenAI API rate limit or usage limit was reached. Please try again later or review API billing.")
        except APIConnectionError:
            st.error("OptiLearn AI could not connect to the OpenAI API. Please try again.")
        except APIError:
            st.error("The OpenAI API could not complete the request.")
        except RuntimeError as error:
            st.error(str(error))

    current_answer_added_to_history = False
    if current_answer is not None:
        _display_tutor_answer(current_answer)
        validated_citations = validate_answer_citations(
            current_answer.answer_text,
            current_answer.retrieved_passages,
        )
        messages = list(st.session_state.get("tutor_messages", []))
        messages.append(
            {
                "question": normalized_question,
                "level": level,
                "answer_text": current_answer.answer_text,
                "cited_page_numbers": validated_citations,
                "model": current_answer.model,
            }
        )
        st.session_state["tutor_messages"] = messages[-6:]
        current_answer_added_to_history = True

    st.header("Conversation History")
    if st.button("Clear tutor history"):
        st.session_state["tutor_messages"] = []
        st.success("Tutor history cleared.")
    history = st.session_state.get("tutor_messages", [])
    if current_answer_added_to_history:
        history = history[:-1]
    if not history:
        st.info("No completed tutor exchanges yet.")
    else:
        for index, item in enumerate(history, start=1):
            with st.expander(f"Question {index} — {item['level']}", expanded=False):
                st.write(f"Question: {item['question']}")
                st.write(item["answer_text"])
                cited_pages = item.get("cited_page_numbers", ())
                st.caption(f"Cited pages: {', '.join(str(page) for page in cited_pages) if cited_pages else 'None'}")
                st.caption(f"Model used: {item['model']}")




def _mode_explorer_presets() -> dict[str, dict[str, float]]:
    """Return deterministic Mode Explorer fiber presets."""
    return {
        "Single-Mode Example": {"wavelength_nm": 1550.0, "core_diameter_um": 8.2, "n_core": 1.450, "n_cladding": 1.444},
        "Few-Mode Example": {"wavelength_nm": 1310.0, "core_diameter_um": 15.0, "n_core": 1.450, "n_cladding": 1.444},
        "Multimode Example": {"wavelength_nm": 850.0, "core_diameter_um": 50.0, "n_core": 1.457, "n_cladding": 1.440},
    }


@st.cache_data(show_spinner=False)
def _cached_lp_modes(wavelength_nm: float, core_diameter_um: float, n_core: float, n_cladding: float, maximum_modes: int):
    """Cache deterministic scalar LP mode summaries for scalar inputs only."""
    return solve_lp_modes(wavelength_nm, core_diameter_um, n_core, n_cladding, max_modes=maximum_modes)


def render_mode_explorer() -> None:
    """Render the educational LP-mode and ray-propagation explorer."""
    render_page_header("LP-Mode and Ray-Propagation Explorer", "Connect Maxwell’s equations to scalar LP modes, Gaussian launch coupling, and geometric ray intuition.", eyebrow="Wave Optics and Ray Optics")
    st.warning("LP modes and geometric rays are complementary educational models. A ray is not an LP mode, and this prototype is not a full-vector electromagnetic solver.")

    st.header("1. From Maxwell’s Equations to LP Modes")
    with st.expander("From Maxwell to the Scalar Wave Equation", expanded=False):
        st.markdown(r"""
Source-free Maxwell equations in a linear, isotropic, nonmagnetic dielectric:

$\nabla \times E = -\mu_0 \partial H/\partial t$,  $\nabla \times H = \epsilon \partial E/\partial t$,  $\nabla \cdot (\epsilon E)=0$,  $\nabla \cdot H=0$.

For a homogeneous region and harmonic fields $E(r,t)=\mathrm{Re}\{E(r)e^{-i\omega t}\}$, the vector wave equation is $\nabla^2 E+n^2k_0^2E=0$ where $k_0=2\pi/\lambda$.

Under weak guidance, $n_1 \approx n_2$ and $\Delta=(n_1^2-n_2^2)/(2n_1^2)\ll1$, a scalar transverse field $\Psi(r,\phi,z)=\psi(r,\phi)e^{i\beta z}$ gives $\nabla_t^2\psi+(n^2k_0^2-\beta^2)\psi=0$.

For a circular step-index fiber, $n(r)=n_1$ for $r<a$ and $n(r)=n_2$ for $r\ge a$. Define $u=a\sqrt{n_1^2k_0^2-\beta^2}$, $w=a\sqrt{\beta^2-n_2^2k_0^2}$, $V^2=u^2+w^2$, $V=k_0a\sqrt{n_1^2-n_2^2}$, and $n_\mathrm{eff}=\beta/k_0$.

LP modes follow from the scalar weak-guidance approximation and are not exact full-vector HE, EH, TE, or TM modes.
""")

    st.header("2. Fiber Parameters")
    presets = _mode_explorer_presets()
    preset = st.selectbox("Fiber Preset", [*presets.keys(), "Custom"], key="mode_explorer_preset")
    defaults = presets.get(preset, presets["Single-Mode Example"])
    previous_preset = st.session_state.get("mode_explorer_previous_preset")
    if preset != "Custom" and previous_preset != preset:
        st.session_state["mode_explorer_wavelength_nm"] = defaults["wavelength_nm"]
        st.session_state["mode_explorer_core_diameter_um"] = defaults["core_diameter_um"]
        st.session_state["mode_explorer_n_core"] = defaults["n_core"]
        st.session_state["mode_explorer_n_cladding"] = defaults["n_cladding"]
    st.session_state["mode_explorer_previous_preset"] = preset
    c1, c2, c3 = st.columns(3)
    with c1:
        wavelength_nm = st.number_input("Wavelength (nm)", 400.0, 2000.0, defaults["wavelength_nm"], 10.0, key="mode_explorer_wavelength_nm")
        core_diameter_um = st.number_input("Core Diameter (µm)", 2.0, 200.0, defaults["core_diameter_um"], 0.1, key="mode_explorer_core_diameter_um")
    with c2:
        n_core = st.number_input("Core Refractive Index", 1.001, 2.5, defaults["n_core"], 0.001, format="%.6f", key="mode_explorer_n_core")
        n_cladding = st.number_input("Cladding Refractive Index", 1.001, 2.5, defaults["n_cladding"], 0.001, format="%.6f", key="mode_explorer_n_cladding")
    with c3:
        displayed_fiber_length_m = st.number_input("Displayed Fiber Length (m)", 0.01, 10.0, 1.0, 0.1, key="mode_explorer_displayed_length")
        maximum_modes = st.slider("Maximum LP Modes", 1, 30, 20, 1, key="mode_explorer_maximum_modes")

    try:
        result = _cached_lp_modes(float(wavelength_nm), float(core_diameter_um), float(n_core), float(n_cladding), int(maximum_modes))
    except ValueError as error:
        st.error(f"Mode Explorer input error: {error}")
        return

    st.header("3. Guided Mode Summary")
    metrics = st.columns(6)
    for column, (label, value) in zip(metrics, [("Numerical Aperture", f"{result.numerical_aperture:.4f}"), ("Acceptance Angle", f"{result.acceptance_angle_deg:.3f}°"), ("Critical Angle", f"{result.critical_angle_deg:.3f}°"), ("V Number", f"{result.v_number:.3f}"), ("Approx. Mode Count", f"{result.approximate_mode_count:.1f}"), ("Guided LP Families Found", str(len(result.guided_modes)))], strict=True):
        column.metric(label, value)
    st.success("Single-mode under scalar LP criterion" if result.is_single_mode else "Multimode under scalar LP criterion")
    st.caption("The V²/2 mode-count approximation is intended for large V, commonly includes polarization degeneracy, and is not exact near cutoff. LP01 remains guided while higher-order families are cut off below the first higher-order cutoff.")
    st.caption("LP01 uses a documented educational fundamental-mode approximation in this prototype; higher-order modes are included only when the scalar characteristic equation has a validated numerical root.")
    st.dataframe([{"Mode": m.label, "l": m.azimuthal_order, "m": m.radial_order, "u": m.u, "w": m.w, "n_eff": m.effective_index, "β in rad/m": m.beta_per_m, "normalized b": m.normalized_propagation_constant, "cutoff V": m.cutoff_v, "guided status": m.is_guided} for m in result.guided_modes], width="stretch")
    if not result.guided_modes:
        st.warning("No finite guided scalar LP modes were found for these inputs.")
        return

    mode_labels = [m.label for m in result.guided_modes]
    selected_label = st.selectbox("Selected LP Mode", mode_labels, index=mode_labels.index("LP01") if "LP01" in mode_labels else 0, key="mode_explorer_selected_mode")
    base_mode = next(m for m in result.guided_modes if m.label == selected_label)
    orientation = "Circularly symmetric"
    if base_mode.azimuthal_order > 0:
        orientation = st.radio("Orientation", ["cos(lφ)", "sin(lφ)"], horizontal=True, key="mode_explorer_orientation")
    selected_mode = base_mode if base_mode.orientation == orientation else type(base_mode)(**{**base_mode.__dict__, "orientation": orientation})

    st.header("4. LP Mode Cross Section")
    x_m, y_m, field = calculate_lp_mode_field(selected_mode, result)
    intensity = calculate_lp_mode_intensity(field)
    st.plotly_chart(create_lp_mode_cross_section_figure(x_m, y_m, intensity, result.core_radius_m, selected_mode.label), width="stretch")

    st.header("5. Longitudinal Mode Propagation")
    long_display = st.selectbox("Longitudinal Display", ["Field Phase", "Intensity"], key="mode_explorer_longitudinal_display")
    xs, zs, real_field, long_intensity = calculate_longitudinal_mode_slice(selected_mode, result, float(displayed_fiber_length_m))
    st.plotly_chart(create_lp_mode_longitudinal_figure(xs, zs, real_field, long_intensity, selected_mode.label, long_display), width="stretch")
    st.caption(f"Actual β = {selected_mode.beta_per_m:.6g} rad/m. The visible phase period is compressed for visualization and does not overwrite the calculated β; one ideal mode has z-invariant intensity in a uniform fiber.")

    st.header("6. Gaussian Launch and Modal Coupling")
    l1, l2, l3 = st.columns(3)
    with l1:
        beam_diameter_um = st.number_input("Launch Beam Diameter (µm)", 0.5, 200.0, float(result.core_diameter_um), 0.1, key="mode_explorer_beam_diameter")
        offset_x_um = st.number_input("Beam Offset X (µm)", -100.0, 100.0, 0.0, 0.1, key="mode_explorer_offset_x")
    with l2:
        offset_y_um = st.number_input("Beam Offset Y (µm)", -100.0, 100.0, 0.0, 0.1, key="mode_explorer_offset_y")
        launch_angle_deg = st.number_input("Launch Angle (degrees)", 0.0, 89.0, 0.0, 0.1, key="mode_explorer_launch_angle")
    with l3:
        launch_azimuth_deg = st.number_input("Launch Azimuth (degrees)", 0.0, 360.0, 0.0, 1.0, key="mode_explorer_launch_azimuth")
    st.info("Inside acceptance cone" if launch_angle_deg <= result.acceptance_angle_deg else "Outside acceptance cone")
    st.caption("Acceptance describes guided ray eligibility in this ideal model; it does not guarantee coupling only into calculated guided LP modes.")
    launch_x, launch_y, launch_field = calculate_gaussian_launch_field(result, beam_diameter_um, offset_x_um, offset_y_um, launch_angle_deg, launch_azimuth_deg)
    st.plotly_chart(create_launch_field_figure(launch_x, launch_y, launch_field, result.core_radius_m, offset_x_um, offset_y_um, launch_azimuth_deg), width="stretch")
    couplings = calculate_mode_coupling(launch_field, result.guided_modes, result, maximum_modes=min(20, maximum_modes))
    if couplings:
        st.metric("Dominant Coupled Mode", couplings[0].mode_label, f"{100 * couplings[0].coupling_fraction:.2f}%")
    st.dataframe([{"Mode": c.mode_label, "Coupling fraction": c.coupling_fraction, "Coupling percentage": 100 * c.coupling_fraction} for c in couplings], width="stretch")
    st.metric("Represented guided-mode overlap total", f"{100 * sum(c.coupling_fraction for c in couplings):.2f}%")
    st.caption("This total is the sum over the finite scalar LP modes calculated and displayed. It is not an experimental power measurement and may not include radiation or omitted higher-order modes.")
    st.plotly_chart(create_mode_coupling_figure(couplings, top_n=10), width="stretch")

    st.header("7. Meridional and Skew Rays")
    r1, r2, r3 = st.columns(3)
    with r1:
        ray_type = st.selectbox("Ray Type", ["Meridional Ray", "Skew Ray"], key="mode_explorer_ray_type")
        ray_length = st.number_input("Ray Fiber Length (m)", 0.01, 10.0, min(float(displayed_fiber_length_m), 1.0), 0.01, key="mode_explorer_ray_length")
    with r2:
        ray_angle = st.number_input("Ray Launch Angle (degrees)", 0.0, min(30.0, max(result.acceptance_angle_deg * 1.5, 1.0)), min(result.acceptance_angle_deg * 0.6, 5.0), 0.1, key="mode_explorer_ray_angle")
        ray_azimuth = st.number_input("Ray Launch Azimuth (degrees)", 0.0, 360.0, 45.0 if ray_type == "Skew Ray" else 0.0, 1.0, key="mode_explorer_ray_azimuth")
    with r3:
        radial_offset = st.slider("Radial Offset Fraction", 0.0, 0.95, 0.35 if ray_type == "Skew Ray" else 0.0, 0.01, key="mode_explorer_ray_offset")
    launch = RayLaunch(ray_type, float(ray_angle), float(ray_azimuth if ray_type == "Skew Ray" else 0.0), float(max(radial_offset, 0.05) if ray_type == "Skew Ray" else radial_offset), float(ray_length), result.core_radius_m, result.n_core, result.n_cladding)
    try:
        ray = trace_skew_ray(launch) if ray_type == "Skew Ray" else trace_meridional_ray(launch)
        st.info(ray.message)
        st.metric("Ray acceptance status", "Accepted" if ray.is_accepted else "Rejected")
        st.metric("Reflection count", ray.reflection_count)
        fig = create_skew_ray_figure(ray, result.core_radius_m) if ray_type == "Skew Ray" else create_meridional_ray_figure(ray, result.core_radius_m)
        st.plotly_chart(fig, width="stretch")
    except ValueError as error:
        st.error(f"Ray-tracing input error: {error}")

    st.header("8. Assumptions and Limitations")
    foundation_tab, engineering_tab, research_tab = st.tabs(["Foundation", "Engineering", "Research Perspective"])
    with foundation_tab:
        st.write("- The core has a slightly higher refractive index than the cladding, enabling total internal reflection for accepted rays.")
        st.write("- LP mode patterns are wave-optics standing transverse field patterns; rays are geometric paths and are not LP modes.")
        st.write("- Launch alignment, offset, and tilt change which calculated scalar modes receive overlap.")
    with engineering_tab:
        st.latex(r"uJ_l'(u)/J_l(u)=wK_l'(w)/K_l(w)")
        st.latex(r"\eta_{lm}=|\iint E_{launch}E_{lm}^*dA|^2/(\iint |E_{launch}|^2dA\,\iint |E_{lm}|^2dA)")
        st.write("- V, NA, β, n_eff, u, and w summarize guiding strength and modal phase propagation.")
        st.write("- Meridional rays cross the axis; skew rays carry azimuthal motion and avoid the axis.")
        st.write("- Cutoff values identify when higher-order scalar LP families become guided.")
    with research_tab:
        st.write("- The solver is scalar and weak-guidance only; it omits full-vector families, polarization, birefringence, perturbations, bends, nonlinearities, FEM, BPM, and FDTD.")
        st.write("- Root finding near Bessel-function poles is numerically sensitive and bounded for education.")
        st.write("- Experimental validation would use near-field imaging, interferometric phase measurements, and careful mode decomposition; future extensions could add FEM or BPM.")
    render_next_step("Test mode intuition", "Open Quiz Lab to practise concepts from deterministic fiber, FSO, mode, and ray explorations.", "Quiz Lab")
    render_footer()

def render_sidebar() -> str:
    """Render sidebar navigation and return the selected page name."""
    pages = ["Home", "Lecture Notes", "Digital Twin", "AI Tutor", "Quiz Lab", "Mode Explorer"]
    requested_page = st.session_state.pop("requested_page", None)
    if requested_page in pages:
        st.session_state["sidebar_navigation"] = requested_page
    index = pages.index(st.session_state.get("sidebar_navigation", "Home")) if st.session_state.get("sidebar_navigation", "Home") in pages else 0
    with st.sidebar:
        st.title("OptiLearn AI")
        st.caption("AI-Powered Educational Digital Twin")
        st.divider()
        page = st.radio("Navigation", options=pages, index=index, key="sidebar_navigation")
        st.caption(f"Current page: {page}")
        st.divider()
        render_status_badge("Final Build Week Prototype", "success")
        st.caption("Version: Milestone 11")
        if _is_demo_mode_enabled():
            render_status_badge("Demo Mode Enabled", "warning")
            st.caption("AI demonstrations are local templates and are not live OpenAI responses.")
        st.caption("Session-based learning tools. No persistent learner profile.")
    return page


def main() -> None:
    """Configure and route the Streamlit application."""
    st.set_page_config(
        page_title="OptiLearn AI",
        page_icon="🔬",
        layout="wide",
    )

    pages: dict[str, PageRenderer] = {
        "Home": render_home,
        "Lecture Notes": render_lecture_notes,
        "Digital Twin": render_digital_twin,
        "AI Tutor": render_ai_tutor,
        "Quiz Lab": render_quiz,
        "Mode Explorer": render_mode_explorer,
    }

    inject_global_styles()
    selected_page = render_sidebar()
    pages[selected_page]()


if __name__ == "__main__":
    main()
