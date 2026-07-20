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

from src.optical_simulator import (
    build_educational_observations,
    simulate_fiber_attenuation,
    simulate_fiber_dispersion,
)
from src.simulation_explainer import (
    build_simulation_evidence,
    format_simulation_evidence,
    generate_simulation_explanation,
    simulation_evidence_fingerprint,
)
from src.visualizations import (
    create_dispersion_comparison_figure,
    create_signal_comparison_figure,
)


PageRenderer = Callable[[], None]


def render_home() -> None:
    """Render the project overview page."""
    st.title("OptiLearn AI")
    st.subheader("AI-Powered Educational Digital Twin\nfor Optical Communication")

    st.write(
        "OptiLearn AI helps engineering students upload optical communication "
        "lecture notes, receive AI-assisted explanations for difficult "
        "concepts, interact with an educational Digital Twin, visualize optical "
        "communication behaviour, and build engineering intuition beyond "
        "memorizing equations."
    )

    columns = st.columns(3)
    features = [
        (
            "📄",
            "Learn from Notes",
            "Upload optical communication lecture notes and prepare them for "
            "AI-assisted learning.",
        ),
        (
            "🔬",
            "Interactive Digital Twin",
            "Explore optical fiber and free-space optical communication through "
            "interactive simulations.",
        ),
        (
            "🤖",
            "Grounded AI Tutor",
            "Ask questions answered from retrieved lecture-note passages with page-level evidence.",
        ),
    ]

    for column, (icon, title, description) in zip(columns, features, strict=True):
        with column:
            st.header(icon)
            st.subheader(title)
            st.write(description)

    st.divider()
    st.header("Learning Workflow")

    workflow_steps = [
        "Upload Lecture Notes",
        "↓",
        "Understand Theory",
        "↓",
        "Explore the Digital Twin",
        "↓",
        "Observe Signal Behaviour",
        "↓",
        "Develop Engineering Intuition",
    ]

    for step in workflow_steps:
        st.write(step)

    st.info(
        "This Build Week prototype is under active development. The Digital Twin "
        "now supports deterministic fiber attenuation, educational chromatic-"
        "dispersion pulse broadening, and AI explanation when API access is configured."
    )


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
    st.title("Lecture Notes")
    st.write(
        "Upload text-based optical communication lecture notes in PDF format. "
        "OptiLearn AI will extract page text and make it available to the "
        "grounded AI Tutor during the current session."
    )
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


def render_digital_twin() -> None:
    """Render the educational Digital Twin page."""
    st.title("Educational Digital Twin")
    st.write(
        "This is the first validated layer of the OptiLearn AI digital twin. "
        "It demonstrates binary NRZ/OOK transmission through a simplified "
        "optical-fiber model with selectable attenuation-only and chromatic-dispersion modes."
    )
    st.info(
        "This deterministic model can include fiber attenuation and an educational "
        "chromatic-dispersion pulse-broadening approximation. It does not include "
        "noise, photodetection, receiver filtering, nonlinearities, or bit-error analysis."
    )

    st.header("Simulation Parameters")
    st.caption("Communication Medium: Optical Fiber")
    st.caption(
        "Free Space Optical is planned as a future extension and is not selectable."
    )

    simulation_mode = st.selectbox(
        "Simulation Mode",
        options=["Attenuation Only", "Attenuation + Chromatic Dispersion"],
        index=0,
        key="digital_twin_simulation_mode",
    )

    left_column, middle_column, right_column = st.columns(3)
    with left_column:
        bit_sequence = st.text_input("Bit Sequence", value="10110010")
        bit_rate_gbps = st.slider(
            "Bit Rate (Gbit/s)",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
        )
    with middle_column:
        transmitted_power_mw = st.slider(
            "Transmitted Optical Power (mW)",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
        )
        fiber_length_km = st.slider(
            "Fiber Length (km)",
            min_value=0,
            max_value=100,
            value=20,
            step=1,
        )
    with right_column:
        attenuation_db_per_km = st.slider(
            "Attenuation Coefficient (dB/km)",
            min_value=0.10,
            max_value=1.00,
            value=0.20,
            step=0.05,
        )

    dispersion_coefficient_ps_nm_km = 0.0
    spectral_width_nm = 0.0
    if simulation_mode == "Attenuation + Chromatic Dispersion":
        dispersion_column, spectral_column = st.columns(2)
        with dispersion_column:
            dispersion_coefficient_ps_nm_km = st.slider(
                "Chromatic Dispersion Coefficient (ps/(nm·km))",
                min_value=-30.0,
                max_value=30.0,
                value=17.0,
                step=0.5,
            )
        with spectral_column:
            spectral_width_nm = st.slider(
                "Source Spectral Width (nm)",
                min_value=0.0,
                max_value=5.0,
                value=0.1,
                step=0.01,
            )

    try:
        if simulation_mode == "Attenuation + Chromatic Dispersion":
            result = simulate_fiber_dispersion(
                bit_sequence=bit_sequence,
                bit_rate_gbps=float(bit_rate_gbps),
                transmitted_power_mw=float(transmitted_power_mw),
                fiber_length_km=float(fiber_length_km),
                attenuation_db_per_km=float(attenuation_db_per_km),
                dispersion_coefficient_ps_nm_km=float(dispersion_coefficient_ps_nm_km),
                spectral_width_nm=float(spectral_width_nm),
            )
        else:
            result = simulate_fiber_attenuation(
                bit_sequence=bit_sequence,
                bit_rate_gbps=float(bit_rate_gbps),
                transmitted_power_mw=float(transmitted_power_mw),
                fiber_length_km=float(fiber_length_km),
                attenuation_db_per_km=float(attenuation_db_per_km),
            )
    except ValueError as error:
        st.error(str(error))
        return

    metric_columns = st.columns(5)
    metric_values = [
        ("Transmitted Power", f"{result.transmitted_power_mw:.3f} mW"),
        ("Received Power", f"{result.received_power_mw:.6g} mW"),
        ("Total Fiber Loss", f"{result.total_loss_db:.3f} dB"),
        ("Remaining Optical Power", f"{result.remaining_power_percent:.3f} %"),
        ("Bit Duration", f"{result.bit_duration_ns:.6g} ns"),
    ]

    for column, (label, value) in zip(metric_columns, metric_values, strict=True):
        with column:
            st.metric(label=label, value=value)

    if result.dispersion_enabled:
        dispersion_metric_columns = st.columns(5)
        dispersion_metric_values = [
            ("Temporal Broadening (ps)", f"{result.temporal_broadening_ps:.6g} ps"),
            ("Temporal Broadening (ns)", f"{result.temporal_broadening_ns:.6g} ns"),
            ("Bit Duration (ns)", f"{result.bit_duration_ns:.6g} ns"),
            ("Broadening Ratio", f"{result.broadening_ratio:.6g}"),
            ("Dispersion Regime", result.dispersion_regime),
        ]
        for column, (label, value) in zip(dispersion_metric_columns, dispersion_metric_values, strict=True):
            with column:
                st.metric(label=label, value=value)

    st.header("Transmitted and Received NRZ/OOK Signals")
    figure = (
        create_dispersion_comparison_figure(result)
        if result.dispersion_enabled
        else create_signal_comparison_figure(result)
    )
    st.plotly_chart(figure, width="stretch")

    st.header("Understand the Result")
    observations = build_educational_observations(result)
    foundation_tab, engineering_tab, research_tab = st.tabs(
        ["Foundation", "Engineering", "Research Perspective"]
    )

    with foundation_tab:
        for observation in observations["foundation"]:
            st.write(f"- {observation}")

    with engineering_tab:
        st.latex(r"A = \alpha L")
        st.write(
            f"Current substitution: A = {result.attenuation_db_per_km:.2f} "
            f"dB/km × {result.fiber_length_km:.0f} km = "
            f"{result.total_loss_db:.3f} dB."
        )
        st.latex(r"T = 10^{-A/10}")
        st.write(
            f"Linear attenuation factor: "
            f"T = {result.linear_attenuation_factor:.12g}."
        )
        st.latex(r"P_{rx} = P_{tx} T")
        st.write(
            f"Current received power: {result.transmitted_power_mw:.3f} mW × "
            f"{result.linear_attenuation_factor:.12g} = "
            f"{result.received_power_mw:.12g} mW."
        )
        st.latex(r"T_b = \frac{1}{R_b}")
        st.write(f"Current bit duration: {result.bit_duration_ns:.6g} ns.")
        for observation in observations["engineering"]:
            st.write(f"- {observation}")

    if result.dispersion_enabled:
        st.info(
            "This model uses a deterministic Gaussian-convolution approximation to "
            "demonstrate chromatic-dispersion-induced temporal broadening. The Gaussian "
            "kernel uses finite, computationally bounded support for interactive "
            "visualization. It is not a full optical field or receiver simulation."
        )
        st.header("Understanding Chromatic Dispersion")
        dispersion_foundation_tab, dispersion_engineering_tab, dispersion_research_tab = st.tabs(
            ["Foundation", "Engineering", "Research Perspective"]
        )
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
        assumptions = [
            "ideal NRZ/OOK transmitter",
            "zero optical power for logical zero",
            "constant attenuation coefficient",
            "no connector or splice loss",
            "no dispersion" if not result.dispersion_enabled else "educational chromatic dispersion included",
            "no noise",
            "ideal bandwidth",
            "ideal detection is not modelled",
        ]
        for assumption in assumptions:
            st.write(f"- {assumption}")

        st.subheader("Validity and limitations")
        st.write("This model is useful for:")
        useful_cases = [
            "verifying dB-to-linear power relationships",
            "studying link-loss sensitivity",
            "teaching attenuation",
            "building the first layer of a digital twin",
        ]
        for useful_case in useful_cases:
            st.write(f"- {useful_case}")

        st.write("This model is not sufficient for:")
        limitations = [
            "waveform fidelity studies",
            "high-speed system design",
            "eye-diagram prediction",
            "BER estimation",
            "nonlinear-regime analysis",
            "experimental receiver prediction",
        ]
        for limitation in limitations:
            st.write(f"- {limitation}")

        st.subheader("Research extensions")
        extensions = [
            "wavelength-dependent attenuation",
            "connector and splice loss",
            "chromatic dispersion",
            "laser chirp",
            "receiver responsivity",
            "shot and thermal noise",
            "OSNR",
            "eye diagrams",
            "BER estimation",
            "nonlinear Schrödinger equation models",
            "validation against laboratory measurements",
        ]
        for extension in extensions:
            st.write(f"- {extension}")

        st.subheader("Experimental connection")
        st.write(
            "The attenuation model could be validated by launching known power "
            "from a calibrated optical source into a known fiber length, measuring "
            "input and output power with an optical power meter, and comparing the "
            "measured loss with the predicted dB loss."
        )
        for observation in observations["research"]:
            st.write(f"- {observation}")

    st.header("AI Explanation of This Simulation")
    st.info(
        "Simulation values are calculated deterministically in Python. "
        "OpenAI explains the supplied results but does not calculate or modify them."
    )
    simulation_evidence = build_simulation_evidence(result)
    current_simulation_fingerprint = simulation_evidence_fingerprint(simulation_evidence)
    evidence_text = format_simulation_evidence(simulation_evidence)
    api_key = _get_openai_api_key()
    model = _get_openai_model()

    if st.button("Clear AI simulation explanation"):
        st.session_state.pop("simulation_ai_explanation", None)
        st.success("AI simulation explanation cleared.")

    if api_key is None:
        st.warning("OpenAI API access is not configured for AI simulation explanations.")
        st.write(
            "Add OPENAI_API_KEY to Streamlit Community Cloud app secrets. "
            "The deterministic Digital Twin remains fully operational without it."
        )
    else:
        with st.form("simulation_ai_explanation_form"):
            explanation_level = st.selectbox(
                "Explanation Level",
                options=["Foundation", "Engineering", "Research Perspective"],
                index=1,
                key="simulation_explanation_level",
            )
            submitted = st.form_submit_button("Explain Current Simulation")

        if submitted:
            try:
                with st.spinner("Generating an AI explanation for the current deterministic result..."):
                    explanation = generate_simulation_explanation(
                        result=result,
                        level=explanation_level,
                        api_key=api_key,
                        model=model,
                    )
                st.session_state["simulation_ai_explanation"] = {
                    "explanation_text": explanation.explanation_text,
                    "model": explanation.model,
                    "level": explanation.level,
                    "simulation_fingerprint": current_simulation_fingerprint,
                }
            except ValueError as error:
                st.error(str(error))
            except AuthenticationError:
                st.error("The OpenAI API key was rejected. Check the app’s secret configuration.")
            except RateLimitError:
                st.error("The OpenAI API rate limit or usage limit was reached. Please try again later or review API billing.")
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
            st.caption(
                "Simulation parameters changed. Generate a new AI explanation for the current result."
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
    st.title("Grounded AI Tutor")
    st.write(
        "Ask questions about the active lecture notes. OptiLearn AI retrieves "
        "relevant page passages before requesting an explanation from OpenAI."
    )
    st.info(
        "Answers are grounded in retrieved text from the uploaded PDF. PDF "
        "extraction may not perfectly preserve equations, tables, or multi-column layouts."
    )

    document = st.session_state.get("active_pdf_document")
    filename = st.session_state.get("active_pdf_filename")
    if not isinstance(document, PDFDocument):
        st.warning("No active lecture notes are available.")
        st.write("Open Lecture Notes, upload a text-based PDF, and return to the AI Tutor.")
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
        st.error("OpenAI API access is not configured for this deployment.")
        st.write("Add OPENAI_API_KEY to Streamlit Community Cloud app secrets. Do not place the key in GitHub.")
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


def render_sidebar() -> str:
    """Render sidebar navigation and return the selected page name."""
    with st.sidebar:
        st.title("OptiLearn AI")
        st.caption("Educational Digital Twin")
        st.divider()
        page = st.radio(
            "Navigation",
            options=["Home", "Lecture Notes", "Digital Twin", "AI Tutor"],
        )
        st.divider()
        st.caption("OpenAI Build Week Hackathon Prototype")

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
    }

    selected_page = render_sidebar()
    pages[selected_page]()


if __name__ == "__main__":
    main()
