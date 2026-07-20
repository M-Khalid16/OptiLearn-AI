# OptiLearn AI Deployment Guide

This guide prepares OptiLearn AI for Streamlit Community Cloud deployment.


## Live Deployment

https://optilearn-ai-h3dgt9c9onvohsxi2u2aa4.streamlit.app/


## Repository settings

- Repository URL: https://github.com/M-Khalid16/OptiLearn-AI
- Clone URL: https://github.com/M-Khalid16/OptiLearn-AI.git
- Default branch: `main`
- App entry point: `app.py`

## Pre-deployment checklist

Run these commands locally before deploying:

```bash
git status
git diff --check
python -m tabnanny app.py
python -m py_compile app.py src/*.py
```

Optional but recommended page-render check:

```bash
python - <<'PY'
from streamlit.testing.v1 import AppTest
pages = ("Home", "Lecture Notes", "Digital Twin", "AI Tutor", "Quiz Lab", "Mode Explorer")
for page in pages:
    at = AppTest.from_file("app.py", default_timeout=15)
    at.session_state["sidebar_navigation"] = page
    at.run()
    if at.exception:
        raise RuntimeError(f"{page} failed: {at.exception}")
    print(f"OK {page}")
PY
```

## Streamlit Community Cloud steps

1. Sign in to Streamlit Community Cloud.
2. Create a new app.
3. Choose repository `M-Khalid16/OptiLearn-AI`.
4. Choose branch `main` after the release branch is merged, or choose the reviewed branch for pre-merge validation.
5. Set the main file path to `app.py`.
6. Deploy.
7. Open the app and validate all pages: Home, Lecture Notes, Digital Twin, AI Tutor, Quiz Lab, and Mode Explorer.

## Optional secrets

OpenAI access is optional. Add secrets only if live AI features are required:

```toml
OPENAI_API_KEY = ""

OPENAI_MODEL = "your-verified-model-name"


OPENAI_MODEL = "your-verified-model-name"

OPENAI_MODEL = "ADD_VERIFIED_MODEL_NAME"


OPTILEARN_DEMO_MODE = "false"
```

Do not commit API keys or Streamlit secrets files.

## Post-deployment validation

- Confirm the deployed app opens without errors.
- Confirm sidebar navigation works across all six pages.
- Upload any small text-based PDF, or export `examples/sample_optical_notes.md` to PDF for testing.
- Run at least one deterministic Digital Twin scenario.
- Answer at least one Quiz Lab question.
- Open Mode Explorer and render a mode or ray visualization.
- If OpenAI is configured, ask one grounded AI Tutor question.
- If OpenAI is not configured, confirm AI-only features fail gracefully.


Record the final deployed URL externally as `https://optilearn-ai-h3dgt9c9onvohsxi2u2aa4.streamlit.app/` once verified.


Record the final deployed URL externally as `https://optilearn-ai-h3dgt9c9onvohsxi2u2aa4.streamlit.app/` once verified.

Record the final deployed URL externally as `ADD_DEPLOYMENT_URL` once verified.


