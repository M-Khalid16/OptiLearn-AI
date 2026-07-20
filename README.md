# OptiLearn AI

**Version 1.0.0 — AI-Powered Educational Digital Twin for Optical Communication**

## Overview

OptiLearn AI is a Streamlit learning workspace for optical communication. It combines deterministic Python simulations, locally graded formative quizzes, optical-fiber mode visualization, PDF lecture-note preparation, and OpenAI-assisted grounded explanations when API access is configured.

## Why This Matters

Students can access more information than ever, but access alone does not create deep engineering understanding. OptiLearn AI is designed to help learners practise reasoning: inspect assumptions, change parameters, interpret plots, compare evidence, and ask grounded questions.

## Live Demo

No deployment URL is included in this repository. Run the app locally or deploy it to Streamlit Community Cloud using the instructions below.

## Core Features

- Lecture-note PDF extraction with page-level provenance.
- Fiber attenuation and received-power exploration.
- Chromatic-dispersion broadening visualization.
- Free-space optical link budget with beam spreading, collection, pointing, and atmospheric loss.
- Grounded AI Tutor using retrieved lecture-note passages when OpenAI API access is available.
- Quiz Lab with deterministic, locally graded formative questions.
- Mode Explorer for scalar LP modes, Gaussian launch coupling, meridional rays, and skew rays.

## Learning Experience

OptiLearn AI supports a progression from reading, to questioning, to modelling, to visualization, to reflection, to assessment, and to deeper investigation.

## Learning Outcomes the Platform Is Designed to Support

The platform is designed to support conceptual understanding, visual intuition, practical modelling skills, critical judgement, scientific curiosity, confidence, and lifelong-learning habits. It does not claim measured educational outcomes or replace formal assessment.

## Scientific Models

The app includes deterministic educational approximations for fiber attenuation, chromatic dispersion, FSO link budgets, scalar weak-guidance LP modes, Gaussian launch coupling, and idealized ray tracing. Model assumptions and exclusions are shown in the interface.

## Architecture

- `app.py`: Streamlit application shell and page orchestration.
- `src/optical_simulator.py`: fiber attenuation and dispersion calculations.
- `src/fso_simulator.py`: free-space optical link calculations.
- `src/lp_mode_solver.py`: scalar LP-mode calculations and coupling.
- `src/ray_tracer.py`: meridional and skew ray tracing.
- `src/quiz_engine.py`: deterministic formative quiz bank and grading.
- `src/pdf_parser.py`: PDF text extraction.
- `src/ai_tutor.py` and `src/simulation_explainer.py`: OpenAI-assisted grounded explanations.
- `src/visualizations.py`: Plotly figures.
- `src/ui_components.py`: reusable Streamlit UI polish.

## Deterministic Python versus OpenAI

Deterministic simulations do not require OpenAI. Quiz Lab does not require OpenAI. Mode Explorer does not require OpenAI. Live tutoring and live simulation explanations require OpenAI API access. ChatGPT Plus does not include API billing.

## Application Pages

- Home
- Lecture Notes
- Digital Twin
- AI Tutor
- Quiz Lab
- Mode Explorer

## Installation

### Windows

```powershell
git clone <repository-url>
cd OptiLearn-AI
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

### macOS/Linux

```bash
git clone <repository-url>
cd OptiLearn-AI
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

## Configuration

Optional environment variables or Streamlit secrets:

- `OPENAI_API_KEY`: enables live AI tutoring and explanations.
- `OPENAI_MODEL`: selects the OpenAI model for live responses.
- `OPTILEARN_DEMO_MODE`: local demo mode; enabled by `1`, `true`, `yes`, or `on`.

## Local Development

```bash
python -m py_compile app.py src/*.py
python -m tabnanny app.py
streamlit run app.py
```

## Streamlit Community Cloud Deployment

Create a Streamlit Community Cloud app pointed at this repository, set `app.py` as the entry point, and add `OPENAI_API_KEY` and `OPENAI_MODEL` only if live AI features should be enabled.

## Demo Workflow

Start on Home, run fiber attenuation, switch to chromatic dispersion, review FSO, explore LP modes and rays, answer Quiz Lab questions, then use the Grounded AI Tutor with a text-based PDF.

## Testing and Validation

Recommended checks include Python compilation, tabnanny, conflict-marker scans, Streamlit AppTest page rendering, scientific regression checks for deterministic calculators, and Streamlit startup validation.

## Privacy and Security

Uploaded PDFs are processed for the current Streamlit session. The app does not implement accounts, persistent learner profiles, telemetry, analytics, or databases. Do not commit API keys.

## Scientific Scope and Limitations

OptiLearn AI is educational software. It does not provide experimental-grade BER, SNR, turbulence, receiver, nonlinear, full-vector electromagnetic, FEM, BPM, or FDTD modelling.

## Repository Structure

See the Architecture section for the main code layout. Documentation includes `README.md`, `DEMO_SCRIPT.md`, and `SUBMISSION.md`.

## Future Extensions

Possible future work includes richer laboratory workflows, broader validated question banks, additional visual comparisons, and advanced models clearly separated from the current educational approximations.

## Hackathon Submission

This repository includes submission-ready documentation while keeping hackathon references out of the user-facing app copy.

## Author

M-Khalid16

## License

Add or update a repository license file before public release if one is not already present.
