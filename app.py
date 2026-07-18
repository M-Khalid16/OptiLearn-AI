"""Streamlit application shell for OptiLearn AI."""

from collections.abc import Callable

import streamlit as st


from src.optical_simulator import (
    build_educational_observations,
    simulate_fiber_attenuation,
)
from src.visualizations import create_signal_comparison_figure




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
            "AI Tutor",
            "Receive educational explanations that connect theory with "
            "interactive simulations.",
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

        "This Build Week prototype is under active development. The first "
        "operational optical-fiber attenuation model is now available in the "
        "Digital Twin section."

        "This Build Week prototype is under active development. Additional "
        "functionality will be added incrementally."

    )


def render_lecture_notes() -> None:
    """Render the lecture notes placeholder page."""
    st.title("Lecture Notes")
    st.write(
        "Future versions will allow students to upload optical communication "
        "lecture notes in PDF format."
    )
    st.file_uploader(
        "Upload PDF lecture notes",
        type=["pdf"],
        disabled=True,
        help="PDF upload is disabled for this milestone.",
    )
    st.info("PDF parsing will be implemented in the next milestone.")


def render_digital_twin() -> None:

    """Render the attenuation-only educational Digital Twin page."""
    st.title("Educational Digital Twin")
    st.write(
        "This is the first validated layer of the OptiLearn AI digital twin. "
        "It demonstrates binary NRZ/OOK transmission through a simplified "
        "attenuation-only optical-fiber model."
    )
    st.info(
        "This model currently includes deterministic fiber attenuation only. "
        "It does not yet include dispersion, noise, photodetection, receiver "
        "filtering, nonlinearities, or bit-error analysis."
    )

    st.header("Simulation Parameters")
    st.caption("Communication Medium: Optical Fiber")
    st.caption(
        "Free Space Optical is planned as a future extension and is not selectable."
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

    try:
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

    st.header("Transmitted and Received NRZ/OOK Signals")
    figure = create_signal_comparison_figure(result)
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

    with research_tab:
        st.subheader("Model assumptions")
        assumptions = [
            "ideal NRZ/OOK transmitter",
            "zero optical power for logical zero",
            "constant attenuation coefficient",
            "no connector or splice loss",
            "no dispersion",
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

    """Render the educational Digital Twin placeholder page."""
    st.title("Educational Digital Twin")
    st.write(
        "This page will become an interactive educational laboratory for "
        "exploring optical fiber and free-space optical communication concepts."
    )

    st.selectbox(
        "Communication Medium",
        options=["Optical Fiber", "Free Space Optical"],
        disabled=True,
    )
    st.slider("Bit Rate", min_value=1, max_value=100, value=10, disabled=True)
    st.caption("Placeholder only.")

    metric_columns = st.columns(3)
    metrics = [
        ("Received Power", "—"),
        ("Pulse Broadening", "—"),
        ("Signal Quality", "—"),
    ]

    for column, (label, value) in zip(metric_columns, metrics, strict=True):
        with column:
            st.metric(label=label, value=value)

    with st.container(border=True):
        st.header("Future Interactive Simulation")
        st.write("Interactive optical communication visualization will appear here.")



def render_ai_tutor() -> None:
    """Render the AI tutor placeholder page."""
    st.title("AI Tutor")
    st.write(
        "Future versions will provide educational explanations that connect "
        "optical communication theory with interactive Digital Twin scenarios."
    )
    st.text_area(
        "Ask a question about optical communication",
        disabled=True,
        placeholder="AI tutor questions will be enabled in a future milestone.",
    )
    st.button("Ask OptiLearn AI", disabled=True)
    st.info("OpenAI integration will be implemented in a future milestone.")


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
