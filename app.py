"""Streamlit application shell for OptiLearn AI."""

from collections.abc import Callable

import streamlit as st


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
